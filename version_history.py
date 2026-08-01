"""Version History — undo/rollback any generated file.

Every time code is generated or updated, the previous version is saved.
Say 'undo', 'rollback', or 'show versions' to manage history.

Say:
- "Undo" / "Undo last change" → reverts to previous version
- "Show versions" / "Version history" → lists all versions of last file
- "Rollback to version 2" → restores a specific version
- "Compare versions" → shows what changed

Usage:
    from version_history import VersionManager
    vm = VersionManager()
    vm.save_version("generated_code/code.py", code_content)  # Before overwrite
    vm.undo()  # Revert
    vm.rollback(2)  # Go to version 2
"""

import os
import sys
import re
import json
import shutil
import time
from datetime import datetime
from typing import Optional


HISTORY_DIR = ".version_history"
HISTORY_INDEX = os.path.join(HISTORY_DIR, "index.json")


class VersionManager:
    """Manages version history of generated files."""

    def __init__(self):
        os.makedirs(HISTORY_DIR, exist_ok=True)
        self._index = self._load_index()
        self._last_file = self._index.get("last_file", "")

    def save_version(self, filepath: str, content: str) -> int:
        """Save current content as a new version before overwriting.
        
        Returns the version number.
        """
        abs_path = os.path.abspath(filepath)
        file_key = abs_path.replace("\\", "/")

        # Get or create file history
        if file_key not in self._index.get("files", {}):
            self._index.setdefault("files", {})[file_key] = {"versions": [], "current": 0}

        file_info = self._index["files"][file_key]
        version_num = len(file_info["versions"]) + 1

        # Save version file
        version_filename = f"v{version_num}_{os.path.basename(filepath)}"
        version_path = os.path.join(HISTORY_DIR, version_filename)

        with open(version_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Update index
        file_info["versions"].append({
            "num": version_num,
            "path": version_path,
            "timestamp": datetime.now().isoformat(),
            "size": len(content),
        })
        file_info["current"] = version_num
        self._index["last_file"] = file_key
        self._last_file = file_key
        self._save_index()

        return version_num

    def undo(self) -> Optional[str]:
        """Undo the last change (revert to previous version).
        
        Returns status message or None if nothing to undo.
        """
        if not self._last_file:
            return "Nothing to undo. No files have been generated yet."

        file_info = self._index.get("files", {}).get(self._last_file)
        if not file_info or len(file_info["versions"]) < 2:
            return "No previous version to revert to."

        # Get previous version
        current_idx = file_info["current"]
        if current_idx <= 1:
            return "Already at the first version. Can't undo further."

        prev_version = file_info["versions"][current_idx - 2]  # -2 because list is 0-indexed
        prev_path = prev_version["path"]

        if not os.path.isfile(prev_path):
            return "Previous version file is missing."

        # Read previous version content
        with open(prev_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Overwrite the actual file
        actual_file = self._last_file.replace("/", os.sep)
        if os.path.dirname(actual_file):
            os.makedirs(os.path.dirname(actual_file), exist_ok=True)
        with open(actual_file, "w", encoding="utf-8") as f:
            f.write(content)

        file_info["current"] = current_idx - 1
        self._save_index()

        filename = os.path.basename(actual_file)
        return f"Undone! Reverted {filename} to version {current_idx - 1}."

    def rollback(self, version_num: int) -> Optional[str]:
        """Rollback to a specific version number."""
        if not self._last_file:
            return "No files to rollback."

        file_info = self._index.get("files", {}).get(self._last_file)
        if not file_info:
            return "No version history for this file."

        if version_num < 1 or version_num > len(file_info["versions"]):
            return f"Version {version_num} doesn't exist. Available: 1-{len(file_info['versions'])}."

        version = file_info["versions"][version_num - 1]
        version_path = version["path"]

        if not os.path.isfile(version_path):
            return f"Version {version_num} file is missing."

        with open(version_path, "r", encoding="utf-8") as f:
            content = f.read()

        actual_file = self._last_file.replace("/", os.sep)
        with open(actual_file, "w", encoding="utf-8") as f:
            f.write(content)

        file_info["current"] = version_num
        self._save_index()

        filename = os.path.basename(actual_file)
        return f"Rolled back {filename} to version {version_num}."

    def show_versions(self) -> str:
        """Show all versions of the last edited file."""
        if not self._last_file:
            return "No version history yet."

        file_info = self._index.get("files", {}).get(self._last_file)
        if not file_info or not file_info["versions"]:
            return "No versions saved for this file."

        filename = os.path.basename(self._last_file)
        lines = [f"📜 Version history for {filename}:\n"]

        for v in file_info["versions"]:
            current = " ← current" if v["num"] == file_info["current"] else ""
            ts = v["timestamp"][:16].replace("T", " ")
            lines.append(f"  v{v['num']}  ({ts}, {v['size']} chars){current}")

        return "\n".join(lines)

    def get_stats(self) -> str:
        """Get version history statistics."""
        total_files = len(self._index.get("files", {}))
        total_versions = sum(
            len(f["versions"]) for f in self._index.get("files", {}).values()
        )
        return f"{total_files} files tracked, {total_versions} total versions saved."

    def _load_index(self) -> dict:
        if os.path.isfile(HISTORY_INDEX):
            try:
                with open(HISTORY_INDEX, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"files": {}, "last_file": ""}

    def _save_index(self):
        try:
            with open(HISTORY_INDEX, "w", encoding="utf-8") as f:
                json.dump(self._index, f, indent=2)
        except OSError:
            pass


# =============================================================================
# VOICE COMMAND HANDLER
# =============================================================================

_vm = VersionManager()


def save_version(filepath: str, content: str) -> int:
    """Call this before overwriting a file. Returns version number."""
    return _vm.save_version(filepath, content)


def handle_version_command(text: str) -> Optional[str]:
    """Handle version-related voice commands."""
    text_lower = text.lower().strip()

    # Undo
    if text_lower in ("undo", "undo last change", "revert", "go back"):
        result = _vm.undo()
        if result:
            print(f"  {result}")
            sys.stdout.flush()
        return result

    # Show versions
    if any(t in text_lower for t in ["show versions", "version history", "list versions", "show history"]):
        result = _vm.show_versions()
        print(f"\n{result}")
        sys.stdout.flush()
        return f"Showing version history. You have {_vm.get_stats()}"

    # Rollback to specific version
    match = re.search(r"(?:rollback|revert|go back) (?:to )?(?:version )?(\d+)", text_lower)
    if match:
        version = int(match.group(1))
        result = _vm.rollback(version)
        if result:
            print(f"  {result}")
            sys.stdout.flush()
        return result

    # Stats
    if "version stats" in text_lower or "how many versions" in text_lower:
        return _vm.get_stats()

    return None
