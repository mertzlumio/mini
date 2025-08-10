import tkinter as tk
from utils import place_bottom_right
from handlers import on_enter, on_up, on_down, toggle_mode
from modes.notes import core as notes_core
from themes import get_current_theme, switch_theme, get_available_themes, get_theme_info, current_theme
import threading
import atexit
import themes

# Try pynput first for global hotkeys, then fallback to keyboard
USE_PYNPUT = False
try:
    from pynput import keyboard as pynput_keyboard
    USE_PYNPUT = True
except ImportError:
    print("pynput not found, falling back to 'keyboard' library for hotkeys.")
    try:
        import keyboard as simple_keyboard
    except ImportError:
        print("Error: Neither pynput nor keyboard library found. Please install one.")
        exit()

# Global state for window visibility and dragging
is_visible = True
drag_data = {"x": 0, "y": 0}

def toggle_window(root):
    """Toggle the visibility of the application window."""
    global is_visible
    if is_visible:
        root.withdraw()
    else:
        root.deiconify()
        root.lift()  # Bring to front
        entry_widget.focus_set()  # Always focus on input
    is_visible = not is_visible

def start_drag(event):
    """Start dragging the window"""
    drag_data["x"] = event.x
    drag_data["y"] = event.y

def on_drag(event):
    """Handle window dragging"""
    x = event.widget.winfo_pointerx() - drag_data["x"]
    y = event.widget.winfo_pointery() - drag_data["y"]
    event.widget.winfo_toplevel().geometry(f"+{x}+{y}")

def force_focus_to_entry(event, entry):
    """Force focus to input entry on any click"""
    entry.focus_set()
    return "break"

# pynput specific hotkey handler
def on_press(key, root, listener_ref):
    """Callback function for pynput.keyboard listener."""
    try:
        # Check for Ctrl+Shift+M for toggling window
        if hasattr(key, 'char') and key.char == 'm' and \
           key.ctrl and key.shift:
            root.after(0, lambda: toggle_window(root))
        # Check for Escape key to exit (global)
        elif key == pynput_keyboard.Key.esc:
            root.after(0, root.destroy)
            return False
    except AttributeError:
        pass

def cleanup_on_exit():
    """Cleanup function called when app exits"""
    try:
        from modes.music.audio_engine import cleanup_audio_engine
        cleanup_audio_engine()
        print("Music engine cleaned up")
    except ImportError:
        pass
    except Exception as e:
        print(f"Error during music cleanup: {e}")

def scroll_console(console, direction):
    """Scroll console content with Ctrl+Arrow keys"""
    if direction == "up":
        console.yview_scroll(-3, "units")
    elif direction == "down":
        console.yview_scroll(3, "units")

def cycle_theme(console, mode_status_label, entry):
    """Cycle through available themes"""
    themes_list = themes.get_available_themes()
    current_key = themes.current_theme
    current_idx = themes_list.index(current_key)
    next_idx = (current_idx + 1) % len(themes_list)
    next_theme = themes_list[next_idx]
    
    if themes.switch_theme(next_theme):
        apply_theme_to_widgets(console, mode_status_label, entry)
        theme_info = themes.get_theme_info()
        console.insert(tk.END, f"\n🎨 {theme_info}\n", "accent")
        console.see(tk.END)

def apply_theme_to_widgets(console, mode_status_label, entry):
    """Apply current theme to all widgets"""
    theme = get_current_theme()
    
    # Update widget colors
    console.config(bg=theme["console_bg"], fg=theme["text"], 
                  insertbackground=theme["accent"], selectbackground=theme["accent"])
    entry.config(bg=theme["console_bg"], fg=theme["text"], 
                insertbackground=theme["accent"], selectbackground=theme["accent"])
    
    # Update console tags
    console.tag_config("success", foreground=theme["success"])
    console.tag_config("warning", foreground=theme["warning"]) 
    console.tag_config("error", foreground=theme["error"])
    console.tag_config("accent", foreground=theme["accent"])
    console.tag_config("dim", foreground=theme["dim"])

# Global reference for entry widget
entry_widget = None

def start_app():
    global entry_widget
    
    root = tk.Tk()
    root.overrideredirect(True)
    root.title("Mini Player")
    root.resizable(False, False)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.95)

    # Register cleanup function
    atexit.register(cleanup_on_exit)

    # Hotkey setup
    if USE_PYNPUT:
        listener = pynput_keyboard.Listener(on_press=lambda k: on_press(k, root, listener))
        listener.start()
        print("Using pynput for global hotkeys (Ctrl+Shift+M to toggle, Escape to exit).")
    else:
        try:
            simple_keyboard.add_hotkey('ctrl+shift+m', lambda: toggle_window(root))
            print("Using 'keyboard' library for global hotkeys (Ctrl+Shift+M to toggle).")
        except Exception as e:
            print(f"Warning: Could not set global hotkey: {e}")
        
        root.bind_all("<Escape>", lambda e: root.destroy())

    place_bottom_right(root)
    
    # Get current theme
    THEME = get_current_theme()
    
    # Main container
    main_frame = tk.Frame(root, bg=THEME["bg"])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    # INTEGRATED HEADER: Drag handle + Mode + Status in one line
    header_frame = tk.Frame(main_frame, bg=THEME["border"], height=26)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)
    
    # Drag handle (small circle)
    drag_handle = tk.Label(
        header_frame, text="●", bg=THEME["border"], fg=THEME["accent"],
        font=("Consolas", 12), width=2, cursor="fleur"
    )
    drag_handle.pack(side=tk.LEFT, pady=3)
    
    # Bind drag events to the handle
    drag_handle.bind("<Button-1>", start_drag)
    drag_handle.bind("<B1-Motion>", on_drag)
    
    # Mode + Status combined label
    mode_status_label = tk.Label(
        header_frame, text="[BASH] Ready", bg=THEME["border"], fg=THEME["text"],
        font=("Consolas", 9), anchor="w"
    )
    mode_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 8), pady=3)
    
    # Separator line
    separator = tk.Frame(main_frame, bg=THEME["border"], height=1)
    separator.pack(fill=tk.X)
    
    # Console area (no scrollbar, clean look)
    console_frame = tk.Frame(main_frame, bg=THEME["console_bg"])
    console_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
    
    console = tk.Text(
        console_frame, height=8, bg=THEME["console_bg"], fg=THEME["text"],
        insertbackground=THEME["accent"], bd=0, highlightthickness=0,
        font=("Cascadia Code", 9), wrap=tk.WORD,
        selectbackground=THEME["accent"], selectforeground=THEME["bg"],
        padx=12, pady=8, cursor="arrow"
    )
    console.pack(fill=tk.BOTH, expand=True)
    
    # Configure text tags
    console.tag_config("success", foreground=THEME["success"])
    console.tag_config("warning", foreground=THEME["warning"]) 
    console.tag_config("error", foreground=THEME["error"])
    console.tag_config("accent", foreground=THEME["accent"])
    console.tag_config("dim", foreground=THEME["dim"])
    
    # Disable console editing and force focus to entry
    console.bind("<Key>", lambda e: "break")
    console.bind("<Button-1>", lambda e: force_focus_to_entry(e, None))
    
    # Bottom separator
    separator2 = tk.Frame(main_frame, bg=THEME["border"], height=1)
    separator2.pack(fill=tk.X)
    
    # FULL-WIDTH INPUT AREA - ENHANCED
    input_frame = tk.Frame(main_frame, bg=THEME["console_bg"], height=35)  # Increased from 32 to 45
    input_frame.pack(fill=tk.X)
    input_frame.pack_propagate(False)

    # Prompt symbol
    prompt_label = tk.Label(
        input_frame, text=">", bg=THEME["console_bg"], fg=THEME["accent"], 
        font=("Cascadia Code", 14, "bold")  # Increased from 9 to 12
    )
    prompt_label.pack(side=tk.LEFT, padx=(2, 2), pady=1)  # Increased padding

    # Entry field (full width) - ENHANCED
    entry = tk.Entry(
        input_frame, bg=THEME["console_bg"], fg=THEME["text"],
        insertbackground=THEME["accent"], bd=0, highlightthickness=0,
        font=("Cascadia Code", 12), selectbackground=THEME["accent"],  # Increased from 9 to 12
        selectforeground=THEME["bg"], insertwidth=3  # Increased cursor width
    )
    entry.pack(fill=tk.X, side=tk.RIGHT, padx=(2, 15), pady=8, ipady=3) 
    
    # Store global reference
    entry_widget = entry
    
    # Set initial focus
    entry.focus_set()
    
    # Override console click to focus entry
    console.bind("<Button-1>", lambda e: force_focus_to_entry(e, entry))
    
    # Bind events
    entry.bind("<Return>", lambda e: on_enter(entry, console, mode_status_label, mode_status_label))
    entry.bind("<Up>", lambda e: on_up(entry))
    entry.bind("<Down>", lambda e: on_down(entry))
    entry.bind("<Control-m>", lambda e: toggle_mode(entry, console, mode_status_label, mode_status_label, prompt_label, THEME))
    
    # Console navigation
    entry.bind("<Control-Up>", lambda e: scroll_console(console, "up"))
    entry.bind("<Control-Down>", lambda e: scroll_console(console, "down"))
    
    # Theme switching
    entry.bind("<Control-t>", lambda e: cycle_theme(console, mode_status_label, entry))
    
    # Force focus on window activation
    root.bind("<FocusIn>", lambda e: entry.focus_set())
    
    # Initialize modes
    notes_core.load_notes()
    
    # Welcome message
    console.insert(tk.END, ">> Mini Player Ready\n", "accent")
    console.insert(tk.END, f"   Theme: {THEME['name']}\n", "dim")
    console.insert(tk.END, "   Modes: BASH → CHAT → NOTES → MUSIC\n", "dim")
    console.insert(tk.END, "   Ctrl+M=modes • Ctrl+T=themes • Ctrl+↑↓=scroll\n", "dim")
    notes_core.display_notes(console)
    console.see(tk.END)
    
    # Cleanup function for window close
    def on_closing():
        cleanup_on_exit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

    # Cleanup pynput listener
    if USE_PYNPUT and listener.is_alive():
        listener.stop()
        listener.join()

if __name__ == "__main__":
    start_app()