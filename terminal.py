"""Voice Terminal — run shell commands by voice.

Say: "run pip install flask", "run python app.py", "run dir"
Executes the command and reads back the output.

Usage:
    from terminal import handle_terminal
    result = handle_terminal("run pip install requests")
    if result: speak(result)
"""

import subprocess
import sys
import re
from typing import Optional


# Safety: commands that are BLOCKED (destructive)
_BLOCKED = ["format", "rmdir /s", "del /s", "rm -rf", "shutdown", "restart"]

# Trigger patterns
_TRIGGERS = ["run ", "execute ", "terminal ", "command "]


def handle_terminal(text: str) -> Optional[str]:
    """Execute a terminal command from voice input.

    Returns output string if command was executed, None if not a terminal request.
    """
    text_lower = text.lower().strip()

    # Check if this is a terminal request
    command = None
    for trigger in _TRIGGERS:
        if text_lower.startswith(trigger):
            command = text[len(trigger):].strip()
            break

    if not command:
        return None

    # Safety check
    for blocked in _BLOCKED:
        if blocked in command.lower():
            return f"Blocked dangerous command: {command}"

    print(f"  $ {command}")
    sys.stdout.flush()

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=30, encoding="utf-8", errors="replace"
        )

        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode == 0:
            if output:
                # Truncate long output for voice
                lines = output.split("\n")
                if len(lines) > 5:
                    short = "\n".join(lines[:5]) + f"\n... ({len(lines)} total lines)"
                    print(f"  {output}")
                    return f"Command succeeded. {lines[0]}"
                print(f"  {output}")
                return f"Done. Output: {output[:150]}"
            return "Command executed successfully."
        else:
            err_short = error[:100] if error else "Unknown error"
            return f"Command failed: {err_short}"

    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {e}"
