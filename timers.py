"""Timers & Voice Reminders — background alerts that speak when done.

Say:
- "Set timer 30 seconds"
- "Remind me in 5 minutes to drink water"
- "Timer 10 minutes"
- "Alarm in 1 hour"
- "Show timers" / "What timers are running"
- "Cancel timer" / "Cancel all timers"

Multiple timers run simultaneously in background threads.
Nova speaks the reminder aloud when each one fires.

Usage:
    from timers import handle_timer_command
    result = handle_timer_command("remind me in 5 minutes to stretch")
    if result: speak(result)
"""

import re
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable


# Active timers
_timers: list[dict] = []
_timer_lock = threading.Lock()
_speak_fn: Optional[Callable] = None


def set_speak_function(fn: Callable):
    """Set the TTS function for timer alerts. Call on startup."""
    global _speak_fn
    _speak_fn = fn


def _timer_thread(timer_id: int, seconds: float, message: str):
    """Background thread that waits then speaks the reminder."""
    time.sleep(seconds)

    with _timer_lock:
        # Mark as fired
        for t in _timers:
            if t["id"] == timer_id:
                t["status"] = "fired"
                break

    # Speak the reminder
    alert = f"Timer done! {message}" if message else "Timer done!"
    print(f"\n  🔔 {alert}")
    sys.stdout.flush()

    if _speak_fn:
        _speak_fn(alert)


def set_timer(seconds: float, message: str = "") -> str:
    """Set a new background timer."""
    with _timer_lock:
        timer_id = len(_timers) + 1
        timer_info = {
            "id": timer_id,
            "seconds": seconds,
            "message": message,
            "status": "running",
            "started": datetime.now().isoformat(),
            "fires_at": (datetime.now() + timedelta(seconds=seconds)).strftime("%H:%M:%S"),
        }
        _timers.append(timer_info)

    # Start background thread
    t = threading.Thread(target=_timer_thread, args=(timer_id, seconds, message), daemon=True)
    t.start()

    # Format time for speech
    if seconds >= 3600:
        time_str = f"{seconds/3600:.1f} hours"
    elif seconds >= 60:
        time_str = f"{seconds/60:.0f} minutes"
    else:
        time_str = f"{seconds:.0f} seconds"

    msg_part = f" to {message}" if message else ""
    return f"Timer set for {time_str}{msg_part}. I'll remind you at {timer_info['fires_at']}."


def list_timers() -> str:
    """List all active timers."""
    with _timer_lock:
        active = [t for t in _timers if t["status"] == "running"]

    if not active:
        return "No active timers."

    lines = [f"⏰ Active timers ({len(active)}):"]
    for t in active:
        msg = f" — {t['message']}" if t["message"] else ""
        lines.append(f"  #{t['id']}: fires at {t['fires_at']}{msg}")
    return "\n".join(lines)


def cancel_all() -> str:
    """Cancel all timers."""
    with _timer_lock:
        count = sum(1 for t in _timers if t["status"] == "running")
        for t in _timers:
            t["status"] = "cancelled"
    return f"Cancelled {count} timers."


# =============================================================================
# VOICE COMMAND PARSER
# =============================================================================

def _parse_time(text: str) -> Optional[float]:
    """Parse time duration from text. Returns seconds or None."""
    text_lower = text.lower()

    # "30 seconds" / "30 sec"
    match = re.search(r"(\d+)\s*(?:seconds?|sec|s)\b", text_lower)
    if match:
        return float(match.group(1))

    # "5 minutes" / "5 min"
    match = re.search(r"(\d+)\s*(?:minutes?|min|m)\b", text_lower)
    if match:
        return float(match.group(1)) * 60

    # "1 hour" / "2 hours"
    match = re.search(r"(\d+\.?\d*)\s*(?:hours?|hr|h)\b", text_lower)
    if match:
        return float(match.group(1)) * 3600

    # "half hour" / "half an hour"
    if "half hour" in text_lower or "half an hour" in text_lower:
        return 1800

    # Just a number (assume minutes)
    match = re.search(r"(?:in|for)\s+(\d+)\b", text_lower)
    if match:
        return float(match.group(1)) * 60

    return None


def _parse_message(text: str) -> str:
    """Extract the reminder message from text."""
    text_lower = text.lower()

    # "remind me in 5 minutes to drink water" → "drink water"
    match = re.search(r"(?:to|about|that)\s+(.+?)$", text_lower)
    if match:
        msg = match.group(1).strip()
        # Remove time parts from message
        msg = re.sub(r"\d+\s*(seconds?|minutes?|hours?|sec|min|hr|s|m|h)", "", msg).strip()
        if msg:
            return msg

    return ""


_TRIGGERS = [
    "set timer", "set a timer", "timer", "remind me",
    "alarm in", "set alarm", "countdown",
    "show timers", "list timers", "what timers",
    "cancel timer", "cancel all timers", "stop timer",
]


def handle_timer_command(text: str) -> Optional[str]:
    """Handle timer-related voice commands."""
    text_lower = text.lower().strip()

    if not any(t in text_lower for t in _TRIGGERS):
        return None

    # Show timers
    if any(t in text_lower for t in ["show timers", "list timers", "what timers", "active timers"]):
        result = list_timers()
        print(f"\n{result}")
        sys.stdout.flush()
        active = [t for t in _timers if t["status"] == "running"]
        return f"You have {len(active)} active timers." if active else "No active timers."

    # Cancel
    if "cancel" in text_lower or "stop timer" in text_lower:
        result = cancel_all()
        return result

    # Set timer
    seconds = _parse_time(text)
    if seconds is None:
        return "I couldn't understand the time. Try: 'timer 5 minutes' or 'remind me in 30 seconds'."

    if seconds <= 0:
        return "Timer needs to be at least 1 second."
    if seconds > 86400:
        return "Maximum timer is 24 hours."

    message = _parse_message(text)
    result = set_timer(seconds, message)
    print(f"  ⏰ {result}")
    sys.stdout.flush()
    return result
