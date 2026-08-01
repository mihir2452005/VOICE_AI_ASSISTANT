"""Smart Project Builder — interactive, asks questions before building.

Instead of generating blindly, Nova:
1. Detects the project type from your request
2. Asks clarifying questions (via voice!)
3. Suggests features you might want
4. Creates the project based on your answers

Example flow:
    You: "Create a website"
    Nova: "What kind of website? Portfolio, landing page, blog, or something else?"
    You: "Portfolio"
    Nova: "Got it! Should I include: about page, projects section, contact form, dark mode?"
    You: "Yes all of them"
    Nova: "Building your portfolio with 5 pages..."
    [generates everything]

Usage:
    from smart_builder import SmartBuilder
    builder = SmartBuilder(speak_fn, listen_fn)
    result = builder.handle("create a website")
"""

import os
import sys
import re
import time
from typing import Optional, Callable

import requests


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
PROJECTS_DIR = "generated_projects"

# Project type templates with suggested features
PROJECT_TEMPLATES = {
    "portfolio": {
        "description": "Personal portfolio showcasing your work",
        "default_pages": ["home", "about", "projects", "contact"],
        "suggestions": [
            "Dark mode toggle",
            "Animated sections",
            "Skills progress bars",
            "Project gallery with filters",
            "Social media links",
            "Downloadable resume",
        ],
        "questions": [
            "What's your name and profession?",
            "Want dark mode and animations?",
        ],
    },
    "landing": {
        "description": "Marketing landing page for a product/service",
        "default_pages": ["home"],
        "suggestions": [
            "Hero section with CTA button",
            "Features/benefits section",
            "Testimonials",
            "Pricing table",
            "FAQ accordion",
            "Newsletter signup",
        ],
        "questions": [
            "What product or service is this for?",
            "Want pricing section and testimonials?",
        ],
    },
    "blog": {
        "description": "Blog or article website",
        "default_pages": ["home", "about", "post"],
        "suggestions": [
            "Article cards with images",
            "Categories/tags",
            "Search functionality",
            "Dark mode",
            "Reading time estimate",
            "Share buttons",
        ],
        "questions": [
            "What topic is the blog about?",
            "Want categories and search?",
        ],
    },
    "dashboard": {
        "description": "Admin dashboard with charts and data",
        "default_pages": ["home", "analytics", "settings"],
        "suggestions": [
            "Sidebar navigation",
            "Charts and graphs",
            "Data tables",
            "Dark theme",
            "User profile section",
            "Notifications panel",
        ],
        "questions": [
            "What kind of data will it show?",
            "Want charts, tables, or both?",
        ],
    },
    "ecommerce": {
        "description": "Online store / product listing",
        "default_pages": ["home", "products", "cart", "contact"],
        "suggestions": [
            "Product grid with filters",
            "Shopping cart",
            "Product detail modal",
            "Search bar",
            "Category navigation",
            "Checkout form",
        ],
        "questions": [
            "What kind of products?",
            "Want cart and checkout?",
        ],
    },
    "webapp": {
        "description": "Interactive web application",
        "default_pages": ["home"],
        "suggestions": [
            "Login/signup form",
            "User dashboard",
            "Settings page",
            "API integration",
            "Real-time updates",
            "Mobile responsive",
        ],
        "questions": [
            "What should the app do?",
            "Want login system and user profiles?",
        ],
    },
}

# Triggers for smart builder
_TRIGGERS = [
    "create a website", "build a website", "make a website",
    "create a site", "build a site", "make me a site",
    "create a web app", "build an app", "make an app",
    "create a page", "build a page",
    "create a project", "start a project",
]


class SmartBuilder:
    """Interactive project builder that asks questions before creating.

    Args:
        speak_fn: Function to speak text aloud (blocks until done)
        listen_fn: Function to record audio and return transcribed text
    """

    def __init__(self, speak_fn: Callable, listen_fn: Callable):
        self._speak = speak_fn
        self._listen = listen_fn
        self._context = {}  # Stores conversation context for current build

    def handle(self, text: str) -> Optional[str]:
        """Handle a project creation request with interactive questioning.

        Returns final result string or None if not a build request.
        """
        text_lower = text.lower().strip()
        if not any(t in text_lower for t in _TRIGGERS):
            return None

        # Step 1: Detect project type
        project_type = self._detect_type(text)

        if not project_type:
            # Ask what type they want
            project_type = self._ask_project_type()
            if not project_type:
                return "No problem, let me know when you're ready to build something."

        template = PROJECT_TEMPLATES[project_type]
        print(f"\n  📋 Project type: {template['description']}")
        sys.stdout.flush()

        # Step 2: Ask clarifying questions
        self._speak(f"Creating a {project_type} website. Let me ask a few quick questions.")
        answers = self._ask_questions(template)

        # Step 3: Suggest features and get confirmation
        features = self._suggest_features(template)

        # Step 4: Build the project
        self._speak("Perfect! Building your project now. This will take about a minute.")
        result = self._build_project(project_type, template, answers, features)

        return result

    def _detect_type(self, text: str) -> Optional[str]:
        """Detect project type from the initial request."""
        text_lower = text.lower()
        type_keywords = {
            "portfolio": ["portfolio", "personal site", "my website", "showcase"],
            "landing": ["landing page", "marketing", "product page", "startup"],
            "blog": ["blog", "articles", "writing", "posts"],
            "dashboard": ["dashboard", "admin", "analytics", "panel"],
            "ecommerce": ["store", "shop", "ecommerce", "products", "sell"],
            "webapp": ["web app", "webapp", "application", "tool"],
        }
        for ptype, keywords in type_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return ptype
        return None

    def _ask_project_type(self) -> Optional[str]:
        """Ask the user what type of project they want."""
        options = "portfolio, landing page, blog, dashboard, store, or web app"
        self._speak(f"What kind of website? Options are: {options}")

        response = self._listen()
        if not response:
            return None

        return self._detect_type(response) or "portfolio"  # Default to portfolio

    def _ask_questions(self, template: dict) -> dict:
        """Ask clarifying questions and collect answers."""
        answers = {}

        for i, question in enumerate(template.get("questions", [])):
            print(f"  ❓ {question}")
            sys.stdout.flush()
            self._speak(question)

            answer = self._listen()
            if answer:
                answers[f"q{i}"] = answer
                print(f"  ✅ Got: {answer}")
                sys.stdout.flush()
            else:
                answers[f"q{i}"] = "yes"  # Default to yes if no response

        return answers

    def _suggest_features(self, template: dict) -> list[str]:
        """Suggest features and ask which ones to include."""
        suggestions = template.get("suggestions", [])[:4]  # Top 4

        if not suggestions:
            return template.get("default_pages", ["home"])

        feature_list = ", ".join(suggestions)
        self._speak(f"I suggest adding: {feature_list}. Should I include all of these?")

        response = self._listen()
        if not response:
            return suggestions  # Include all by default

        resp_lower = response.lower()
        if any(w in resp_lower for w in ["yes", "yeah", "all", "sure", "go ahead"]):
            print("  ✅ Including all suggested features")
            sys.stdout.flush()
            return suggestions
        elif any(w in resp_lower for w in ["no", "nah", "skip", "basic"]):
            print("  ⚡ Keeping it minimal")
            sys.stdout.flush()
            return []
        else:
            # Try to figure out what they want
            selected = [s for s in suggestions if any(w in resp_lower for w in s.lower().split())]
            return selected if selected else suggestions


    def _build_project(self, project_type: str, template: dict,
                       answers: dict, features: list[str]) -> str:
        """Actually generate the project files."""
        # Combine all context into a rich prompt
        context = (
            f"Project type: {project_type} - {template['description']}\n"
            f"Pages: {', '.join(template.get('default_pages', ['home']))}\n"
            f"Features to include: {', '.join(features)}\n"
            f"User preferences: {'; '.join(answers.values())}\n"
        )

        project_name = f"{project_type}_{time.strftime('%H%M%S')}"
        project_path = os.path.join(PROJECTS_DIR, project_name)
        os.makedirs(project_path, exist_ok=True)

        files_created = []

        # Generate index.html
        print("  [1/3] Creating HTML...", end=" ")
        sys.stdout.flush()
        html = self._gen_code(
            f"Create index.html for:\n{context}\n"
            f"Include navigation links to: {', '.join(template.get('default_pages', []))}\n"
            f"Link to style.css and script.js. Modern HTML5. Responsive.",
            800
        )
        if html:
            self._save(project_path, "index.html", html)
            files_created.append("index.html")
            print("✓")
        else:
            print("✗")
        sys.stdout.flush()

        # Generate CSS
        print("  [2/3] Creating CSS...", end=" ")
        sys.stdout.flush()
        css = self._gen_code(
            f"Create style.css for a {project_type} website.\n"
            f"Features: {', '.join(features)}\n"
            f"Modern, responsive, clean. Include animations if requested.",
            600
        )
        if css:
            self._save(project_path, "style.css", css)
            files_created.append("style.css")
            print("✓")
        else:
            print("✗")
        sys.stdout.flush()

        # Generate JS
        print("  [3/3] Creating JS...", end=" ")
        sys.stdout.flush()
        js = self._gen_code(
            f"Create script.js for a {project_type} website.\n"
            f"Include: smooth scroll, mobile menu toggle, "
            f"and any interactivity for: {', '.join(features)}",
            400
        )
        if js:
            self._save(project_path, "script.js", js)
            files_created.append("script.js")
            print("✓")
        else:
            self._save(project_path, "script.js",
                      "// Nova generated\ndocument.addEventListener('DOMContentLoaded', () => {\n  console.log('Ready');\n});\n")
            files_created.append("script.js")
            print("✓ (basic)")
        sys.stdout.flush()

        # Generate extra pages
        for page in template.get("default_pages", [])[1:]:  # Skip 'home'
            print(f"  [+] Creating {page}.html...", end=" ")
            sys.stdout.flush()
            page_html = self._gen_code(
                f"Create {page}.html for a {project_type} website.\n"
                f"Context: {context}\n"
                f"Link to style.css and script.js. Same nav as index.",
                600
            )
            if page_html:
                self._save(project_path, f"{page}.html", page_html)
                files_created.append(f"{page}.html")
                print("✓")
            else:
                print("✗")
            sys.stdout.flush()

        # Show results
        print(f"\n  📁 Project: {project_path}/")
        for f in sorted(files_created):
            print(f"     └── {f}")
        sys.stdout.flush()

        # Auto-open
        index = os.path.abspath(os.path.join(project_path, "index.html"))
        try:
            import webbrowser
            webbrowser.open(f"file:///{index.replace(os.sep, '/')}")
            print("  🌐 Opened in browser!")
        except Exception:
            pass
        sys.stdout.flush()

        return f"Done! Created {project_type} site with {len(files_created)} files. Check your browser!"

    def _gen_code(self, prompt: str, max_tokens: int = 600) -> str:
        """Generate code via Ollama."""
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": "Output ONLY code. No explanations. No markdown formatting unless it's a code block."},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": 0.2},
                },
                timeout=120,
            )
            if r.status_code == 200:
                content = r.json().get("message", {}).get("content", "")
                # Extract from code block if present
                match = re.search(r"```\w*\n(.*?)```", content, re.DOTALL)
                return match.group(1).strip() if match else content.strip()
            return ""
        except Exception:
            return ""

    def _save(self, path: str, filename: str, content: str) -> None:
        """Save a file."""
        filepath = os.path.join(path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
