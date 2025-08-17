import os
import json
import tkinter as tk
from tkinter import END
import requests
from datetime import datetime
import atexit
import threading
import time
import re
import queue
from concurrent.futures import ThreadPoolExecutor

from config import CHAT_HISTORY_DIR, CHAT_HISTORY_LENGTH, MEMORY_DIR
from .utils.api_client import call_mistral_api
from .capabilities.agent import handle_agent_response
from .memory.history_sanitizer import sanitize_and_trim_history
from .memory.memory_manager import MemoryManager
from .utils.async_display import AsyncSmoothResponseDisplay

try:
    from .markdown_formatter import create_markdown_formatter
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("Markdown formatter not available - using plain text display")


# Global memory manager - this replaces simple session history!
_memory_manager = None

def get_memory_manager():
    """Get or create the memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        memory_dir = MEMORY_DIR
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

def handle_command(cmd, console, status_label, entry, on_complete_callback=None):
    """Enhanced chat handler with async smooth response display and completion callback."""
    memory_manager = get_memory_manager()
    
    # Create async response display handler
    response_display = AsyncSmoothResponseDisplay(console, status_label)
    
    def command_complete():
        """Function to call when any command is done."""
        if on_complete_callback:
            console.after(0, on_complete_callback)

    # Memory-specific commands (these are synchronous and finish immediately)
    if cmd.lower().startswith(("/search", "/find", "/remember")):
        query = cmd.split(maxsplit=1)[1] if len(cmd.split()) > 1 else ""
        if not query:
            console.insert(END, "Usage: /search <query>\n", "warning")
            command_complete()
            return
        
        results = memory_manager.search_memory(query)
        console.insert(END, f"{results}\n", "accent")
        status_label.config(text="Ready")
        command_complete()
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
        command_complete()
        return
    
    if cmd.lower() == "/compress":
        if len(memory_manager.working_memory) > 10:
            compressed = memory_manager.compress_working_memory(keep_recent=5)
            console.insert(END, f"✨ Compressed {compressed} messages to long-term memory\n", "success")
        else:
            console.insert(END, "Not enough messages to compress\n", "dim")
        status_label.config(text="Ready")
        command_complete()
        return
    
    # Session management commands (synchronous)
    if cmd.lower() in ("/new", "/reset"):
        if memory_manager.working_memory:
            saved_path = save_current_session()
            if saved_path:
                console.insert(END, f"💾 Previous session saved and processed\n", "dim")
        
        count = clear_session_history()
        console.insert(END, f"✨ New chat session started (cleared {count} messages)\n", "accent")
        status_label.config(text="Ready")
        command_complete()
        return

    if cmd.lower() == "/save":
        saved_path = save_current_session()
        if saved_path:
            console.insert(END, f"💾 Session saved to {os.path.basename(saved_path)}\n", "success")
        else:
            console.insert(END, f"❌ Failed to save session\n", "error")
        status_label.config(text="Ready")
        command_complete()
        return

    # Regular chat processing with async animations
    response_display.show_thinking_dots()
    console.update_idletasks()
    
    # Get enhanced history
    history = load_history()
    
    # Add user message
    user_message = {"role": "user", "content": cmd}
    history.append(user_message)
    add_to_session_history(user_message)

    def process_in_background():
        """Process API call in background, with a robust loop for chained tool use."""
        try:
            max_loops = 10
            for loop_count in range(max_loops):
                # Get the latest history from the memory manager
                current_history = load_history()
                
                # 1. Call the API with the current history
                response = call_mistral_api(current_history)
                
                # 2. Add the assistant's response to our history.
                # This is crucial for maintaining the correct conversation structure.
                add_to_session_history(response)

                # 3. Check for tool calls
                if not response.get("tool_calls"):
                    # No tools called, this is the end of the chain.
                    # Display the final content and break the loop.
                    console.after(0, lambda: response_display.display_response_naturally(
                        response.get("content", "Task complete."), on_complete_callback=on_complete_callback
                    ))
                    return

                # --- Tools were called, continue the loop ---
                console.after(0, lambda: response_display.show_working("Mini using tools"))

                # 4. Execute the tools. The new agent handler is a clean function
                # that only executes tools and returns the results.
                tool_results = handle_agent_response(response, response_display.console)

                # 5. Add all tool results to the session history.
                # This completes the valid sequence: [assistant_call, tool_result_1, tool_result_2, ...]
                for result in tool_results:
                    add_to_session_history(result)
                
                # 6. (Optional but recommended) Inject a client-side prompt to guide the next step.
                instruction = {
                    "role": "system",
                    "content": "Review the results of the tool(s) you just used. Decide the next step. If the goal is complete, provide a final answer to the user. Otherwise, call the next tool required to continue the task."
                }
                add_to_session_history(instruction)

            # If the loop finishes due to reaching max_loops
            console.after(0, lambda: response_display._safe_console_insert(
                "⚠️ Agent reached maximum toolchain length. Breaking loop.\n", "warning"
            ))
            if on_complete_callback:
                console.after(0, on_complete_callback)

        except requests.exceptions.HTTPError as e:
            console.after(0, lambda: handle_api_error_async(e, response_display, on_complete_callback))
        except Exception as e:
            console.after(0, lambda: handle_general_error_async(e, response_display, on_complete_callback))

    # Process API call in background thread
    thread = threading.Thread(target=process_in_background, daemon=True)
    thread.start()


def handle_api_error_async(e, response_display, on_complete_callback=None):
    """Handle API errors with async display"""
    response_display.stop_animation()
    
    if hasattr(e, 'response') and e.response:
        error_text = f"❌ API Error {e.response.status_code}\n"
        error_details = e.response.text[:200] + "..." if len(e.response.text) > 200 else e.response.text
        error_text += f"Details: {error_details}\n"
    else:
        error_text = f"❌ API Error: {str(e)}\n"
    
    response_display._safe_console_insert(error_text, "error")
    response_display._safe_status_update("Ready")
    if on_complete_callback:
        response_display.console.after(0, on_complete_callback)


def handle_general_error_async(e, response_display, on_complete_callback=None):
    """Handle general errors with async display"""
    response_display.stop_animation()
    response_display._safe_console_insert(f"❌ Error: {str(e)}\n", "error")
    response_display._safe_status_update("Ready")
    if on_complete_callback:
        response_display.console.after(0, on_complete_callback)



# Register exit handler
def _exit_handler():
    """Save session and process for long-term memory on exit"""
    memory_manager = get_memory_manager()
    if memory_manager.working_memory:
        save_current_session()
        print("Chat session saved and processed for long-term memory")

atexit.register(_exit_handler)