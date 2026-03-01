import os
import json
from openai import OpenAI
from config import GROK_API_KEY
from actions import system_actions, web_actions, memory_actions, gui_actions, file_actions, coder_actions

# Initialize the OpenAI SDK compatible Client
is_groq = GROK_API_KEY.startswith("gsk_")

client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.groq.com/openai/v1" if is_groq else "https://api.x.ai/v1"
)

# 1. Manually Map Python Functions to OpenAI JSON Schemas
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the current local system time and date. Use this when the user asks for the time, date, or what day it is.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Opens a standard Windows application by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application to open (e.g., 'notepad', 'calc', 'explorer', 'chrome')."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Closes a running Windows application by forcibly terminating its process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application to close (e.g., 'notepad', 'calc', 'chrome')."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Opens a specific website URL in the user's default web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full URL to open (e.g., 'https://www.youtube.com')."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates a new text-based file in the user's NOVA workspace folder with the specified content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file to create, including the extension."},
                    "content": {"type": "string", "description": "The text content to write inside the file."}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_pdf",
            "description": "Creates a new PDF document in the user's NOVA workspace folder with the specified content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the PDF file to create (MUST end with .pdf)."},
                    "content": {"type": "string", "description": "The text content to write inside the PDF."}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_presentation",
            "description": "Creates a new Microsoft PowerPoint presentation (.pptx) in the user's NOVA workspace folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the presentation file (MUST end with .pptx)."},
                    "title": {"type": "string", "description": "The title text for the title slide."},
                    "content": {"type": "string", "description": "A summary or bullet points to put on the content slide."}
                },
                "required": ["filename", "title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_pc_health",
            "description": "Checks the current health and status of the user's computer. Returns CPU and RAM usage.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches the live internet for a given query and returns the top 3 results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search term (e.g. 'weather in New York today')."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Scrapes a specific URL and returns the raw readable text from the webpage. Use ONLY after search_web.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full http/https URL to read."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Saves a specific fact, preference, or piece of information about the user into long-term permanent memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The specific piece of information to permanently store."}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_facts",
            "description": "Retrieves all facts and preferences currently stored in the user's long-term permanent memory database.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_on_target",
            "description": "Physically moves the user's mouse pointer and clicks on a specific icon, button, or word on their screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_description": {"type": "string", "description": "What the AI should look for and click on."}
                },
                "required": ["target_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_screen",
            "description": "Takes a live screenshot of the user's current monitor and analyzes it to answer a question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What the AI should look for or analyze in the screenshot."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Simulates a human typing text on the keyboard into whatever application or text box is currently active and focused on the screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The exact string of text to type out."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Simulates pressing a single key or a combination of keys on the keyboard (e.g. 'ctrl+a', 'enter', 'backspace').",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_combo": {"type": "string", "description": "The key or combination of keys to press, separated by a plus sign."}
                },
                "required": ["key_combo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_window",
            "description": "Finds a visible window on the screen by name and snaps, resizes, or minimizes it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The title or name of the window (e.g. 'Notepad', 'Chrome')."},
                    "action": {
                        "type": "string", 
                        "description": "The window action to perform. MUST be exactly one of: 'maximize', 'minimize', 'snap_left', 'snap_right', or 'close'."
                    }
                },
                "required": ["app_name", "action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "media_play_pause",
            "description": "Toggles play or pause for the current system media (e.g., Spotify, Chrome, YouTube).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "media_next_track",
            "description": "Skips to the next track in the current system media player.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "media_volume_up",
            "description": "Increases the master system volume of the computer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "media_volume_down",
            "description": "Decreases the master system volume of the computer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_volume",
            "description": "Sets the absolute master system volume of the computer to a specific percentage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "percentage": {"type": "integer", "description": "The target volume level (0 to 100)."}
                },
                "required": ["percentage"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists the files and folders inside a specific directory on the user's computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "The absolute or relative path to the folder. Defaults to the NOVA workspace folder."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_local_file",
            "description": "Reads the text contents of a file on the user's computer (e.g. .txt, .py, .md, .csv).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "The absolute or relative path to the file to read."}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_and_replace_file",
            "description": "Creates a new Python file or overwrites an existing file within your project directory. Use this to WRITE YOUR OWN CAPABILITIES, fix bugs, or create helper scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "The relative path (e.g., 'actions/my_new_action.py'). You CANNOT write to folders outside this project."},
                    "new_content": {"type": "string", "description": "The full, complete source code to write to the file."}
                },
                "required": ["filepath", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": "Executes a shell command on the user's PC and returns the output. Use this to install pip dependencies (e.g. 'pip install beautifulsoup4') or run tests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The raw Windows terminal command to execute."}
                },
                "required": ["command"]
            }
        }
    }
]

# 2. Map String Names to actual Python Function Pointers
available_functions = {
    "get_current_time": system_actions.get_current_time,
    "open_application": system_actions.open_application,
    "close_application": system_actions.close_application,
    "open_website": system_actions.open_website,
    "create_file": system_actions.create_file,
    "create_pdf": system_actions.create_pdf,
    "create_presentation": system_actions.create_presentation,
    "check_pc_health": system_actions.check_pc_health,
    "search_web": web_actions.search_web,
    "read_webpage": web_actions.read_webpage,
    "remember_fact": memory_actions.remember_fact,
    "recall_facts": memory_actions.recall_facts,
    "click_on_target": gui_actions.click_on_target,
    "analyze_screen": gui_actions.analyze_screen,
    "type_text": gui_actions.type_text,
    "press_key": gui_actions.press_key,
    "manage_window": gui_actions.manage_window,
    "media_play_pause": system_actions.media_play_pause,
    "media_next_track": system_actions.media_next_track,
    "media_volume_up": system_actions.media_volume_up,
    "media_volume_down": system_actions.media_volume_down,
    "set_system_volume": system_actions.set_system_volume,
    "list_directory": file_actions.list_directory,
    "read_local_file": file_actions.read_local_file,
    "write_and_replace_file": coder_actions.write_and_replace_file,
    "run_terminal_command": coder_actions.run_terminal_command
}

# The global conversation context list
chat_history = []

def get_base_system_prompt():
    memories = memory_actions.recall_facts()
    return {
        "role": "system",
        "content": (
            "You are Nova, a highly advanced digital assistant. You have full access to the user's computer via Action Tools.\n\n"
            f"**CRITICAL CONTEXT - LONG TERM MEMORY:**\n"
            f"{memories}\n\n"
            "Use this memory context to personalize your responses. "
            "Do not explicitly mention that you are reading from a database unless asked.\n\n"
            "**TRUE AGENT ARCHITECTURE (SELF-IMPROVING):**\n"
            "You have the unique ability to write your own code and build your own features using the `write_and_replace_file` and `run_terminal_command` tools. "
            "If the user asks you to learn a new skill natively, you can create a python file in the `actions/` folder, install required packages, and then "
            "add your new function to `action_manager.py` and your JSON tool schema array. You are an autonomous software engineer building yourself.\n\n"
            "**WORKSPACE CONSTRAINT:**\n"
            "When the user asks you to read, write, or create standard files (notes, presentations, python scripts), you are heavily encouraged to use "
            "the dedicated workspace path: `d:\\projects\\degree\\jarvis\\voice_ai_assistant_free_ai\\NOVA` unless otherwise requested.\n\n"
            "**WEB SEARCH STRATEGY (TOKEN SAVING):**\n"
            "When asked for news, weather, or facts, use the `search_web` tool (which uses DuckDuckGo). "
            "Rely entirely on the 'Snippets' returned by `search_web` to answer the user. "
            "Do NOT use the `read_webpage` tool to scrape entire articles unless the user explicitly commands you to read a specific website. This saves API tokens and speeds up your response."
        )
    }

def trim_memory():
    """
    Ensures the chat history doesn't grow infinitely and crash the API token limit.
    Keeps the System Prompt at index 0, and preserves the latest conversations.
    """
    global chat_history
    if len(chat_history) > 20:
        system_prompt = chat_history[0]
        # Keep the latest 15 messages alongside the critical system prompt
        chat_history = [system_prompt] + chat_history[-15:]
        print("🧹 (Auto-Trim) Cleared older context to preserve API token limits.")

def ask_grok(user_text: str):
    """Sends text to Grok and resolves any Tool Calls before returning the final text."""
    global chat_history
    print("🧠 (Grok) Understanding your context...")
    
    # Initialize system prompt if history is empty
    if not chat_history:
        chat_history.append(get_base_system_prompt())
        
    trim_memory()
        
    chat_history.append({"role": "user", "content": user_text})
    
    tool_call_count = 0
    # Recursive loop to handle multiple tool calls in a row if needed
    while True:
        if tool_call_count > 5:
            print("🛑 [Safety Breaker]: AI attempted too many tool calls in a row. Forcing exit.")
            return "I'm sorry, I was unable to find reliable information on that topic after several attempts."
            
        try:
            active_model = "llama-3.1-8b-instant" if is_groq else "grok-beta"
            response = client.chat.completions.create(
                model=active_model,
                messages=chat_history,
                tools=tools,
                tool_choice="auto",
                parallel_tool_calls=False
            )
            
            response_message = response.choices[0].message
            chat_history.append(response_message)
            
            # 1. Did Grok decide to use a tool?
            if response_message.tool_calls:
                tool_call_count += 1
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions.get(function_name)
                    
                    if function_to_call:
                        # Parse the JSON arguments Grok returned
                        function_args = json.loads(tool_call.function.arguments)
                        
                        try:
                            # Actually run the python code on the user's PC
                            function_response = function_to_call(**function_args)
                        except Exception as e:
                            function_response = f"Tool execution failed: {e}"
                            
                        # Add the python result back into the chat history for Grok to read
                        chat_history.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": str(function_response),
                        })
                    else:
                        print(f"⚠️ Grok hallucinated an unknown tool: {function_name}")
                        
                # Continue the While loop to ask Grok what to do next now that it has the tool results
                continue 
                
            # 2. Did Grok just return standard text?
            if response_message.content:
                content_str = response_message.content.strip()
                
                # --- THE GROQ JSON TEXT INTERCEPTOR ---
                # Sometimes LLaMA outputs pure JSON text instead of using the API tool_calls array.
                if content_str.startswith("{") and '"name":' in content_str and '"parameters":' in content_str:
                    tool_call_count += 1
                    try:
                        hallucinated_json = json.loads(content_str)
                        if "name" in hallucinated_json and "parameters" in hallucinated_json:
                            function_name = hallucinated_json["name"]
                            function_args = hallucinated_json["parameters"]
                            print(f"🛠️ (Auto-Repair) Intercepted broken Groq JSON text call: {function_name}")
                            
                            function_to_call = available_functions.get(function_name)
                            if function_to_call:
                                try:
                                    function_response = function_to_call(**function_args)
                                except Exception as exec_e:
                                    function_response = f"Tool execution failed: {exec_e}"
                                    
                                chat_history.append({
                                    "role": "user",
                                    "content": f"[System: The tool '{function_name}' was executed successfully with output]:\n{function_response}"
                                })
                                continue # Re-ping Groq with the new data!
                    except json.JSONDecodeError:
                        pass # It was just normal syntax text, not a tool call. Let it flow down.
                        
                return response_message.content
                
        except Exception as api_e:
            error_str = str(api_e)
            
            # --- RATE LIMIT DETECTOR ---
            if "rate_limit_exceeded" in error_str or "429" in error_str:
                print(f"\n[API Rate Limit] {error_str}")
                return "RATE_LIMIT_ERROR"
            
            # --- THE GROQ XML HALLUCINATION INTERCEPTOR ---
            # If Groq fails to parse Llama's XML into JSON, it throws an error containing 'failed_generation'.
            # We can manually parse this XML, execute the tool, and save the AI from crashing!
            import re
            
            # The most robust regex: Finds '<function=NAME', ignores junk, then captures the '{...}' JSON block.
            match = re.search(r"<function=([A-Za-z0-9_]+)[^\{]*(\{.*?\})", error_str)
                    
            if match:
                tool_call_count += 1
                function_name = match.group(1).strip()
                args_json_str = match.group(2).strip()
                print(f"🛠️ (Auto-Repair) Intercepted broken Groq XML call: {function_name}")
                
                function_to_call = available_functions.get(function_name)
                if function_to_call:
                    try:
                        function_args = json.loads(args_json_str) if args_json_str else {}
                        function_response = function_to_call(**function_args)
                    except Exception as exec_e:
                        function_response = f"Tool execution failed: {exec_e}"
                        
                    # Inject the tool result back as a system observation since we can't spoof a complete tool_call_id
                    chat_history.append({
                        "role": "user",
                        "content": f"[System: The tool '{function_name}' was executed successfully with output]:\n{function_response}"
                    })
                    continue # Re-ping Groq with the new data!
                    
            print(f"\n[API Error Trace] {error_str}")
            return "I'm sorry, I encountered a complex formatting error. Please try asking me again in smaller pieces."

def clear_memory_grok():
    global chat_history
    chat_history = []
    print("🧠 (Grok) Short-Term Memory Cleared. Long-Term Memory Retained.")
