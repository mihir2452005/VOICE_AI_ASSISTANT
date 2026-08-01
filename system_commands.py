"""System Commands — instant local actions without calling Ollama.

Handles: open/close apps, volume control, media playback, time/date,
screenshot, and system info. All execute in <50ms (no LLM needed).

Usage from main.py:
    from system_commands import handle_command
    result = handle_command("open chrome")
    if result:
        speak(result)  # Handled locally
    else:
        # Not a system command, send to Ollama
"""

import os
import re
import sys
import subprocess
import time
from datetime import datetime
from typing import Optional


# =============================================================================
# APP MANAGEMENT
# =============================================================================

# Common Windows app mappings
APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "files": "explorer.exe",
    "terminal": "cmd.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "settings": "ms-settings:",
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "brave": "brave",
    "spotify": "spotify",
    "discord": "discord",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
}


def open_app(name: str) -> str:
    """Open a Windows application by name."""
    name_lower = name.lower().strip()
    exe = APP_MAP.get(name_lower, name_lower)

    try:
        if exe.startswith("ms-"):
            os.startfile(exe)
        else:
            subprocess.Popen(
                exe, shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return f"Opening {name}."
    except Exception as e:
        return f"Couldn't open {name}: {e}"


def close_app(name: str) -> str:
    """Close a running application by process name."""
    name_lower = name.lower().strip()
    exe = APP_MAP.get(name_lower, name_lower)

    # Get the actual exe name for taskkill
    if not exe.endswith(".exe"):
        exe = exe + ".exe"

    try:
        subprocess.run(
            ["taskkill", "/f", "/im", exe],
            capture_output=True, timeout=5,
        )
        return f"Closed {name}."
    except Exception:
        return f"Couldn't close {name}."


# =============================================================================
# MEDIA & VOLUME CONTROL
# =============================================================================

def media_play_pause() -> str:
    """Toggle media play/pause using Windows media key."""
    try:
        import ctypes
        VK_MEDIA_PLAY_PAUSE = 0xB3
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
        return "Toggled playback."
    except Exception:
        return "Couldn't control media."


def media_next() -> str:
    """Skip to next track."""
    try:
        import ctypes
        VK_MEDIA_NEXT = 0xB0
        ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT, 0, 2, 0)
        return "Next track."
    except Exception:
        return "Couldn't skip track."


def volume_up() -> str:
    """Increase system volume."""
    try:
        import ctypes
        VK_VOLUME_UP = 0xAF
        for _ in range(5):  # 5 presses = noticeable increase
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
        return "Volume up."
    except Exception:
        return "Couldn't change volume."


def volume_down() -> str:
    """Decrease system volume."""
    try:
        import ctypes
        VK_VOLUME_DOWN = 0xAE
        for _ in range(5):
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
        return "Volume down."
    except Exception:
        return "Couldn't change volume."


def volume_mute() -> str:
    """Toggle mute."""
    try:
        import ctypes
        VK_VOLUME_MUTE = 0xAD
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
        return "Toggled mute."
    except Exception:
        return "Couldn't mute."


# =============================================================================
# SYSTEM INFO
# =============================================================================

def get_time() -> str:
    """Get current time and date."""
    now = datetime.now()
    return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."


def get_system_info() -> str:
    """Get basic CPU/RAM usage."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        return (
            f"CPU at {cpu}%, RAM using {ram.percent}% "
            f"({ram.used // (1024**3):.1f} of {ram.total // (1024**3):.1f} GB)."
        )
    except ImportError:
        return "Install psutil for system info: pip install psutil"


def take_screenshot() -> str:
    """Take a screenshot and save it."""
    try:
        from PIL import ImageGrab
        os.makedirs("output", exist_ok=True)
        filename = f"output/screenshot_{datetime.now().strftime('%H%M%S')}.png"
        img = ImageGrab.grab()
        img.save(filename)
        return f"Screenshot saved: {filename}"
    except ImportError:
        return "Install Pillow for screenshots: pip install Pillow"


# =============================================================================
# COMMAND ROUTER — matches voice input to actions
# =============================================================================

# Pattern: (regex, handler function)
_COMMANDS = [
    # Time
    (r"(what time|what's the time|tell me the time|current time|what date|today's date)", lambda m: get_time()),

    # Open app
    (r"open\s+(.+)", lambda m: open_app(m.group(1))),

    # Close app
    (r"close\s+(.+)", lambda m: close_app(m.group(1))),

    # Volume
    (r"(volume up|louder|increase volume|turn it up)", lambda m: volume_up()),
    (r"(volume down|quieter|decrease volume|turn it down)", lambda m: volume_down()),
    (r"(mute|unmute|toggle mute)", lambda m: volume_mute()),

    # Media
    (r"(play music|pause music|play|pause|resume)", lambda m: media_play_pause()),
    (r"(next track|skip track|next song|skip song)", lambda m: media_next()),

    # System info
    (r"(system info|pc health|cpu usage|ram usage|how's my pc|system status)", lambda m: get_system_info()),

    # Screenshot
    (r"(take a screenshot|screenshot|capture screen|take screenshot)", lambda m: take_screenshot()),
]


def handle_command(text: str) -> Optional[str]:
    """Try to match text against known system commands.

    Args:
        text: The user's transcribed speech.

    Returns:
        Response string if command matched, None if not a system command.
    """
    text_lower = text.lower().strip()

    # Skip if it's clearly a question for the LLM
    if len(text_lower.split()) > 8 and not any(
        kw in text_lower for kw in ["open", "close", "volume", "mute", "play", "pause", "screenshot"]
    ):
        return None

    for pattern, handler in _COMMANDS:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return handler(match)
            except Exception as e:
                return f"Command failed: {e}"

    return None
