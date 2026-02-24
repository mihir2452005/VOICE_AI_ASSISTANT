import pyttsx3
import os
from datetime import datetime

engine = pyttsx3.init()

voices = engine.getProperty("voices")
for v in voices:
    if "female" in v.name.lower():
        engine.setProperty("voice", v.id)
        break

engine.setProperty("rate", 170)

os.makedirs("output/audio_output", exist_ok=True)

def speak_and_save(text):
    engine.stop()
    filename = f"output/audio_output/reply_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    engine.save_to_file(text, filename)
    engine.runAndWait()
    print("🔊 Audio saved:", filename)
