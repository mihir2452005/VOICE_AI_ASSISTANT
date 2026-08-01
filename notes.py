"""Voice Notes — hands-free note-taking by voice.

Say:
- "Take a note: idea for AI chatbot project"
- "Note: buy milk tomorrow"
- "Save note meeting with professor at 3pm"
- "Read my notes" / "Read today's notes"
- "What did I note today"
- "Delete last note"
- "How many notes today"

Notes are saved to dated .txt files in the notes/ folder.
Each note has a timestamp for easy review.

Usage:
    from notes import handle_note_command
    result = handle_note_command("take a note project deadline is friday")
    if result: speak(result)
"""

import os
import sys
import re
from datetime import datetime, date
from typing import Optional


NOTES_DIR = "notes"


def _today_file() -> str:
    """Get path to today's notes file."""
    os.makedirs(NOTES_DIR, exist_ok=True)
    return os.path.join(NOTES_DIR, f"notes_{date.today().isoformat()}.txt")


def _save_note(content: str) -> str:
    """Save a note with timestamp to today's file."""
    filepath = _today_file()
    timestamp = datetime.now().strftime("%H:%M")

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {content}\n")

    return f"Noted: {content[:50]}"


def _read_notes(target_date: Optional[date] = None) -> list[str]:
    """Read all notes from a date (default: today)."""
    d = target_date or date.today()
    filepath = os.path.join(NOTES_DIR, f"notes_{d.isoformat()}.txt")

    if not os.path.isfile(filepath):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    return lines


def _count_notes() -> int:
    """Count today's notes."""
    return len(_read_notes())


def _delete_last_note() -> str:
    """Delete the last note from today's file."""
    filepath = _today_file()
    if not os.path.isfile(filepath):
        return "No notes to delete."

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [l for l in f.readlines() if l.strip()]

    if not lines:
        return "No notes to delete."

    deleted = lines.pop().strip()
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return f"Deleted last note: {deleted[:40]}"


# =============================================================================
# VOICE COMMAND HANDLER
# =============================================================================

_NOTE_TRIGGERS = [
    "take a note", "note:", "save note", "make a note",
    "add a note", "write a note", "jot down",
]

_READ_TRIGGERS = [
    "read my notes", "read today's notes", "read notes",
    "what did i note", "show my notes", "play my notes",
    "my notes today", "notes from today",
]


def handle_note_command(text: str) -> Optional[str]:
    """Handle voice note commands. Returns spoken result or None."""
    text_lower = text.lower().strip()

    # Save a note
    for trigger in _NOTE_TRIGGERS:
        if text_lower.startswith(trigger) or trigger in text_lower:
            # Extract note content
            content = text
            for t in _NOTE_TRIGGERS:
                if t in text_lower:
                    idx = text_lower.find(t) + len(t)
                    content = text[idx:].strip().lstrip(":").strip()
                    break
            if not content:
                content = text
            result = _save_note(content)
            count = _count_notes()
            print(f"  📝 {result} (#{count} today)")
            sys.stdout.flush()
            return f"Got it. That's note number {count} today."

    # Read notes
    if any(t in text_lower for t in _READ_TRIGGERS):
        notes = _read_notes()
        if not notes:
            return "No notes today. Say 'take a note' to start."

        print(f"\n  📝 Today's Notes ({len(notes)}):")
        for note in notes:
            print(f"     {note}")
        sys.stdout.flush()

        # Speak summary (not all notes — too long)
        if len(notes) <= 3:
            spoken = ". ".join(n.split("] ", 1)[-1] for n in notes)
            return f"You have {len(notes)} notes today: {spoken}"
        else:
            first_3 = ". ".join(n.split("] ", 1)[-1] for n in notes[:3])
            return f"You have {len(notes)} notes today. First three: {first_3}"

    # Delete last note
    if "delete last note" in text_lower or "remove last note" in text_lower:
        result = _delete_last_note()
        return result

    # Count notes
    if "how many notes" in text_lower:
        count = _count_notes()
        return f"You have {count} notes today."

    return None
