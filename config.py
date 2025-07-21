import os

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") or "your api key"
MISTRAL_MODEL = "mistral-medium"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
NOTES_FILE = os.path.expanduser("~/.local/share/mini-console/notes.txt")
