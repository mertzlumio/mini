from tkinter import END
import importlib

# Mode management
modes = ["bash", "chat", "notes"]
mode_index = 0
mode = modes[mode_index]

# History management (shared across all modes)
history = []
history_index = -1

# Mode configuration for UI display
MODE_CONFIG = {
    "bash": {"symbol": "[BASH]", "color": "#f0f6fc"},
    "chat": {"symbol": "[CHAT]", "color": "#58a6ff"}, 
    "notes": {"symbol": "[NOTE]", "color": "#3fb950"}
}

# Dynamic mode loading
def get_mode_handler(mode_name):
    """Dynamically load mode handler"""
    try:
        module = importlib.import_module(f"modes.{mode_name}.core")
        return module
    except ImportError as e:
        print(f"Error loading mode {mode_name}: {e}")
        return None

def toggle_mode(entry, console, mode_label, status_label, prompt_label):
    """Mode switching only - no mode-specific logic"""
    global mode_index, mode
    mode_index = (mode_index + 1) % len(modes)
    mode = modes[mode_index]
    
    # Update UI elements
    config = MODE_CONFIG[mode]
    mode_label.config(text=config['symbol'])
    prompt_label.config(fg=config['color'])
    status_label.config(text=f"Switched to {mode}")
    
    # Visual feedback in console
    console.insert(END, f"\n>> Mode: {config['symbol']}\n", "accent")
    
    # Let the mode handle its own initialization if needed
    mode_handler = get_mode_handler(mode)
    if mode_handler and hasattr(mode_handler, 'on_mode_enter'):
        mode_handler.on_mode_enter(console)
    
    console.see(END)
    return "break"

def on_enter(entry, console, mode_label, status_label):
    """Delegate to current mode handler"""
    global history, history_index
    
    cmd = entry.get().strip()
    if not cmd:
        return

    # Add to shared history
    history.append(cmd)
    history_index = len(history)
    
    # Show command with clean formatting
    console.insert(END, f"\n> {cmd}\n", "dim")
    
    # Update status
    status_label.config(text="Processing...")

    # Delegate to current mode
    mode_handler = get_mode_handler(mode)
    if mode_handler and hasattr(mode_handler, 'handle_input'):
        mode_handler.handle_input(cmd, console)
    else:
        console.insert(END, f"Mode '{mode}' not implemented yet.\n", "error")

    # Reset status and clean up
    status_label.config(text="Ready")
    console.see(END)
    entry.delete(0, END)
    
    # Keep console manageable (max 100 lines)
    lines = console.get(1.0, END).count('\n')
    if lines > 100:
        console.delete(1.0, "10.0")

def on_up(entry):
    """Navigate command history up"""
    global history_index
    if history and history_index > 0:
        history_index -= 1
        entry.delete(0, END)
        entry.insert(0, history[history_index])
    return "break"

def on_down(entry):
    """Navigate command history down"""
    global history_index
    if history:
        if history_index < len(history) - 1:
            history_index += 1
            entry.delete(0, END)
            entry.insert(0, history[history_index])
        else:
            history_index = len(history)
            entry.delete(0, END)
    return "break"