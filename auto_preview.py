"""Auto Preview — instantly open generated files in browser or run them.

When Nova generates HTML/CSS → auto-opens in Chrome/default browser
When Nova generates Python → auto-runs it and shows output
Say 'show me' or 'preview it' to open the last generated file

Usage from main.py:
    from auto_preview import auto_preview, handle_preview_command
    
    # After code generation:
    auto_preview("generated_code/page.html")  # Opens in browser
    auto_preview("generated_code/script.py")  # Runs and shows output
    
    # Voice command:
    result = handle_preview_command("show me")
    if result: speak(result)
"""

import os
import sys
import subprocess
import webbrowser
import time
from typing import Optional


# Track last previewed file
_last_preview = ""


def auto_preview(filepath: str) -> str:
    """Auto-preview a file based on its type.
    
    - HTML/CSS/SVG → opens in default browser
    - Python → runs and returns output
    - JS/JSON/TXT → opens in notepad
    
    Returns status message.
    """
    global _last_preview

    if not filepath or not os.path.isfile(filepath):
        return ""

    _last_preview = filepath
    ext = os.path.splitext(filepath)[1].lower()
    abs_path = os.path.abspath(filepath)

    # HTML/CSS/SVG → open in browser
    if ext in (".html", ".htm", ".svg"):
        try:
            webbrowser.open(f"file:///{abs_path.replace(os.sep, '/')}")
            print(f"  🌐 Opened in browser: {filepath}")
            sys.stdout.flush()
            return "Opened in your browser."
        except Exception as e:
            return f"Couldn't open browser: {e}"

    # Python → run and capture output
    elif ext == ".py":
        try:
            print(f"  ▶️ Running: python {filepath}")
            sys.stdout.flush()
            result = subprocess.run(
                ["python", filepath],
                capture_output=True, text=True,
                timeout=10, encoding="utf-8", errors="replace"
            )
            output = result.stdout.strip()
            error = result.stderr.strip()

            if result.returncode == 0:
                if output:
                    print(f"  Output: {output[:200]}")
                    sys.stdout.flush()
                    return f"Script ran successfully. Output: {output[:100]}"
                return "Script ran successfully with no output."
            else:
                print(f"  ❌ Error: {error[:200]}")
                sys.stdout.flush()
                return f"Script had an error: {error[:80]}"

        except subprocess.TimeoutExpired:
            return "Script timed out after 10 seconds."
        except Exception as e:
            return f"Couldn't run script: {e}"

    # Other text files → open in default editor
    else:
        try:
            os.startfile(abs_path)
            print(f"  📂 Opened: {filepath}")
            sys.stdout.flush()
            return f"Opened {os.path.basename(filepath)}."
        except Exception as e:
            return f"Couldn't open file: {e}"


def handle_preview_command(text: str) -> Optional[str]:
    """Handle 'show me' / 'preview it' / 'open it' voice commands.
    
    Returns result string or None if not a preview command.
    """
    text_lower = text.lower().strip()

    triggers = [
        "show me", "preview it", "open it", "preview",
        "show the result", "open the file", "run it",
        "show me the result", "let me see", "display it",
    ]

    if not any(t in text_lower for t in triggers):
        return None

    # Check if user specified a file
    # e.g., "show me main.py" or "preview portfolio.html"
    words = text.split()
    for word in words:
        if "." in word and len(word) > 2:
            # Looks like a filename
            if os.path.isfile(word):
                return auto_preview(word)
            # Check generated_code folder
            gen_path = os.path.join("generated_code", word)
            if os.path.isfile(gen_path):
                return auto_preview(gen_path)

    # No specific file — use last generated/previewed file
    if _last_preview and os.path.isfile(_last_preview):
        return auto_preview(_last_preview)

    # Try last file in generated_code
    gen_dir = "generated_code"
    if os.path.isdir(gen_dir):
        files = sorted(os.listdir(gen_dir), key=lambda f: os.path.getmtime(os.path.join(gen_dir, f)), reverse=True)
        if files:
            return auto_preview(os.path.join(gen_dir, files[0]))

    return "No file to preview. Generate some code first."


def set_last_preview(filepath: str) -> None:
    """Set the last generated file path (called by coder.py after generation)."""
    global _last_preview
    _last_preview = filepath
