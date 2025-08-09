import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (one level up from this file)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Configuration settings  
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# TEXT MODEL - for regular chat (your existing model)
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-medium")

# VISION MODEL - FIXED: Use correct vision model name
MISTRAL_VISION_MODEL = os.getenv("MISTRAL_VISION_MODEL", "pixtral-large-latest")

MISTRAL_URL = os.getenv("MISTRAL_URL", "https://api.mistral.ai/v1/chat/completions")
NOTES_FILE = os.path.expanduser(os.getenv("NOTES_FILE", "~/notes.txt"))

# Enhanced chat history and memory configuration
CHAT_HISTORY_DIR = os.path.expanduser(os.getenv("CHAT_HISTORY_DIR", "~/mini_chat_data"))
CHAT_HISTORY_LENGTH = int(os.getenv("CHAT_HISTORY_LENGTH", "20"))

# Memory system settings
MEMORY_DIR = os.path.join(CHAT_HISTORY_DIR, "memory")
AUTO_COMPRESS_THRESHOLD = int(os.getenv("AUTO_COMPRESS_THRESHOLD", "40"))
FACT_IMPORTANCE_THRESHOLD = float(os.getenv("FACT_IMPORTANCE_THRESHOLD", "0.6"))

# Vision settings
SCREENSHOT_QUALITY = int(os.getenv("SCREENSHOT_QUALITY", "75"))
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "1024"))

# Validation
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY must be set in environment variables or .env file")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# FIXED: Updated vision-capable models list (December 2024)
VISION_MODELS = [
    "pixtral-large-latest",     # Current best vision model
    "pixtral-12b-latest",       # Alternative vision model  
    "pixtral-12b-2409",         # Specific version
    # Note: mistral-medium/small models don't actually support vision
]

def get_vision_model():
    """Get the model to use for vision calls"""
    return MISTRAL_VISION_MODEL

def get_text_model():
    """Get the model to use for regular text calls"""
    return MISTRAL_MODEL

def supports_vision(model_name=None):
    """Check if a model supports vision"""
    if model_name is None:
        model_name = MISTRAL_VISION_MODEL
    return model_name in VISION_MODELS

# Print current configuration for debugging
if DEBUG:
    print(f"Project root: {project_root}")
    print(f"Loaded .env from: {env_path}")
    print(f"Text Model: {MISTRAL_MODEL}")
    print(f"Vision Model: {MISTRAL_VISION_MODEL}")
    print(f"Vision Support: {supports_vision()}")
    print(f"Available Vision Models: {VISION_MODELS}")

# ADDITIONAL: Validate vision model
if MISTRAL_VISION_MODEL not in VISION_MODELS:
    print(f"WARNING: Vision model '{MISTRAL_VISION_MODEL}' may not support vision!")
    print(f"Consider using one of: {VISION_MODELS}")