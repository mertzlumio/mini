import os
import json
import requests
import re
from config import MISTRAL_API_KEY, MISTRAL_MODEL, MISTRAL_URL, CHAT_HISTORY_FILE, CHAT_HISTORY_LENGTH
from prompts.base_system import get_base_system_prompt
from screenshot import VisualAssistant

# Initialize visual assistant
visual_assistant = VisualAssistant()

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

def detect_visual_commands(prompt):
    """Detect if user wants visual assistance"""
    visual_patterns = {
        'screenshot': r'\b(screenshot|capture screen|take screen|screen shot)\b',
        'screen_info': r'\b(screen size|screen info|display info|resolution)\b',
        'region_screenshot': r'\b(capture region|region screenshot|crop screen)\b',
        'list_screenshots': r'\b(list screenshots|show screenshots|recent screens)\b',
        'cleanup': r'\b(cleanup screenshots|delete old screens|clean screens)\b'
    }
    
    prompt_lower = prompt.lower()
    
    for command, pattern in visual_patterns.items():
        if re.search(pattern, prompt_lower):
            return command
    
    return None

def detect_task_intent(prompt):
    """Smart task detection using regex patterns"""
    task_patterns = [
        r'\b(?:remind me to|i need to|i have to|todo:|task:)\s+(.+)',
        r'\b(?:add task|add to list|remember to)\s+(.+)',
        r'\b(?:deadline|due by|meeting at|appointment)\s+(.+)',
        r'\b(?:buy|pick up|get|purchase)\s+(.+)',
        r'\b(?:call|email|contact)\s+(.+)'
    ]
    
    for pattern in task_patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            return match.group(1).strip()
    
    return None

def handle_visual_command(command, prompt):
    """Handle visual assistance commands"""
    try:
        if command == 'screenshot':
            result = visual_assistant.take_screenshot()
            if result['success']:
                return {
                    "response": f"📸 Screenshot taken successfully!\nSaved as: {result['filename']}\nSize: {result['size'][0]}x{result['size'][1]}",
                    "screenshot_path": result['filepath'],
                    "visual_data": True
                }
            else:
                return {"response": f"❌ Failed to take screenshot: {result['error']}"}
        
        elif command == 'screen_info':
            result = visual_assistant.get_screen_info()
            if result['success']:
                return {
                    "response": f"🖥️ Screen Information:\nResolution: {result['width']}x{result['height']}\nTotal pixels: {result['total_pixels']:,}"
                }
            else:
                return {"response": f"❌ Failed to get screen info: {result['error']}"}
        
        elif command == 'list_screenshots':
            result = visual_assistant.list_screenshots()
            if result['success']:
                if result['screenshots']:
                    screenshot_list = "\n".join([
                        f"• {shot['filename']} ({shot['size_kb']}KB) - {shot['modified']}"
                        for shot in result['screenshots']
                    ])
                    return {
                        "response": f"📁 Recent Screenshots ({result['total_count']} total):\n{screenshot_list}"
                    }
                else:
                    return {"response": "📁 No screenshots found."}
            else:
                return {"response": f"❌ Failed to list screenshots: {result['error']}"}
        
        elif command == 'cleanup':
            result = visual_assistant.cleanup_old_screenshots()
            if result['success']:
                return {"response": f"🧹 {result['message']}"}
            else:
                return {"response": f"❌ Failed to cleanup: {result['error']}"}
        
        elif command == 'region_screenshot':
            # Extract coordinates if provided, otherwise give instructions
            coords_match = re.search(r'(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)', prompt)
            if coords_match:
                x1, y1, x2, y2 = map(int, coords_match.groups())
                result = visual_assistant.take_region_screenshot(x1, y1, x2, y2)
                if result['success']:
                    return {
                        "response": f"📸 Region screenshot taken!\nArea: ({x1},{y1}) to ({x2},{y2})\nSaved as: {result['filename']}",
                        "screenshot_path": result['filepath'],
                        "visual_data": True
                    }
                else:
                    return {"response": f"❌ Failed to take region screenshot: {result['error']}"}
            else:
                return {
                    "response": "📐 To take a region screenshot, provide coordinates:\nExample: 'capture region 100 100 500 400'\nFormat: x1 y1 x2 y2"
                }
        
    except Exception as e:
        return {"response": f"❌ Visual command error: {str(e)}"}

def call_mistral(prompt):
    """Enhanced Mistral API call with visual capabilities"""
    
    # First check for visual commands
    visual_command = detect_visual_commands(prompt)
    if visual_command:
        return handle_visual_command(visual_command, prompt)
    
    # Check for task intent
    task_content = detect_task_intent(prompt)
    
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
        
        # Add detected task if found
        if task_content and "task" not in assistant_message_json:
            assistant_message_json["task"] = task_content
        
        # Save the full user and assistant exchange to history
        history.append({"role": "assistant", "content": assistant_message_str})
        save_history(history)
        
        return assistant_message_json # Return the parsed JSON {"response": "...", "task": "..."}
        
    except requests.exceptions.RequestException as e:
        return {"response": f"API Error: {e}"}
    except (KeyError, IndexError):
        return {"response": "Error: Invalid response format from API."}
    except json.JSONDecodeError:
        return {"response": "Error: Failed to decode JSON response from AI."}