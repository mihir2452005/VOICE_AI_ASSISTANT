"""Adaptive Learning — Nova gets smarter the more you use her.

Tracks:
- Command frequency (what you ask most)
- Time patterns (when you use certain features)
- Coding preferences (languages, themes, styles)
- Common corrections (words you repeat/rephrase)

Uses this data to:
- Auto-suggest next actions after completing a task
- Pre-load likely features (e.g., if you always code at night)
- Default to your preferred language/theme for code gen
- Offer proactive tips based on patterns

Usage:
    from adaptive import Adaptive
    nova_brain = Adaptive()
    nova_brain.track("code_generation", {"language": "python", "type": "function"})
    suggestion = nova_brain.suggest_next()  # "You usually search next. Want me to search something?"
"""

import os
import json
import time
from datetime import datetime, timedelta
from collections import Counter
from typing import Optional


DATA_FILE = "nova_learning.json"


class Adaptive:
    """Tracks usage patterns and suggests next actions."""

    def __init__(self, filepath: str = DATA_FILE):
        self._filepath = filepath
        self._data = {
            "commands": [],       # History of commands (last 500)
            "preferences": {},    # Learned preferences
            "patterns": {},       # Time-based patterns
            "corrections": [],    # When user rephrases
            "sessions": 0,        # Total sessions
            "total_interactions": 0,
        }
        self._session_commands = []  # Commands this session
        self._load()
        self._data["sessions"] += 1
        self._save()

    def track(self, action: str, details: dict = None) -> None:
        """Track a user action for learning.

        Args:
            action: Action type (e.g., "code_gen", "search", "system_cmd", "chat")
            details: Extra context (language, topic, etc.)
        """
        entry = {
            "action": action,
            "details": details or {},
            "time": datetime.now().isoformat(),
            "hour": datetime.now().hour,
        }

        self._data["commands"].append(entry)
        self._session_commands.append(entry)
        self._data["total_interactions"] += 1

        # Keep last 500 commands
        if len(self._data["commands"]) > 500:
            self._data["commands"] = self._data["commands"][-500:]

        # Learn preferences
        self._learn_preferences(action, details)

        # Learn time patterns
        self._learn_time_patterns(action)

        self._save()

    def suggest_next(self) -> Optional[str]:
        """Suggest what the user might want to do next.

        Based on:
        - What usually follows the last action
        - Time of day patterns
        - Session frequency

        Returns suggestion string or None.
        """
        if len(self._session_commands) < 1:
            return self._suggest_from_time()

        last_action = self._session_commands[-1]["action"]

        # What usually follows this action?
        sequences = self._get_common_sequences(last_action)
        if sequences:
            next_action, count = sequences[0]
            confidence = count / max(len(self._data["commands"]), 1)
            if confidence > 0.2:  # Only suggest if pattern is strong
                return self._action_to_suggestion(next_action)

        return None

    def get_preferences(self) -> dict:
        """Get learned user preferences."""
        return dict(self._data.get("preferences", {}))

    def get_preferred_language(self) -> str:
        """Get most-used programming language."""
        prefs = self._data.get("preferences", {})
        langs = prefs.get("languages", {})
        if langs:
            return max(langs, key=langs.get)
        return "python"

    def get_preferred_theme(self) -> str:
        """Get preferred design theme."""
        prefs = self._data.get("preferences", {})
        return prefs.get("theme", "modern dark")

    def get_stats(self) -> str:
        """Get usage statistics as a speakable string."""
        total = self._data["total_interactions"]
        sessions = self._data["sessions"]
        top_actions = self._get_top_actions(3)

        top_str = ", ".join([f"{a} ({c} times)" for a, c in top_actions])
        return (
            f"I've helped you {total} times across {sessions} sessions. "
            f"Your most common actions: {top_str}."
        )

    def should_suggest(self) -> bool:
        """Whether we have enough data to make suggestions."""
        return len(self._data["commands"]) >= 10

    def track_correction(self, original: str, corrected: str) -> None:
        """Track when user rephrases (helps learn intent better)."""
        self._data["corrections"].append({
            "original": original,
            "corrected": corrected,
            "time": datetime.now().isoformat(),
        })
        if len(self._data["corrections"]) > 100:
            self._data["corrections"] = self._data["corrections"][-100:]
        self._save()

    # --- Private methods ---

    def _learn_preferences(self, action: str, details: dict) -> None:
        """Update preferences based on tracked actions."""
        prefs = self._data.setdefault("preferences", {})

        if details:
            # Track language preference
            if "language" in details:
                langs = prefs.setdefault("languages", {})
                lang = details["language"]
                langs[lang] = langs.get(lang, 0) + 1

            # Track theme preference
            if "theme" in details:
                prefs["theme"] = details["theme"]

            # Track project type preference
            if "project_type" in details:
                types = prefs.setdefault("project_types", {})
                ptype = details["project_type"]
                types[ptype] = types.get(ptype, 0) + 1

    def _learn_time_patterns(self, action: str) -> None:
        """Learn what the user does at different times."""
        hour = datetime.now().hour
        patterns = self._data.setdefault("patterns", {})
        hour_key = f"hour_{hour}"
        hour_data = patterns.setdefault(hour_key, {})
        hour_data[action] = hour_data.get(action, 0) + 1

    def _get_common_sequences(self, last_action: str) -> list[tuple[str, int]]:
        """Find what actions commonly follow a given action."""
        commands = self._data["commands"]
        next_actions = Counter()

        for i in range(len(commands) - 1):
            if commands[i]["action"] == last_action:
                next_actions[commands[i + 1]["action"]] += 1

        return next_actions.most_common(3)

    def _get_top_actions(self, n: int = 3) -> list[tuple[str, int]]:
        """Get the N most common actions."""
        actions = Counter(cmd["action"] for cmd in self._data["commands"])
        return actions.most_common(n)

    def _suggest_from_time(self) -> Optional[str]:
        """Suggest based on time of day patterns."""
        hour = datetime.now().hour
        patterns = self._data.get("patterns", {})
        hour_key = f"hour_{hour}"

        if hour_key in patterns:
            hour_data = patterns[hour_key]
            if hour_data:
                top_action = max(hour_data, key=hour_data.get)
                return self._action_to_suggestion(top_action)
        return None

    def _action_to_suggestion(self, action: str) -> str:
        """Convert an action name to a spoken suggestion."""
        suggestions = {
            "code_gen": "Want me to help you write some code?",
            "search": "Would you like me to search for something?",
            "system_cmd": "Need me to open or control something?",
            "chat": "Want to chat or ask me something?",
            "project": "Ready to build a project?",
            "screen_read": "Should I check your screen for errors?",
            "math": "Need help with any calculations?",
            "memory": "Want me to remember something for you?",
            "explain": "Should I explain some code for you?",
        }
        return suggestions.get(action, "What can I help you with?")

    def _load(self) -> None:
        """Load learning data from disk."""
        if os.path.exists(self._filepath):
            try:
                with open(self._filepath, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        """Save learning data to disk."""
        try:
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass
