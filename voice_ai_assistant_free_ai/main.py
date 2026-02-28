from record_audio import record_audio, transcribe_audio_to_text
from tts_offline import speak_and_save
from brain_gemini import ask_gemini, clear_memory
from config import ACTIVE_PROVIDER
import brain_grok
import time
from vision import capture_screen

def run_assistant():
    """The main loop of the voice assistant."""
    print(f"\n🎙️ Agentic Voice AI Assistant: Online [{ACTIVE_PROVIDER.upper()} Engine Active]")
    print("Ctrl+C to stop.\n")

    while True:
        # 1. Wait for and record the user's voice
        audio_file = record_audio()
        
        # 2. Process based on the Provider configuration
        provider = ACTIVE_PROVIDER.lower()
        
        # --- DYNAMIC INTENT ROUTER ("AUTO" MODE) ---
        if provider == "auto":
            # Eagerly transcribe the audio to see what the user wants FIRST
            user_text = transcribe_audio_to_text(audio_file)
            if not user_text:
                continue # Ignore silent/unrecognized noise
                
            # Scan for keywords that specifically require Vision capabilities
            vision_keywords = ["screen", "look", "see", "photo", "image", "picture", "read", "monitor"]
            if any(word in user_text.lower() for word in vision_keywords):
                print("⚡ [Auto-Router]: Vision intent detected! Routing to Gemini...")
                response_text = ask_gemini(audio_file)
            else:
                print("⚡ [Auto-Router]: Fast Chat / Web intent detected! Routing to Grok/Groq...")
                response_text = brain_grok.ask_grok(user_text)
                
                # --- AUTO-FALLBACK TO GEMINI IF GROQ RATE LIMIT IS HIT ---
                if response_text == "RATE_LIMIT_ERROR":
                    print("⚠️ [Auto-Router]: Groq rate limit reached! Instantly falling back to Gemini backup...")
                    response_text = ask_gemini(audio_file)
                
        # --- MANUAL OVERRIDES ---
        elif provider == "gemini":
            response_text = ask_gemini(audio_file)
            
        elif provider == "grok":
            user_text = transcribe_audio_to_text(audio_file)
            if not user_text:
                continue 
            response_text = brain_grok.ask_grok(user_text)
            
        else:
            response_text = f"Invalid ACTIVE_PROVIDER: {ACTIVE_PROVIDER}"
        
        print(f"AI: {response_text}")

        # 4. Speak the response out loud
        speak_and_save(response_text)
        print("-" * 40)

if __name__ == "__main__":
    try:
        run_assistant()
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
