import time
import traceback
import sys
from main import run_assistant
from tts_offline import speak_and_save
import brain_grok

def auto_repair_with_grok(error_trace):
    """Sends the crash trace directly to the AI so it can rewrite its own code."""
    prompt = f"""
    [SYSTEM CRITICAL ALERT]: YOUR CORE PROCESS JUST CRASHED.
    You are in Emergency Self-Repair Mode. 
    Review the following Python traceback:
    
    {error_trace}
    
    INSTRUCTIONS:
    1. Identify exactly which of your python files caused the crash.
    2. Use your `read_local_file` tool to inspect the broken code.
    3. Use your `write_and_replace_file` tool to rewrite the file and fix the bug.
    4. Once you have saved the fix, return a short 1-sentence summary of what you did. I will read this summary out loud to the user before restarting.
    """
    print("\n[XAgent] 🚨 CRITICAL CRASH INITIATING SELF-REPAIR PROTOCOL...")
    try:
        # We bypass the audio loop and directly query the brain with the error.
        response_text = brain_grok.ask_grok(prompt)
        return response_text
    except Exception as e:
        return f"Self-repair failed. Fatal Engine Error: {e}"

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
            
            # 1. Trigger the Auto-Coder to fix the bug
            diagnosis = auto_repair_with_grok(error_trace)
            print(f"\n[XAgent] 🛠️ Self-Repair Log: {diagnosis}\n")
            
            # 2. Inform the user audibly
            speak_and_save("I experienced a fatal crash, but I have rewritten my own code to fix it. " + diagnosis[:150] + "... Rebooting now.")
            
            # 3. Heal / Restart
            print(f"[XAgent] Restarting in 3 seconds... (Attempt {restart_count}/{max_restarts})\n")
            time.sleep(3)
            print("==================================================")

    if restart_count >= max_restarts:
        print("\n[XAgent] 💥 Maximum restart attempts reached. System failure. Shutting down.")
        speak_and_save("Critical system failure. I am unable to recover and must shut down.")

import sys

if __name__ == "__main__":
    try:
        start_supervisor()
    except KeyboardInterrupt:
        print("\n[XAgent] 🛑 Assistant stopped manually by user. Shutting down Supervisor.")
        sys.exit(0)
