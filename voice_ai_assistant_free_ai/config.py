import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

AI_MODE = "gemini"

# Get the API Key securely from the .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "models/gemini-flash-latest"
