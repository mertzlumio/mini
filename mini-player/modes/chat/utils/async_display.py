import asyncio
import threading
import queue
import time
import re
import tkinter as tk
from tkinter import END
from concurrent.futures import ThreadPoolExecutor

class AsyncSmoothResponseDisplay:
    """Thread-safe smooth response display with proper tkinter threading"""
    
    def __init__(self, console, status_label):
        self.console = console
        self.status_label = status_label
        
        # Animation control
        self.animation_active = False
        self.stop_animation_event = threading.Event()
        
        # Thread-safe communication queues
        self.gui_queue = queue.Queue()
        self.animation_queue = queue.Queue()
        
        # Response display control
        self.display_active = False
        
        # Scroll state
        self.user_has_scrolled = False
        self.auto_scroll_enabled = True
        
        # Thread pool for background tasks
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mini_display")
        
        self._setup_scroll_detection()
        self._setup_markdown_tags()
        self._start_gui_queue_processor()
    
    def _setup_markdown_tags(self):
        """Setup basic markdown text tags"""
        try:
            from themes import get_current_theme
            theme = get_current_theme()
        except ImportError:
            # Fallback theme
            theme = {
                "accent": "#00ff88",
                "text": "#ffffff", 
                "border": "#333333",
                "dim": "#888888"
            }
        
        # Headers
        self.console.tag_config("h1", font=("JetBrains Mono", 14, "bold"), foreground=theme["accent"])
        self.console.tag_config("h2", font=("JetBrains Mono", 12, "bold"), foreground=theme["accent"])
        self.console.tag_config("h3", font=("JetBrains Mono", 11, "bold"), foreground=theme["text"])
        
        # Text formatting
        self.console.tag_config("bold", font=("Cascadia Code", 10, "bold"))
        self.console.tag_config("italic", font=("Cascadia Code", 10, "italic"))
        self.console.tag_config("code_inline", 
                               font=("Cascadia Code", 9), 
                               background=theme["border"],
                               foreground=theme["accent"])
        
        # Code blocks
        self.console.tag_config("code_block", 
                               font=("Cascadia Code", 9),
                               background=theme["border"],
                               foreground=theme["text"],
                               lmargin1=20, lmargin2=20,
                               rmargin=20,
                               spacing1=5, spacing3=5)
        
        # Status tags
        self.console.tag_config("success", foreground="#00ff88")
        self.console.tag_config("error", foreground="#ff4444")
        self.console.tag_config("warning", foreground="#ffaa00")
        self.console.tag_config("accent", foreground=theme["accent"])
        self.console.tag_config("dim", foreground=theme["dim"])
    
    def _start_gui_queue_processor(self):
        """Start processing GUI updates from the queue on the main thread"""
        def process_gui_queue():
            try:
                # Process multiple items at once for better performance
                items_processed = 0
                while items_processed < 10:  # Limit to prevent blocking
                    try:
                        task = self.gui_queue.get_nowait()
                        task_type, args = task
                        
                        if task_type == "insert":
                            text, tag = args
                            self.console.insert(END, text, tag or ())
                            if self._should_auto_scroll():
                                self.console.see(END)
                        
                        elif task_type == "status":
                            text = args[0]
                            self.status_label.config(text=text)
                        
                        elif task_type == "animation":
                            animation_type, message = args
                            self._update_animation_display(animation_type, message)
                        
                        elif task_type == "stop_animation":
                            self._stop_animation_display()
                        
                        elif task_type == "complete":
                            callback = args[0] if args else None
                            if callback:
                                callback()
                        
                        elif task_type == "stop":
                            # Shutdown signal
                            return
                        
                        self.gui_queue.task_done()
                        items_processed += 1
                        
                    except queue.Empty:
                        break
                        
            except Exception as e:
                print(f"GUI queue processor error: {e}")
            
            # Schedule next check
            self.console.after(50, process_gui_queue)  # Check every 50ms
        
        # Start the processor
        self.console.after(10, process_gui_queue)
    
    def _queue_gui_update(self, task_type, args):
        """Thread-safe way to queue GUI updates"""
        self.gui_queue.put((task_type, args))
    
    def _safe_console_insert(self, text, tag=None):
        """Thread-safe console insertion"""
        self._queue_gui_update("insert", (text, tag))
    
    def _safe_status_update(self, text):
        """Thread-safe status label update"""
        self._queue_gui_update("status", (text,))
    
    def _safe_animation_update(self, animation_type, message):
        """Thread-safe animation update"""
        self._queue_gui_update("animation", (animation_type, message))
    
    def _safe_complete_callback(self, callback):
        """Thread-safe callback execution"""
        if callback:
            self._queue_gui_update("complete", (callback,))
    
    def _update_animation_display(self, animation_type, message):
        """Update animation display on main thread"""
        if animation_type == "thinking":
            dots = ['', '.', '..', '...']
            dot_count = getattr(self, '_thinking_dots', 0)
            current_dots = dots[dot_count % len(dots)]
            self.status_label.config(text=f"{message}{current_dots}")
            self._thinking_dots = dot_count + 1
            
        elif animation_type == "working":
            chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            char_count = getattr(self, '_working_chars', 0)
            char = chars[char_count % len(chars)]
            self.status_label.config(text=f"{message} {char}")
            self._working_chars = char_count + 1
            
        elif animation_type == "typing":
            states = ['⌨️ ', '⌨️.', '⌨️..', '⌨️...']
            state_count = getattr(self, '_typing_states', 0)
            state = states[state_count % len(states)]
            self.status_label.config(text=f"{message} {state}")
            self._typing_states = state_count + 1
    
    def _stop_animation_display(self):
        """Stop animation display on main thread"""
        # Reset animation counters
        self._thinking_dots = 0
        self._working_chars = 0
        self._typing_states = 0
    
    def show_thinking_dots(self, base_message="Mini thinking"):
        """Start async thinking dots animation"""
        self.stop_animation()
        self.animation_active = True
        self.stop_animation_event.clear()
        
        def animate_thinking():
            while not self.stop_animation_event.is_set():
                self._safe_animation_update("thinking", base_message)
                if self.stop_animation_event.wait(0.4):
                    break
        
        self.animation_thread = threading.Thread(target=animate_thinking, daemon=True)
        self.animation_thread.start()
        return self
    
    def show_working(self, message="Mini working"):
        """Start async working spinner animation"""
        self.stop_animation()
        self.animation_active = True
        self.stop_animation_event.clear()
        
        def animate_working():
            while not self.stop_animation_event.is_set():
                self._safe_animation_update("working", message)
                if self.stop_animation_event.wait(0.15):
                    break
        
        self.animation_thread = threading.Thread(target=animate_working, daemon=True)
        self.animation_thread.start()
        return self
    
    def show_typing(self, message="Mini typing"):
        """Start async typing indicator animation"""
        self.stop_animation()
        self.animation_active = True
        self.stop_animation_event.clear()
        
        def animate_typing():
            while not self.stop_animation_event.is_set():
                self._safe_animation_update("typing", message)
                if self.stop_animation_event.wait(0.3):
                    break
        
        self.animation_thread = threading.Thread(target=animate_typing, daemon=True)
        self.animation_thread.start()
        return self
    
    def stop_animation(self):
        """Stop current animation"""
        if self.animation_active:
            self.animation_active = False
            self.stop_animation_event.set()
            self._queue_gui_update("stop_animation", ())
            
            if hasattr(self, 'animation_thread') and self.animation_thread and self.animation_thread.is_alive():
                self.animation_thread.join(timeout=0.5)
    
    def display_response_naturally(self, response_text, prefix="Mini: ", on_complete_callback=None):
        """Display response with non-blocking animations and a completion callback."""
        self.stop_animation()
        self.reset_scroll_state()
        
        response_text = response_text.strip()
        if not response_text:
            self._safe_status_update("Ready")
            self._safe_complete_callback(on_complete_callback)
            return
        
        # Insert prefix immediately
        self._safe_console_insert(prefix)
        
        # Start typing animation
        self.show_typing("Mini responding")
        
        # Execute display in background
        def execute_display():
            try:
                if self._has_markdown_formatting(response_text):
                    self._execute_markdown_display(response_text)
                else:
                    self._execute_typewriter_effect(response_text)
                
                # Finish response
                self._safe_console_insert('\n')
                self.stop_animation()
                self._safe_status_update("Ready")
                self._safe_complete_callback(on_complete_callback)
                
            except Exception as e:
                print(f"Display execution error: {e}")
                self.stop_animation()
                self._safe_status_update("Ready")
                self._safe_complete_callback(on_complete_callback)
        
        self.executor.submit(execute_display)
    
    def _has_markdown_formatting(self, text):
        """Quick check for common markdown patterns"""
        markdown_indicators = [
            r'^#+\s',           # Headers
            r'```',             # Code blocks
            r'\*\*.*?\*\*',     # Bold
            r'`[^`]+`',         # Inline code
            r'^\s*[-*+]\s',     # Lists
            r'^\>',             # Quotes
        ]
        
        for pattern in markdown_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False
    
    def _execute_markdown_display(self, text):
        """Execute markdown display in background"""
        lines = text.split('\n')
        in_code_block = False
        code_lines = []
        
        for line in lines:
            if self.stop_animation_event.is_set():
                break
                
            # Handle code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    if code_lines:
                        code_text = '\n'.join(code_lines)
                        self._safe_console_insert(code_text + '\n', "code_block")
                    code_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue
            
            if in_code_block:
                code_lines.append(line)
                continue
            
            # Process regular line
            self._insert_line_with_formatting_async(line + '\n')
            
            # Small delay between lines for natural flow
            time.sleep(0.05)
        
        # Handle remaining code block
        if code_lines:
            code_text = '\n'.join(code_lines)
            self._safe_console_insert(code_text + '\n', "code_block")
    
    def _insert_line_with_formatting_async(self, line):
        """Insert line with formatting (async-safe)"""
        # Headers
        if line.startswith('# '):
            self._safe_console_insert(line[2:], "h1")
            return
        elif line.startswith('## '):
            self._safe_console_insert(line[3:], "h2") 
            return
        elif line.startswith('### '):
            self._safe_console_insert(line[4:], "h3")
            return
        elif line.startswith('> '):
            self._safe_console_insert(line[2:], "quote")
            return
        elif re.match(r'^\s*[-*+]\s', line):
            self._safe_console_insert(line, "list_item")
            return
        
        # Process inline formatting
        self._insert_with_inline_formatting_async(line)
    
    def _insert_with_inline_formatting_async(self, text):
        """Insert text with inline formatting (async-safe)"""
        remaining = text
        
        while remaining:
            if self.stop_animation_event.is_set():
                break
                
            patterns = [
                (r'\*\*([^*]+)\*\*', 'bold'),
                (r'\*([^*]+)\*', 'italic'),
                (r'`([^`]+)`', 'code_inline'),
            ]
            
            earliest_match = None
            earliest_pos = len(remaining)
            
            for pattern, tag in patterns:
                match = re.search(pattern, remaining)
                if match and match.start() < earliest_pos:
                    earliest_pos = match.start()
                    earliest_match = (match, tag)
            
            if earliest_match:
                match, tag = earliest_match
                
                if match.start() > 0:
                    self._safe_console_insert(remaining[:match.start()])
                
                self._safe_console_insert(match.group(1), tag)
                remaining = remaining[match.end():]
            else:
                self._safe_console_insert(remaining)
                break
    
    def _execute_typewriter_effect(self, text):
        """Execute typewriter effect in background"""
        chunks = self._split_into_natural_chunks(text)
        
        for chunk in chunks:
            if self.stop_animation_event.is_set():
                break
                
            if chunk == '\n':
                self._safe_console_insert('\n\n')
                time.sleep(0.3)
                continue
            
            # Type character by character
            for char in chunk:
                if self.stop_animation_event.is_set():
                    break
                    
                self._safe_console_insert(char)
                
                # Variable delay based on character
                delay = self._get_char_delay(char)
                time.sleep(delay / 1000.0)  # Convert to seconds
            
            # Pause between chunks
            if chunk != chunks[-1]:
                self._safe_console_insert(' ')
                time.sleep(0.1)
    
    def _split_into_natural_chunks(self, text):
        """Split text into natural reading chunks"""
        paragraphs = text.split('\n\n')
        chunks = []
        
        for para in paragraphs:
            if len(para) < 100:
                chunks.append(para.strip())
            else:
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
            
            if para != paragraphs[-1]:
                chunks.append('\n')
        
        return [chunk for chunk in chunks if chunk]
    
    def _get_char_delay(self, char):
        """Get delay for character (in milliseconds)"""
        base_delay = 20
        
        if char in '.!?':
            return base_delay * 4
        elif char in ',;:':
            return base_delay * 2
        elif char == '\n':
            return base_delay * 3
        elif char == ' ':
            return base_delay * 0.8
        else:
            import random
            return base_delay + random.randint(-5, 8)
    
    def _should_auto_scroll(self):
        """Check if should auto-scroll"""
        if not self.auto_scroll_enabled:
            return False
            
        try:
            top, bottom = self.console.yview()
            return bottom > 0.8 and self.auto_scroll_enabled
        except:
            return self.auto_scroll_enabled
    
    def _setup_scroll_detection(self):
        """Setup scroll event detection"""
        def on_manual_scroll(event):
            self.user_has_scrolled = True
            self.auto_scroll_enabled = False
        
        self.console.bind('<MouseWheel>', on_manual_scroll)
        self.console.bind('<Button-4>', on_manual_scroll)
        self.console.bind('<Button-5>', on_manual_scroll)
        self.console.bind('<Key>', lambda e: on_manual_scroll(e) if e.keysym in ['Up', 'Down', 'Page_Up', 'Page_Down'] else None)
    
    def reset_scroll_state(self):
        """Reset scroll state"""
        self.user_has_scrolled = False
        self.auto_scroll_enabled = True
    
    def display_agent_response_smoothly(self, response, session_history, on_complete_callback=None):
        """Handle agent responses with async animations and a completion callback."""
        tool_calls = response.get("tool_calls")
        
        if not tool_calls:
            content = response.get("content", "I'm not sure how to respond.")
            self.display_response_naturally(content, on_complete_callback=on_complete_callback)
            return
        
        # Show working animation while tools execute
        self.show_working("Mini using tools")
        self._safe_console_insert("🛠️ Mini is working with tools...\n", "accent")
        
        # Execute agent work in background thread
        def execute_agent_work():
            try:
                # Import here to avoid circular imports
                from ..capabilities.agent import handle_agent_response
                
                # Create a custom console wrapper to capture output
                class OutputCapture:
                    def __init__(self, display_handler):
                        self.display_handler = display_handler
                        self.captured = []
                    
                    def insert(self, pos, text, tag=None):
                        if pos == tk.END:
                            self.captured.append((text, tag))
                            self.display_handler._safe_console_insert(text, tag)
                        # Ignore other positions for now
                    
                    def see(self, pos):
                        # Auto-scroll is handled by the queue processor
                        pass
                    
                    def after(self, delay, callback):
                        # For simple callbacks, execute immediately in thread
                        # For GUI updates, this should go through the queue
                        if hasattr(callback, '__call__'):
                            try:
                                callback()
                            except:
                                pass
                    
                    def after_idle(self, callback):
                        # Similar handling for after_idle
                        if hasattr(callback, '__call__'):
                            try:
                                callback()
                            except:
                                pass
                
                # Create wrapped console
                wrapped_console = OutputCapture(self)
                
                # Execute agent response
                handle_agent_response(response, session_history, wrapped_console, self.status_label)
                
                # Finish up
                time.sleep(0.2)  # Brief pause before finishing
                self.stop_animation()
                self._safe_status_update("Ready")
                self._safe_complete_callback(on_complete_callback)
                
            except Exception as e:
                print(f"Agent execution error: {e}")
                self.stop_animation()
                self._safe_console_insert(f"\n❌ Error during tool execution: {str(e)}\n", "error")
                self._safe_status_update("Ready")
                self._safe_complete_callback(on_complete_callback)
        
        # Run agent work in background
        self.executor.submit(execute_agent_work)
    
    def shutdown(self):
        """Clean shutdown of async components"""
        self.stop_animation()
        
        # Signal GUI queue processor to stop
        self._queue_gui_update("stop", ())
        
        # Shutdown executor
        self.executor.shutdown(wait=False)


# Enhanced integration function for core.py
def create_async_response_display(console, status_label):
    """Factory function to create async response display"""
    return AsyncSmoothResponseDisplay(console, status_label)