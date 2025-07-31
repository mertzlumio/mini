import os
import json
import requests
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL, CHAT_HISTORY_FILE, CHAT_HISTORY_LENGTH
from prompts.base_system import get_base_system_prompt

def load_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def clear_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)

def call_mistral(prompt):
    if not MISTRAL_API_KEY:
        return {"response": "MISTRAL_API_KEY not found. Please set it in your .env file."}

    history = load_history()
    
    # Add the new user message to the history
    history.append({"role": "user", "content": prompt})
    
    # Trim history to the desired length
    if len(history) > CHAT_HISTORY_LENGTH:
        history = history[-CHAT_HISTORY_LENGTH:]

    # Prepare the messages for the API call
    system_prompt = get_base_system_prompt()
    messages_to_send = [{"role": "system", "content": system_prompt}] + history

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MISTRAL_MODEL,
        "messages": messages_to_send,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(MISTRAL_URL, headers=headers, json=data)
        response.raise_for_status()
        
        # The response from the API is a JSON string, which we need to parse
        response_data = response.json()
        assistant_message_str = response_data['choices'][0]['message']['content']
        
        # The content itself is a JSON string, so we parse it again
        assistant_message_json = json.loads(assistant_message_str)
        
        # Save the full user and assistant exchange to history
        # We save the structured JSON from the assistant, not just the text response
        history.append({"role": "assistant", "content": assistant_message_str})
        save_history(history)
        
        return assistant_message_json # Return the parsed JSON {"response": "...", "task": "..."}
        
    except requests.exceptions.RequestException as e:
        return {"response": f"API Error: {e}"}
    except (KeyError, IndexError):
        return {"response": "Error: Invalid response format from API."}
    except json.JSONDecodeError:
        return {"response": "Error: Failed to decode JSON response from AI."}
