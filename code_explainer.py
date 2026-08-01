"""Code Explainer — read any file and explain it in plain English.

Say: "explain main.py", "what does coder.py do", "what functions are in memory.py"
Reads the file, sends to Ollama, speaks a summary.

Usage:
    from code_explainer import handle_explain
    result = handle_explain("explain main.py")
    if result: speak(result)
"""

import os
import re
import sys
import requests
from typing import Optional


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

_TRIGGERS = [
    "explain ", "what does ", "what's in ", "describe ",
    "read and explain ", "what functions are in ",
    "summarize the file ", "analyze ",
]


def _find_file(name: str) -> Optional[str]:
    """Find a file by name in current directory or common locations."""
    # Direct path
    if os.path.isfile(name):
        return name

    # Check current directory
    if os.path.isfile(os.path.join(".", name)):
        return os.path.join(".", name)

    # Check common extensions
    for ext in ["", ".py", ".js", ".html", ".css", ".txt", ".md"]:
        path = name + ext
        if os.path.isfile(path):
            return path

    # Search in current dir
    for f in os.listdir("."):
        if name.lower() in f.lower():
            return f

    return None


def handle_explain(text: str) -> Optional[str]:
    """Explain a code file by voice.

    Returns explanation string or None if not an explain request.
    """
    text_lower = text.lower().strip()

    # Extract filename
    filename = None
    for trigger in _TRIGGERS:
        if text_lower.startswith(trigger):
            filename = text[len(trigger):].strip()
            break

    if not filename:
        # Try "what does X do" pattern
        match = re.search(r"what does (.+?) do", text_lower)
        if match:
            filename = match.group(1).strip()

    if not filename:
        return None

    # Find the file
    filepath = _find_file(filename)
    if not filepath:
        return f"Can't find file: {filename}"

    # Read file content
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return f"Can't read {filename}: {e}"

    # Truncate if too long (keep first 2000 chars for small model)
    if len(content) > 2000:
        content = content[:2000] + "\n... (truncated)"

    print(f"  📄 Reading: {filepath} ({len(content)} chars)")
    sys.stdout.flush()

    # Ask Ollama to explain
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": "Explain code briefly in 2-3 sentences. List main functions if asked. This will be spoken aloud."},
                    {"role": "user", "content": f"Explain this file ({filepath}):\n\n{content}"},
                ],
                "stream": False,
                "options": {"num_predict": 200, "temperature": 0.3},
            },
            timeout=60,
        )
        if r.status_code == 200:
            return r.json().get("message", {}).get("content", "").strip()
        return f"Ollama error: HTTP {r.status_code}"
    except Exception as e:
        return f"Error explaining file: {e}"
