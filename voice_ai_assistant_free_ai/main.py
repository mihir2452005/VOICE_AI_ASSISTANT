from record_audio import record_audio
from stt_whisper import transcribe_audio
from brain_gemini import ask_ai
from tts_offline import speak

print("🎙️ Voice AI Assistant with Online Brain")
print("Ctrl+C to stop")

while True:
    audio_file = record_audio()
    user_text = transcribe_audio(audio_file)

    if user_text.lower() in ["exit", "quit", "stop"]:
        print("👋 Exiting...")
        break

    print("You:", user_text)

    ai_reply = ask_ai(user_text)
    print("AI:", ai_reply)

    speak(ai_reply)
