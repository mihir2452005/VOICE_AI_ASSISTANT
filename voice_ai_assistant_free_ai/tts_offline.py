import os
import winsound
import multiprocessing
from datetime import datetime

os.makedirs("output/audio_output", exist_ok=True)

def _generate_tts(text, filename):
    import pyttsx3
    engine = pyttsx3.init()

    voices = engine.getProperty("voices")
    for v in voices:
        if "female" in v.name.lower():
            engine.setProperty("voice", v.id)
            break

    engine.setProperty("rate", 170)
    engine.save_to_file(text, filename)
    engine.runAndWait()

def speak_and_save(text):
    filename = f"output/audio_output/reply_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    
    # Run the engine in an isolated Process to prevent Windows SAPI5 from freezing
    p = multiprocessing.Process(target=_generate_tts, args=(text, filename))
    p.start()
    p.join()  # Wait for the audio file to finish generating
    
    print("🔊 Audio played and saved:", filename)
    winsound.PlaySound(filename, winsound.SND_FILENAME)
