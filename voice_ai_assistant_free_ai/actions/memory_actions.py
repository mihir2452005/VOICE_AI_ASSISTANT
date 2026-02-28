import sqlite3
import os

DB_FILE = "long_term_memory.db"

def _init_db():
    """Initializes the SQLite database and creates the memories table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the db when the module is imported
_init_db()

def remember_fact(fact: str):
    """
    Saves a specific fact, preference, or piece of information about the user into long-term permanent memory.
    Use this ONLY when the user explicitly asks you to remember something (e.g., "Remember that my wife's name is Sarah", or "Save my wifi password: password123").
    Args:
        fact: The specific piece of information to permanently store.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memories (fact) VALUES (?)", (fact,))
        conn.commit()
        conn.close()
        return f"Successfully saved to long-term memory: '{fact}'"
    except Exception as e:
        return f"Failed to save to memory. Error: {e}"

def recall_facts():
    """
    Retrieves all facts and preferences currently stored in the user's long-term permanent memory database.
    Use this if the user asks you what you remember about them, or asks you to recall a specific detail you may have stored in the past.
    """
    try:
        if not os.path.exists(DB_FILE):
             return "Long-term memory is currently empty."
             
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT fact, timestamp FROM memories ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "Long-term memory is currently empty."
            
        formatted_memories = "Here is everything stored in Long-Term Memory:\n"
        for fact, timestamp in rows:
            formatted_memories += f"- {fact} (Stored on: {timestamp})\n"
            
        return formatted_memories
    except Exception as e:
        return f"Failed to recall memories. Error: {e}"
