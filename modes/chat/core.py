import os
import json
from tkinter import END
import requests
from datetime import datetime
import atexit

from config import CHAT_HISTORY_DIR, CHAT_HISTORY_LENGTH
from .api_client import call_mistral_api
from .capabilities.agent import handle_agent_response
from .history.history_sanitizer import sanitize_and_trim_history
from .memory.memory_manager import MemoryManager

# Global memory manager - this replaces simple session history!
_memory_manager = None

def get_memory_manager():
    """Get or create the memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        memory_dir = os.path.join(CHAT_HISTORY_DIR, 'memory')
        _memory_manager = MemoryManager(memory_dir, call_mistral_api)
    return _memory_manager

def load_history():
    """Returns enhanced history with long-term memory context"""
    memory_manager = get_memory_manager()
    return memory_manager.get_enhanced_history(max_recent=CHAT_HISTORY_LENGTH)

def save_current_session():
    """Save current session and process for long-term memory"""
    memory_manager = get_memory_manager()
    
    if not memory_manager.working_memory:
        return None
    
    # Process conversation for long-term storage
    if len(memory_manager.working_memory) > 5:
        memory_manager.process_conversation_chunk(memory_manager.working_memory)
    
    # Save raw session log (as before)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"chat_session_{timestamp}.json"
    
    os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
    log_path = os.path.join(CHAT_HISTORY_DIR, log_filename)
    
    try:
        # Save sanitized working memory
        sanitized_history = sanitize_and_trim_history(
            memory_manager.working_memory, 
            max_messages=CHAT_HISTORY_LENGTH * 2
        )
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(sanitized_history, f, indent=2, ensure_ascii=False)
        
        stats = memory_manager.get_stats()
        print(f"Session saved to {log_path}")
        print(f"Memory stats: {stats['total_facts']} facts, {stats['total_summaries']} summaries")
        return log_path
    except Exception as e:
        print(f"Error saving session: {e}")
        return None

def clear_session_history():
    """Clear current session and process for long-term storage"""
    memory_manager = get_memory_manager()
    old_count = len(memory_manager.working_memory)
    
    # Process current session before clearing
    memory_manager.clear_session()
    
    return old_count

def add_to_session_history(message):
    """Add message to working memory"""
    memory_manager = get_memory_manager()
    memory_manager.add_to_working_memory(message)
    
    # Auto-compress if working memory gets too large
    if memory_manager.should_compress_memory(threshold=40):
        compressed_count = memory_manager.compress_working_memory(keep_recent=15)
        print(f"Auto-compressed {compressed_count} old messages to long-term memory")

def handle_command(cmd, console, status_label, entry):
    """Enhanced chat handler with memory commands"""
    memory_manager = get_memory_manager()
    
    # Memory-specific commands
    if cmd.lower().startswith(("/search", "/find", "/remember")):
        query = cmd.split(maxsplit=1)[1] if len(cmd.split()) > 1 else ""
        if not query:
            console.insert(END, "Usage: /search <query>\n", "warning")
            return
        
        results = memory_manager.search_memory(query)
        console.insert(END, f"{results}\n", "accent")
        status_label.config(text="Ready")
        return
    
    if cmd.lower() in ("/memory", "/stats"):
        stats = memory_manager.get_stats()
        console.insert(END, f"🧠 Memory Statistics:\n", "accent")
        console.insert(END, f"  Working Memory: {stats['working_memory_size']} messages\n")
        console.insert(END, f"  Long-term Facts: {stats['total_facts']}\n")
        console.insert(END, f"  Conversation Summaries: {stats['total_summaries']}\n") 
        console.insert(END, f"  User Preferences: {stats['preferences_count']}\n")
        console.insert(END, f"  Session ID: {stats['session_id']}\n", "dim")
        status_label.config(text="Ready")
        return
    
    if cmd.lower() == "/compress":
        if len(memory_manager.working_memory) > 10:
            compressed = memory_manager.compress_working_memory(keep_recent=5)
            console.insert(END, f"✨ Compressed {compressed} messages to long-term memory\n", "success")
        else:
            console.insert(END, "Not enough messages to compress\n", "dim")
        status_label.config(text="Ready")
        return
    
    # Existing commands
    if cmd.lower() in ("/new", "/reset"):
        if memory_manager.working_memory:
            saved_path = save_current_session()
            if saved_path:
                console.insert(END, f"💾 Previous session saved and processed\n", "dim")
        
        count = clear_session_history()
        console.insert(END, f"✨ New chat session started (cleared {count} messages)\n", "accent")
        status_label.config(text="Ready")
        return

    if cmd.lower() == "/save":
        saved_path = save_current_session()
        if saved_path:
            console.insert(END, f"💾 Session saved to {os.path.basename(saved_path)}\n", "success")
        else:
            console.insert(END, f"❌ Failed to save session\n", "error")
        status_label.config(text="Ready")
        return

    # Regular chat processing
    status_label.config(text="Thinking...")
    console.update_idletasks()
    
    # Get enhanced history (includes long-term memory context)
    history = load_history()
    
    # Add user message
    user_message = {"role": "user", "content": cmd}
    history.append(user_message)
    add_to_session_history(user_message)

    try:
        console.insert(END, "🤔 Processing...\n", "dim")
        
        # Get response from API (now with memory context!)
        response = call_mistral_api(history)
        
        # Add assistant response to memory
        add_to_session_history(response)
        
        # Handle response (agent capabilities)
        handle_agent_response(response, memory_manager.working_memory, console, status_label)

    except requests.exceptions.HTTPError as e:
        console.insert(END, f"❌ API Error {e.response.status_code}\n", "error")
        console.insert(END, f"Details: {e.response.text[:200]}...\n", "dim")
    except Exception as e:
        console.insert(END, f"❌ Error: {str(e)}\n", "error")
    finally:
        status_label.config(text="Ready")

# Register exit handler
def _exit_handler():
    """Save session and process for long-term memory on exit"""
    memory_manager = get_memory_manager()
    if memory_manager.working_memory:
        save_current_session()
        print("Chat session saved and processed for long-term memory")

atexit.register(_exit_handler)
