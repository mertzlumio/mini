# Updated config.py - Now with Vision Model Support
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration settings  
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Updated model selection - now defaults to vision-capable model
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "pixtral-12b-latest")  # Changed default to vision model!

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
VISION_MODEL_OVERRIDE = os.getenv("VISION_MODEL_OVERRIDE")  # Optional override for vision calls
SCREENSHOT_QUALITY = int(os.getenv("SCREENSHOT_QUALITY", "75"))  # JPEG quality for screenshots
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "1024"))  # Max image size for API

# Validation
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY must be set in environment variables or .env file")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Vision-capable models (as per Mistral docs)
VISION_MODELS = [
    "pixtral-12b-latest",
    "pixtral-large-latest", 
    "mistral-medium-latest",
    "mistral-small-latest",
    "pixtral-12b-2409"
]

def get_effective_vision_model():
    """Get the model to use for vision calls"""
    if VISION_MODEL_OVERRIDE:
        return VISION_MODEL_OVERRIDE
    
    # If current model supports vision, use it
    if MISTRAL_MODEL in VISION_MODELS:
        return MISTRAL_MODEL
    
    # Otherwise default to Pixtral 12B
    return "pixtral-12b-latest"

def model_supports_vision(model_name=None):
    """Check if a model supports vision"""
    if model_name is None:
        model_name = MISTRAL_MODEL
    return model_name in VISION_MODELS