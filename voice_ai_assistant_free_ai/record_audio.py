import sounddevice as sd
import numpy as np
import wave
import os
from datetime import datetime

SAMPLE_RATE = 16000
DURATION = 5

def record_audio():
    os.makedirs("output/audio_input", exist_ok=True)

    print("🎤 Recording chunk...")
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype=np.int16)
    sd.wait()

    filename = f"output/audio_input/chunk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    print("💾 Saved:", filename)
    return filename
