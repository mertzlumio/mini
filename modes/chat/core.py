import os
import json
from tkinter import END
import requests
from datetime import datetime

# Configuration
from config import CHAT_HISTORY_FILE, CHAT_HISTORY_LENGTH, CHAT_HISTORY_DIR
from .api_client import call_mistral_api
from .capabilities.agent import handle_agent_response
from .history.history_sanitizer import sanitize_and_trim_history

def load_history():
    """Always starts a new session, so returns an empty history."""
    return []

def save_history(history):
    """Saves the final chat history to a timestamped log file."""
    if not history:
        return # Don't save empty histories

    # Sanitize one last time before saving
    history = sanitize_and_trim_history(history, max_messages=CHAT_HISTORY_LENGTH * 2) # Save a bit more context
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"chat_log_{timestamp}.json"
    log_path = os.path.join(CHAT_HISTORY_DIR, log_filename)
    
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"Session saved to {log_path}")


def clear_history():
    """Clears the in-memory history for the current session."""
    # This function is now mostly for the /new command, to clear the current session
    # without having to restart the application.
    return []

def handle_command(cmd, console, status_label, entry):
    """Main chat handler - delegates to agent capabilities."""
    if cmd.lower() in ("/new", "/reset"):
        # The actual history clearing will be handled by the caller
        console.insert(END, "✨ New chat session started.\n", "accent")
        status_label.config(text="Ready")
        # Signal to the main app to clear the history list
        return "clear_session"

    status_label.config(text="Thinking...")
    console.update_idletasks()
    
    history = load_history()
    
    # Sanitize and trim history before sending to the API
    history = sanitize_and_trim_history(history, max_messages=CHAT_HISTORY_LENGTH)
    
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
        # The final history is saved by the main application loop upon exit.
        # This prevents saving incomplete logs if the app crashes.
