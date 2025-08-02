import os
import json
import requests
import uuid
from tkinter import END

# Configuration and System Prompts
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL, CHAT_HISTORY_FILE, CHAT_HISTORY_LENGTH
from .prompts.system import get_system_prompt

# Import the actual tool implementations
from .capabilities import task_manager, web_search

# --- Tool & History Management ---
AVAILABLE_TOOLS = {
    "add_task_to_notes": task_manager.add_task_to_notes,
    "search_web": web_search.search_web,
}

def load_history():
    if not os.path.exists(CHAT_HISTORY_FILE): return []
    with open(CHAT_HISTORY_FILE, 'r') as f:
        try: return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError): return []

def save_history(history):
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def clear_history():
    if os.path.exists(CHAT_HISTORY_FILE): os.remove(CHAT_HISTORY_FILE)

# --- Mistral-Compliant Agentic Loop ---

def handle_command(cmd, console, status_label, entry):
    """Handles chat commands using a Mistral-compliant two-step agentic loop."""
    if cmd.lower() in ("/new", "/reset"):
        clear_history()
        console.insert(END, "✨ New chat session started.\n", "accent")
        status_label.config(text="Ready")
        entry.delete(0, END)
        return

    status_label.config(text="Thinking...")
    console.update_idletasks()
    
    history = load_history()
    history.append({"role": "user", "content": cmd})

    try:
        # === STEP 1: Get the AI's plan (which may include a tool call) ===
        console.insert(END, "🤔 Planning...\n", "dim")
        assistant_response = call_mistral(history)
        history.append(assistant_response)

        tool_calls = assistant_response.get("tool_calls")

        # === STEP 2: If no tool is needed, display the response and exit ===
        if not tool_calls:
            final_content = assistant_response.get("content", "I'm not sure how to respond.")
            console.insert(END, f"AI: {final_content}\n")
            status_label.config(text="Ready")
            save_history(history)
            return

        # === STEP 3: Execute the planned tool(s) ===
        console.insert(END, f"🛠️ Using tool(s)...\n", "accent")
        tool_outputs = []
        for tool_call in tool_calls:
            tool_id = tool_call.get("id")
            function_info = tool_call.get("function", {})
            tool_name = function_info.get("name")
            
            if tool_name in AVAILABLE_TOOLS:
                try:
                    # Arguments are a JSON string, so they must be parsed
                    arguments = json.loads(function_info.get("arguments", "{}"))
                    tool_function = AVAILABLE_TOOLS[tool_name]
                    
                    # Execute the tool
                    result = tool_function(**arguments)
                    
                    # Append the successful result
                    tool_outputs.append({"role": "tool", "tool_call_id": tool_id, "name": tool_name, "content": json.dumps({"result": result})})
                except Exception as e:
                    # Append the error result
                    tool_outputs.append({"role": "tool", "tool_call_id": tool_id, "name": tool_name, "content": json.dumps({"error": str(e)})})
            else:
                 tool_outputs.append({"role": "tool", "tool_call_id": tool_id, "name": tool_name, "content": json.dumps({"error": f"Tool '{tool_name}' not found."})})

        # Add all tool outputs to history
        history.extend(tool_outputs)

        # === STEP 4: Get the final, user-facing response from the AI ===
        console.insert(END, "💬 Formulating final response...\n", "dim")
        final_response = call_mistral(history)
        history.append(final_response)
        
        final_content = final_response.get("content", "I have completed the task.")
        console.insert(END, f"AI: {final_content}\n")

    except Exception as e:
        console.insert(END, f"❌ An unexpected error occurred: {e}\n", "error")
    finally:
        status_label.config(text="Ready")
        save_history(history)


def call_mistral(history):
    """Calls the Mistral API with the current history, returning the assistant's response."""
    system_prompt = get_system_prompt()
    messages = [{"role": "system", "content": system_prompt}] + history

    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    data = {"model": MISTRAL_MODEL, "messages": messages}
    
    response = requests.post(MISTRAL_URL, headers=headers, json=data)
    response.raise_for_status()
    
    return response.json()['choices'][0]['message']