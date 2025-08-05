# modes/chat/api_client.py
import requests
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL
from .prompts.system import get_system_prompt
from .prompts.capability_prompts import get_mistral_tools

def call_mistral_api(history):
    """Pure API communication - returns raw response."""
    messages = [{"role": "system", "content": get_system_prompt()}]
    
    # Add conversation history
    for msg in history:
        if msg.get("role") in ["user", "assistant", "tool"]:
            messages.append(msg)
    
    # Prepare request
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
    
    return response.json()['choices'][0]['message']