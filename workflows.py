"""Smart Browser Workflows — multi-step automations by voice.

Say complex commands that chain multiple browser actions:
- "Open WhatsApp, find John, type good morning, send it"
- "Open YouTube and search for Python tutorials"
- "Open Gmail and compose new email"
- "Go to LinkedIn and open my profile"
- "Open Google and search for weather today"

Nova parses the command into steps and executes them sequentially
with appropriate delays between each action.

Usage:
    from workflows import handle_workflow
    result = handle_workflow("open whatsapp and send hello to Mom")
    if result: speak(result)
"""

import os
import sys
import time
import re
from typing import Optional

import pyautogui


# =============================================================================
# WORKFLOW DEFINITIONS (pre-built automations)
# =============================================================================

WORKFLOWS = {
    "whatsapp_message": {
        "triggers": ["send message on whatsapp", "whatsapp send", "message on whatsapp",
                     "open whatsapp and send", "open whatsapp and message"],
        "steps": ["open_whatsapp", "wait", "search_contact", "wait", "type_message", "send"],
    },
    "youtube_search": {
        "triggers": ["search on youtube", "youtube search", "open youtube and search",
                     "find on youtube", "play on youtube"],
        "steps": ["open_youtube", "wait_long", "search_youtube"],
    },
    "google_search": {
        "triggers": ["google search", "search on google", "open google and search",
                     "google for"],
        "steps": ["open_google", "wait", "type_search", "submit"],
    },
    "gmail_compose": {
        "triggers": ["compose email", "new email", "write email", "send email",
                     "open gmail and compose"],
        "steps": ["open_gmail", "wait_long", "compose_new"],
    },
    "linkedin_profile": {
        "triggers": ["open my linkedin", "go to linkedin profile", "linkedin profile"],
        "steps": ["open_linkedin", "wait", "go_to_profile"],
    },
}


# =============================================================================
# STEP EXECUTORS
# =============================================================================

def _wait(seconds: float = 1.5):
    """Wait for page to load."""
    time.sleep(seconds)


def _wait_long():
    """Wait longer for heavy pages."""
    time.sleep(3.0)


def _open_site(url: str):
    """Open a URL in current browser."""
    from browser_control import open_browser
    open_browser(url)


def _search_contact(contact: str):
    """Search for a contact in WhatsApp."""
    pyautogui.hotkey("ctrl", "shift", "k")  # WhatsApp search
    time.sleep(0.5)
    _type_unicode(contact)
    time.sleep(1.0)
    pyautogui.press("enter")  # Select first result
    time.sleep(0.5)


def _type_unicode(text: str):
    """Type text including unicode."""
    import pyperclip
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")


def _search_youtube(query: str):
    """Search on YouTube."""
    pyautogui.press("/")  # YouTube search shortcut
    time.sleep(0.3)
    pyautogui.typewrite(query, interval=0.03)
    pyautogui.press("enter")


def _type_and_submit(text: str):
    """Type text in search bar and submit."""
    pyautogui.typewrite(text, interval=0.03)
    pyautogui.press("enter")


# =============================================================================
# SMART PARSER — breaks complex voice commands into actionable steps
# =============================================================================

def _parse_workflow(text: str) -> Optional[dict]:
    """Parse a complex voice command into a structured workflow.
    
    Returns: {type, contact, message, query, url} or None
    """
    text_lower = text.lower().strip()

    # WhatsApp: "open whatsapp and send hello to Mom"
    match = re.search(
        r"(?:open whatsapp|whatsapp).+?(?:send|message|type)\s+(.+?)(?:\s+to\s+(.+))?$",
        text_lower
    )
    if match:
        message = match.group(1).strip()
        contact = match.group(2).strip() if match.group(2) else ""
        # Clean message (remove "to X" if parsed wrong)
        if " to " in message and not contact:
            parts = message.rsplit(" to ", 1)
            message = parts[0]
            contact = parts[1]
        return {"type": "whatsapp_message", "message": message, "contact": contact}

    # YouTube: "open youtube and search for X"
    match = re.search(
        r"(?:open youtube|youtube).+?(?:search|find|play|look)\s+(?:for\s+)?(.+)",
        text_lower
    )
    if match:
        return {"type": "youtube_search", "query": match.group(1).strip()}

    # Google: "google search for X" or "open google and search X"
    match = re.search(
        r"(?:google|open google).+?(?:search|find|look)\s+(?:for\s+)?(.+)",
        text_lower
    )
    if match:
        return {"type": "google_search", "query": match.group(1).strip()}

    # Gmail compose
    if "compose" in text_lower or ("email" in text_lower and "new" in text_lower):
        return {"type": "gmail_compose"}

    # Generic "open X and do Y"
    match = re.search(r"open\s+(\w+)\s+and\s+(.+)", text_lower)
    if match:
        site = match.group(1)
        action = match.group(2).strip()
        return {"type": "generic", "site": site, "action": action}

    return None


# =============================================================================
# WORKFLOW EXECUTOR
# =============================================================================

def _execute_workflow(workflow: dict) -> str:
    """Execute a parsed workflow."""
    wf_type = workflow["type"]

    if wf_type == "whatsapp_message":
        contact = workflow.get("contact", "")
        message = workflow.get("message", "")

        print("  [1/4] Opening WhatsApp...")
        sys.stdout.flush()
        _open_site("https://web.whatsapp.com")
        _wait_long()
        _wait_long()  # WhatsApp takes time to load

        if contact:
            print(f"  [2/4] Finding {contact}...")
            sys.stdout.flush()
            _search_contact(contact)
            _wait()

        print(f"  [3/4] Typing message...")
        sys.stdout.flush()
        _type_unicode(message)
        _wait(0.3)

        print("  [4/4] Sending!")
        sys.stdout.flush()
        pyautogui.press("enter")

        return f"Sent '{message}' to {contact or 'current chat'} on WhatsApp."

    elif wf_type == "youtube_search":
        query = workflow.get("query", "")

        print("  [1/2] Opening YouTube...")
        sys.stdout.flush()
        _open_site("https://www.youtube.com")
        _wait_long()

        print(f"  [2/2] Searching: {query}")
        sys.stdout.flush()
        _search_youtube(query)

        return f"Searching YouTube for '{query}'."

    elif wf_type == "google_search":
        query = workflow.get("query", "")

        print("  [1/2] Opening Google...")
        sys.stdout.flush()
        _open_site("https://www.google.com")
        _wait()

        print(f"  [2/2] Searching: {query}")
        sys.stdout.flush()
        _type_and_submit(query)

        return f"Searched Google for '{query}'."

    elif wf_type == "gmail_compose":
        print("  [1/2] Opening Gmail...")
        sys.stdout.flush()
        _open_site("https://mail.google.com")
        _wait_long()

        print("  [2/2] Opening compose...")
        sys.stdout.flush()
        pyautogui.press("c")  # Gmail compose shortcut
        _wait()

        return "Opened Gmail compose. Dictate your email."

    elif wf_type == "generic":
        site = workflow.get("site", "")
        action = workflow.get("action", "")

        from browser_control import BOOKMARKS
        url = BOOKMARKS.get(site, f"https://www.{site}.com")

        print(f"  [1/2] Opening {site}...")
        sys.stdout.flush()
        _open_site(url)
        _wait_long()

        print(f"  [2/2] Action: {action}")
        sys.stdout.flush()

        # Try to interpret the action
        if "search" in action:
            query = action.replace("search for", "").replace("search", "").strip()
            pyautogui.hotkey("ctrl", "l")
            _wait(0.2)
            _type_and_submit(f"{site} {query}")
            return f"Opened {site} and searched for {query}."
        elif "type" in action:
            text_to_type = action.replace("type", "").strip()
            _type_unicode(text_to_type)
            return f"Opened {site} and typed text."

        return f"Opened {site}."

    return "Workflow not recognized."


# =============================================================================
# VOICE COMMAND HANDLER
# =============================================================================

_TRIGGERS = [
    "open .+ and ", "send .+ on whatsapp", "whatsapp .+ to ",
    "youtube .+ search", "search .+ on youtube",
    "google .+ search", "search .+ on google",
    "compose email", "new email",
]


def handle_workflow(text: str) -> Optional[str]:
    """Handle multi-step browser workflow commands.

    Returns result string or None if not a workflow command.
    """
    text_lower = text.lower().strip()

    # Quick check: does it look like a multi-step command?
    has_and = " and " in text_lower
    has_workflow_pattern = any(
        re.search(pattern, text_lower)
        for pattern in _TRIGGERS
    )

    if not has_and and not has_workflow_pattern:
        return None

    # Try to parse the workflow
    workflow = _parse_workflow(text)
    if not workflow:
        return None

    print(f"🔄 Executing workflow: {workflow['type']}")
    sys.stdout.flush()

    result = _execute_workflow(workflow)
    return result


# =============================================================================
# CUSTOM WORKFLOWS — record and replay your own automations
# =============================================================================

import json

CUSTOM_WORKFLOWS_FILE = "custom_workflows.json"
_recording = False
_recorded_steps: list[dict] = []
_custom_workflows: dict = {}


def _load_custom_workflows():
    """Load saved custom workflows from disk."""
    global _custom_workflows
    if os.path.isfile(CUSTOM_WORKFLOWS_FILE):
        try:
            with open(CUSTOM_WORKFLOWS_FILE, "r", encoding="utf-8") as f:
                _custom_workflows = json.load(f)
        except Exception:
            _custom_workflows = {}


def _save_custom_workflows():
    """Save custom workflows to disk."""
    try:
        with open(CUSTOM_WORKFLOWS_FILE, "w", encoding="utf-8") as f:
            json.dump(_custom_workflows, f, indent=2)
    except Exception:
        pass


# Load on import
_load_custom_workflows()


def start_recording() -> str:
    """Start recording a new custom workflow."""
    global _recording, _recorded_steps
    _recording = True
    _recorded_steps = []
    return "Recording started. Do your actions and say 'stop recording' when done."


def stop_recording(name: str) -> str:
    """Stop recording and save the workflow with a name."""
    global _recording
    _recording = False

    if not _recorded_steps:
        return "Nothing was recorded. Try again."

    _custom_workflows[name.lower()] = {
        "name": name,
        "steps": list(_recorded_steps),
        "created": time.strftime("%Y-%m-%d %H:%M"),
    }
    _save_custom_workflows()
    count = len(_recorded_steps)
    return f"Saved workflow '{name}' with {count} steps. Say 'run {name}' to replay."


def record_step(action: str, details: dict = None):
    """Record a step during workflow recording (called by other modules)."""
    if _recording:
        step = {"action": action, "details": details or {}, "delay": 1.0}
        _recorded_steps.append(step)


def run_custom_workflow(name: str) -> str:
    """Replay a saved custom workflow."""
    name_lower = name.lower().strip()

    if name_lower not in _custom_workflows:
        available = ", ".join(_custom_workflows.keys()) if _custom_workflows else "none"
        return f"No workflow named '{name}'. Available: {available}"

    workflow = _custom_workflows[name_lower]
    steps = workflow["steps"]

    print(f"  ▶️ Running '{workflow['name']}' ({len(steps)} steps)")
    sys.stdout.flush()

    for i, step in enumerate(steps, 1):
        action = step["action"]
        details = step.get("details", {})
        delay = step.get("delay", 1.0)

        print(f"    [{i}/{len(steps)}] {action}...")
        sys.stdout.flush()

        _execute_step(action, details)
        time.sleep(delay)

    return f"Completed workflow '{workflow['name']}'."


def _execute_step(action: str, details: dict):
    """Execute a single recorded step."""
    if action == "open_url":
        from browser_control import open_browser
        open_browser(details.get("url", ""))
    elif action == "type":
        _type_unicode(details.get("text", ""))
    elif action == "click":
        x, y = details.get("x", 0), details.get("y", 0)
        pyautogui.click(x, y)
    elif action == "press_key":
        pyautogui.press(details.get("key", "enter"))
    elif action == "hotkey":
        keys = details.get("keys", [])
        if keys:
            pyautogui.hotkey(*keys)
    elif action == "wait":
        time.sleep(details.get("seconds", 1.0))
    elif action == "scroll":
        pyautogui.scroll(details.get("amount", -3))


def list_custom_workflows() -> str:
    """List all saved custom workflows."""
    if not _custom_workflows:
        return "No custom workflows saved. Say 'start recording' to create one."

    lines = ["📋 Your custom workflows:"]
    for name, wf in _custom_workflows.items():
        lines.append(f"  • {wf['name']} ({len(wf['steps'])} steps, created {wf['created']})")
    return "\n".join(lines)


def delete_workflow(name: str) -> str:
    """Delete a saved workflow."""
    name_lower = name.lower()
    if name_lower in _custom_workflows:
        del _custom_workflows[name_lower]
        _save_custom_workflows()
        return f"Deleted workflow '{name}'."
    return f"No workflow named '{name}'."


# =============================================================================
# EXTENDED VOICE HANDLER — now includes custom workflow commands
# =============================================================================

_CUSTOM_TRIGGERS = [
    "start recording", "stop recording", "save workflow",
    "run workflow", "play workflow", "my workflows",
    "list workflows", "delete workflow", "show workflows",
]


def handle_custom_workflow(text: str) -> Optional[str]:
    """Handle custom workflow voice commands. Returns result or None."""
    text_lower = text.lower().strip()

    if not any(t in text_lower for t in _CUSTOM_TRIGGERS):
        # Also check for "run <workflow_name>" pattern
        if not text_lower.startswith("run "):
            return None

    # Start recording
    if "start recording" in text_lower or "record workflow" in text_lower:
        return start_recording()

    # Stop recording + save
    if "stop recording" in text_lower or "save workflow" in text_lower:
        # Extract name
        match = re.search(r"(?:save|call it|name it|as)\s+(.+?)$", text_lower)
        name = match.group(1).strip() if match else f"workflow_{len(_custom_workflows)+1}"
        return stop_recording(name)

    # List workflows
    if any(t in text_lower for t in ["list workflows", "my workflows", "show workflows"]):
        result = list_custom_workflows()
        print(f"\n{result}")
        sys.stdout.flush()
        spoken_count = len(_custom_workflows)
        return f"You have {spoken_count} custom workflows." if spoken_count else "No custom workflows yet."

    # Run workflow
    match = re.search(r"(?:run|play|execute)\s+(?:workflow\s+)?(.+?)$", text_lower)
    if match:
        name = match.group(1).strip()
        return run_custom_workflow(name)

    # Delete workflow
    match = re.search(r"delete workflow\s+(.+?)$", text_lower)
    if match:
        return delete_workflow(match.group(1).strip())

    return None
