from google import genai
import time
from config import GEMINI_API_KEY, MODEL_NAME

# Initialize the new SDK Client
client = genai.Client(api_key=GEMINI_API_KEY)

# Start a global chat session for memory
chat_session = client.chats.create(model=MODEL_NAME)

def ask_gemini(audio_file_path):
    """Uploads voice audio directly to Gemini using the new GenAI SDK."""
    try:
        print("🧠 Understanding your voice directly...")
        
        # Upload using the new files API
        audio_clip = client.files.upload(file=audio_file_path)
        
        # We add a tiny delay to allow Google processing
        time.sleep(1)

        # Send the file handle along with the prompt to the chat session
        response = chat_session.send_message(
            message=[audio_clip, "Please listen to the audio and respond conversationally."]
        )
        
        return response.text
        
    except Exception as e:
        return f"Gemini GenAI Error: {e}"

def clear_memory():
    """Resets the conversation history."""
    global chat_session
    chat_session = client.chats.create(model=MODEL_NAME)
    print("🧠 Memory Cleared.")


