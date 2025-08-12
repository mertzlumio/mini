# modes/chat/startup/integration.py
"""
Integration layer to connect autonomous startup to existing Mini chat system
"""

import threading
import time
from typing import Dict, Optional, Callable
from .autonomous_startup import AutonomousStartupManager

class StartupIntegrationManager:
    """Manages integration between autonomous startup and existing chat system"""
    
    def __init__(self, 
                 memory_manager, 
                 api_client,
                 console_widget,
                 status_label,
                 memory_dir: str):
        self.memory_manager = memory_manager
        self.api_client = api_client
        self.console = console_widget
        self.status_label = status_label
        self.memory_dir = memory_dir
        
        # Initialize autonomous startup manager
        self.startup_manager = AutonomousStartupManager(
            memory_dir, memory_manager, api_client
        )
        
        # State tracking
        self.startup_active = False
        self.awaiting_user_response = False
        self.current_step_data = None
        
        # Callbacks for UI integration
        self.on_startup_complete = None
        self.on_user_input_needed = None
    
    def initiate_autonomous_startup(self, 
                                  on_complete: Optional[Callable] = None,
                                  on_input_needed: Optional[Callable] = None):
        """Start the autonomous startup sequence with UI integration"""
        
        self.on_startup_complete = on_complete
        self.on_user_input_needed = on_input_needed
        self.startup_active = True
        
        # Show startup indicator
        self.status_label.config(text="🚀 Mini starting up...")
        self.console.insert("end", "=" * 50 + "\n", "accent")
        self.console.insert("end", "🤖 MINI AUTONOMOUS STARTUP\n", "accent")
        self.console.insert("end", "=" * 50 + "\n", "accent")
        
        # Start startup sequence in background
        startup_thread = threading.Thread(
            target=self._execute_startup_sequence,
            daemon=True
        )
        startup_thread.start()
    
    def _execute_startup_sequence(self):
        """Execute startup sequence with proper UI updates"""
        try:
            # Initiate startup
            result = self.startup_manager.initiate_startup()
            
            # Update UI on main thread
            self.console.after(0, lambda: self._handle_startup_step(result))
            
        except Exception as e:
            error_msg = f"Startup error: {str(e)}"
            self.console.after(0, lambda: self._handle_startup_error(error_msg))
    
    def _handle_startup_step(self, step_result: Dict):
        """Handle a step in the startup sequence"""
        step_type = step_result.get("type")
        message = step_result.get("message", "")
        
        if step_type == "complete":
            self._handle_startup_complete()
            
        elif step_type == "greeting":
            self._display_mini_message(message, "greeting")
            
            if step_result.get("awaiting_response"):
                self._setup_user_input_waiting()
                
        elif step_type == "planning":
            self._display_mini_message(message, "planning")
            
            if step_result.get("awaiting_response"):
                self._setup_user_input_waiting()
                
        elif step_type == "error":
            self._handle_startup_error(message)
        
        self.current_step_data = step_result
    
    def _display_mini_message(self, message: str, message_type: str = "general"):
        """Display Mini's message with appropriate formatting"""
        
        # Add icon based on message type
        if message_type == "greeting":
            icon = "👋"
        elif message_type == "planning":
            icon = "📋"
        else:
            icon = "🤖"
        
        # Display with smooth typing effect (reuse existing smooth display)
        self.console.insert("end", f"\n{icon} Mini: ", "accent")
        
        # Use existing smooth response display if available
        try:
            from ..core import SmoothResponseDisplay
            smooth_display = SmoothResponseDisplay(self.console, self.status_label)
            smooth_display.display_response_naturally(message, prefix="")
        except ImportError:
            # Fallback to simple display
            self.console.insert("end", f"{message}\n")
            self.console.see("end")
    
    def _setup_user_input_waiting(self):
        """Setup UI to wait for user input"""
        self.awaiting_user_response = True
        self.status_label.config(text="💭 Waiting for your response...")
        
        # Enable input field and set focus
        if self.on_user_input_needed:
            self.on_user_input_needed()
    
    def handle_user_input(self, user_input: str):
        """Handle user input during startup sequence"""
        if not self.awaiting_user_response or not self.startup_active:
            return False  # Not handled by startup system
        
        # Add user message to console
        self.console.insert("end", f"\nYou: {user_input}\n", "user")
        self.console.see("end")
        
        # Process response
        self.awaiting_user_response = False
        self.status_label.config(text="🤔 Mini thinking...")
        
        # Process in background
        def process_response():
            try:
                result = self.startup_manager.process_user_response(user_input)
                self.console.after(0, lambda: self._handle_startup_step(result))
            except Exception as e:
                error_msg = f"Error processing response: {str(e)}"
                self.console.after(0, lambda: self._handle_startup_error(error_msg))
        
        response_thread = threading.Thread(target=process_response, daemon=True)
        response_thread.start()
        
        return True  # Handled by startup system
    
    def _handle_startup_complete(self):
        """Handle completion of startup sequence"""
        self.startup_active = False
        self.awaiting_user_response = False
        
        self.console.insert("end", "\n" + "=" * 50 + "\n", "success")
        self.console.insert("end", "✅ Startup complete! Ready to assist you.\n", "success")
        self.console.insert("end", "=" * 50 + "\n\n", "success")
        
        self.status_label.config(text="Ready")
        
        # Call completion callback
        if self.on_startup_complete:
            self.on_startup_complete()
    
    def _handle_startup_error(self, error_message: str):
        """Handle startup errors"""
        self.startup_active = False
        self.awaiting_user_response = False
        
        self.console.insert("end", f"\n❌ {error_message}\n", "error")
        self.console.insert("end", "Falling back to normal chat mode...\n", "dim")
        
        self.status_label.config(text="Ready (Startup failed)")
        
        # Still call completion callback to restore normal operation
        if self.on_startup_complete:
            self.on_startup_complete()
    
    def is_startup_active(self) -> bool:
        """Check if startup sequence is currently active"""
        return self.startup_active
    
    def is_awaiting_user_input(self) -> bool:
        """Check if startup is waiting for user input"""
        return self.awaiting_user_response
    
    def get_startup_progress(self) -> Dict:
        """Get current startup progress"""
        if not self.startup_active:
            return {"active": False}
        
        status = self.startup_manager.get_startup_status()
        status["active"] = True
        status["awaiting_input"] = self.awaiting_user_response
        return status
    
    def force_complete_startup(self):
        """Force complete startup sequence (emergency fallback)"""
        self.startup_active = False
        self.awaiting_user_response = False
        self.status_label.config(text="Ready")
        
        if self.on_startup_complete:
            self.on_startup_complete()


# Modified chat core integration
class StartupEnabledChatHandler:
    """Enhanced chat handler with autonomous startup capability"""
    
    def __init__(self, console, status_label, entry_widget, memory_dir: str):
        self.console = console
        self.status_label = status_label
        self.entry_widget = entry_widget
        self.memory_dir = memory_dir
        
        # Initialize components (will be set by main app)
        self.memory_manager = None
        self.api_client = None
        self.startup_integration = None
        
        # State
        self.normal_chat_enabled = False
        self.startup_completed = False
    
    def initialize_components(self, memory_manager, api_client):
        """Initialize with memory manager and API client"""
        self.memory_manager = memory_manager
        self.api_client = api_client
        
        # Initialize startup integration
        self.startup_integration = StartupIntegrationManager(
            memory_manager=memory_manager,
            api_client=api_client,
            console_widget=self.console,
            status_label=self.status_label,
            memory_dir=self.memory_dir
        )
    
    def start_mini_session(self):
        """Start Mini session with autonomous startup"""
        if not self.memory_manager or not self.api_client:
            self.console.insert("end", "❌ Components not initialized\n", "error")
            return
        
        # Disable normal chat during startup
        self.normal_chat_enabled = False
        self.startup_completed = False
        
        # Start autonomous startup
        self.startup_integration.initiate_autonomous_startup(
            on_complete=self._on_startup_complete,
            on_input_needed=self._on_input_needed
        )
    
    def _on_startup_complete(self):
        """Called when startup sequence is complete"""
        self.normal_chat_enabled = True
        self.startup_completed = True
        
        # Re-enable normal chat input
        self.entry_widget.config(state='normal')
        self.entry_widget.focus_set()
        
        self.console.insert("end", "💬 You can now chat normally or give me tasks!\n", "dim")
    
    def _on_input_needed(self):
        """Called when startup needs user input"""
        # Enable input field for startup response
        self.entry_widget.config(state='normal')
        self.entry_widget.focus_set()
    
    def handle_user_input(self, user_input: str) -> bool:
        """Handle user input - routes to startup or normal chat"""
        
        # Check if startup should handle this input
        if (self.startup_integration and 
            self.startup_integration.is_startup_active() and 
            self.startup_integration.is_awaiting_user_input()):
            
            return self.startup_integration.handle_user_input(user_input)
        
        # Handle normal chat if startup is complete
        elif self.normal_chat_enabled and self.startup_completed:
            return self._handle_normal_chat(user_input)
        
        # Not ready for input
        else:
            self.console.insert("end", "⏳ Please wait for Mini to finish starting up...\n", "warning")
            return True
    
    def _handle_normal_chat(self, user_input: str) -> bool:
        """Handle normal chat after startup is complete"""
        # Import and use existing chat handler
        try:
            from ..core import handle_command
            handle_command(user_input, self.console, self.status_label, self.entry_widget)
            return True
        except Exception as e:
            self.console.insert("end", f"❌ Chat error: {str(e)}\n", "error")
            return True
    
    def is_ready_for_chat(self) -> bool:
        """Check if ready for normal chat"""
        return self.normal_chat_enabled and self.startup_completed
    
    def get_status(self) -> Dict:
        """Get current status"""
        if self.startup_integration and self.startup_integration.is_startup_active():
            return {
                "mode": "startup",
                "ready": False,
                "startup_progress": self.startup_integration.get_startup_progress()
            }
        elif self.startup_completed:
            return {
                "mode": "chat",
                "ready": True,
                "startup_progress": None
            }
        else:
            return {
                "mode": "initializing",
                "ready": False,
                "startup_progress": None
            }


# Integration with existing chat UI
def integrate_startup_with_existing_ui(chat_window_class):
    """Decorator to integrate startup system with existing chat window"""
    
    class StartupEnabledChatWindow(chat_window_class):
        """Enhanced chat window with autonomous startup"""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            # Initialize startup handler
            self.startup_handler = StartupEnabledChatHandler(
                console=self.console,
                status_label=self.status_label,
                entry_widget=self.entry,
                memory_dir=self.get_memory_dir()  # Assume this method exists
            )
            
            # Override entry handling
            self._setup_startup_integration()
        
        def _setup_startup_integration(self):
            """Setup integration with existing UI"""
            # Store original entry handler
            self._original_handle_entry = getattr(self, 'handle_entry', None)
            
            # Override entry handling
            def enhanced_handle_entry(event=None):
                user_input = self.entry.get().strip()
                if not user_input:
                    return
                
                # Clear entry
                self.entry.delete(0, 'end')
                
                # Route to startup handler
                handled = self.startup_handler.handle_user_input(user_input)
                
                # If not handled by startup, use original handler
                if not handled and self._original_handle_entry:
                    self._original_handle_entry(event)
            
            # Bind new handler
            self.entry.bind('<Return>', enhanced_handle_entry)
            
            # Add startup button or auto-start
            self._add_startup_controls()
        
        def _add_startup_controls(self):
            """Add startup controls to UI"""
            # This would depend on your UI framework
            # For now, auto-start on window creation
            self.after(500, self._auto_start_mini)
        
        def _auto_start_mini(self):
            """Auto-start Mini with autonomous startup"""
            try:
                # Initialize startup handler with components
                from ..core import get_memory_manager
                from ..api_client import call_mistral_api
                
                memory_manager = get_memory_manager()
                self.startup_handler.initialize_components(memory_manager, call_mistral_api)
                
                # Start Mini session
                self.startup_handler.start_mini_session()
                
            except Exception as e:
                self.console.insert("end", f"❌ Failed to start Mini: {str(e)}\n", "error")
                self.console.insert("end", "Falling back to normal chat mode...\n", "dim")
                self.status_label.config(text="Ready (No startup)")
        
        def get_memory_dir(self):
            """Get memory directory - implement based on your config"""
            try:
                from config import MEMORY_DIR
                return MEMORY_DIR
            except ImportError:
                return "memory"
    
    return StartupEnabledChatWindow


# Simple integration function for existing code
def add_autonomous_startup_to_chat_mode(console, status_label, entry_widget, memory_dir: str):
    """Simple function to add autonomous startup to existing chat mode"""
    
    # Initialize startup handler
    startup_handler = StartupEnabledChatHandler(console, status_label, entry_widget, memory_dir)
    
    # Initialize with components
    try:
        from ..core import get_memory_manager
        from ..api_client import call_mistral_api
        
        memory_manager = get_memory_manager()
        startup_handler.initialize_components(memory_manager, call_mistral_api)
        
        # Start Mini session
        startup_handler.start_mini_session()
        
        return startup_handler
        
    except Exception as e:
        console.insert("end", f"❌ Failed to initialize autonomous startup: {str(e)}\n", "error")
        return None


# Example usage and testing
def test_startup_integration():
    """Test the startup integration system"""
    import tkinter as tk
    from tkinter import scrolledtext
    
    # Create test window
    root = tk.Tk()
    root.title("Mini Startup Test")
    root.geometry("600x400")
    
    # Create UI elements
    console = scrolledtext.ScrolledText(root, height=20, width=80)
    console.pack(padx=10, pady=5, fill='both', expand=True)
    
    status_frame = tk.Frame(root)
    status_frame.pack(fill='x', padx=10, pady=5)
    
    status_label = tk.Label(status_frame, text="Ready", anchor='w')
    status_label.pack(side='left')
    
    entry = tk.Entry(root, width=80)
    entry.pack(padx=10, pady=5, fill='x')
    
    # Add autonomous startup
    startup_handler = add_autonomous_startup_to_chat_mode(
        console, status_label, entry, "test_memory"
    )
    
    # Bind entry
    def handle_entry(event=None):
        if startup_handler:
            user_input = entry.get().strip()
            if user_input:
                entry.delete(0, 'end')
                startup_handler.handle_user_input(user_input)
    
    entry.bind('<Return>', handle_entry)
    entry.focus_set()
    
    root.mainloop()

if __name__ == "__main__":
    test_startup_integration()