"""Proactive Assistance — Nova helps before you even ask.

Detects when you might be stuck and offers help:
- Repeated similar questions → "You've asked about this before. Want me to try differently?"
- Error patterns on screen → "I noticed errors. Want me to diagnose them?"
- Long silence after code gen → "Want me to improve the code or explain it?"
- Same command repeated → "Having trouble? Let me help another way."
- Time-based suggestions → "It's late. Want me to save your work?"

Also provides contextual follow-ups:
- After code gen → "Want me to run it, explain it, or improve it?"
- After search → "Want me to search more or summarize the results?"
- After error → "Want me to fix this or explain what happened?"

Usage:
    from proactive import ProactiveHelper
    helper = ProactiveHelper()
    suggestion = helper.check_and_suggest(last_action, text, response)
    if suggestion: speak(suggestion)
"""

import time
from datetime import datetime
from collections import Counter
from typing import Optional


class ProactiveHelper:
    """Monitors conversation patterns and offers proactive help."""

    def __init__(self):
        self._recent_inputs: list[str] = []       # Last 10 user inputs
        self._recent_actions: list[str] = []      # Last 10 action types
        self._error_count: int = 0                # Consecutive errors
        self._last_suggestion_time: float = 0     # Avoid spamming
        self._repeated_queries: Counter = Counter()
        self._session_start: float = time.time()

    def track_input(self, text: str, action_type: str, had_error: bool = False) -> None:
        """Track user input for pattern detection."""
        self._recent_inputs.append(text.lower().strip())
        self._recent_actions.append(action_type)
        self._repeated_queries[text.lower().strip()[:50]] += 1

        if had_error:
            self._error_count += 1
        else:
            self._error_count = 0

        # Keep lists manageable
        if len(self._recent_inputs) > 10:
            self._recent_inputs.pop(0)
        if len(self._recent_actions) > 10:
            self._recent_actions.pop(0)

    def check_and_suggest(self, last_action: str, user_text: str, response: str) -> Optional[str]:
        """Check patterns and return a proactive suggestion if appropriate.

        Args:
            last_action: What type of action was just performed
            user_text: What the user said
            response: What Nova responded

        Returns:
            Suggestion string to speak, or None if no suggestion needed.
        """
        # Don't suggest too frequently (minimum 60s between suggestions)
        now = time.time()
        if now - self._last_suggestion_time < 60:
            return None

        suggestion = None

        # --- PATTERN 1: Repeated errors ---
        if self._error_count >= 2:
            suggestion = self._suggest_for_errors(user_text, response)

        # --- PATTERN 2: Same question asked repeatedly ---
        elif self._is_repeated_query(user_text):
            suggestion = self._suggest_for_repetition(user_text)

        # --- PATTERN 3: Contextual follow-up after actions ---
        elif last_action in ("code_gen", "project"):
            suggestion = self._suggest_after_code(response)

        elif last_action == "search":
            suggestion = self._suggest_after_search()

        # --- PATTERN 4: Time-based ---
        elif self._should_suggest_break():
            suggestion = self._suggest_break()

        # --- PATTERN 5: Stuck detection (same action type repeated) ---
        elif self._is_stuck():
            suggestion = self._suggest_when_stuck()

        if suggestion:
            self._last_suggestion_time = now

        return suggestion

    def get_contextual_followup(self, action: str, response: str) -> Optional[str]:
        """Get a quick follow-up suggestion after an action completes.

        These are SHORT and only shown in terminal (not spoken unless asked).
        """
        if action in ("code_gen", "project", "multi_file"):
            return "💡 Say: 'improve it', 'run it', 'show me', or 'explain it'"
        elif action == "search":
            return "💡 Say: 'tell me more', 'search again', or ask a follow-up"
        elif action == "error_fix":
            return "💡 Say: 'try again', 'explain the error', or 'different approach'"
        elif action == "browser":
            return "💡 Say: 'scroll down', 'click send', 'new tab', or 'go back'"
        return None

    # --- Private detection methods ---

    def _is_repeated_query(self, text: str) -> bool:
        """Check if user asked the same thing 2+ times."""
        key = text.lower().strip()[:50]
        return self._repeated_queries.get(key, 0) >= 2

    def _is_stuck(self) -> bool:
        """Check if user seems stuck (same action type 3+ times in a row)."""
        if len(self._recent_actions) < 3:
            return False
        last_3 = self._recent_actions[-3:]
        return len(set(last_3)) == 1 and last_3[0] not in ("chat", "system_cmd")

    def _should_suggest_break(self) -> bool:
        """Suggest a break after 45 minutes of continuous use."""
        elapsed = time.time() - self._session_start
        return elapsed > 2700  # 45 minutes

    # --- Suggestion generators ---

    def _suggest_for_errors(self, user_text: str, response: str) -> str:
        """Suggest help after repeated errors."""
        if "timeout" in response.lower() or "took too long" in response.lower():
            return "I'm having trouble processing that. Try breaking it into smaller parts, or say 'use simpler words'."
        elif "error" in response.lower():
            return "I've hit a few errors. Want me to try a different approach, or should I explain what's going wrong?"
        return "Having some trouble. Would you like me to try differently?"

    def _suggest_for_repetition(self, user_text: str) -> str:
        """Suggest alternatives when user repeats themselves."""
        return "You've asked about this before. Want me to try a different approach or give more detail?"

    def _suggest_after_code(self, response: str) -> str:
        """Suggest follow-ups after code generation."""
        if "html" in response.lower() or "website" in response.lower():
            return "Code is ready! Want me to open it in the browser, add more features, or change the style?"
        return "Code generated! Say 'run it' to test, 'improve it' to refine, or 'explain it' for a walkthrough."

    def _suggest_after_search(self) -> str:
        return "Found some results. Want me to dig deeper, summarize, or search for something related?"

    def _suggest_break(self) -> str:
        hour = datetime.now().hour
        if hour >= 23 or hour < 5:
            return "It's getting late. Want me to save your progress and set a reminder for tomorrow?"
        return "You've been working for a while. Want me to save a summary of what we did today?"

    def _suggest_when_stuck(self) -> str:
        last_action = self._recent_actions[-1] if self._recent_actions else "chat"
        if last_action == "code_gen":
            return "Seems like the code generation isn't quite right. Want me to try a completely different approach?"
        elif last_action == "browser":
            return "Having trouble with the browser? Try saying exactly what you see and what you want to click."
        elif last_action == "search":
            return "Not finding what you need? Try different keywords or ask me to explain the topic instead."
        return "Need help with something else? I can write code, search the web, control your browser, or just chat."
