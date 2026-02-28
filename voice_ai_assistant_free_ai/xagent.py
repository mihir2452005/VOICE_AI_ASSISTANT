import time
import traceback
from google import genai
from config import GEMINI_API_KEY, MODEL_NAME
from main import run_assistant
from tts_offline import speak_and_save

def analyze_error_with_gemini(error_trace):
    """Sends the error traceback to Gemini to diagnose the issue."""
    prompt = f"""
    You are an expert Python System Supervisor for a Voice AI Assistant.
    The Voice Assistant just crashed with the following error traceback:
    
    {error_trace}
    
    Briefly explain in 1 or 2 sentences what caused this error, and suggest how to fix it. 
    Do not use markdown formatting, just plain text that can be read aloud.
    """
    print("\n[XAgent] 🔍 Analyzing crash with Gemini...")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Unable to reach Gemini for diagnosis. Error: {e}"

def start_supervisor():
    """Wraps the main assistant loop in a self-healing try-catch block."""
    print("==================================================")
    print("🛡️ XAgent Supervisor Layer Active")
    print("Monitoring Voice Assistant for crashes and errors...")
    print("==================================================\n")

    restart_count = 0
    max_restarts = 5

    while restart_count < max_restarts:
        try:
            # Attempt to run the main Voice Assistant loop
            run_assistant()
            
        except KeyboardInterrupt:
            # User manually stopped the script
            print("\n[XAgent] 🛑 Assistant stopped manually by user. Shutting down Supervisor.")
            break
            
        except Exception as e:
            # Oh no! The assistant crashed. Catch the error.
            restart_count += 1
            error_trace = traceback.format_exc()
            
            print(f"\n[XAgent] ⚠️ CRITICAL ERROR DETECTED: {e}")
            print("[XAgent] Initiating self-healing protocols...")
            
            # 1. Analyze the error
            diagnosis = analyze_error_with_gemini(error_trace)
            print(f"\n[XAgent] 🤖 Diagnosis: {diagnosis}\n")
            
            # 2. Inform the user audibly
            speak_and_save("I experienced a technical glitch. " + diagnosis[:150] + "... Restarting my core systems.")
            
            # 3. Heal / Restart
            print(f"[XAgent] Restarting in 3 seconds... (Attempt {restart_count}/{max_restarts})\n")
            time.sleep(3)
            print("==================================================")

    if restart_count >= max_restarts:
        print("\n[XAgent] 💥 Maximum restart attempts reached. System failure. Shutting down.")
        speak_and_save("Critical system failure. I am unable to recover and must shut down.")

if __name__ == "__main__":
    start_supervisor()
