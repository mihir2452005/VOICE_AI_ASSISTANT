"""Persistent Memory — Nova remembers things about you across restarts.

Stores facts, preferences, and personal info in a local JSON file.
No cloud, no database — just a simple file that survives restarts.

Usage from main.py:
    from memory import Memory
    mem = Memory()
    mem.remember("personal", "User's name is Arjun")
    mem.remember("preference", "Likes dark mode")
    facts = mem.recall()  # Get all facts
    facts = mem.recall("name")  # Search for facts about 'name'
    mem.forget_all()  # Clear everything
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional


MEMORY_FILE = "memory.json"
MAX_FACTS = 200


class Memory:
    """Persistent fact storage with search and auto-save."""

    def __init__(self, filepath: str = MEMORY_FILE):
        self._filepath = filepath
        self._facts: list[dict] = []
        self._load()

    def remember(self, category: str, fact: str) -> None:
        """Store a fact. Auto-saves to disk.

        Args:
            category: Group label (e.g., 'personal', 'preference', 'work')
            fact: The information to remember
        """
        entry = {
            "category": category,
            "fact": fact,
            "timestamp": datetime.now().isoformat(),
        }

        # Don't store duplicates
        for existing in self._facts:
            if existing["fact"].lower() == fact.lower():
                return

        self._facts.append(entry)

        # Cap at MAX_FACTS (remove oldest)
        if len(self._facts) > MAX_FACTS:
            self._facts = self._facts[-MAX_FACTS:]

        self._save()

    def recall(self, query: str = "") -> list[dict]:
        """Retrieve facts, optionally filtered by search query.

        Args:
            query: Search term (matches category or fact text). Empty = all.

        Returns:
            List of matching fact dicts with category, fact, timestamp.
        """
        if not query:
            return list(self._facts)

        q = query.lower()
        return [
            f for f in self._facts
            if q in f["category"].lower() or q in f["fact"].lower()
        ]

    def recall_as_text(self, query: str = "") -> str:
        """Get facts as a formatted string (for injecting into LLM context)."""
        facts = self.recall(query)
        if not facts:
            return "No memories stored yet."
        lines = [f"- [{f['category']}] {f['fact']}" for f in facts[-20:]]  # Last 20
        return "\n".join(lines)

    def forget(self, query: str) -> int:
        """Remove facts matching a query. Returns count removed."""
        q = query.lower()
        before = len(self._facts)
        self._facts = [
            f for f in self._facts
            if q not in f["category"].lower() and q not in f["fact"].lower()
        ]
        removed = before - len(self._facts)
        if removed > 0:
            self._save()
        return removed

    def forget_all(self) -> None:
        """Clear all memories."""
        self._facts = []
        self._save()

    @property
    def count(self) -> int:
        """Number of stored facts."""
        return len(self._facts)

    def _load(self) -> None:
        """Load facts from disk."""
        if not os.path.exists(self._filepath):
            return
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._facts = data
        except (json.JSONDecodeError, OSError):
            self._facts = []

    def _save(self) -> None:
        """Persist facts to disk."""
        try:
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(self._facts, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"⚠️ Memory save failed: {e}", file=sys.stderr)


# =============================================================================
# AUTO-LEARN — silently extract facts from every conversation
# =============================================================================

import re


# Patterns that indicate personal information worth remembering
_EXTRACTION_PATTERNS = [
    # Name patterns
    (r"(?:my name is|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", "personal", "User's name is {0}"),
    (r"^i'm\s+([A-Z][a-z]+)(?:\s|$|,|\.)", "personal", "User's name is {0}"),

    # Profession/role
    (r"i (?:am|work as|work at)\s+(?:a |an )?(.+?)(?:\.|$|,)", "professional", "User works as {0}"),
    (r"i'm (?:a |an )?(\w+ (?:engineer|developer|designer|student|teacher|doctor|manager|analyst))", "professional", "User is {0}"),

    # Preferences
    (r"i (?:like|love|prefer|enjoy)\s+(.+?)(?:\.|$|,)", "preference", "User likes {0}"),
    (r"i (?:hate|dislike|don't like)\s+(.+?)(?:\.|$|,)", "preference", "User dislikes {0}"),
    (r"my favorite (\w+) is (.+?)(?:\.|$|,)", "preference", "User's favorite {0} is {1}"),

    # Personal info
    (r"i live in\s+(.+?)(?:\.|$|,)", "personal", "User lives in {0}"),
    (r"i'm from\s+(.+?)(?:\.|$|,)", "personal", "User is from {0}"),
    (r"i (?:study|studying)\s+(.+?)(?:\.|$|,)", "education", "User studies {0}"),
    (r"i go to\s+(.+?)(?:\.|$|university|college)", "education", "User attends {0}"),
    (r"my (?:birthday|bday) is\s+(.+?)(?:\.|$|,)", "personal", "User's birthday is {0}"),

    # Technical preferences
    (r"i (?:use|code in|program in|work with)\s+(.+?)(?:\.|$|,)", "tech", "User uses {0}"),
    (r"i prefer\s+(\w+)\s+(?:over|instead of|rather than)\s+(\w+)", "preference", "User prefers {0} over {1}"),
    (r"(?:always|usually) use (?:dark|light) (?:mode|theme)", "preference", "User prefers dark mode"),

    # Project info
    (r"(?:my|our) project (?:is|about)\s+(.+?)(?:\.|$|,)", "project", "User's project: {0}"),
    (r"i'm (?:working on|building)\s+(.+?)(?:\.|$|,)", "project", "User is building {0}"),
]


class AutoLearn:
    """Silently extract facts from conversations and store them.
    
    Call analyze() on every user input to passively learn about the user.
    Only stores NEW information (no duplicates).
    """

    def __init__(self, memory: 'Memory'):
        self._memory = memory
        self._learned_this_session: set = set()  # Avoid re-learning same facts

    def analyze(self, user_text: str) -> list[str]:
        """Analyze user text and extract any personal facts.
        
        Args:
            user_text: What the user said (transcribed speech).
            
        Returns:
            List of facts that were learned (empty if nothing new).
        """
        learned = []

        for pattern, category, template in _EXTRACTION_PATTERNS:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                # Build the fact from template
                groups = match.groups()
                try:
                    fact = template.format(*groups)
                except (IndexError, KeyError):
                    fact = template.format(groups[0] if groups else "")

                # Clean up
                fact = fact.strip().rstrip(".,!?")
                if len(fact) < 5 or len(fact) > 200:
                    continue

                # Skip if already known or learned this session
                fact_lower = fact.lower()
                if fact_lower in self._learned_this_session:
                    continue

                # Check if already in memory
                existing = self._memory.recall(fact.split()[-1])
                already_known = any(
                    fact_lower in existing_fact.get("fact", "").lower()
                    for existing_fact in existing
                )
                if already_known:
                    continue

                # Store it!
                self._memory.remember(category, fact)
                self._learned_this_session.add(fact_lower)
                learned.append(fact)

        return learned

    def analyze_response(self, user_text: str, nova_response: str) -> None:
        """Analyze the full exchange for context learning.
        
        Learns things like what topics the user frequently asks about.
        """
        # Track frequent topics (simple word frequency)
        words = user_text.lower().split()
        topic_words = [w for w in words if len(w) > 4 and w.isalpha()]

        # If user asks about the same topic 3+ times, remember it as interest
        # (This is handled by adaptive.py — we just focus on explicit facts here)
        pass
