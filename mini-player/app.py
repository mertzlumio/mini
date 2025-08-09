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

# Global state for window visibility
is_visible = True

def toggle_window(root):
    """
    Toggles the visibility of the application window.
    This function is called by the global hotkey.
    """
    global is_visible
    if is_visible:
        root.withdraw()
    else:
        root.deiconify()
    is_visible = not is_visible

# pynput specific hotkey handler
def on_press(key, root, listener_ref):
    """
    Callback function for pynput.keyboard listener.
    Handles global hotkeys.
    """
    try:
        # Check for Ctrl+Shift+M for toggling window
        if hasattr(key, 'char') and key.char == 'm' and \
           key.ctrl and key.shift:
            # Schedule the window toggle on the main Tkinter thread
            root.after(0, lambda: toggle_window(root))
        # Check for Escape key to exit (global)
        elif key == pynput_keyboard.Key.esc:
            root.after(0, root.destroy) # Destroy window on main thread
            return False # Stop the pynput listener
    except AttributeError:
        # Handle special keys that don't have a .char attribute
        pass

def cleanup_on_exit():
    """Cleanup function called when app exits"""
    try:
        # Cleanup music engine
        from modes.music.audio_engine import cleanup_audio_engine
        cleanup_audio_engine()
        print("Music engine cleaned up")
    except ImportError:
        # Music mode not available
        pass
    except Exception as e:
        print(f"Error during music cleanup: {e}")

def scroll_console(console, direction):
    """Scroll console content with Ctrl+Arrow keys"""
    if direction == "up":
        console.yview_scroll(-3, "units")
    elif direction == "down":
        console.yview_scroll(3, "units")


def cycle_theme(console, mode_label, status_label, prompt_label, entry):
    """Cycle through available themes"""
    themes_list = themes.get_available_themes()
    current_key = themes.current_theme  # gets updated value
    current_idx = themes_list.index(current_key)
    next_idx = (current_idx + 1) % len(themes_list)
    next_theme = themes_list[next_idx]
    
    if themes.switch_theme(next_theme):
        apply_theme_to_widgets(console, mode_label, status_label, prompt_label, entry)
        theme_info = themes.get_theme_info()
        console.insert(tk.END, f"\n🎨 {theme_info}\n", "accent")
        console.see(tk.END)

def apply_theme_to_widgets(console, mode_label, status_label, prompt_label, entry):
    """Apply current theme to all widgets"""
    theme = get_current_theme()
    
    # Update widget colors
    console.config(bg=theme["console_bg"], fg=theme["text"], 
                  insertbackground=theme["accent"], selectbackground=theme["accent"])
    entry.config(bg=theme["entry_bg"], fg=theme["text"], 
                insertbackground=theme["accent"], selectbackground=theme["accent"])
    
    # Update console tags
    console.tag_config("success", foreground=theme["success"])
    console.tag_config("warning", foreground=theme["warning"]) 
    console.tag_config("error", foreground=theme["error"])
    console.tag_config("accent", foreground=theme["accent"])
    console.tag_config("dim", foreground=theme["dim"])

def start_app():
    root = tk.Tk()
    root.overrideredirect(True)
    root.title("Mini Player")
    root.resizable(False, False)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.95)

    # Register cleanup function
    atexit.register(cleanup_on_exit)

    # Hotkey setup based on which library is available
    if USE_PYNPUT:
        # pynput listener runs in a separate thread
        listener = pynput_keyboard.Listener(on_press=lambda k: on_press(k, root, listener))
        listener.start()
        print("Using pynput for global hotkeys (Ctrl+Shift+M to toggle, Escape to exit).")
    else:
        # keyboard library setup
        try:
            simple_keyboard.add_hotkey('ctrl+shift+m', lambda: toggle_window(root))
            print("Using 'keyboard' library for global hotkeys (Ctrl+Shift+M to toggle).")
        except Exception as e:
            print(f"Warning: Could not set global hotkey with 'keyboard' library: {e}")
            print("You might need to run as root or adjust permissions on Linux.")
        
        # Tkinter's own Escape binding for local window closure
        root.bind_all("<Escape>", lambda e: root.destroy())
        print("Press Escape to exit the window locally.")

    place_bottom_right(root)
    
    # Get current theme
    THEME = get_current_theme()
    
    main_frame = tk.Frame(root, bg=THEME["bg"])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    status_frame = tk.Frame(main_frame, bg=THEME["border"], height=24)
    status_frame.pack(fill=tk.X)
    status_frame.pack_propagate(False)
    
    mode_label = tk.Label(
        status_frame, text="[BASH]", bg=THEME["border"], fg=THEME["accent"],
        font=("Consolas", 8, "bold"), anchor="w"
    )
    mode_label.pack(side=tk.LEFT, padx=8, pady=2)
    
    status_label = tk.Label(
        status_frame, text="Ready", bg=THEME["border"], fg=THEME["text"],
        font=("Consolas", 8), anchor="e"
    )
    status_label.pack(side=tk.RIGHT, padx=8, pady=2)
    
    console_frame = tk.Frame(main_frame, bg=THEME["console_bg"])
    console_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=1)
    
    # NO SCROLLBAR - just the console
    console = tk.Text(
        console_frame, height=8, bg=THEME["console_bg"], fg=THEME["text"],
        insertbackground=THEME["accent"], bd=0, highlightthickness=0,
        font=("Cascadia Code", 9), wrap=tk.WORD,
        selectbackground=THEME["accent"], selectforeground=THEME["bg"],
        padx=8, pady=6
    )
    console.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)
    
    console.tag_config("success", foreground=THEME["success"])
    console.tag_config("warning", foreground=THEME["warning"]) 
    console.tag_config("error", foreground=THEME["error"])
    console.tag_config("accent", foreground=THEME["accent"])
    console.tag_config("dim", foreground=THEME["dim"])
    
    console.bind("<Key>", lambda e: "break")
    console.bind("<Button-1>", lambda e: entry.focus())
    
    entry_frame = tk.Frame(main_frame, bg=THEME["bg"])
    entry_frame.pack(fill=tk.X, pady=(1, 0))
    
    prompt_label = tk.Label(
        entry_frame, text=">", bg=THEME["bg"], fg=THEME["accent"], 
        font=("Cascadia Code", 9, "bold")
    )
    prompt_label.pack(side=tk.LEFT, padx=(8, 4), pady=4)
    
    entry = tk.Entry(
        entry_frame, bg=THEME["entry_bg"], fg=THEME["text"],
        insertbackground=THEME["accent"], bd=0, highlightthickness=1,
        highlightcolor=THEME["accent"], highlightbackground=THEME["border"],
        font=("Cascadia Code", 9), selectbackground=THEME["accent"],
        selectforeground=THEME["bg"]
    )
    entry.pack(fill=tk.X, side=tk.RIGHT, padx=(0, 8), pady=4)
    entry.focus()
    
    # Bind events
    entry.bind("<Return>", lambda e: on_enter(entry, console, mode_label, status_label))
    entry.bind("<Up>", lambda e: on_up(entry))
    entry.bind("<Down>", lambda e: on_down(entry))
    entry.bind("<Control-m>", lambda e: toggle_mode(entry, console, mode_label, status_label, prompt_label, THEME))
    
    # Console navigation with Ctrl+Arrow keys
    entry.bind("<Control-Up>", lambda e: scroll_console(console, "up"))
    entry.bind("<Control-Down>", lambda e: scroll_console(console, "down"))
    
    # Theme switching with Ctrl+T
    entry.bind("<Control-t>", lambda e: cycle_theme(console, mode_label, status_label, prompt_label, entry))
    
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

    # Ensure pynput listener is stopped if it was started
    if USE_PYNPUT and listener.is_alive():
        listener.stop()
        listener.join() # Wait for the thread to finish