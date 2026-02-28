import os
import winsound
import multiprocessing
from datetime import datetime



def _generate_tts(text):
    import pyttsx3
    engine = pyttsx3.init()

    voices = engine.getProperty("voices")
    for v in voices:
        if "female" in v.name.lower():
            engine.setProperty("voice", v.id)
            break

    engine.setProperty("rate", 170)
    # Stream directly to the speakers
    engine.say(text)
    engine.runAndWait()

def speak_and_save(text):
    # Run SAPI5 streaming in an isolated Process to prevent thread hanging
    p = multiprocessing.Process(target=_generate_tts, args=(text,))
    p.start()
    p.join()  # Wait for the audio to finish playing out loud
    
    print("🔊 Audio streamed directly via SAPI5.")
