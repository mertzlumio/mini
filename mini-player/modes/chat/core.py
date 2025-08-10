# Fixed modes/chat/core.py - Complete replacement to eliminate recursion error
import os
import json
from tkinter import END
import requests
from datetime import datetime
import atexit
import threading
import time
import re

from config import CHAT_HISTORY_DIR, CHAT_HISTORY_LENGTH
from .api_client import call_mistral_api
from .capabilities.agent import handle_agent_response
from .memory.history_sanitizer import sanitize_and_trim_history
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

class SmoothResponseDisplay:
    """Handles smooth, natural response display with proper pacing"""
    
    def __init__(self, console, status_label):
        self.console = console
        self.status_label = status_label
        self.is_active = False
        self.current_animation = None
        self.output_buffer = []
        self.is_capturing = False
        
    def show_thinking_dots(self, base_message="Mini thinking"):
        """Show animated thinking dots"""
        dots = ['', '.', '..', '...']
        dot_index = [0]
        self.is_active = True
        
        def animate_dots():
            if self.is_active:
                current_dots = dots[dot_index[0] % len(dots)]
                self.status_label.config(text=f"{base_message}{current_dots}")
                dot_index[0] += 1
                self.current_animation = self.console.after(400, animate_dots)
        
        animate_dots()
        return self
    
    def show_working(self, message="Mini working"):
        """Show working indicator for agent actions"""
        chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        char_index = [0]
        self.is_active = True
        
        def animate_working():
            if self.is_active:
                char = chars[char_index[0] % len(chars)]
                self.status_label.config(text=f"{message} {char}")
                char_index[0] += 1
                self.current_animation = self.console.after(150, animate_working)
        
        animate_working()
        return self
    
    def stop_animation(self):
        """Stop current animation - FIXED VERSION"""
        self.is_active = False
        if self.current_animation:
            self.console.after_cancel(self.current_animation)
            self.current_animation = None
    
    def display_response_naturally(self, response_text, prefix="Mini: "):
        """Display response with natural pacing and smooth scrolling"""
        self.stop_animation()
        
        # Clean up the response text
        response_text = response_text.strip()
        if not response_text:
            self.status_label.config(text="Ready")
            return
        
        # Insert prefix
        self.console.insert(END, prefix)
        self.console.see(END)
        
        # Split into natural chunks (sentences, paragraphs, etc.)
        chunks = self._split_into_natural_chunks(response_text)
        chunk_index = [0]
        
        def display_next_chunk():
            if chunk_index[0] < len(chunks):
                chunk = chunks[chunk_index[0]]
                
                # Type out the chunk character by character with smart pacing
                self._type_chunk_smoothly(chunk, chunk_index[0], len(chunks), display_next_chunk)
                chunk_index[0] += 1
            else:
                # All chunks displayed
                self.console.insert(END, '\n')
                self._smooth_scroll_to_end()
                self.status_label.config(text="Ready")
        
        display_next_chunk()
    
    def _split_into_natural_chunks(self, text):
        """Split text into natural reading chunks"""
        # First split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        chunks = []
        
        for para in paragraphs:
            if len(para) < 100:
                # Short paragraph, keep as one chunk
                chunks.append(para.strip())
            else:
                # Long paragraph, split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) < 120:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
                
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            
            # Add paragraph break marker
            if para != paragraphs[-1]:  # Not the last paragraph
                chunks.append('\n')
        
        return [chunk for chunk in chunks if chunk]
    
    def _type_chunk_smoothly(self, chunk, chunk_num, total_chunks, callback):
        """Type a chunk with smooth character-by-character display"""
        if chunk == '\n':
            self.console.insert(END, '\n\n')
            self._smooth_scroll_to_end()
            self.console.after(300, callback)  # Pause between paragraphs
            return
        
        chars = list(chunk)
        char_index = [0]
        
        def type_next_char():
            if char_index[0] < len(chars):
                char = chars[char_index[0]]
                self.console.insert(END, char)
                
                # Smart scrolling - only scroll if near bottom
                self._smart_scroll()
                
                # Variable delay based on character type
                delay = self._get_char_delay(char, char_index[0], len(chars))
                
                char_index[0] += 1
                self.console.after(delay, type_next_char)
            else:
                # Chunk complete
                if chunk_num < total_chunks - 1:
                    self.console.insert(END, ' ')
                    self.console.after(200, callback)  # Brief pause between chunks
                else:
                    callback()
        
        type_next_char()
    
    def _get_char_delay(self, char, position, total_length):
        """Get appropriate delay for character based on context"""
        base_delay = 25  # Base typing speed
        
        # Punctuation gets longer pauses
        if char in '.!?':
            return base_delay * 3
        elif char in ',;:':
            return base_delay * 2
        elif char == '\n':
            return base_delay * 2
        elif char == ' ':
            return base_delay
        else:
            # Regular characters - slight variation for natural feel
            import random
            return base_delay + random.randint(-5, 10)
    
    def _smart_scroll(self):
        """Only scroll if user is near the bottom"""
        # Check if we're near the bottom of the text
        try:
            # Get the current view position
            top, bottom = self.console.yview()
            
            # If we're viewing the bottom 20% of content, auto-scroll
            if bottom > 0.8:
                self.console.see(END)
        except:
            # Fallback to always scroll
            self.console.see(END)
    
    def _smooth_scroll_to_end(self):
        """Smoothly scroll to the end"""
        def scroll_step(steps_remaining=5):
            if steps_remaining > 0:
                self.console.see(END)
                self.console.after(50, lambda: scroll_step(steps_remaining - 1))
        
        scroll_step()
    
    def start_output_capture(self):
        """Start capturing console output"""
        self.output_buffer = []
        self.is_capturing = True
        
        # Store original console methods
        self.original_insert = self.console.insert
        self.original_see = self.console.see
        
        # Replace with capturing versions
        def capturing_insert(position, text, tag=None):
            if self.is_capturing and position == END:
                # Buffer the output instead of writing directly
                self.output_buffer.append({
                    'text': text,
                    'tag': tag
                })
            else:
                # Pass through for non-END insertions or when not capturing
                self.original_insert(position, text, tag)
        
        def capturing_see(position):
            # Don't scroll during capture
            if not self.is_capturing:
                self.original_see(position)
        
        self.console.insert = capturing_insert
        self.console.see = capturing_see
    
    def stop_output_capture(self):
        """Stop capturing and restore original console methods"""
        self.is_capturing = False
        if hasattr(self, 'original_insert'):
            self.console.insert = self.original_insert
        if hasattr(self, 'original_see'):
            self.console.see = self.original_see
    
    def play_captured_output(self):
        """Play back captured output with typewriter effect"""
        if not self.output_buffer:
            self.stop_animation()
            self.status_label.config(text="Ready")
            return
        
        # Combine all captured text while preserving tags
        combined_text = ""
        for item in self.output_buffer:
            combined_text += item['text']
        
        # Clear the buffer
        self.output_buffer = []
        
        # Play with typewriter effect
        if combined_text.strip():
            # Add completion message before the actual output
            completion_msg = "\n✨ Here's what I found:\n\n"
            self.display_response_naturally(completion_msg + combined_text, prefix="")
        else:
            self.stop_animation()
            self.console.insert(END, "✨ Task completed\n", "success")
            self.status_label.config(text="Ready")
    
    def display_agent_response_smoothly(self, response, session_history):
        """Handle agent responses with universal typewriter effect"""
        # Check if AI decided to use tools
        tool_calls = response.get("tool_calls")
        
        if not tool_calls:
            # Simple response with natural display
            content = response.get("content", "I'm not sure how to respond.")
            self.display_response_naturally(content)
            return
        
        # Agent response - start capturing output and keep working indicator
        self.show_working("Mini using tools")
        
        # Display initial working message normally (not captured)
        self.console.insert(END, "Mini is working with tools...\n", "accent")
        self.console.see(END)
        
        # Start capturing all subsequent output
        self.start_output_capture()
        
        def process_agent_work():
            try:
                # Run agent handler - all its output will be captured
                handle_agent_response(response, session_history, self.console, self.status_label)
                
                # Stop capturing and play back with typewriter effect
                self.stop_output_capture()
                
                # Play the captured output with typewriter effect
                self.console.after(500, self.play_captured_output)
                
            except Exception as e:
                self.stop_output_capture()
                self.stop_animation()
                self.console.insert(END, f"\n❌ Error during Mini using tools: {str(e)}\n", "error")
                self.status_label.config(text="Ready")
        
        # Start agent processing after a brief delay
        self.console.after(800, process_agent_work)

def handle_command(cmd, console, status_label, entry):
    """Enhanced chat handler with smooth response display"""
    memory_manager = get_memory_manager()
    
    # Create response display handler
    response_display = SmoothResponseDisplay(console, status_label)
    
    # Memory-specific commands (unchanged)
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
    
    # Existing commands (unchanged)
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

    # Regular chat processing with enhanced UX
    response_display.show_thinking_dots()
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
            
            # Add assistant response to memory
            add_to_session_history(response)
            
            # Display response with smooth UX
            console.after(0, lambda: response_display.display_agent_response_smoothly(
                response, memory_manager.working_memory
            ))

        except requests.exceptions.HTTPError as e:
            response_display.stop_animation()
            console.after(0, lambda: handle_api_error(e, console, status_label))
        except Exception as e:
            response_display.stop_animation()
            console.after(0, lambda: handle_general_error(e, console, status_label))

    # Process API call in background thread
    thread = threading.Thread(target=process_in_background, daemon=True)
    thread.start()

def handle_api_error(e, console, status_label):
    """Handle API errors with better messaging"""
    if hasattr(e, 'response') and e.response:
        console.insert(END, f"❌ API Error {e.response.status_code}\n", "error")
        error_details = e.response.text[:200] + "..." if len(e.response.text) > 200 else e.response.text
        console.insert(END, f"Details: {error_details}\n", "dim")
    else:
        console.insert(END, f"❌ API Error: {str(e)}\n", "error")
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