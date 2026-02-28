from google import genai
import time
from config import GEMINI_API_KEY, MODEL_NAME

# Initialize the new SDK Client
client = genai.Client(api_key=GEMINI_API_KEY)

# Start a global chat session for memory
chat_session = client.chats.create(model=MODEL_NAME)

def ask_gemini(audio_file_path, image_file_path=None):
    """Uploads voice audio (and optionally a screenshot) directly to Gemini."""
    try:
        print("🧠 Understanding your context directly...")
        
        # 1. Upload the Audio
        audio_clip = client.files.upload(file=audio_file_path)
        
        # 2. Upload the Image (if present)
        image_clip = None
        if image_file_path:
            print("👁️ Giving Gemini access to your screen...")
            image_clip = client.files.upload(file=image_file_path)
        
        time.sleep(1)

        # 3. Build the Multimodal Payload
        prompt_instructions = "Please listen to the audio and respond conversationally. Use the provided screenshot of the user's screen for visual context if applicable."
        
        payload = [audio_clip]
        if image_clip:
            payload.append(image_clip)
        payload.append(prompt_instructions)

        # 4. Send the payload to the chat session
        response = chat_session.send_message(message=payload)
        
        return response.text
        
    except Exception as e:
        return f"Gemini GenAI Error: {e}"

def clear_memory():
    """Resets the conversation history."""
    global chat_session
    chat_session = client.chats.create(model=MODEL_NAME)
    print("🧠 Memory Cleared.")


