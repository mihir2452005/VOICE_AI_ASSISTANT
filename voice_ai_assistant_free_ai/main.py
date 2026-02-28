from record_audio import record_audio
from tts_offline import speak_and_save
from brain_gemini import ask_gemini, clear_memory
import time

def run_assistant():
    print("🎙️ Agentic Voice AI Assistant: Online (Native Audio)")
    print("Ctrl+C to stop.\n")

    while True:
        # 1. Record Audio (VAD handles stopping automatically)
        audio_file = record_audio()

        # 2. Send the raw Audio File directly to the Gemini API
        print("🤔 Processing audio...")
        ai_reply = ask_gemini(audio_file)
        
        # 3. Print the AI's response and speak it
        print("AI:", ai_reply)

        speak_and_save(ai_reply)
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        run_assistant()
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
