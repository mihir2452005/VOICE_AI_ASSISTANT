"""Clipboard Code Fixer — fix or refactor code from clipboard.

Say: "fix my clipboard code", "refactor clipboard", "improve the code in clipboard"
Reads code from clipboard, fixes it via Ollama, puts result back in clipboard.

Usage:
    from code_fixer import handle_clipboard_fix
    result = handle_clipboard_fix("fix my clipboard code")
    if result: speak(result)
"""

import os
import sys
import subprocess
import re
import requests
from typing import Optional


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

_TRIGGERS = [
    "fix my clipboard", "fix the clipboard", "fix clipboard code",
    "refactor clipboard", "refactor my clipboard",
    "improve clipboard", "improve the code in clipboard",
    "fix the code in my clipboard", "clean up clipboard",
    "optimize clipboard", "debug clipboard",
]


def _get_clipboard() -> str:
    """Get text from Windows clipboard."""
    try:
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _set_clipboard(text: str) -> bool:
    """Set text to Windows clipboard."""
    try:
        process = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
        process.communicate(text.encode("utf-8"))
        return True
    except Exception:
        return False


def handle_clipboard_fix(text: str) -> Optional[str]:
    """Fix code from clipboard. Returns summary or None."""
    text_lower = text.lower().strip()

    # Check trigger
    if not any(t in text_lower for t in _TRIGGERS):
        return None

    # Get clipboard content
    code = _get_clipboard()
    if not code:
        return "Clipboard is empty. Copy some code first."

    if len(code) < 5:
        return "Clipboard content is too short to be code."

    print(f"  📋 Clipboard: {len(code)} chars")
    print("  🔧 Fixing...", end=" ")
    sys.stdout.flush()

    # Determine intent
    if "refactor" in text_lower:
        task = "Refactor this code for better readability and efficiency"
    elif "optimize" in text_lower:
        task = "Optimize this code for performance"
    else:
        task = "Fix any bugs in this code and improve it"

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a code fixer. Output ONLY the corrected code in a ```language block. Then ONE sentence explaining what you changed."},
                    {"role": "user", "content": f"{task}:\n\n```\n{code[:2000]}\n```"},
                ],
                "stream": False,
                "options": {"num_predict": 800, "temperature": 0.1},
            },
            timeout=90,
        )

        if r.status_code != 200:
            return "Ollama error during fix."

        response = r.json().get("message", {}).get("content", "")
        print("Done")

        # Extract fixed code
        match = re.search(r"```\w*\n(.*?)```", response, re.DOTALL)
        if match:
            fixed_code = match.group(1).strip()
            _set_clipboard(fixed_code)
            # Extract explanation
            explanation = re.sub(r"```\w*\n.*?```", "", response, flags=re.DOTALL).strip()
            short_exp = explanation.split(".")[0] + "." if explanation else "Code fixed."
            print(f"  ✅ Fixed code copied back to clipboard!")
            sys.stdout.flush()
            return f"Fixed and copied to clipboard. {short_exp}"
        else:
            return "Couldn't extract fixed code from response."

    except Exception as e:
        return f"Fix failed: {e}"
