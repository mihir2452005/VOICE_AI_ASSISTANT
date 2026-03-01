import os
import glob

def list_directory(folder_path: str = r"d:\projects\degree\jarvis\voice_ai_assistant_free_ai\NOVA"):
    """
    Lists the files and folders inside a specific directory on the user's computer.
    Args:
        folder_path: The absolute or relative path to the folder. Defaults to the NOVA workspace.
    """
    try:
        if not os.path.exists(folder_path):
            return f"Error: The directory '{folder_path}' does not exist on this PC."
            
        if not os.path.isdir(folder_path):
            return f"Error: '{folder_path}' is a file, not a directory."
            
        entries = os.listdir(folder_path)
        
        folders = []
        files = []
        
        for entry in entries:
            full_path = os.path.join(folder_path, entry)
            if os.path.isdir(full_path):
                folders.append(f"[Folder] {entry}")
            else:
                size_kb = os.path.getsize(full_path) / 1024
                files.append(f"[File] {entry} ({size_kb:.1f} KB)")
                
        folders.sort()
        files.sort()
        
        result = f"Contents of directory '{os.path.abspath(folder_path)}':\n"
        result += "\n".join(folders) + "\n" + "\n".join(files)
        
        if not entries:
            result += "Directory is empty."
            
        return result
        
    except Exception as e:
        return f"Failed to list directory contents: {e}"

def read_local_file(filepath: str):
    """
    Reads the text contents of a file on the user's computer.
    Only use this for text-based files like .txt, .md, .py, .json, .csv, etc.
    Args:
        filepath: The absolute or relative path to the file to read.
    """
    try:
        if not os.path.exists(filepath):
            return f"Error: The file '{filepath}' does not exist on this PC."
            
        if not os.path.isfile(filepath):
            return f"Error: '{filepath}' is a directory, not a file."
            
        # Protect against massive files crashing the context window
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if file_size_mb > 2:
            return f"Error: The file is too large to read ({file_size_mb:.1f} MB). Max supported is 2 MB."
            
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        return f"--- Content of '{os.path.abspath(filepath)}' ---\n\n{content}"
        
    except UnicodeDecodeError:
        return f"Error: Failed to read '{filepath}'. It appears to be a binary file (like an image or PDF) which I cannot read as plain text."
    except Exception as e:
        return f"Failed to read file: {e}"
