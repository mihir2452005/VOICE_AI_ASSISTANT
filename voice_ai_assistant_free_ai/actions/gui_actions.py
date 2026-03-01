import pyautogui
import time
from PIL import ImageGrab
import os
from google import genai
from config import GEMINI_API_KEY
import pygetwindow as gw

from PIL import ImageDraw, ImageFont

def click_on_target(target_description: str):
    """
    Physically moves the user's mouse pointer and clicks on a specific icon, button, or word on their screen.
    Args:
        target_description: What the AI should look for and click on.
    """
    try:
        temp_screenshot = "temp_gui_vision.png"
        screenshot = ImageGrab.grab()
        
        # 1. Generate a 16x10 Grid Overlay (Set-of-Mark)
        draw = ImageDraw.Draw(screenshot)
        screen_width, screen_height = screenshot.size
        
        rows = 10
        cols = 16
        cell_w = screen_width / cols
        cell_h = screen_height / rows
        
        # Draw grid lines
        for i in range(1, cols):
            x = i * cell_w
            draw.line([(x, 0), (x, screen_height)], fill="red", width=2)
        for i in range(1, rows):
            y = i * cell_h
            draw.line([(0, y), (screen_width, y)], fill="red", width=2)
            
        # Draw cell numbers
        font = ImageFont.load_default()
        for r in range(rows):
            for c in range(cols):
                x = c * cell_w + (cell_w / 2)
                y = r * cell_h + (cell_h / 2)
                cell_num = r * cols + c
                draw.text((x-5, y-5), str(cell_num), fill="yellow", font=font)
                
        screenshot.save(temp_screenshot)
        
        # 2. Ask Gemini for the Grid Number
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
        Look at the numbered grid overlaying this screen.
        Find the UI element matching this description: '{target_description}'.
        Reply with ONLY the exact integer number of the cell that contains the center of the target.
        Do NOT return any other text. If you cannot find it, return '-1'.
        """
        
        image_file = client.files.upload(file=temp_screenshot)
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=[image_file, prompt]
        )
        
        if os.path.exists(temp_screenshot):
            os.remove(temp_screenshot)
            
        result = response.text.strip()
        if "-1" in result:
             return f"Failed to click. I could not locate '{target_description}' on the screen."
             
        # 3. Calculate exact coordinates from the Cell Number
        try:
            import re
            numbers = re.findall(r'-?\d+', result)
            if not numbers:
                return f"Failed to parse cell number. Vision model returned: '{result}'"
            
            target_cell = int(numbers[-1])
            r = target_cell // cols
            c = target_cell % cols
            
            target_x = int(c * cell_w + (cell_w / 2))
            target_y = int(r * cell_h + (cell_h / 2))
            
        except Exception as parse_e:
            return f"Failed to parse cell number from Vision model. It returned: '{result}'. Error: {parse_e}"
            
        # 4. Physically move the mouse
        pyautogui.moveTo(target_x, target_y, duration=0.8)
        pyautogui.click()
        
        return f"Successfully clicked cell {target_cell} at ({target_x}, {target_y}) for '{target_description}'."
        
    except Exception as e:
        return f"Failed to perform GUI click action. Error: {e}"

def analyze_screen(query: str):
    """
    Takes a live screenshot of the user's current monitor and analyzes it to answer a question.
    Use this tool ONLY if the user specifically asks you to look at their screen, read an error message, or describe what they are looking at.
    Args:
        query: What the AI should look for or analyze in the screenshot (e.g., "What is the error message?", "Describe the image on the screen", "Read the text").
    """
    try:
        print("📸 Action Tool: Capturing screen on-demand...")
        temp_screenshot = "temp_on_demand_vision.png"
        screenshot = ImageGrab.grab()
        screenshot.save(temp_screenshot)
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        image_file = client.files.upload(file=temp_screenshot)
        
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=[image_file, query]
        )
        
        if os.path.exists(temp_screenshot):
            os.remove(temp_screenshot)
            
        return f"Vision Analysis Result:\n{response.text}"
        
    except Exception as e:
        return f"Failed to analyze screen. Error: {e}"

def type_text(text: str):
    """
    Simulates a human typing text on the keyboard. It will type into whatever application or text box is currently active and focused on the screen.
    Args:
        text: The exact string of text to type out.
    """
    try:
        # Small delay to give the user a split second if they are doing something
        time.sleep(0.5) 
        pyautogui.write(text, interval=0.01)
        return f"Successfully typed: '{text}'"
    except Exception as e:
        return f"Failed to type text. Error: {e}"

def press_key(key_combo: str):
    """
    Simulates pressing a single key or a combination of keys on the keyboard.
    Use this for shortcuts (like 'ctrl+a', 'ctrl+c', 'ctrl+v', 'ctrl+s') or single actions (like 'enter', 'backspace', 'delete', 'tab', 'shift').
    Args:
        key_combo: The key or combination of keys to press, separated by a plus sign (e.g. 'ctrl+a' or 'enter').
    """
    try:
        keys = [k.strip().lower() for k in key_combo.split("+")]
        pyautogui.hotkey(*keys)
        return f"Successfully pressed the key combination: '{key_combo}'"
    except Exception as e:
        return f"Failed to press key(s). Error: {e}"

def manage_window(app_name: str, action: str):
    """
    Finds a visible window on the screen by name and snaps, resizes, or minimizes it.
    Args:
        app_name: The title of the window (e.g. "Notepad" or "Chrome").
        action: The action to perform. MUST be one of: 'maximize', 'minimize', 'snap_left', 'snap_right', 'close'.
    """
    try:
        # Find windows that contain the app_name in their title (case insensitive)
        windows = [w for w in gw.getAllWindows() if app_name.lower() in w.title.lower()]
        
        if not windows:
            return f"Failed to find any open window matching '{app_name}'."
            
        target_window = windows[0]
        action = action.lower().strip()
        
        screen_width, screen_height = pyautogui.size()
        
        if action == "maximize":
            target_window.maximize()
            return f"Successfully maximized {target_window.title}."
        elif action == "minimize":
            target_window.minimize()
            return f"Successfully minimized {target_window.title}."
        elif action == "snap_left":
            if target_window.isMaximized:
                target_window.restore()
            target_window.resizeTo(screen_width // 2, screen_height)
            target_window.moveTo(0, 0)
            return f"Successfully snapped {target_window.title} to the left."
        elif action == "snap_right":
            if target_window.isMaximized:
                target_window.restore()
            target_window.resizeTo(screen_width // 2, screen_height)
            target_window.moveTo(screen_width // 2, 0)
            return f"Successfully snapped {target_window.title} to the right."
        elif action == "close":
            target_window.close()
            return f"Successfully closed {target_window.title}."
        else:
            return f"Invalid action '{action}'. Mode must be maximize, minimize, snap_left, snap_right, or close."
            
    except Exception as e:
        return f"Failed to manage window for {app_name}. Error: {e}"
