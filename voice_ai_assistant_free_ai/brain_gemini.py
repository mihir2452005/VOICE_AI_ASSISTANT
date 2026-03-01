from google import genai
from google.genai import types
import time
from config import GEMINI_API_KEY, MODEL_NAME
from action_manager import get_all_tools
from actions.memory_actions import recall_facts

# Initialize the new SDK Client
client = genai.Client(api_key=GEMINI_API_KEY)

def create_chat_session():
    """Builds the AI session, dynamically injecting Long-Term Memories into its core personality."""
    system_prompt = (
        "You are Nova, a highly advanced digital assistant. You have full access to the user's computer via Action Tools.\n\n"
        f"**CRITICAL CONTEXT - LONG TERM MEMORY:**\n"
        f"{recall_facts()}\n\n"
        "Use this memory context to personalize your responses. "
        "Do not explicitly mention that you are reading from a database unless asked.\n\n"
        "**WORKSPACE CONSTRAINT:**\n"
        "When the user asks you to read, write, or create standard files (notes, presentations, python scripts), you are heavily encouraged to use "
        "the dedicated workspace path: `d:\\projects\\degree\\jarvis\\voice_ai_assistant_free_ai\\NOVA` unless otherwise requested."
    )
    
    return client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=get_all_tools()
        )
    )

# Start a global chat session for memory (with tools enabled)
chat_session = create_chat_session()

def ask_gemini(audio_file_path):
    """Uploads voice audio directly to Gemini using inline bytes."""
    try:
        print("🧠 Understanding your context directly...")
        
        # 1. Read audio bytes and create an inline Part
        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()
            
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type="audio/wav"
        )

        # 2. Build the Payload
        prompt_instructions = "Please listen to the audio and respond conversationally."
        
        payload = [audio_part, prompt_instructions]

        # 3. Send the payload to the chat session
        response = chat_session.send_message(message=payload)
        
        return response.text
        
    except Exception as e:
        return f"Gemini GenAI Error: {e}"

def clear_memory():
    """Resets the conversation history, but retains long-term permanent memory."""
    global chat_session
    chat_session = create_chat_session()
    print("🧠 Short-Term Memory Cleared. Long-Term Memory Retained.")


