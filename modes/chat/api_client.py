# Updated modes/chat/api_client.py - Using separate models
import requests
import time
from config import MISTRAL_API_KEY, MISTRAL_URL, get_text_model, get_vision_model
from .prompts.system import get_system_prompt
from .prompts.capability_prompts import get_mistral_tools

_last_call_time = 0

def call_mistral_api(history, min_interval=1.5):
    """
    Standard Mistral API call for text-only conversations
    Uses your regular text model (mistral-medium)
    """
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time

    if elapsed < min_interval:
        wait_time = min_interval - elapsed
        time.sleep(wait_time)

    # Use TEXT model for regular chat
    text_model = get_text_model()
    print(f"DEBUG: Using text model: {text_model}")

    messages = [{"role": "system", "content": get_system_prompt()}]
    for msg in history:
        if msg.get("role") in ["user", "assistant", "tool"]:
            messages.append(msg)

    data = {
        "model": text_model,  # mistral-medium
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
    Mistral Vision API call for screen analysis
    Uses separate vision model (pixtral-12b-latest)
    """
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time

    if elapsed < min_interval:
        wait_time = min_interval - elapsed
        time.sleep(wait_time)

    # Use VISION model for screen analysis
    vision_model = get_vision_model()
    print(f"DEBUG: Using vision model: {vision_model}")
    
    messages = [{"role": "system", "content": get_system_prompt()}]
    
    # Add recent history (but keep it simple for vision)
    recent_history = history[-3:] if len(history) > 3 else history
    for msg in recent_history:
        if msg.get("role") in ["user", "assistant"]:
            messages.append(msg)
    
    # Add the vision message
    vision_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "I've captured my current screen. Please analyze what you see and help me understand the content."
            },
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{image_base64}"
            }
        ]
    }
    messages.append(vision_message)

    # Simplified request for vision (no tools to avoid conflicts)
    data = {
        "model": vision_model,  # pixtral-12b-latest
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        print(f"DEBUG: Making vision API call with {vision_model}")
        response = requests.post(MISTRAL_URL, headers=headers, json=data)
        
        if response.status_code != 200:
            print(f"DEBUG: Vision API Status: {response.status_code}")
            print(f"DEBUG: Vision API Response: {response.text}")
        
        response.raise_for_status()
        _last_call_time = time.time()
        return response.json()['choices'][0]['message']
        
    except Exception as e:
        print(f"DEBUG: Vision API failed: {e}")
        # Fallback to text model with description
        fallback_message = {
            "role": "assistant", 
            "content": "I captured your screen but couldn't analyze the visual content. However, I can still help you with text-based assistance."
        }
        return fallback_message

def supports_vision():
    """Check if vision is available"""
    from config import supports_vision as config_supports_vision
    return config_supports_vision()