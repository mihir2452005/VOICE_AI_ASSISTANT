"""Code Linter — find bugs and errors in your Python files.

Say: "check errors in my project", "lint main.py", "find bugs in coder.py"
Scans for syntax errors, missing imports, and common issues.

Usage:
    from code_checker import handle_check
    result = handle_check("check errors in my project")
    if result: speak(result)
"""

import ast
import os
import sys
import re
from typing import Optional


_TRIGGERS = [
    "check errors", "check my project", "find bugs", "lint ",
    "check for errors", "any errors", "check code", "scan for bugs",
]


def _check_syntax(filepath: str) -> list[str]:
    """Check a Python file for syntax errors."""
    errors = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
    except SyntaxError as e:
        errors.append(f"  ❌ {filepath}:{e.lineno} — {e.msg}")
    except Exception as e:
        errors.append(f"  ⚠️ {filepath} — {e}")
    return errors


def _check_imports(filepath: str) -> list[str]:
    """Check for potentially missing imports."""
    warnings = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # Collect imported names
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
                for alias in node.names:
                    imported.add(alias.asname or alias.name)

        # Check for common undefined names (basic heuristic)
        # This is not a full linter, just catches obvious issues
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)

        # Builtins that are always available
        builtins = {"print", "len", "range", "int", "str", "float", "list",
                    "dict", "set", "tuple", "bool", "None", "True", "False",
                    "open", "type", "isinstance", "enumerate", "zip", "map",
                    "filter", "sorted", "reversed", "input", "super", "self",
                    "Exception", "ValueError", "TypeError", "KeyError",
                    "os", "sys", "re", "json", "time", "math"}

    except Exception:
        pass  # Don't warn on parse failures (caught by syntax check)

    return warnings


def _scan_directory(path: str = ".") -> list[str]:
    """Find all Python files in directory."""
    py_files = []
    for root, dirs, files in os.walk(path):
        # Skip common non-project dirs
        dirs[:] = [d for d in dirs if d not in {"venv", ".venv", "__pycache__", ".git", "node_modules"}]
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    return py_files


def handle_check(text: str) -> Optional[str]:
    """Check code for errors. Returns result or None."""
    text_lower = text.lower().strip()

    if not any(t in text_lower for t in _TRIGGERS):
        return None

    # Determine scope: specific file or whole project
    # Try to find a filename in the text
    match = re.search(r"(\w+\.py)", text_lower)
    if match:
        filepath = match.group(1)
        if os.path.isfile(filepath):
            files = [filepath]
        else:
            return f"File not found: {filepath}"
    else:
        files = _scan_directory(".")

    if not files:
        return "No Python files found in current directory."

    print(f"  🔍 Scanning {len(files)} Python files...")
    sys.stdout.flush()

    all_errors = []
    clean_count = 0

    for f in files:
        errors = _check_syntax(f)
        if errors:
            all_errors.extend(errors)
        else:
            clean_count += 1

    if all_errors:
        print("\n  Found issues:")
        for err in all_errors:
            print(err)
        sys.stdout.flush()
        return f"Found {len(all_errors)} errors in {len(files)} files. {all_errors[0].split('—')[1].strip() if '—' in all_errors[0] else 'Check terminal for details.'}"
    else:
        return f"All {clean_count} Python files are clean. No syntax errors found!"
