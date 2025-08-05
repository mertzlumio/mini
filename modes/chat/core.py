import os
import json
from tkinter import END

# Configuration
from config import CHAT_HISTORY_FILE, CHAT_HISTORY_LENGTH
from .api_client import call_mistral_api
from .capabilities.agent import handle_agent_response

def load_history():
    if not os.path.exists(CHAT_HISTORY_FILE): 
        return []
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): 
        return []

def save_history(history):
    if len(history) > CHAT_HISTORY_LENGTH:
        history = history[-CHAT_HISTORY_LENGTH:]
    
    os.makedirs(os.path.dirname(CHAT_HISTORY_FILE), exist_ok=True)
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def clear_history():
    if os.path.exists(CHAT_HISTORY_FILE): 
        os.remove(CHAT_HISTORY_FILE)

def handle_command(cmd, console, status_label, entry):
    """Main chat handler - delegates to agent capabilities."""
    if cmd.lower() in ("/new", "/reset"):
        clear_history()
        console.insert(END, "✨ New chat session started.\n", "accent")
        status_label.config(text="Ready")
        return

    status_label.config(text="Thinking...")
    console.update_idletasks()
    
    history = load_history()
    
    # Trim history if getting too long
    if len(history) > 15:
        console.insert(END, "🧹 Trimming conversation...\n", "dim")
        history = history[-10:]
    
    history.append({"role": "user", "content": cmd})

    try:
        console.insert(END, "🤔 Processing...\n", "dim")
        
        # Get response from API
        response = call_mistral_api(history)
        
        # Let agent capability handle the response logic
        handle_agent_response(response, history, console, status_label)

    except requests.exceptions.HTTPError as e:
        console.insert(END, f"❌ API Error {e.response.status_code}\n", "error")
        console.insert(END, f"Details: {e.response.text[:200]}...\n", "dim")
    except Exception as e:
        console.insert(END, f"❌ Error: {str(e)}\n", "error")
    finally:
        status_label.config(text="Ready")
        save_history(history)