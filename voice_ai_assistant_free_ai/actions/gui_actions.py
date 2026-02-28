import pyautogui
import time
from PIL import ImageGrab
import os
from google import genai
from config import GEMINI_API_KEY

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
