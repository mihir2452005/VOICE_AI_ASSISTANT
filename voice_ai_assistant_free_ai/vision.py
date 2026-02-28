import os
from PIL import ImageGrab
from datetime import datetime

os.makedirs("output/vision_input", exist_ok=True)

def capture_screen():
    """Takes a full screenshot of the primary monitor and saves it to disk."""
    try:
        # Generate a timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"output/vision_input/screenshot_{timestamp}.png"
        
        # Capture the entire screen
        screenshot = ImageGrab.grab()
        
        # Save the image to the output directory
        screenshot.save(filename)
        
        return filename
    except Exception as e:
        print(f"❌ Vision Error: Could not capture screen -> {e}")
        return None
