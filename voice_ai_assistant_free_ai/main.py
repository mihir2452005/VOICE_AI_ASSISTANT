from record_audio import record_audio
from tts_offline import speak_and_save
from brain_gemini import ask_gemini, clear_memory
import time
from vision import capture_screen

def run_assistant():
    """The main loop of the voice assistant."""
    print("\n🎙️ Agentic Voice AI Assistant: Online (Vision Enabled)")
    print("Ctrl+C to stop.\n")

    while True:
        # 1. Wait for and record the user's voice
        audio_file = record_audio()
        
        # 2. Silently capture the current screen context
        print("📸 Capturing screen...")
        image_file = capture_screen()

        # 3. Process the audio & image using Gemini Multimodal
        print("🤔 Processing input...")
        response_text = ask_gemini(audio_file, image_file)
        
        print(f"AI: {response_text}")

        # 4. Speak the response out loud
        speak_and_save(response_text)
        print("-" * 40)

if __name__ == "__main__":
    try:
        run_assistant()
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
