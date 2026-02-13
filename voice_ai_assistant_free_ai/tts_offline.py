import pyttsx3

def speak(text):
    engine = pyttsx3.init()   # re-init every time

    engine.setProperty("rate", 170)

    voices = engine.getProperty("voices")
    for v in voices:
        if "female" in v.name.lower():
            engine.setProperty("voice", v.id)
            break

    engine.say(text)
    engine.runAndWait()
    engine.stop()
