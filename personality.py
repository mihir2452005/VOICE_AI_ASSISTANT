"""Personality Modes — switch Nova's speaking style on the fly.

Say "be more casual", "switch to professional", "be funny", or "be brief"
to change how Nova responds. Persists until changed again.

Usage from main.py:
    from personality import PersonalityManager
    persona = PersonalityManager()
    persona.switch("casual")
    prompt = persona.get_system_prompt()  # Inject into Ollama context
    
    # Check if user wants to switch
    new_mode = persona.detect_switch("be more professional")
    if new_mode:
        persona.switch(new_mode)
"""

from typing import Optional


# Available personality modes
MODES = {
    "default": {
        "name": "Default",
        "prompt": (
            "You are Nova, a helpful voice AI assistant. "
            "Keep responses short and conversational (1-3 sentences). "
            "Be friendly and natural."
        ),
        "emoji": "🤖",
    },
    "casual": {
        "name": "Casual",
        "prompt": (
            "You are Nova, a super chill voice assistant. "
            "Talk like a friendly buddy — use casual language, contractions, "
            "maybe some slang. Keep it short and fun. No formality needed."
        ),
        "emoji": "😎",
    },
    "professional": {
        "name": "Professional",
        "prompt": (
            "You are Nova, a professional voice assistant. "
            "Respond formally and precisely. Use proper grammar, "
            "avoid slang or casual language. Be concise but thorough."
        ),
        "emoji": "👔",
    },
    "funny": {
        "name": "Funny",
        "prompt": (
            "You are Nova, a witty and humorous voice assistant. "
            "Always include a joke, pun, or funny observation in your responses. "
            "Be entertaining but still helpful. Keep it short — one-liners preferred."
        ),
        "emoji": "😂",
    },
    "brief": {
        "name": "Brief",
        "prompt": (
            "You are Nova, an extremely concise voice assistant. "
            "Answer in as FEW words as possible. One sentence max. "
            "No filler, no pleasantries, just the answer."
        ),
        "emoji": "⚡",
    },
    "teacher": {
        "name": "Teacher",
        "prompt": (
            "You are Nova, a patient and encouraging teacher. "
            "Explain things clearly with simple examples. "
            "Break complex topics into easy steps. "
            "Keep voice responses to 2-3 sentences."
        ),
        "emoji": "📚",
    },
}

# Trigger phrases that activate each mode
_SWITCH_TRIGGERS = {
    "casual": ["be casual", "be more casual", "casual mode", "chill mode", "be chill"],
    "professional": ["be professional", "professional mode", "be formal", "formal mode"],
    "funny": ["be funny", "funny mode", "be humorous", "make me laugh", "comedy mode"],
    "brief": ["be brief", "brief mode", "short answers", "be concise", "less words"],
    "teacher": ["teacher mode", "explain mode", "be a teacher", "teach me"],
    "default": ["normal mode", "default mode", "be normal", "reset personality"],
}


class PersonalityManager:
    """Manages Nova's personality/speaking style."""

    def __init__(self):
        self._current = "default"

    @property
    def current_mode(self) -> str:
        """Current active mode name."""
        return self._current

    @property
    def current_emoji(self) -> str:
        """Emoji for current mode."""
        return MODES[self._current]["emoji"]

    @property
    def mode_display(self) -> str:
        """Display name of current mode."""
        return MODES[self._current]["name"]

    def switch(self, mode: str) -> bool:
        """Switch to a personality mode. Returns True if valid."""
        if mode in MODES:
            self._current = mode
            return True
        return False

    def get_system_prompt(self) -> str:
        """Get the system prompt for the current personality."""
        return MODES[self._current]["prompt"]

    def detect_switch(self, text: str) -> Optional[str]:
        """Check if user text is asking to switch personality.

        Args:
            text: User's transcribed speech (lowercased).

        Returns:
            Mode name if switch detected, None otherwise.
        """
        text_lower = text.lower()
        for mode, triggers in _SWITCH_TRIGGERS.items():
            for trigger in triggers:
                if trigger in text_lower:
                    return mode
        return None

    def list_modes(self) -> str:
        """Get a speakable list of available modes."""
        names = [f"{v['emoji']} {v['name']}" for v in MODES.values()]
        return "Available modes: " + ", ".join(names)
