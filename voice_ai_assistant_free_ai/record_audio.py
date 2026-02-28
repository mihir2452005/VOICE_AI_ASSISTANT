import pyaudio
import wave
import os
import audioop
import time
from datetime import datetime

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# VAD / Silence Detection parameters
SILENCE_THRESHOLD = 500  # Baseline volume threshold (adjust if too sensitive/deaf)
SILENCE_DURATION = 1.5   # Seconds of silence before stopping recording
MAX_RECORD_SECONDS = 15  # Maximum length of any single recording

os.makedirs("output/audio_input", exist_ok=True)

def record_audio():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("\n🎤 Listening... (Speak now)")

    frames = []
    silent_chunks = 0
    speaking_started = False
    
    # Calculate how many chunks equal our silence duration
    chunks_per_second = RATE / CHUNK
    max_silent_chunks = int(chunks_per_second * SILENCE_DURATION)
    max_total_chunks = int(chunks_per_second * MAX_RECORD_SECONDS)

    for i in range(max_total_chunks):
        data = stream.read(CHUNK)
        frames.append(data)
        
        # Calculate the root mean square (volume/energy) of the audio chunk
        rms = audioop.rms(data, 2)
        
        if rms > SILENCE_THRESHOLD:
            # We hear speaking
            speaking_started = True
            silent_chunks = 0
        elif speaking_started:
            # We heard speaking before, but now it's quiet
            silent_chunks += 1
            
        # If we have spoken, and now have been silent for X seconds, stop recording
        if speaking_started and silent_chunks > max_silent_chunks:
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Create filename
    filename = f"output/audio_input/chunk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    
    # Save the audio
    wf = wave.open(filename, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    print(f"💾 Saved ({len(frames) / chunks_per_second:.1f}s): {filename}")
    return filename

def transcribe_audio_to_text(filename: str) -> str:
    """Takes a .wav file and converts it entirely to text using the free Google Speech API."""
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    
    print("📝 Transcribing audio to text for Grok...")
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)
        try:
            # Requires an active internet connection to ping google's free transcriber
            text = recognizer.recognize_google(audio_data)
            print(f"🗣️ You said: '{text}'")
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            return f"Error with STT Middleware: {e}"
