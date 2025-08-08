# Updated modes/chat/api_client.py - Now with Vision Support!
import requests
import time
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL
from .prompts.system import get_system_prompt
from .prompts.capability_prompts import get_mistral_tools

_last_call_time = 0  # module-level private state

def call_mistral_api(history, min_interval=1.5):
    """Standard Mistral API call for text-only conversations"""
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time

    if elapsed < min_interval:
        wait_time = min_interval - elapsed
        time.sleep(wait_time)

    messages = [{"role": "system", "content": get_system_prompt()}]
    for msg in history:
        if msg.get("role") in ["user", "assistant", "tool"]:
            messages.append(msg)

    data = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "tools": get_mistral_tools(),
        "tool_choice": "auto"
    }

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(MISTRAL_URL, headers=headers, json=data)
    response.raise_for_status()
    _last_call_time = time.time()
    return response.json()['choices'][0]['message']

def call_mistral_vision_api(history, image_base64, min_interval=1.5):
    """
    Enhanced Mistral API call with vision support
    Uses vision-capable models like pixtral-12b-latest
    """
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time

    if elapsed < min_interval:
        wait_time = min_interval - elapsed
        time.sleep(wait_time)

    # Use vision-capable model
    vision_model = get_vision_model()
    
    messages = [{"role": "system", "content": get_system_prompt()}]
    
    # Add history messages
    for msg in history:
        if msg.get("role") in ["user", "assistant", "tool"]:
            messages.append(msg)
    
    # Add the vision message with the captured screenshot
    vision_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "I've captured a screenshot of my current screen. Please analyze what you see and help me with any questions I have about the visual content."
            },
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{image_base64}"
            }
        ]
    }
    messages.append(vision_message)

    data = {
        "model": vision_model,
        "messages": messages,
        "tools": get_mistral_tools(),
        "tool_choice": "auto",
        "max_tokens": 1024  # Reasonable limit for vision responses
    }

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(MISTRAL_URL, headers=headers, json=data)
        response.raise_for_status()
        _last_call_time = time.time()
        return response.json()['choices'][0]['message']
    except Exception as e:
        print(f"Vision API call failed: {e}")
        # Fallback to regular API call
        return call_mistral_api(history, min_interval)

def get_vision_model():
    """
    Get the appropriate vision model based on current configuration
    Falls back to pixtral-12b-latest if current model doesn't support vision
    """
    from config import MISTRAL_MODEL
    
    # Vision-capable models from Mistral documentation
    vision_models = [
        "pixtral-12b-latest",
        "pixtral-large-latest", 
        "mistral-medium-latest",
        "mistral-small-latest",
        "pixtral-12b-2409"  # Specific version mentioned in docs
    ]
    
    # If current model supports vision, use it
    if MISTRAL_MODEL in vision_models:
        return MISTRAL_MODEL
    
    # Otherwise, default to Pixtral 12B
    print(f"Current model {MISTRAL_MODEL} doesn't support vision, using pixtral-12b-latest")
    return "pixtral-12b-latest"

def supports_vision(model_name=None):
    """Check if a model supports vision capabilities"""
    if model_name is None:
        model_name = MISTRAL_MODEL
    
    vision_models = [
        "pixtral-12b-latest",
        "pixtral-large-latest", 
        "mistral-medium-latest",
        "mistral-small-latest",
        "pixtral-12b-2409"
    ]
    
    return model_name in vision_models