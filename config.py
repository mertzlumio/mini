import os
from dotenv import load_dotenv

load_dotenv()

# Configuration settings  
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-medium") 
MISTRAL_URL = os.getenv("MISTRAL_URL", "https://api.mistral.ai/v1/chat/completions")
NOTES_FILE = os.path.expanduser(os.getenv("NOTES_FILE", "~/notes.txt"))

# Enhanced chat history and memory configuration
CHAT_HISTORY_DIR = os.path.expanduser(os.getenv("CHAT_HISTORY_DIR", "~/mini_chat_data"))
CHAT_HISTORY_LENGTH = int(os.getenv("CHAT_HISTORY_LENGTH", "20"))

# Memory system settings
MEMORY_DIR = os.path.join(CHAT_HISTORY_DIR, "memory")
AUTO_COMPRESS_THRESHOLD = int(os.getenv("AUTO_COMPRESS_THRESHOLD", "40"))
FACT_IMPORTANCE_THRESHOLD = float(os.getenv("FACT_IMPORTANCE_THRESHOLD", "0.6"))

# Validation
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY must be set in environment variables or .env file")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")