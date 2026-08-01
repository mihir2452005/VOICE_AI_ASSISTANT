"""Bookmark Manager — read, search, and open Brave/Chrome bookmarks by voice.

Reads actual bookmarks from Brave/Chrome profile. No manual config needed.

Say:
- "Show my bookmarks" → lists all bookmark folders and sites
- "Open YouTube from bookmarks" → finds and opens the bookmark
- "Open my Drive bookmark" → fuzzy matches bookmark names
- "What bookmarks do I have" → speaks a summary
- "Open bookmarks in folder X" → lists folder contents

Usage:
    from bookmarks import handle_bookmark_command, get_all_bookmarks
    result = handle_bookmark_command("open YouTube from bookmarks")
    if result: speak(result)
"""

import os
import sys
import json
import re
from typing import Optional


# Brave/Chrome bookmark file paths
_BOOKMARK_PATHS = [
    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Bookmarks"),
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks"),
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Bookmarks"),
]

# Cache
_bookmarks_cache: list[dict] = []
_folders_cache: list[dict] = []
_loaded = False


def _find_bookmark_file() -> Optional[str]:
    """Find the first existing bookmark file."""
    for path in _BOOKMARK_PATHS:
        if os.path.isfile(path):
            return path
    return None


def _load_bookmarks() -> None:
    """Load and flatten all bookmarks from the browser profile."""
    global _bookmarks_cache, _folders_cache, _loaded

    if _loaded:
        return

    path = _find_bookmark_file()
    if not path:
        _loaded = True
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        _loaded = True
        return

    _bookmarks_cache = []
    _folders_cache = []

    def _walk(node, folder_path=""):
        if node.get("type") == "folder":
            name = node.get("name", "")
            current_path = f"{folder_path}/{name}" if folder_path else name
            children = node.get("children", [])

            _folders_cache.append({
                "name": name,
                "path": current_path,
                "count": len([c for c in children if c.get("type") == "url"]),
            })

            for child in children:
                _walk(child, current_path)

        elif node.get("type") == "url":
            _bookmarks_cache.append({
                "name": node.get("name", ""),
                "url": node.get("url", ""),
                "folder": folder_path,
            })

    roots = data.get("roots", {})
    for key in ["bookmark_bar", "other", "synced"]:
        root = roots.get(key)
        if root:
            _walk(root)

    _loaded = True


def get_all_bookmarks() -> list[dict]:
    """Get all bookmarks as a flat list of {name, url, folder}."""
    _load_bookmarks()
    return _bookmarks_cache


def get_folders() -> list[dict]:
    """Get all bookmark folders."""
    _load_bookmarks()
    return _folders_cache


def find_bookmark(query: str) -> Optional[dict]:
    """Fuzzy-find a bookmark by name. Returns best match or None."""
    _load_bookmarks()
    query_lower = query.lower().strip()

    # Exact match first
    for bm in _bookmarks_cache:
        if bm["name"].lower() == query_lower:
            return bm

    # Contains match
    matches = []
    for bm in _bookmarks_cache:
        name_lower = bm["name"].lower()
        if query_lower in name_lower:
            matches.append(bm)
        elif any(word in name_lower for word in query_lower.split()):
            matches.append(bm)

    return matches[0] if matches else None


def find_bookmarks_in_folder(folder_name: str) -> list[dict]:
    """Get all bookmarks in a specific folder."""
    _load_bookmarks()
    folder_lower = folder_name.lower()
    return [
        bm for bm in _bookmarks_cache
        if folder_lower in bm["folder"].lower()
    ]


def list_bookmarks_spoken() -> str:
    """Get a spoken summary of all bookmarks."""
    _load_bookmarks()

    if not _bookmarks_cache:
        return "No bookmarks found in your browser."

    total = len(_bookmarks_cache)
    folders = [f for f in _folders_cache if f["count"] > 0]

    # List top bookmarks
    top_names = [bm["name"] for bm in _bookmarks_cache[:8]]
    names_str = ", ".join(top_names)

    if len(_bookmarks_cache) > 8:
        return f"You have {total} bookmarks. Some of them: {names_str}, and {total - 8} more."
    return f"You have {total} bookmarks: {names_str}."


def list_bookmarks_display() -> str:
    """Get a formatted display of all bookmarks (for terminal)."""
    _load_bookmarks()

    if not _bookmarks_cache:
        return "No bookmarks found."

    lines = [f"📑 Your Bookmarks ({len(_bookmarks_cache)} total):\n"]

    # Group by folder
    by_folder: dict[str, list] = {}
    for bm in _bookmarks_cache:
        folder = bm["folder"] or "Root"
        by_folder.setdefault(folder, []).append(bm)

    for folder, bookmarks in by_folder.items():
        lines.append(f"  📁 {folder}:")
        for bm in bookmarks[:10]:
            lines.append(f"     🔗 {bm['name'][:45]}")
        if len(bookmarks) > 10:
            lines.append(f"     ... +{len(bookmarks) - 10} more")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# VOICE COMMAND HANDLER
# =============================================================================

_TRIGGERS = [
    "bookmark", "bookmarks", "from bookmarks", "my bookmarks",
    "show bookmarks", "list bookmarks", "open bookmark",
]


def handle_bookmark_command(text: str) -> Optional[str]:
    """Handle bookmark-related voice commands.
    
    Returns result string or None if not a bookmark command.
    """
    text_lower = text.lower().strip()

    if not any(t in text_lower for t in _TRIGGERS):
        return None

    # "Show my bookmarks" / "List bookmarks"
    if any(t in text_lower for t in ["show bookmarks", "show my bookmarks",
                                      "list bookmarks", "what bookmarks",
                                      "list my bookmarks"]):
        display = list_bookmarks_display()
        print(f"\n{display}")
        sys.stdout.flush()
        return list_bookmarks_spoken()

    # "Open X from bookmarks" / "Open bookmark X"
    match = re.search(
        r"open\s+(?:bookmark\s+)?(.+?)(?:\s+from bookmarks?|\s+bookmark)?$",
        text_lower
    )
    if match:
        query = match.group(1).strip()
        # Clean up the query
        query = query.replace("from bookmarks", "").replace("bookmark", "").strip()

        if not query:
            return list_bookmarks_spoken()

        bm = find_bookmark(query)
        if bm:
            # Open it
            from browser_control import open_browser
            result = open_browser(bm["url"])
            print(f"  🔗 Opening bookmark: {bm['name']}")
            print(f"     URL: {bm['url'][:60]}")
            sys.stdout.flush()
            return f"Opening {bm['name']} from your bookmarks."
        else:
            return f"Couldn't find a bookmark matching '{query}'. Say 'show my bookmarks' to see all."

    # "Bookmarks in folder X"
    match = re.search(r"bookmarks? (?:in|from) folder (.+)", text_lower)
    if match:
        folder = match.group(1).strip()
        items = find_bookmarks_in_folder(folder)
        if items:
            names = ", ".join(bm["name"] for bm in items[:5])
            print(f"\n  📁 Bookmarks in '{folder}':")
            for bm in items[:8]:
                print(f"     🔗 {bm['name'][:45]}")
            sys.stdout.flush()
            return f"Found {len(items)} bookmarks in {folder}: {names}."
        return f"No bookmarks found in folder '{folder}'."

    return list_bookmarks_spoken()
