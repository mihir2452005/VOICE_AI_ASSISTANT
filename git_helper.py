"""Git Helper — full git workflow by voice.

Say: "git status", "commit with message fixed login bug", "push to main", "git diff"
Executes git commands and reads back results.

Usage:
    from git_helper import handle_git
    result = handle_git("git status")
    if result: speak(result)
"""

import subprocess
import sys
import re
from typing import Optional


_TRIGGERS = {
    "git status": ["git status", "what changed", "show changes"],
    "git diff": ["git diff", "show diff", "what's different"],
    "git log": ["git log", "show commits", "recent commits", "commit history"],
    "git add": ["git add", "stage all", "stage changes", "add all"],
    "git commit": ["commit with message", "commit message", "git commit"],
    "git push": ["git push", "push to", "push changes", "push it"],
    "git pull": ["git pull", "pull changes", "pull latest"],
    "git branch": ["git branch", "what branch", "current branch", "show branches"],
}


def _run_git(command: str) -> tuple[str, bool]:
    """Run a git command and return (output, success)."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=15, encoding="utf-8", errors="replace"
        )
        output = (result.stdout + result.stderr).strip()
        return output, result.returncode == 0
    except subprocess.TimeoutExpired:
        return "Git command timed out.", False
    except Exception as e:
        return f"Error: {e}", False


def handle_git(text: str) -> Optional[str]:
    """Handle git commands by voice. Returns result or None."""
    text_lower = text.lower().strip()

    # Git status
    if any(t in text_lower for t in _TRIGGERS["git status"]):
        output, ok = _run_git("git status --short")
        if ok:
            if not output:
                return "Working tree is clean. Nothing to commit."
            lines = output.strip().split("\n")
            return f"{len(lines)} files changed. {lines[0]}"
        return f"Git error: {output[:100]}"

    # Git diff
    if any(t in text_lower for t in _TRIGGERS["git diff"]):
        output, ok = _run_git("git diff --stat")
        if ok:
            if not output:
                return "No differences found."
            lines = output.strip().split("\n")
            return f"Changes in {len(lines)} files. {lines[-1] if lines else ''}"
        return "Not a git repository or no changes."

    # Git log
    if any(t in text_lower for t in _TRIGGERS["git log"]):
        output, ok = _run_git("git log --oneline -5")
        if ok:
            lines = output.strip().split("\n")
            return f"Last {len(lines)} commits. Most recent: {lines[0]}"
        return "No git history found."

    # Git add all
    if any(t in text_lower for t in _TRIGGERS["git add"]):
        output, ok = _run_git("git add -A")
        if ok:
            return "All changes staged for commit."
        return f"Staging failed: {output[:100]}"

    # Git commit
    if any(t in text_lower for t in _TRIGGERS["git commit"]):
        # Extract commit message
        msg = ""
        for pattern in [r"commit (?:with )?message (.+)", r"commit (.+)"]:
            match = re.search(pattern, text_lower)
            if match:
                msg = match.group(1).strip()
                break
        if not msg:
            msg = "Update via voice assistant"

        # Stage everything first
        _run_git("git add -A")
        output, ok = _run_git(f'git commit -m "{msg}"')
        if ok:
            return f"Committed: {msg}"
        if "nothing to commit" in output.lower():
            return "Nothing to commit. Working tree is clean."
        return f"Commit failed: {output[:100]}"

    # Git push
    if any(t in text_lower for t in _TRIGGERS["git push"]):
        print("  ⬆️ Pushing...")
        sys.stdout.flush()
        output, ok = _run_git("git push")
        if ok:
            return "Pushed successfully."
        return f"Push failed: {output[:100]}"

    # Git pull
    if any(t in text_lower for t in _TRIGGERS["git pull"]):
        print("  ⬇️ Pulling...")
        sys.stdout.flush()
        output, ok = _run_git("git pull")
        if ok:
            return f"Pulled latest changes. {output[:80]}"
        return f"Pull failed: {output[:100]}"

    # Git branch
    if any(t in text_lower for t in _TRIGGERS["git branch"]):
        output, ok = _run_git("git branch --show-current")
        if ok:
            return f"Current branch: {output.strip()}"
        return "Not in a git repository."

    return None
