import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration settings
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-medium")  # Default fallback
MISTRAL_URL = os.getenv("MISTRAL_URL", "https://api.mistral.ai/v1/chat/completions")
NOTES_FILE = os.path.expanduser(os.getenv("NOTES_FILE", "~/notes.txt"))  # Default fallback
CHAT_HISTORY_FILE = os.path.expanduser(os.getenv("CHAT_HISTORY_FILE", "modes/chat/history/chat_history.json"))
CHAT_HISTORY_LENGTH = int(os.getenv("CHAT_HISTORY_LENGTH", "20")) # Keep last 20 messages
CHAT_HISTORY_DIR = "history/chat"


# Validation
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY must be set in environment variables or .env file")

# Optional: Add other configuration constants
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")