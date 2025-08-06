# modes/chat/api_client.py
import requests
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL
from .prompts.system import get_system_prompt
from .prompts.capability_prompts import get_mistral_tools
# api_client.py
import time

_last_call_time = 0  # module-level private state

def call_mistral_api(history, min_interval=1.5):
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
    _last_call_time = time.time()  # update AFTER successful call
    return response.json()['choices'][0]['message']
