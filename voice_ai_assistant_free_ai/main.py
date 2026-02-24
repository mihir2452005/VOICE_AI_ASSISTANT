from record_audio import record_audio
from stt_whisper import transcribe
from tts_offline import speak_and_save
from brain_gemini import ask_gemini
import time

print("🎙️ Voice AI Assistant (PyAudio + Whisper + Gemini)")
print("Ctrl+C to stop\n")

try:
    while True:
        audio_file = record_audio()
        user_text, lang = transcribe(audio_file)

        if not user_text.strip():
            continue

        print("You:", user_text)

        ai_reply = ask_gemini(user_text)
        print("AI:", ai_reply)

        speak_and_save(ai_reply)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n🛑 Stopped.")
