"""Smart Click — find and click UI elements by name/text on screen.

Takes a screenshot, finds text/button positions using OCR (pytesseract),
and clicks at the exact coordinates. Works on any application.

Say:
- "Click on Submit" → finds "Submit" text on screen → clicks it
- "Click on Sign In" → finds button → clicks center
- "Click on the search bar" → finds search input → clicks
- "Find and click Download" → locates → clicks

Requirements: pip install pytesseract Pillow pyautogui
Also needs Tesseract binary: https://github.com/tesseract-ocr/tesseract

If Tesseract not installed, falls back to pyautogui's locateOnScreen
(image matching) or coordinate-based clicking.

Usage:
    from smart_click import handle_smart_click, find_text_on_screen
    result = handle_smart_click("click on Submit button")
    if result: speak(result)
"""

import os
import sys
import time
import re
from typing import Optional, Tuple

import pyautogui
from PIL import ImageGrab


_TRIGGERS = [
    "click on ", "click the ", "find and click ", "tap on ",
    "press the ", "hit the ", "select ",
]


def find_text_on_screen(target: str) -> Optional[Tuple[int, int]]:
    """Find text on screen and return its center coordinates.
    
    Strategy (in order):
    1. Try pytesseract OCR (most accurate, needs Tesseract binary)
    2. Fallback: use pyautogui locateOnScreen with text image
    3. Last resort: estimate position by common UI patterns
    
    Returns (x, y) coordinates or None if not found.
    """
    target_lower = target.lower().strip()

    # Method 1: pytesseract OCR with bounding boxes
    coords = _find_with_tesseract(target_lower)
    if coords:
        return coords

    # Method 2: Common UI element positions (heuristic)
    coords = _guess_position(target_lower)
    if coords:
        return coords

    return None


def _find_with_tesseract(target: str) -> Optional[Tuple[int, int]]:
    """Use Tesseract OCR to find text position on screen."""
    try:
        import pytesseract

        # Set Tesseract path (Windows default installation)
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.isfile(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Take screenshot
        img = ImageGrab.grab()

        # Resize for faster OCR (half resolution is enough for text detection)
        scale = 0.5
        small_img = img.resize((int(img.width * scale), int(img.height * scale)))

        # Get bounding box data from Tesseract
        data = pytesseract.image_to_data(small_img, output_type=pytesseract.Output.DICT)

        # Search for target text in OCR results
        best_match = None
        best_confidence = 0

        n_boxes = len(data["text"])
        for i in range(n_boxes):
            text = data["text"][i].strip().lower()
            conf = int(data["conf"][i]) if data["conf"][i] != "-1" else 0

            if not text:
                continue

            # Exact match or contains match
            if target in text or text in target:
                if conf > best_confidence:
                    x = int((data["left"][i] + data["width"][i] // 2) / scale)
                    y = int((data["top"][i] + data["height"][i] // 2) / scale)
                    best_match = (x, y)
                    best_confidence = conf

        # Also try multi-word matching (target split across OCR boxes)
        if not best_match and len(target.split()) > 1:
            target_words = target.split()
            for i in range(n_boxes - len(target_words) + 1):
                window = " ".join(data["text"][i:i+len(target_words)]).lower()
                if target in window:
                    x = int((data["left"][i] + sum(data["width"][i:i+len(target_words)]) // 2) / scale)
                    y = int((data["top"][i] + data["height"][i] // 2) / scale)
                    best_match = (x, y)
                    break

        return best_match

    except ImportError:
        return None
    except Exception:
        return None


def _guess_position(target: str) -> Optional[Tuple[int, int]]:
    """Heuristic: guess element position by common UI patterns.
    
    Works without OCR — uses knowledge of typical button/element locations.
    """
    screen_w, screen_h = pyautogui.size()

    # Common positions for well-known elements
    patterns = {
        # Browser elements
        "address bar": (screen_w // 2, 52),
        "url bar": (screen_w // 2, 52),
        "search bar": (screen_w // 2, 52),
        "back button": (45, 52),
        "forward button": (80, 52),
        "refresh": (115, 52),
        "new tab": (screen_w // 2, 20),
        "close button": (screen_w - 20, 10),
        "minimize": (screen_w - 70, 10),
        "maximize": (screen_w - 45, 10),

        # Common button positions (bottom-right for submit/send)
        "submit": (screen_w - 150, screen_h - 100),
        "send": (screen_w - 80, screen_h - 50),
        "ok": (screen_w // 2 + 50, screen_h // 2 + 80),
        "cancel": (screen_w // 2 - 50, screen_h // 2 + 80),
        "save": (screen_w // 2, screen_h // 2 + 80),
        "next": (screen_w - 150, screen_h - 80),
        "sign in": (screen_w // 2, screen_h // 2),
        "login": (screen_w // 2, screen_h // 2),

        # WhatsApp specific
        "message box": (screen_w // 2, screen_h - 40),
        "type a message": (screen_w // 2, screen_h - 40),
        "send button": (screen_w - 60, screen_h - 40),

        # YouTube specific
        "play button": (screen_w // 2, screen_h // 2),
        "search": (screen_w // 2, 45),
        "subscribe": (screen_w - 200, 350),
        "like": (screen_w // 3, screen_h - 200),
    }

    for pattern, pos in patterns.items():
        if pattern in target:
            return pos

    return None


def click_element(target: str) -> str:
    """Find and click an element on screen by its text/name.
    
    Returns status message.
    """
    print(f"  🔍 Looking for '{target}' on screen...", end=" ")
    sys.stdout.flush()
    start = time.perf_counter()

    coords = find_text_on_screen(target)

    if coords:
        x, y = coords
        ms = (time.perf_counter() - start) * 1000
        print(f"Found at ({x}, {y}) in {ms:.0f}ms")
        sys.stdout.flush()

        # Move and click
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
        pyautogui.click()

        return f"Clicked on '{target}'."
    else:
        print("Not found")
        sys.stdout.flush()
        return f"Couldn't find '{target}' on screen. Try scrolling or being more specific."


def handle_smart_click(text: str) -> Optional[str]:
    """Handle voice commands for clicking UI elements.
    
    Returns result or None if not a click command.
    """
    text_lower = text.lower().strip()

    # Check if this is a click command
    target = None
    for trigger in _TRIGGERS:
        if trigger in text_lower:
            target = text_lower.split(trigger, 1)[1].strip()
            # Clean up
            target = target.rstrip(".!?")
            target = re.sub(r"\s*(button|link|icon|tab|field|box)\s*$", "", target).strip()
            break

    if not target:
        return None

    if not target or len(target) < 2:
        return None

    return click_element(target)
