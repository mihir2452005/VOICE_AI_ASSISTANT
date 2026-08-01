"""Browser Control — full voice control of Brave/Chrome browser.

Controls:
- Open browser, URLs, bookmarks
- Navigate: back, forward, refresh, home
- Tabs: new tab, close tab, switch tabs
- Scroll: up, down, top, bottom
- Type: in search bars, text fields
- Click: send button, submit, links (via Tab navigation)
- Sites: YouTube, WhatsApp, Gmail, etc.

All via keyboard shortcuts + pyautogui — no GPU, no API.

Usage:
    from browser_control import handle_browser
    result = handle_browser("open youtube")
    if result: speak(result)
"""

import os
import sys
import time
import subprocess
import re
from typing import Optional

import pyautogui


# Configure pyautogui
pyautogui.PAUSE = 0.1  # 100ms between actions (fast but stable)
pyautogui.FAILSAFE = True  # Move mouse to corner to abort

# Default browser path (Brave)
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Detect which browser is installed
if os.path.exists(BRAVE_PATH):
    BROWSER_PATH = BRAVE_PATH
    BROWSER_NAME = "Brave"
elif os.path.exists(CHROME_PATH):
    BROWSER_PATH = CHROME_PATH
    BROWSER_NAME = "Chrome"
else:
    BROWSER_PATH = "brave"  # Try system PATH
    BROWSER_NAME = "Browser"

# Bookmarks / quick sites (auto-loaded from browser + common defaults)
BOOKMARKS = {
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "chatgpt": "https://chat.openai.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "spotify": "https://open.spotify.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "stackoverflow": "https://stackoverflow.com",
}

# Also load real bookmarks from browser
try:
    from bookmarks import get_all_bookmarks
    for bm in get_all_bookmarks():
        # Add each bookmark by its name (lowercase, simplified)
        short_name = bm["name"].lower().strip()
        short_name = re.sub(r"[^a-z0-9\s]", "", short_name).strip()
        if short_name and short_name not in BOOKMARKS:
            BOOKMARKS[short_name] = bm["url"]
except Exception:
    pass  # bookmarks.py not available or no bookmarks


# =============================================================================
# BROWSER ACTIONS
# =============================================================================

def open_browser(url: str = "") -> str:
    """Open Brave/Chrome with optional URL."""
    try:
        if url:
            subprocess.Popen([BROWSER_PATH, url])
            return f"Opening {url} in {BROWSER_NAME}."
        else:
            subprocess.Popen([BROWSER_PATH])
            return f"Opened {BROWSER_NAME}."
    except Exception:
        # Fallback: use os.startfile
        try:
            if url:
                os.startfile(url)
            else:
                os.startfile(BROWSER_PATH)
            return f"Opened {BROWSER_NAME}."
        except Exception as e:
            return f"Couldn't open browser: {e}"


def new_tab(url: str = "") -> str:
    """Open a new tab."""
    pyautogui.hotkey("ctrl", "t")
    time.sleep(0.3)
    if url:
        pyautogui.typewrite(url, interval=0.02)
        pyautogui.press("enter")
        return f"New tab: {url}"
    return "New tab opened."


def close_tab() -> str:
    pyautogui.hotkey("ctrl", "w")
    return "Tab closed."


def switch_tab(direction: str = "next") -> str:
    if direction == "next":
        pyautogui.hotkey("ctrl", "tab")
        return "Switched to next tab."
    else:
        pyautogui.hotkey("ctrl", "shift", "tab")
        return "Switched to previous tab."


def go_back() -> str:
    pyautogui.hotkey("alt", "left")
    return "Going back."


def go_forward() -> str:
    pyautogui.hotkey("alt", "right")
    return "Going forward."


def refresh() -> str:
    pyautogui.press("f5")
    return "Refreshed."


def go_to_url(url: str) -> str:
    """Navigate to a URL in the current tab."""
    pyautogui.hotkey("ctrl", "l")  # Focus address bar
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")  # Select all
    pyautogui.typewrite(url, interval=0.02)
    pyautogui.press("enter")
    return f"Navigating to {url}."


def scroll_down(amount: int = 5) -> str:
    pyautogui.scroll(-amount)
    return "Scrolled down."


def scroll_up(amount: int = 5) -> str:
    pyautogui.scroll(amount)
    return "Scrolled up."


def scroll_to_top() -> str:
    pyautogui.hotkey("ctrl", "Home")
    return "Scrolled to top."


def scroll_to_bottom() -> str:
    pyautogui.hotkey("ctrl", "End")
    return "Scrolled to bottom."


def type_text(text: str) -> str:
    """Type text into the currently focused field."""
    pyautogui.typewrite(text, interval=0.03)
    return f"Typed: {text[:30]}"


def type_text_unicode(text: str) -> str:
    """Type text including unicode/special chars (slower but accurate)."""
    import pyperclip
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    return f"Typed: {text[:30]}"


def press_enter() -> str:
    pyautogui.press("enter")
    return "Pressed enter."


def press_tab() -> str:
    pyautogui.press("tab")
    return "Pressed tab."


def click_here() -> str:
    """Click at current mouse position."""
    pyautogui.click()
    return "Clicked."


def search_in_page(query: str) -> str:
    """Use Ctrl+F to find text on page."""
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.2)
    pyautogui.typewrite(query, interval=0.03)
    pyautogui.press("enter")
    return f"Searching for: {query}"


def zoom_in() -> str:
    pyautogui.hotkey("ctrl", "+")
    return "Zoomed in."


def zoom_out() -> str:
    pyautogui.hotkey("ctrl", "-")
    return "Zoomed out."


def full_screen() -> str:
    pyautogui.press("f11")
    return "Toggled fullscreen."


# =============================================================================
# WHATSAPP WEB SPECIFIC
# =============================================================================

def whatsapp_send(message: str, contact: str = "") -> str:
    """Send a WhatsApp message.
    
    If contact specified, searches for them first.
    """
    if contact:
        # Click search / new chat
        pyautogui.hotkey("ctrl", "shift", "k")  # Search in WhatsApp
        time.sleep(0.5)
        type_text_unicode(contact)
        time.sleep(1)
        pyautogui.press("enter")  # Select first result
        time.sleep(0.5)

    # Type message
    type_text_unicode(message)
    time.sleep(0.2)
    pyautogui.press("enter")  # Send
    return f"Sent message to {contact or 'current chat'}."


# =============================================================================
# YOUTUBE SPECIFIC
# =============================================================================

def youtube_search(query: str) -> str:
    """Search YouTube."""
    pyautogui.press("/")  # YouTube search shortcut
    time.sleep(0.3)
    pyautogui.typewrite(query, interval=0.03)
    pyautogui.press("enter")
    return f"Searching YouTube for: {query}"


def youtube_play_pause() -> str:
    pyautogui.press("k")  # YouTube play/pause shortcut
    return "Play/pause toggled."


def youtube_fullscreen() -> str:
    pyautogui.press("f")  # YouTube fullscreen
    return "YouTube fullscreen toggled."


def youtube_skip(seconds: int = 10) -> str:
    """Skip forward in YouTube video."""
    pyautogui.press("l")  # Skip 10s forward
    return f"Skipped forward."


def youtube_rewind(seconds: int = 10) -> str:
    pyautogui.press("j")  # Skip 10s back
    return "Rewound."


# =============================================================================
# VOICE COMMAND ROUTER
# =============================================================================

def handle_browser(text: str) -> Optional[str]:
    """Handle browser voice commands. Returns result or None."""
    text_lower = text.lower().strip()

    # --- OPEN BROWSER / SITES ---
    if "open browser" in text_lower or "open brave" in text_lower or "open chrome" in text_lower:
        return open_browser()

    # Open bookmarked sites
    for site, url in BOOKMARKS.items():
        if f"open {site}" in text_lower or f"go to {site}" in text_lower:
            return open_browser(url)

    # Open URL directly
    match = re.search(r"(?:open|go to|navigate to)\s+(https?://\S+)", text_lower)
    if match:
        return open_browser(match.group(1))

    # Open .com/.in sites
    match = re.search(r"(?:open|go to)\s+([\w]+\.(?:com|org|net|in|io|dev))", text_lower)
    if match:
        return open_browser(f"https://{match.group(1)}")

    # --- NAVIGATION ---
    if "go back" in text_lower or "back page" in text_lower:
        return go_back()
    if "go forward" in text_lower or "forward page" in text_lower:
        return go_forward()
    if text_lower in ("refresh", "reload", "refresh page"):
        return refresh()

    # --- TABS ---
    if "new tab" in text_lower:
        # Check if they want to open something in new tab
        match = re.search(r"new tab (?:with |for )?(.*)", text_lower)
        if match and match.group(1).strip():
            site = match.group(1).strip()
            url = BOOKMARKS.get(site, f"https://www.google.com/search?q={site}")
            return new_tab(url)
        return new_tab()
    if "close tab" in text_lower or "close this tab" in text_lower:
        return close_tab()
    if "next tab" in text_lower or "switch tab" in text_lower:
        return switch_tab("next")
    if "previous tab" in text_lower or "last tab" in text_lower:
        return switch_tab("previous")

    # --- SCROLLING ---
    if "scroll down" in text_lower:
        amount = 10 if "more" in text_lower or "lot" in text_lower else 5
        return scroll_down(amount)
    if "scroll up" in text_lower:
        amount = 10 if "more" in text_lower or "lot" in text_lower else 5
        return scroll_up(amount)
    if "scroll to top" in text_lower or "go to top" in text_lower:
        return scroll_to_top()
    if "scroll to bottom" in text_lower or "go to bottom" in text_lower:
        return scroll_to_bottom()

    # --- TYPING ---
    match = re.search(r"(?:type|write|enter)\s+[\"']?(.+?)[\"']?$", text_lower)
    if match and any(w in text_lower for w in ["type", "write in", "enter text"]):
        content = match.group(1).strip().strip("'\"")
        type_text_unicode(content)
        return f"Typed: {content[:40]}"

    # --- CLICKING ---
    if "click" in text_lower and ("send" in text_lower or "submit" in text_lower):
        press_enter()
        return "Clicked send/submit."
    if "click" in text_lower or "press enter" in text_lower:
        press_enter()
        return "Pressed enter."
    if "press tab" in text_lower or "next field" in text_lower:
        return press_tab()

    # --- SEARCH ---
    if "search in page" in text_lower or "find on page" in text_lower:
        match = re.search(r"(?:search in page|find on page)\s+(.+)", text_lower)
        if match:
            return search_in_page(match.group(1))

    if "search" in text_lower and "youtube" in text_lower:
        match = re.search(r"search (?:youtube |on youtube )?(?:for )?(.+)", text_lower)
        if match:
            query = match.group(1).replace("on youtube", "").replace("youtube", "").strip()
            return youtube_search(query)

    # --- ZOOM ---
    if "zoom in" in text_lower:
        return zoom_in()
    if "zoom out" in text_lower:
        return zoom_out()
    if "full screen" in text_lower or "fullscreen" in text_lower:
        return full_screen()

    # --- YOUTUBE ---
    if "play video" in text_lower or "pause video" in text_lower:
        return youtube_play_pause()
    if "skip" in text_lower and "video" in text_lower:
        return youtube_skip()
    if "rewind" in text_lower:
        return youtube_rewind()

    # --- WHATSAPP ---
    if "send message" in text_lower or "whatsapp" in text_lower:
        # Extract message and optional contact
        match = re.search(r"(?:send|message)\s+(.+?)(?:\s+to\s+(.+))?$", text_lower)
        if match:
            message = match.group(1).strip()
            contact = match.group(2).strip() if match.group(2) else ""
            # Remove "to" from message if contact not found
            if not contact and " to " in message:
                parts = message.rsplit(" to ", 1)
                message = parts[0]
                contact = parts[1]
            return whatsapp_send(message, contact)

    return None
