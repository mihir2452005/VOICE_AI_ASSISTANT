"""Multi-File Project Generator — create full websites/apps by voice.

Say: "Create a full website with home, about, and contact pages"
     "Build a portfolio website with dark theme"
     "Make a todo app with HTML CSS and JavaScript"

Generates proper folder structure with linked files:
- index.html (with navigation to all pages)
- style.css (shared stylesheet)
- script.js (shared interactivity)
- Additional pages (about.html, contact.html, etc.)

Auto-opens in browser after generation.

Usage:
    from multi_file_gen import handle_multi_file
    result = handle_multi_file("create a website with home about contact pages")
    if result: speak(result)
"""

import os
import sys
import re
import time
import json
from typing import Optional

import requests


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
PROJECTS_DIR = "generated_projects"

_TRIGGERS = [
    "create a full website", "create a website", "build a website",
    "make a website", "generate a website", "create a full app",
    "multi page", "multiple pages", "with pages",
    "with home", "with html css", "html css js",
    "build a full", "create a portfolio site",
]


def handle_multi_file(text: str) -> Optional[str]:
    """Generate a multi-file website/app project.

    Returns summary string or None if not a multi-file request.
    """
    text_lower = text.lower()

    if not any(t in text_lower for t in _TRIGGERS):
        return None

    # Extract project name from request
    project_name = _extract_project_name(text)

    print(f"🏗️ Building project: {project_name}")
    print("  Generating multiple files (this may take 1-2 minutes)...")
    sys.stdout.flush()

    start = time.perf_counter()

    # Generate files step by step (more reliable than one-shot JSON)
    files = {}

    # Step 1: Generate HTML structure
    print("  [1/3] Creating HTML...", end=" ")
    sys.stdout.flush()
    html = _generate_file(text, "html", project_name)
    if html:
        files["index.html"] = html
        print("✓")
    else:
        print("✗")
    sys.stdout.flush()

    # Step 2: Generate CSS
    print("  [2/3] Creating CSS...", end=" ")
    sys.stdout.flush()
    css = _generate_css(text, html)
    if css:
        files["style.css"] = css
        print("✓")
    else:
        print("✗")
    sys.stdout.flush()

    # Step 3: Generate JS (if needed)
    print("  [3/3] Creating JS...", end=" ")
    sys.stdout.flush()
    js = _generate_js(text, html)
    if js:
        files["script.js"] = js
        print("✓")
    else:
        files["script.js"] = "// Nova generated\nconsole.log('Page loaded');\n"
        print("✓ (minimal)")
    sys.stdout.flush()

    # Detect additional pages
    extra_pages = _detect_pages(text)
    for page in extra_pages:
        print(f"  [+] Creating {page}.html...", end=" ")
        sys.stdout.flush()
        page_html = _generate_page(page, text, project_name)
        if page_html:
            files[f"{page}.html"] = page_html
            print("✓")
        else:
            print("✗")
        sys.stdout.flush()

    if not files:
        return "Couldn't generate project files. Try a simpler description."

    # Save all files
    project_path = os.path.join(PROJECTS_DIR, project_name)
    os.makedirs(project_path, exist_ok=True)

    for filename, content in files.items():
        filepath = os.path.join(project_path, filename)
        # Auto-lint before saving
        try:
            from auto_lint import lint_and_fix
            ext = os.path.splitext(filename)[1].lstrip(".")
            lang_map = {"py": "python", "html": "html", "htm": "html",
                        "js": "javascript", "css": "css"}
            lang = lang_map.get(ext, ext)
            content = lint_and_fix(content, lang)
        except ImportError:
            pass
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    elapsed = time.perf_counter() - start

    # Display result
    print(f"\n  📁 Project: {project_path}/")
    for f in sorted(files.keys()):
        size = len(files[f])
        print(f"     └── {f} ({size} chars)")
    print(f"  ⏱️ Generated in {elapsed:.0f}s")
    sys.stdout.flush()

    # Auto-open in browser
    index_path = os.path.abspath(os.path.join(project_path, "index.html"))
    try:
        import webbrowser
        webbrowser.open(f"file:///{index_path.replace(os.sep, '/')}")
        print("  🌐 Opened in browser!")
    except Exception:
        pass
    sys.stdout.flush()

    return f"Created {project_name} with {len(files)} files. Opened in browser."


def _extract_project_name(text: str) -> str:
    """Extract a project folder name from the request."""
    text_lower = text.lower()
    # Common patterns
    for pattern in [r"called (\w+)", r"named (\w+)", r"portfolio", r"todo", r"blog"]:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    # Default from keywords
    if "portfolio" in text_lower:
        return "portfolio"
    if "todo" in text_lower or "task" in text_lower:
        return "todo_app"
    if "blog" in text_lower:
        return "blog"
    if "landing" in text_lower:
        return "landing_page"
    return f"website_{time.strftime('%H%M%S')}"


def _detect_pages(text: str) -> list[str]:
    """Detect which additional pages the user wants."""
    text_lower = text.lower()
    pages = []
    page_keywords = {
        "about": ["about", "about us", "about me"],
        "contact": ["contact", "contact us", "get in touch"],
        "services": ["services", "what we do"],
        "projects": ["projects", "portfolio", "work"],
        "blog": ["blog", "articles", "posts"],
    }
    for page, keywords in page_keywords.items():
        if any(kw in text_lower for kw in keywords):
            pages.append(page)
    return pages


def _ask_ollama(prompt: str, max_tokens: int = 800) -> str:
    """Send prompt to Ollama for code generation."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a web developer. Output ONLY code inside a ``` block. No explanations."},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.2},
            },
            timeout=120,
        )
        if r.status_code == 200:
            content = r.json().get("message", {}).get("content", "")
            # Extract code block
            match = re.search(r"```\w*\n(.*?)```", content, re.DOTALL)
            if match:
                return match.group(1).strip()
            return content.strip()
        return ""
    except Exception:
        return ""


def _generate_file(description: str, file_type: str, project_name: str) -> str:
    """Generate main HTML file."""
    prompt = (
        f"Create a complete index.html for: {description}\n\n"
        f"Requirements:\n"
        f"- Link to style.css and script.js\n"
        f"- Include navigation with links to other pages\n"
        f"- Responsive design with viewport meta tag\n"
        f"- Modern HTML5 structure\n"
        f"- Title: {project_name}\n"
        f"Output only the HTML code."
    )
    return _ask_ollama(prompt, 800)


def _generate_css(description: str, html: str) -> str:
    """Generate CSS stylesheet."""
    prompt = (
        f"Create a complete style.css for this website: {description}\n\n"
        f"Requirements:\n"
        f"- Modern, clean design\n"
        f"- Responsive (mobile-friendly)\n"
        f"- Navigation styling\n"
        f"- Smooth transitions/animations\n"
        f"- Good typography and spacing\n"
        f"- Color palette that matches the theme\n"
        f"Output only the CSS code."
    )
    return _ask_ollama(prompt, 600)


def _generate_js(description: str, html: str) -> str:
    """Generate JavaScript file."""
    prompt = (
        f"Create a script.js for this website: {description}\n\n"
        f"Requirements:\n"
        f"- Smooth scroll for navigation links\n"
        f"- Mobile menu toggle\n"
        f"- Any interactive features the site needs\n"
        f"- Keep it simple and working\n"
        f"Output only the JavaScript code."
    )
    return _ask_ollama(prompt, 400)


def _generate_page(page_name: str, description: str, project_name: str) -> str:
    """Generate an additional HTML page."""
    prompt = (
        f"Create {page_name}.html for: {description}\n\n"
        f"Requirements:\n"
        f"- Same navigation as index.html\n"
        f"- Link to style.css and script.js\n"
        f"- Content appropriate for a '{page_name}' page\n"
        f"- Title: {page_name.title()} - {project_name}\n"
        f"Output only the HTML code."
    )
    return _ask_ollama(prompt, 600)
