"""
Chat mode - LLM integration and agentic capabilities
"""
import os
import json
import requests
from tkinter import END

from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL, CHAT_HISTORY_FILE, CHAT_HISTORY_LENGTH
from .prompts.system import get_chat_system_prompt
from .capabilities.task_manager import TaskCapability
from .capabilities.visual_assistant import VisualCapability

# Initialize capabilities
task_capability = TaskCapability()
visual_capability = VisualCapability()

def load_history():
    """Load chat history from file"""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    """Save chat history to file"""
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def clear_history():
    """Clear chat history"""
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)

def handle_input(user_input, console):
    """Main chat input handler - orchestrates capabilities"""
    
    # Handle special commands
    if user_input.lower() in ("/new", "/reset"):
        clear_history()
        console.insert(END, "✨ New chat session started.\n", "accent")
        return

    # Check if any capability can handle this input
    response_data = None
    
    # Try visual capability first
    if visual_capability.can_handle(user_input):
        response_data = visual_capability.handle(user_input)
    
    # If no capability handled it, send to LLM
    if not response_data:
        response_data = call_mistral(user_input)
    
    # Display main response
    if "response" in response_data:
        console.insert(END, f"AI: {response_data['response']}\n")
    
    # Handle any capability-specific outputs
    if "task" in response_data:
        task_capability.add_task(response_data["task"], console)
    
    if "visual_data" in response_data:
        console.insert(END, "📸 Visual data processed\n", "success")

def call_mistral(prompt):
    """Core LLM API call"""
    if not MISTRAL_API_KEY:
        return {"response": "MISTRAL_API_KEY not found. Please set it in your .env file."}

    history = load_history()
    
    # Add user message
    history.append({"role": "user", "content": prompt})
    
    # Trim history
    if len(history) > CHAT_HISTORY_LENGTH:
        history = history[-CHAT_HISTORY_LENGTH:]

    # Check for task intent using task capability
    detected_task = task_capability.detect_task_intent(prompt)
    
    # Prepare API call
    system_prompt = get_chat_system_prompt()
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
        
        response_data = response.json()
        assistant_message_str = response_data['choices'][0]['message']['content']
        assistant_message_json = json.loads(assistant_message_str)
        
        # Add detected task if found
        if detected_task and "task" not in assistant_message_json:
            assistant_message_json["task"] = detected_task
        
        # Save to history
        history.append({"role": "assistant", "content": assistant_message_str})
        save_history(history)
        
        return assistant_message_json
        
    except requests.exceptions.RequestException as e:
        return {"response": f"API Error: {e}"}
    except (KeyError, IndexError):
        return {"response": "Error: Invalid response format from API."}
    except json.JSONDecodeError:
        return {"response": "Error: Failed to decode JSON response from AI."}

def on_mode_enter(console):
    """Called when entering chat mode"""
    console.insert(END, "Chat mode ready. Type /new to reset conversation.\n", "dim")