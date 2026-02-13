import whisper

model = whisper.load_model("base")

def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    text = result["text"].strip()
    lang = result["language"]
    print(f"🧠 DETECTED: {text} [{lang}]")
    return text
