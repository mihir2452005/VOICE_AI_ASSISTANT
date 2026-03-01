import os
import subprocess

# The strict absolute path to the Voice Assistant directory.
# Nova is FORBIDDEN from reading, writing, or executing code outside of this folder.
PROJECT_ROOT = os.path.abspath(r"d:\projects\degree\jarvis\voice_ai_assistant_free_ai")

def _is_path_safe(filepath: str) -> bool:
    """Internal security check to ensure a filepath is inside the allowed sandbox."""
    try:
        # Resolve any '..' or relative paths into a solid absolute path
        target_path = os.path.abspath(os.path.join(PROJECT_ROOT, filepath))
        
        # Check if the resolved path starts with our locked root directory
        return target_path.startswith(PROJECT_ROOT)
    except Exception:
        return False

def write_and_replace_file(filepath: str, new_content: str):
    """
    Creates a new Python file or overwrites an existing file within the Nova project directory.
    Use this tool to WRITE YOUR OWN CAPABILITIES, fix bugs in your own code, or create helper scripts.
    
    Args:
        filepath: The relative path (e.g., 'actions/my_new_action.py' or 'brain_grok.py'). 
                  You CANNOT write to folders outside this project.
        new_content: The full, complete source code to write to the file.
    """
    try:
        if not _is_path_safe(filepath):
            return f"🛑 SECURITY BLOCK: You are not authorized to write files outside of '{PROJECT_ROOT}'."
            
        target_path = os.path.abspath(os.path.join(PROJECT_ROOT, filepath))
        
        # Ensure subdirectories exist (e.g. if they say 'scripts/new_tool.py')
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        return f"✅ SUCCESS: Overwrote and saved the file at '{target_path}'."
        
    except Exception as e:
        return f"Failed to write file: {e}"

def run_terminal_command(command: str):
    """
    Executes a shell command on the user's PC and returns the output.
    Use this to install pip dependencies (e.g. 'pip install beautifulsoup4') or run tests.
    
    Args:
        command: The raw Windows terminal command to execute.
    """
    try:
        print(f"⚠️ [Security Alert] Nova is executing a terminal command: {command}")
        
        # We run the command explicitly inside the project root directory
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30 # Prevent the AI from running infinite blocking loops
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if result.returncode == 0:
            return f"✅ COMMAND EXECUTED SUCCESSFULLY.\nOUTPUT:\n{output}"
        else:
            return f"❌ COMMAND FAILED (Return Code: {result.returncode}).\nERROR:\n{error}\nOUTPUT:\n{output}"
            
    except subprocess.TimeoutExpired:
        return "🛑 COMMAND TIMED OUT: The process took longer than 30 seconds and was killed."
    except Exception as e:
        return f"Failed to execute command: {e}"
