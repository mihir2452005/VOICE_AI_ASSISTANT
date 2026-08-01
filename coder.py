"""Code Generator — write, explain, fix, and ITERATE on code by voice.

Say things like:
- "Write a Python function to sort a list"
- "Write a Flask hello world app"
- "Explain what a decorator is"
- "Fix this code: def add(a b): return a + b"
- "Improve it" / "Make it better" / "Add dark mode"  ← ITERATIVE REFINEMENT
- "Make the buttons bigger" / "Change color to blue"

Generated code is:
1. Displayed in terminal
2. Copied to clipboard (ready to paste)
3. Saved to generated_code/ folder
4. Tracked for iteration — say "improve it" to refine the last generation

Usage from main.py:
    from coder import handle_code_request
    result = handle_code_request("write a python function to reverse a string")
    if result:
        speak(result["summary"])
"""

import os
import re
import sys
import json
import time
from typing import Optional

import requests


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

# Track last generation for iteration
_last_generated = {
    "code": "",
    "language": "",
    "file": "",
    "request": "",
}

# Patterns that trigger code generation
_CODE_TRIGGERS = [
    "write a", "write me a", "create a", "generate a", "make a",
    "write code", "code for", "write a function", "write a script",
    "write a class", "write a program", "give me code",
    "how to code", "write python", "write html", "write javascript",
    "write css", "write sql", "write a query",
]

# Patterns for iterative refinement (modifying last generated code)
_ITERATE_TRIGGERS = [
    "improve it", "make it better", "iterate", "refine it",
    "change it", "modify it", "update it", "fix it",
    "add to it", "make the", "change the", "add a",
    "remove the", "bigger", "smaller", "more",
    "different color", "change color", "add animation",
    "add dark mode", "make it responsive", "add a button",
    "continue", "keep going", "same thing",
]

# Patterns for code explanation
_EXPLAIN_TRIGGERS = [
    "explain this code", "explain what", "what does this code",
    "how does this work", "explain the code", "what is a",
]

# Patterns for code fixing
_FIX_TRIGGERS = [
    "fix this code", "fix the code", "debug this", "find the bug",
    "what's wrong with", "correct this",
]


def _detect_intent(text: str) -> Optional[str]:
    """Detect if text is a coding request and what type.

    Returns: "generate", "explain", "fix", "iterate", or None
    """
    text_lower = text.lower()

    # Check iteration FIRST (highest priority if we have previous code)
    if _last_generated["code"]:
        for trigger in _ITERATE_TRIGGERS:
            if trigger in text_lower:
                return "iterate"

    for trigger in _FIX_TRIGGERS:
        if trigger in text_lower:
            return "fix"

    for trigger in _EXPLAIN_TRIGGERS:
        if trigger in text_lower:
            return "explain"

    for trigger in _CODE_TRIGGERS:
        if trigger in text_lower:
            return "generate"

    return None


def _get_user_context() -> str:
    """Build personalization context from stored memories.
    
    Reads user's name, profession, preferences, and style from memory.json.
    Returns a string to inject into code generation prompts.
    """
    try:
        from memory import Memory
        mem = Memory()
        facts = mem.recall()
        
        if not facts:
            return ""
        
        context_parts = []
        name = ""
        profession = ""
        preferences = []
        
        for fact in facts:
            f = fact.get("fact", "").lower()
            cat = fact.get("category", "")
            
            if "name is" in f:
                name = fact["fact"].split("name is")[-1].strip().title()
            elif cat == "professional" or "work" in f or "engineer" in f:
                profession = fact["fact"]
            elif cat == "preference" or "likes" in f or "prefers" in f:
                preferences.append(fact["fact"])
        
        if name:
            context_parts.append(f"User's name: {name}")
        if profession:
            context_parts.append(f"Profession: {profession}")
        if preferences:
            context_parts.append(f"Preferences: {'; '.join(preferences[:5])}")
        
        if context_parts:
            return "\n".join(context_parts)
        return ""
    except Exception:
        return ""


def _ask_ollama_code(prompt: str) -> str:
    """Send a coding prompt to Ollama with personalization from memory."""
    
    # Get user identity for personalization
    user_context = _get_user_context()
    personalization = ""
    if user_context:
        personalization = (
            f"\n\n**IMPORTANT — Personalize the code with this user info:**\n"
            f"{user_context}\n"
            f"- Use the user's actual name in any portfolio/about/personal pages\n"
            f"- Apply their preferences (dark mode, colors, style) by default\n"
            f"- Use their preferred programming language if applicable\n"
        )
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a code assistant. Rules:\n"
                "- Output ONLY a code block and one summary line\n"
                "- Start with ```language immediately\n"
                "- Code must be complete and working\n"
                "- Add brief comments inside the code\n"
                "- End with: Summary: <one sentence>\n"
                "- NO extra explanation, NO markdown headers\n"
                "- For explanations: give 2 sentences + a short code example"
                f"{personalization}"
            ),
        },
        {"role": "user", "content": prompt},
    ]

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.2,      # Low randomness = more reliable code
                    "top_p": 0.9,
                    "num_predict": 800,      # Enough for code + comments + example
                },
            },
            timeout=90,  # Allow up to 90s for slow hardware
        )
        if r.status_code == 200:
            return r.json().get("message", {}).get("content", "")
        return f"Ollama HTTP {r.status_code}"
    except requests.exceptions.Timeout:
        return "Code generation timed out. Try a simpler request."
    except Exception as e:
        return f"Error: {e}"


def _extract_code_block(response: str) -> tuple[str, str]:
    """Extract code block and language from markdown response.

    Returns: (code, language)
    """
    # Match ```python\ncode\n```
    match = re.search(r"```(\w*)\n(.*?)```", response, re.DOTALL)
    if match:
        lang = match.group(1) or "python"
        code = match.group(2).strip()
        return code, lang
    return "", ""


def _extract_summary(response: str) -> str:
    """Extract the summary/explanation from the response."""
    # Look for explicit "Summary:" line first
    for line in response.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith("summary:"):
            return stripped[len("summary:"):].strip()

    # Remove code blocks and get remaining text
    text = re.sub(r"```\w*\n.*?```", "", response, flags=re.DOTALL)
    text = text.strip()

    if not text:
        # Try to extract from the docstring in the code
        code, _ = _extract_code_block(response)
        doc_match = re.search(r'"""(.+?)"""', code, re.DOTALL)
        if doc_match:
            first_line = doc_match.group(1).strip().split("\n")[0]
            return f"Generated: {first_line}"
        return "Code generated and copied to clipboard."

    # Take first meaningful sentence
    sentences = re.split(r"[.!?]\s", text)
    for s in sentences:
        s = s.strip()
        if len(s) > 10:
            return s + "." if not s.endswith(".") else s

    return "Code generated and copied to clipboard."


def _copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard."""
    try:
        import subprocess
        process = subprocess.Popen(
            ["clip"], stdin=subprocess.PIPE, shell=True
        )
        process.communicate(text.encode("utf-8"))
        return True
    except Exception:
        return False


def _save_code_file(code: str, language: str) -> str:
    """Save generated code to a file. Returns filepath."""
    ext_map = {
        "python": ".py", "py": ".py",
        "javascript": ".js", "js": ".js",
        "html": ".html", "css": ".css",
        "sql": ".sql", "bash": ".sh",
        "typescript": ".ts", "java": ".java",
        "c": ".c", "cpp": ".cpp",
    }

    ext = ext_map.get(language.lower(), ".txt")
    os.makedirs("generated_code", exist_ok=True)

    # Generate filename from timestamp
    timestamp = time.strftime("%H%M%S")
    filename = f"generated_code/code_{timestamp}{ext}"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    return filename


def handle_code_request(text: str) -> Optional[dict]:
    """Handle a voice coding request, including iterative refinement.

    Args:
        text: User's transcribed speech.

    Returns:
        Dict with keys: summary (str), code (str), language (str), file (str)
        None if not a code request.
    """
    intent = _detect_intent(text)
    if intent is None:
        return None

    print("💻 Generating code...", end=" ")
    sys.stdout.flush()
    start = time.perf_counter()

    # Build prompt based on intent
    if intent == "iterate":
        # Iterative refinement: modify the last generated code
        prompt = (
            f"Here is the current code:\n\n```{_last_generated['language']}\n"
            f"{_last_generated['code']}\n```\n\n"
            f"User wants to: {text}\n\n"
            f"Modify the code to fulfill this request. "
            f"Output the COMPLETE updated code (not just the changes)."
        )
        print(f"(iterating on {_last_generated['file']})...", end=" ")
        sys.stdout.flush()
    elif intent == "generate":
        prompt = (
            f"{text}\n\n"
            "Write complete, working code. Include comments and example usage."
        )
    elif intent == "explain":
        prompt = (
            f"{text}\n\n"
            "Explain in 2-3 simple sentences. This will be spoken aloud, so be brief."
        )
    elif intent == "fix":
        prompt = (
            f"{text}\n\n"
            "Fix the code, show the corrected version, and explain what was wrong in one sentence."
        )
    else:
        prompt = text

    # Ask Ollama
    response = _ask_ollama_code(prompt)
    ms = (time.perf_counter() - start) * 1000
    print(f"({ms/1000:.1f}s)")
    sys.stdout.flush()

    if not response or "timed out" in response.lower() or "error" in response.lower()[:20]:
        return {"summary": response or "Generation failed.", "code": "", "language": "", "file": ""}

    # Extract code and summary
    code, language = _extract_code_block(response)
    summary = _extract_summary(response)

    # Display code in terminal
    if code:
        # AUTO-LINT: fix code before saving
        try:
            from auto_lint import lint_and_fix, check_syntax, analyze_logic, suggest_improvements
            
            # Level 1: Fix syntax
            issues_before = check_syntax(code, language)
            if issues_before:
                print(f"  🔧 Auto-fixing {len(issues_before)} syntax issues...")
                sys.stdout.flush()
                code = lint_and_fix(code, language)
                issues_after = check_syntax(code, language)
                if not issues_after:
                    print(f"  ✅ All syntax issues fixed!")
                else:
                    print(f"  ⚠️ {len(issues_after)} syntax issues remain")
                sys.stdout.flush()
            
            # Level 2: Logic analysis
            logic_issues = analyze_logic(code, language)
            if logic_issues:
                print(f"  🧠 Logic analysis ({len(logic_issues)} findings):")
                for issue in logic_issues[:5]:
                    print(f"     {issue}")
                sys.stdout.flush()
            
            # Level 3: AI suggestions (only for larger code)
            if len(code) > 200:
                suggestions = suggest_improvements(code, language)
                if suggestions:
                    print(f"  💡 Suggestions:")
                    for s in suggestions[:3]:
                        print(f"     • {s}")
                    sys.stdout.flush()
                    
        except ImportError:
            pass  # auto_lint not available

        print(f"\n{'─' * 50}")
        print(f"  📄 {language.upper()} Code {'(v' + str(_get_version()) + ' - updated)' if intent == 'iterate' else ''}:")
        print(f"{'─' * 50}")
        for line in code.split("\n"):
            print(f"  {line}")
        print(f"{'─' * 50}")
        sys.stdout.flush()

        # Copy to clipboard
        if _copy_to_clipboard(code):
            print("  📋 Copied to clipboard!")
        else:
            print("  (clipboard copy failed)")

        # Save to file (overwrite if iterating on same file)
        if intent == "iterate" and _last_generated["file"]:
            filepath = _last_generated["file"]
            # Save version before overwriting
            try:
                from version_history import save_version
                with open(filepath, "r", encoding="utf-8") as f:
                    old_content = f.read()
                save_version(filepath, old_content)
            except Exception:
                pass
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"  💾 Updated: {filepath}")
        else:
            filepath = _save_code_file(code, language)
            # Save first version
            try:
                from version_history import save_version
                save_version(filepath, code)
            except Exception:
                pass
            print(f"  💾 Saved: {filepath}")

        sys.stdout.flush()

        # Track for future iteration
        _last_generated["code"] = code
        _last_generated["language"] = language
        _last_generated["file"] = filepath
        _last_generated["request"] = text

        # Set for auto_preview
        try:
            from auto_preview import set_last_preview
            set_last_preview(filepath)
        except ImportError:
            pass

        return {
            "summary": summary,
            "code": code,
            "language": language,
            "file": filepath,
        }
    else:
        # No code block — just an explanation
        return {
            "summary": summary,
            "code": "",
            "language": "",
            "file": "",
        }


def _get_version() -> int:
    """Count how many times we've iterated on the current file."""
    if not _last_generated["file"]:
        return 1
    try:
        # Count modifications by checking file mtime changes
        return 2  # Simplified: just show it's an update
    except Exception:
        return 1
