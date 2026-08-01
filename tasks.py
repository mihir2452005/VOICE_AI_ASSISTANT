"""Voice Task Manager — manage a todo list by voice.

Say:
- "Add task finish the report"
- "Add task buy groceries priority high"
- "What are my tasks" / "Show my todos"
- "Mark task 1 done" / "Complete first task"
- "Delete task 2" / "Remove task 2"
- "Clear all tasks" / "Clear completed"
- "How many tasks do I have"

Tasks persist across restarts in tasks.json.
Nova reminds you of pending tasks on startup.

Usage:
    from tasks import handle_task_command, get_pending_summary
    result = handle_task_command("add task finish the report")
    if result: speak(result)
    
    # On startup:
    summary = get_pending_summary()
    if summary: speak(summary)
"""

import os
import json
import sys
from datetime import datetime
from typing import Optional
import re


TASKS_FILE = "tasks.json"


class TaskManager:
    """Simple voice-driven task list with priorities."""

    def __init__(self, filepath: str = TASKS_FILE):
        self._filepath = filepath
        self._tasks: list[dict] = []
        self._load()

    def add(self, title: str, priority: str = "normal") -> str:
        """Add a new task."""
        task = {
            "id": len(self._tasks) + 1,
            "title": title,
            "priority": priority,  # low, normal, high
            "done": False,
            "created": datetime.now().isoformat(),
            "completed_at": None,
        }
        self._tasks.append(task)
        self._reindex()
        self._save()
        return f"Added task {task['id']}: {title}"

    def complete(self, task_id: int) -> str:
        """Mark a task as done."""
        task = self._find(task_id)
        if not task:
            return f"Task {task_id} not found."
        if task["done"]:
            return f"Task {task_id} is already done."
        task["done"] = True
        task["completed_at"] = datetime.now().isoformat()
        self._save()
        return f"Done! Completed: {task['title']}"

    def delete(self, task_id: int) -> str:
        """Delete a task."""
        task = self._find(task_id)
        if not task:
            return f"Task {task_id} not found."
        self._tasks.remove(task)
        self._reindex()
        self._save()
        return f"Deleted: {task['title']}"

    def list_tasks(self, show_done: bool = False) -> str:
        """List all pending tasks (or all if show_done=True)."""
        tasks = self._tasks if show_done else [t for t in self._tasks if not t["done"]]
        if not tasks:
            return "No pending tasks. You're all caught up!"

        lines = []
        for t in tasks:
            status = "✅" if t["done"] else "⬜"
            priority_icon = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(t["priority"], "🟡")
            lines.append(f"  {status} {t['id']}. {priority_icon} {t['title']}")

        header = f"📋 Tasks ({len(tasks)}):"
        return header + "\n" + "\n".join(lines)

    def clear_completed(self) -> str:
        """Remove all completed tasks."""
        before = len(self._tasks)
        self._tasks = [t for t in self._tasks if not t["done"]]
        self._reindex()
        self._save()
        removed = before - len(self._tasks)
        return f"Cleared {removed} completed tasks."

    def clear_all(self) -> str:
        """Remove all tasks."""
        count = len(self._tasks)
        self._tasks = []
        self._save()
        return f"Cleared all {count} tasks."

    @property
    def pending_count(self) -> int:
        return sum(1 for t in self._tasks if not t["done"])

    @property
    def total_count(self) -> int:
        return len(self._tasks)

    def get_pending_summary(self) -> str:
        """Get a spoken summary of pending tasks (for startup)."""
        pending = [t for t in self._tasks if not t["done"]]
        if not pending:
            return ""
        high = [t for t in pending if t["priority"] == "high"]
        if high:
            return f"You have {len(pending)} pending tasks. {len(high)} are high priority: {high[0]['title']}."
        return f"You have {len(pending)} pending tasks. First one: {pending[0]['title']}."

    def _find(self, task_id: int) -> Optional[dict]:
        for t in self._tasks:
            if t["id"] == task_id:
                return t
        return None

    def _reindex(self):
        for i, t in enumerate(self._tasks, 1):
            t["id"] = i

    def _load(self):
        if os.path.exists(self._filepath):
            try:
                with open(self._filepath, "r", encoding="utf-8") as f:
                    self._tasks = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._tasks = []

    def _save(self):
        try:
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(self._tasks, f, indent=2, ensure_ascii=False)
        except OSError:
            pass


# =============================================================================
# Voice command handler
# =============================================================================

_task_mgr = TaskManager()


def handle_task_command(text: str) -> Optional[str]:
    """Handle task-related voice commands.

    Returns result string or None if not a task command.
    """
    text_lower = text.lower().strip()

    # Add task
    match = re.search(r"add task[:\s]+(.+)", text_lower)
    if match or text_lower.startswith("add task"):
        title = match.group(1).strip() if match else text_lower.replace("add task", "").strip()
        if not title:
            return None

        # Detect priority
        priority = "normal"
        if "high priority" in title or "urgent" in title or "important" in title:
            priority = "high"
            title = re.sub(r"\s*(high priority|urgent|important)\s*", " ", title).strip()
        elif "low priority" in title:
            priority = "low"
            title = title.replace("low priority", "").strip()

        result = _task_mgr.add(title, priority)
        print(f"  {result}")
        sys.stdout.flush()
        return result

    # List tasks
    if any(t in text_lower for t in ["my tasks", "show tasks", "list tasks",
                                      "what are my tasks", "show my todos",
                                      "pending tasks", "what do i need to do"]):
        result = _task_mgr.list_tasks()
        print(f"\n{result}")
        sys.stdout.flush()
        spoken = f"You have {_task_mgr.pending_count} pending tasks." if _task_mgr.pending_count else "No pending tasks."
        return spoken

    # Complete task
    match = re.search(r"(?:mark|complete|finish|done)\s*(?:task)?\s*(\d+)", text_lower)
    if match:
        task_id = int(match.group(1))
        result = _task_mgr.complete(task_id)
        print(f"  {result}")
        sys.stdout.flush()
        return result

    # Also handle "complete first/second task"
    ordinals = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
    for word, num in ordinals.items():
        if f"complete {word}" in text_lower or f"mark {word}" in text_lower or f"finish {word}" in text_lower:
            result = _task_mgr.complete(num)
            print(f"  {result}")
            sys.stdout.flush()
            return result

    # Delete task
    match = re.search(r"(?:delete|remove)\s*(?:task)?\s*(\d+)", text_lower)
    if match:
        task_id = int(match.group(1))
        result = _task_mgr.delete(task_id)
        print(f"  {result}")
        sys.stdout.flush()
        return result

    # Clear
    if "clear all tasks" in text_lower or "delete all tasks" in text_lower:
        result = _task_mgr.clear_all()
        return result
    if "clear completed" in text_lower or "clear done" in text_lower:
        result = _task_mgr.clear_completed()
        return result

    # Count
    if "how many tasks" in text_lower:
        return f"You have {_task_mgr.pending_count} pending and {_task_mgr.total_count} total tasks."

    return None


def get_pending_summary() -> str:
    """Get startup summary of pending tasks."""
    return _task_mgr.get_pending_summary()
