import pyaudio
import pyttsx3
from google import genai
from config import GEMINI_API_KEY, MODEL_NAME
import time
import os

print("\n" + "="*50)
print("🛠️ VOICE AI ASSISTANT - SYSTEM DIAGNOSTIC TEST 🛠️")
print("="*50 + "\n")

# --- TEST 1: Microphone (PyAudio) ---
def test_microphone():
    print("▶️ [TEST 1] Testing Microphone Access...")
    try:
        audio = pyaudio.PyAudio()
        info = audio.get_default_input_device_info()
        print(f"   ✅ Microphone Detected: {info['name']} (Sample Rate: {info['defaultSampleRate']})")
        audio.terminate()
        return True
    except Exception as e:
        print(f"   ❌ Microphone Error: {e}")
        print("      Tip: Check your privacy settings and ensure your mic is plugged in.")
        return False

# --- TEST 2: Speakers (TTS) ---
def test_speakers():
    print("\n▶️ [TEST 2] Testing Speaker/TTS Engine...")
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        print("   🔊 You should hear: 'Testing speaker output...'")
        engine.say("Testing speaker output.")
        engine.runAndWait()
        print("   ✅ TTS Engine Working.")
        return True
    except Exception as e:
        print(f"   ❌ Speaker/TTS Error: {e}")
        return False

# --- TEST 3: Gemini API & Internet ---
def test_gemini_text_api():
    print("\n▶️ [TEST 3] Testing Google Gemini API Connection...")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test a very fast text inference to ensure keys are working
        print("   🧠 Asking Gemini: 'What is 1 + 1? Reply with just the number.'")
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents="What is 1 + 1? Reply with just the number."
        )
        
        print(f"   ✅ Gemini Responded: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"   ❌ Gemini API Error: {e}")
        print("      Tip: Check your .env file, ensure your GEMINI_API_KEY is correct, and check your internet connection.")
        return False


# --- Run Tests ---
mic_ok = test_microphone()
tts_ok = test_speakers()
api_ok = test_gemini_text_api()

print("\n" + "="*50)
if mic_ok and tts_ok and api_ok:
    print("🎉 ALL SYSTEMS GO! Your AI Assistant is perfectly configured.")
    print("\n👉 How to test the actual Voice/Agent features:")
    print("   1. Run `python xagent.py`")
    print("   2. Speak when it says 'Listening...'")
    print("   3. Stop speaking. It should auto-detect silence (VAD test).")
    print("   4. Say 'clear memory' to test the memory wipe.")
    print("   5. (Dangerous!) While it's 'Listening...', unplug your microphone to trigger an intentional crash. The XAgent should catch it and auto-repair!")
else:
    print("⚠️ SOME TESTS FAILED. Please check the errors above before running xagent.py.")
print("="*50 + "\n")
