"""File Explorer by Voice — browse folders and understand project structure.

Say: "what files are here", "show project structure", "list files in projects"
Reads directory trees and describes the layout.

Usage:
    from file_explorer import handle_explore
    result = handle_explore("what files are in my project")
    if result: speak(result)
"""

import os
import sys
import re
from typing import Optional


_TRIGGERS = [
    "what files", "list files", "show files", "show structure",
    "project structure", "folder structure", "what's in ",
    "browse ", "explore ", "show me the files",
]

# Skip these directories
_SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", ".idea", ".kiro"}


def _tree(path: str, prefix: str = "", max_depth: int = 3, depth: int = 0) -> list[str]:
    """Generate a tree view of a directory."""
    if depth >= max_depth:
        return []

    lines = []
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return [f"{prefix}(permission denied)"]

    # Separate dirs and files
    dirs = [e for e in entries if os.path.isdir(os.path.join(path, e)) and e not in _SKIP_DIRS]
    files = [e for e in entries if os.path.isfile(os.path.join(path, e))]

    # Show files first
    for f in files[:15]:  # Cap at 15 files
        lines.append(f"{prefix}├── {f}")
    if len(files) > 15:
        lines.append(f"{prefix}├── ... ({len(files) - 15} more files)")

    # Then directories
    for i, d in enumerate(dirs[:8]):  # Cap at 8 dirs
        is_last = (i == len(dirs) - 1) or (i == 7)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{d}/")
        sub_prefix = prefix + ("    " if is_last else "│   ")
        lines.extend(_tree(os.path.join(path, d), sub_prefix, max_depth, depth + 1))

    if len(dirs) > 8:
        lines.append(f"{prefix}└── ... ({len(dirs) - 8} more folders)")

    return lines


def handle_explore(text: str) -> Optional[str]:
    """Explore file structure by voice. Returns description or None."""
    text_lower = text.lower().strip()

    if not any(t in text_lower for t in _TRIGGERS):
        return None

    # Determine target directory
    target = "."

    # Check for specific folder mention
    match = re.search(r"(?:in|of|inside)\s+(.+?)(?:\s+folder|\s+directory)?$", text_lower)
    if match:
        folder = match.group(1).strip()
        if os.path.isdir(folder):
            target = folder
        elif os.path.isdir(os.path.join(".", folder)):
            target = os.path.join(".", folder)

    # Generate tree
    tree_lines = _tree(target)

    if not tree_lines:
        return f"Folder is empty or doesn't exist: {target}"

    # Count stats
    total_files = sum(1 for l in tree_lines if "├── " in l and "/" not in l.split("── ")[-1])
    total_dirs = sum(1 for l in tree_lines if l.rstrip().endswith("/"))

    # Display
    print(f"\n  📁 {os.path.abspath(target)}/")
    for line in tree_lines[:25]:  # Show max 25 lines
        print(f"  {line}")
    if len(tree_lines) > 25:
        print(f"  ... ({len(tree_lines) - 25} more entries)")
    sys.stdout.flush()

    # Spoken summary
    py_files = sum(1 for l in tree_lines if ".py" in l)
    return f"Found {total_files} files and {total_dirs} folders. {py_files} Python files."
