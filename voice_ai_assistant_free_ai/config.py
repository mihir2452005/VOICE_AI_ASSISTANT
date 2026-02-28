import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

AI_MODE = "gemini"

# Get the API Key securely from the .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-flash-latest"

GROK_API_KEY = os.getenv("GROK_API_KEY")
ACTIVE_PROVIDER = "auto" # "gemini", "grok", or "auto" (dynamically routes based on vision intent)
