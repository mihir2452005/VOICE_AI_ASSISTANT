"""Conversation Logger — saves all interactions to timestamped files.

Logs every exchange (user speech + Nova response) with timestamps.
Creates daily log files in the logs/ folder for easy review.

Usage from main.py:
    from logger import ConversationLogger
    log = ConversationLogger()
    log.log_user("what time is it")
    log.log_nova("It's 3:30 PM on Friday.")
    log.log_system("Opened Chrome")  # For system commands
"""

import os
from datetime import datetime


LOGS_DIR = "logs"


class ConversationLogger:
    """Saves conversations to daily text files."""

    def __init__(self, logs_dir: str = LOGS_DIR):
        self._logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        self._session_start = datetime.now()
        self._turn_count = 0

        # Write session header
        self._write(f"\n{'='*50}")
        self._write(f"  Session started: {self._session_start.strftime('%I:%M %p')}")
        self._write(f"{'='*50}\n")

    def log_user(self, text: str) -> None:
        """Log what the user said."""
        self._turn_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{timestamp}] 👤 You: {text}")

    def log_nova(self, text: str) -> None:
        """Log Nova's response."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{timestamp}] 🤖 Nova: {text}")

    def log_system(self, action: str) -> None:
        """Log a system command that was executed."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{timestamp}] ⚡ System: {action}")

    def log_search(self, query: str, result_count: int) -> None:
        """Log a web search."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{timestamp}] 🔍 Search: \"{query}\" ({result_count} results)")

    @property
    def today_file(self) -> str:
        """Path to today's log file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self._logs_dir, f"conversation_{date_str}.txt")

    @property
    def turn_count(self) -> int:
        """Number of user turns this session."""
        return self._turn_count

    def _write(self, line: str) -> None:
        """Append a line to today's log file."""
        try:
            with open(self.today_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass
