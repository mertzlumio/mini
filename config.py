import os

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") or "YOUR_API_KEY"
MISTRAL_MODEL = "mistral-medium"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
NOTES_FILE = os.path.expanduser("PATH_TO_YOUR_NOTES_FILE")
