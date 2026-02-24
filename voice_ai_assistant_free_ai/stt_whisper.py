import whisper
import os

model = whisper.load_model("base")

os.makedirs("output/transcripts", exist_ok=True)

def transcribe(audio_path):
    result = model.transcribe(audio_path)
    text = result["text"]
    lang = result["language"]

    with open("output/transcripts/latest.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print(f"🧠 DETECTED: {text} [{lang}]")
    return text, lang
