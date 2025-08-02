import os
import json
import requests
from tkinter import END

# Configuration
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL, CHAT_HISTORY_FILE, CHAT_HISTORY_LENGTH
from .prompts.system import get_system_prompt
from .prompts.capability_prompts import get_mistral_tools
from .capabilities import task_manager, web_search

# Tool registry - maps tool names to actual functions
TOOL_REGISTRY = {
    "add_task_to_notes": task_manager.add_task_to_notes,
    "search_web": web_search.search_web,
}

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
    """Main chat handler - routes between API and tools."""
    if cmd.lower() in ("/new", "/reset"):
        clear_history()
        console.insert(END, "✨ New chat session started.\n", "accent")
        status_label.config(text="Ready")
        return

    status_label.config(text="Thinking...")
    console.update_idletasks()
    
    history = load_history()
    
    # Check if last message was a tool - if so, we need to complete the tool cycle first
    if history and history[-1].get("role") == "tool":
        console.insert(END, "🔄 Completing previous tool usage...\n", "dim")
        # Get assistant response to the tool result first
        assistant_response = call_mistral_api(history)
        history.append(assistant_response)
        
        # Display the assistant's response
        content = assistant_response.get("content", "Task completed.")
        console.insert(END, f"AI: {content}\n")
    
    # Now add the new user message
    history.append({"role": "user", "content": cmd})

    try:
        # Get AI response to new user message
        console.insert(END, "🤔 Processing...\n", "dim")
        assistant_response = call_mistral_api(history)
        history.append(assistant_response)

        # Check if AI wants to use tools
        tool_calls = assistant_response.get("tool_calls")
        if not tool_calls:
            # Direct response, no tools needed
            content = assistant_response.get("content", "I'm not sure how to respond.")
            console.insert(END, f"AI: {content}\n")
            status_label.config(text="Ready")
            save_history(history)
            return

        # Execute tools
        console.insert(END, f"🛠️ Using tool(s)...\n", "accent")
        execute_tools(tool_calls, history)
        
        # Get final response after tool execution
        console.insert(END, "💬 Formulating response...\n", "dim")
        final_response = call_mistral_api(history)
        history.append(final_response)
        
        content = final_response.get("content", "Task completed.")
        console.insert(END, f"AI: {content}\n")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            console.insert(END, f"❌ API Error (400): Invalid request\n", "error")
            console.insert(END, f"Details: {e.response.text}\n", "dim")
        else:
            console.insert(END, f"❌ API Error ({e.response.status_code})\n", "error")
    except Exception as e:
        console.insert(END, f"❌ Error: {str(e)}\n", "error")
    finally:
        status_label.config(text="Ready")
        save_history(history)

def validate_message_sequence(messages):
    """Ensure message sequence follows Mistral's rules."""
    if len(messages) < 2:
        return messages
    
    validated = [messages[0]]  # Keep system message
    
    for i, msg in enumerate(messages[1:], 1):
        prev_msg = validated[-1] if validated else None
        
        # Rule: tool message must be followed by assistant message
        if prev_msg and prev_msg.get("role") == "tool" and msg.get("role") == "user":
            # Insert a dummy assistant message to complete the tool cycle
            validated.append({
                "role": "assistant", 
                "content": "Task completed."
            })
        
        validated.append(msg)
    
    return validated

def call_mistral_api(history):
    """Pure API communication - no business logic."""
    messages = [{"role": "system", "content": get_system_prompt()}]
    
    # Add conversation history
    for msg in history:
        if msg.get("role") in ["user", "assistant", "tool"]:
            messages.append(msg)
    
    # Validate message sequence
    messages = validate_message_sequence(messages)
    
    # Prepare API request
    data = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "tools": get_mistral_tools(),  # Tool definitions from prompts
        "tool_choice": "auto"
    }
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(MISTRAL_URL, headers=headers, json=data)
    response.raise_for_status()
    
    return response.json()['choices'][0]['message']

def execute_tools(tool_calls, history):
    """Execute tool calls and add results to history."""
    for tool_call in tool_calls:
        tool_id = tool_call.get("id")
        function_info = tool_call.get("function", {})
        tool_name = function_info.get("name")
        
        if tool_name in TOOL_REGISTRY:
            try:
                # Parse arguments and execute tool
                arguments = json.loads(function_info.get("arguments", "{}"))
                tool_function = TOOL_REGISTRY[tool_name]
                result = tool_function(**arguments)
                
                # Add successful result to history
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": str(result)
                })
                
            except Exception as e:
                # Add error result to history
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": f"Error: {str(e)}"
                })
        else:
            # Unknown tool
            history.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": f"Error: Tool '{tool_name}' not available."
            })