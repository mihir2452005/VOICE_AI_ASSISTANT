"""Daily Briefing — smart startup summary that makes Nova feel alive.

On startup, Nova greets you with:
- Current date, time, and day of week
- Weather (via DuckDuckGo search, if internet available)
- Pending tasks reminder
- Motivational quote (rotates daily)
- System health (RAM/CPU)

Usage:
    from daily_brief import get_daily_briefing
    briefing = get_daily_briefing()
    speak(briefing)
"""

import os
import sys
import time
import random
from datetime import datetime
from typing import Optional


# Motivational quotes (rotated daily)
_QUOTES = [
    "The only way to do great work is to love what you do.",
    "Code is like humor. When you have to explain it, it's bad.",
    "First, solve the problem. Then, write the code.",
    "Every expert was once a beginner.",
    "The best time to start was yesterday. The next best time is now.",
    "Stay hungry, stay foolish.",
    "Think different. Build different.",
    "Progress, not perfection.",
    "Small steps every day lead to big results.",
    "Your limitation is only your imagination.",
    "Push yourself, because no one else is going to do it for you.",
    "The harder you work, the luckier you get.",
    "Dream big. Start small. Act now.",
    "Success is not final, failure is not fatal.",
    "Believe you can and you're halfway there.",
    "Be the change you wish to see in the world.",
    "It always seems impossible until it's done.",
    "Don't watch the clock. Do what it does. Keep going.",
    "The future depends on what you do today.",
    "A journey of a thousand miles begins with a single step.",
    "What you do today can improve all your tomorrows.",
    "Strive for progress, not perfection.",
    "The secret of getting ahead is getting started.",
    "You don't have to be great to start, but you have to start to be great.",
    "Action is the foundational key to success.",
    "Opportunities don't happen. You create them.",
    "Don't let yesterday take up too much of today.",
    "Whether you think you can or think you can't, you're right.",
    "It does not matter how slowly you go as long as you do not stop.",
    "Everything you've ever wanted is on the other side of fear.",
]


def _get_greeting() -> str:
    """Get time-appropriate greeting."""
    hour = datetime.now().hour
    if hour < 5:
        return "Still up? Hope you're doing something exciting"
    elif hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    elif hour < 21:
        return "Good evening"
    else:
        return "Working late"


def _get_date_info() -> str:
    """Get current date and time."""
    now = datetime.now()
    return f"It's {now.strftime('%A, %B %d')} at {now.strftime('%I:%M %p')}."


def _get_weather() -> str:
    """Try to get weather via web search (fast, no API key)."""
    try:
        from web_search import web_search
        results = web_search("weather today", max_results=1)
        if results:
            # Extract temperature/condition from snippet
            first_result = results.split("\n")[0] if results else ""
            if first_result and len(first_result) > 20:
                return first_result[:100]
        return ""
    except Exception:
        return ""


def _get_tasks_summary() -> str:
    """Get pending tasks count."""
    try:
        from tasks import get_pending_summary
        summary = get_pending_summary()
        return summary if summary else ""
    except Exception:
        return ""


def _get_system_health() -> str:
    """Get basic system status."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory()
        if cpu > 80 or ram.percent > 85:
            return f"Heads up: system is under load. CPU {cpu}%, RAM {ram.percent}%."
        return ""
    except ImportError:
        return ""


def _get_quote() -> str:
    """Get today's motivational quote (changes daily)."""
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(_QUOTES)
    return _QUOTES[idx]


def get_daily_briefing(user_name: str = "") -> str:
    """Generate the full daily briefing.
    
    Args:
        user_name: User's name from memory (for personalized greeting).
    
    Returns:
        Complete briefing string to speak.
    """
    parts = []

    # Greeting
    greeting = _get_greeting()
    if user_name:
        parts.append(f"{greeting}, {user_name}!")
    else:
        parts.append(f"{greeting}!")

    # Date/time
    parts.append(_get_date_info())

    # Tasks
    tasks = _get_tasks_summary()
    if tasks:
        parts.append(tasks)

    # System health (only warn if high)
    health = _get_system_health()
    if health:
        parts.append(health)

    # Quote
    parts.append(f"Today's thought: {_get_quote()}")

    # Ready message
    parts.append("I'm ready to help. What would you like to do?")

    return " ".join(parts)


def print_briefing_banner(user_name: str = "") -> None:
    """Print a formatted briefing to terminal + return speakable text."""
    now = datetime.now()
    greeting = _get_greeting()
    name_str = f", {user_name}" if user_name else ""

    print(f"\n  {greeting}{name_str}!")
    print(f"  📅 {now.strftime('%A, %B %d, %Y')} • {now.strftime('%I:%M %p')}")

    tasks = _get_tasks_summary()
    if tasks:
        print(f"  📋 {tasks}")

    health = _get_system_health()
    if health:
        print(f"  ⚠️ {health}")

    quote = _get_quote()
    print(f"  💬 \"{quote}\"")
    print()
    sys.stdout.flush()
