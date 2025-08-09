# Updated modes/chat/core.py - Progressive text display and better UX
import os
import json
from tkinter import END
import requests
from datetime import datetime
import atexit
import threading
import time

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

def typewriter_effect(console, text, delay=0.02):
    """
    Display text with typewriter effect for better UX
    """
    def type_char(char_index=0):
        if char_index < len(text):
            console.insert(END, text[char_index])
            console.see(END)
            console.update_idletasks()
            # Schedule next character
            console.after(int(delay * 1000), lambda: type_char(char_index + 1))
    
    type_char()

def display_response_progressively(console, response_text, prefix="AI: "):
    """
    Display AI response with better formatting and progressive reveal
    """
    # Add the prefix immediately
    console.insert(END, prefix)
    console.see(END)
    console.update_idletasks()
    
    # Split into chunks for progressive display
    chunks = response_text.split('\n\n')  # Split by double newlines (paragraphs)
    
    for i, chunk in enumerate(chunks):
        if chunk.strip():  # Skip empty chunks
            # Display chunk with slight delay
            time.sleep(0.1)  # Small pause between paragraphs
            console.insert(END, chunk)
            
            # Add paragraph break if not the last chunk
            if i < len(chunks) - 1:
                console.insert(END, '\n\n')
            
            console.see(END)
            console.update_idletasks()
    
    console.insert(END, '\n')  # Final newline
    console.see(END)

def show_thinking_animation(console, status_label):
    """
    Show animated thinking indicator
    """
    thinking_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    char_index = [0]  # Use list to make it mutable in nested function
    thinking_active = [True]
    
    def animate():
        if thinking_active[0]:
            char = thinking_chars[char_index[0] % len(thinking_chars)]
            status_label.config(text=f"Thinking {char}")
            char_index[0] += 1
            # Schedule next animation frame
            console.after(150, animate)
    
    animate()
    return thinking_active  # Return reference to stop animation

def handle_command(cmd, console, status_label, entry):
    """Enhanced chat handler with progressive display and better UX"""
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

    # Regular chat processing with improved UX
    thinking_animation = show_thinking_animation(console, status_label)
    console.update_idletasks()
    
    # Get enhanced history (includes long-term memory context)
    history = load_history()
    
    # Add user message
    user_message = {"role": "user", "content": cmd}
    history.append(user_message)
    add_to_session_history(user_message)

    def process_in_background():
        try:
            # Get response from API (now with memory context!)
            response = call_mistral_api(history)
            
            # Stop thinking animation
            thinking_animation[0] = False
            
            # Add assistant response to memory
            add_to_session_history(response)
            
            # Display response with better UX
            console.after(0, lambda: display_agent_response(response, memory_manager.working_memory, console, status_label))

        except requests.exceptions.HTTPError as e:
            thinking_animation[0] = False
            console.after(0, lambda: handle_api_error(e, console, status_label))
        except Exception as e:
            thinking_animation[0] = False
            console.after(0, lambda: handle_general_error(e, console, status_label))

    # Process API call in background thread
    thread = threading.Thread(target=process_in_background, daemon=True)
    thread.start()

def display_agent_response(response, session_history, console, status_label):
    """Display agent response with progressive text and better formatting"""
    # Check if AI decided to use tools
    tool_calls = response.get("tool_calls")
    
    if not tool_calls:
        # Simple response with progressive display
        content = response.get("content", "I'm not sure how to respond.")
        display_response_progressively(console, content)
        status_label.config(text="Ready")
        return
    
    # Handle tool-based responses (existing agent logic but with better display)
    console.insert(END, "🛠️ Agent working...\n", "accent")
    console.update_idletasks()
    
    # Use existing agent handler but improve the display
    handle_agent_response(response, session_history, console, status_label)
    status_label.config(text="Ready")

def handle_api_error(e, console, status_label):
    """Handle API errors with better messaging"""
    console.insert(END, f"❌ API Error {e.response.status_code}\n", "error")
    error_details = e.response.text[:200] + "..." if len(e.response.text) > 200 else e.response.text
    console.insert(END, f"Details: {error_details}\n", "dim")
    status_label.config(text="Ready")

def handle_general_error(e, console, status_label):
    """Handle general errors"""
    console.insert(END, f"❌ Error: {str(e)}\n", "error")
    status_label.config(text="Ready")

# Register exit handler
def _exit_handler():
    """Save session and process for long-term memory on exit"""
    memory_manager = get_memory_manager()
    if memory_manager.working_memory:
        save_current_session()
        print("Chat session saved and processed for long-term memory")

atexit.register(_exit_handler)