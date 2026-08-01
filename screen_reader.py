"""Screen Reader — read text from screen using multiple fast methods.

Strategy (in order of speed):
1. Active window title + clipboard content (instant)
2. Windows UI Automation (reads text from focused app, ~200ms)
3. PowerShell Get-Process for window titles (~100ms)
4. OCR via Tesseract if installed (last resort, ~2s)

Say:
- "Read my screen" → reads visible text from active window
- "What error is on my screen" → finds error text + asks Ollama to explain
- "What's on my screen" → summarizes active content via Ollama

Usage:
    from screen_reader import handle_screen_command
    result = handle_screen_command("read my screen")
    if result: speak(result)
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from typing import Optional

import requests


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

_READ_TRIGGERS = [
    "read my screen", "read the screen", "what's on my screen",
    "what is on my screen", "read screen", "screen text",
    "what does it say", "read what's there",
]
_ERROR_TRIGGERS = [
    "what error", "what's the error", "read the error",
    "what went wrong", "diagnose my screen", "explain the error",
    "fix the error on screen", "debug my screen",
]
_UNDERSTAND_TRIGGERS = [
    "what's happening on screen", "summarize my screen",
    "explain my screen", "understand my screen",
    "what am I looking at", "describe my screen",
]


def _get_active_window_text() -> str:
    """Get text from the currently focused window using UI Automation."""
    try:
        # Get active window title
        ps = '''
$fw = (Get-Process | Where-Object { $_.MainWindowHandle -eq (
    Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();' -Name Win32 -Namespace Native -PassThru
)::GetForegroundWindow() }).MainWindowTitle
Write-Output "ACTIVE_WINDOW: $fw"
'''
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_all_window_titles() -> str:
    """Get titles of all visible windows."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
             "Select-Object -ExpandProperty MainWindowTitle"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_clipboard() -> str:
    """Read current clipboard content."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=3
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_terminal_output() -> str:
    """Try to get recent terminal/console output (for error detection)."""
    # Check if there's a recent log file or terminal buffer
    # This is a best-effort approach
    recent_text = ""

    # Check clipboard (users often copy errors)
    clip = _get_clipboard()
    if clip and any(w in clip.lower() for w in ["error", "traceback", "exception", "failed"]):
        recent_text += f"[Clipboard]:\n{clip}\n\n"

    # Check for recent log files
    log_candidates = ["output/nova.log", "logs/"]
    for path in log_candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    last_lines = "".join(lines[-20:])
                    if last_lines.strip():
                        recent_text += f"[Recent log]:\n{last_lines}\n"
            except Exception:
                pass

    return recent_text


def _screenshot_with_ocr() -> str:
    """Take screenshot and try OCR (tesseract if available, else skip)."""
    from PIL import ImageGrab
    os.makedirs("output", exist_ok=True)
    filename = f"output/screen_{datetime.now().strftime('%H%M%S')}.png"
    img = ImageGrab.grab()
    img.save(filename)

    # Try Tesseract
    try:
        import pytesseract
        text = pytesseract.image_to_string(img)
        if text.strip():
            return text.strip()
    except Exception:
        pass

    # Try EasyOCR (slower but doesn't need binary)
    try:
        import easyocr
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        results = reader.readtext(filename, detail=0, paragraph=True)
        if results:
            return "\n".join(results)
    except Exception:
        pass

    return ""


def extract_screen_text() -> str:
    """Extract text from screen using best available method.
    
    Combines multiple sources for the most complete picture:
    - Active window info
    - Clipboard content (often has copied errors)
    - OCR if available
    """
    print("  📸 Reading screen...", end=" ")
    sys.stdout.flush()
    start = time.perf_counter()

    parts = []

    # 1. Active window title
    active = _get_active_window_text()
    if active:
        parts.append(active)

    # 2. All visible windows
    windows = _get_all_window_titles()
    if windows:
        parts.append(f"Open windows:\n{windows}")

    # 3. Clipboard (often has error text the user copied)
    clip = _get_clipboard()
    if clip and len(clip) > 10:
        parts.append(f"Clipboard content:\n{clip}")

    # 4. Terminal/recent output
    terminal = _get_terminal_output()
    if terminal:
        parts.append(terminal)

    # 5. OCR (if other methods gave little text)
    total_so_far = "\n".join(parts)
    if len(total_so_far) < 100:
        ocr_text = _screenshot_with_ocr()
        if ocr_text:
            parts.append(f"Screen OCR:\n{ocr_text}")

    elapsed = time.perf_counter() - start
    text = "\n\n".join(parts)
    print(f"({elapsed:.1f}s, {len(text)} chars)")
    sys.stdout.flush()
    return text


def _ask_ollama_about_screen(screen_text: str, question: str) -> str:
    """Send extracted screen text to Ollama for understanding."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are reading text from a user's computer screen. "
                            "Answer briefly (2-3 sentences). "
                            "If there's an error, explain what caused it and how to fix it."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Screen content:\n{screen_text[:2000]}\n\nQuestion: {question}",
                    },
                ],
                "stream": False,
                "options": {"num_predict": 200, "temperature": 0.3},
            },
            timeout=60,
        )
        if r.status_code == 200:
            return r.json().get("message", {}).get("content", "").strip()
        return "Couldn't analyze the screen text."
    except Exception as e:
        return f"Analysis error: {e}"


def handle_screen_command(text: str) -> Optional[str]:
    """Handle screen reading voice commands."""
    text_lower = text.lower().strip()

    intent = None
    if any(t in text_lower for t in _ERROR_TRIGGERS):
        intent = "error"
    elif any(t in text_lower for t in _UNDERSTAND_TRIGGERS):
        intent = "understand"
    elif any(t in text_lower for t in _READ_TRIGGERS):
        intent = "read"
    else:
        return None

    screen_text = extract_screen_text()

    if not screen_text or len(screen_text) < 10:
        return "I couldn't read anything from your screen. Try copying the text to clipboard first."

    if intent == "read":
        lines = [l.strip() for l in screen_text.split("\n") if l.strip()]
        print(f"\n  Screen content ({len(lines)} lines):")
        for line in lines[:8]:
            print(f"    {line[:80]}")
        if len(lines) > 8:
            print(f"    ... ({len(lines) - 8} more)")
        sys.stdout.flush()
        spoken = ". ".join(lines[:3])[:200]
        return f"On your screen: {spoken}"

    elif intent == "error":
        error_keywords = ["error", "exception", "failed", "traceback",
                         "warning", "fatal", "denied", "not found"]
        error_lines = [
            l for l in screen_text.split("\n")
            if any(w in l.lower() for w in error_keywords)
        ]
        if error_lines:
            print(f"\n  🔴 Errors detected:")
            for line in error_lines[:5]:
                print(f"    {line[:80]}")
            sys.stdout.flush()
        explanation = _ask_ollama_about_screen(
            screen_text, "What errors or issues are visible? How to fix them?"
        )
        return explanation

    elif intent == "understand":
        print("  🧠 Analyzing...")
        sys.stdout.flush()
        return _ask_ollama_about_screen(
            screen_text, "Briefly describe what's on this screen."
        )

    return None
