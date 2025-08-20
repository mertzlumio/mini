import tkinter as tk
from utils import place_bottom_right, toggle_window_size
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

# Global state for window visibility, dragging, and sizing
is_visible = True
is_expanded = False  # Track window size state
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

def toggle_size(root):
    """Toggle between default and expanded window size with adaptive padding"""
    global is_expanded
    is_expanded = toggle_window_size(root, is_expanded)
    
    # Update the size toggle icon based on current state
    if is_expanded:
        # Expanded mode - icon points southeast (down-right)
        size_toggle_btn.config(text="⇲")  # Southeast arrow
        # Increase console height for expanded mode
        for console in consoles.values():
            console.config(height=20)  # More lines for expanded mode
        # Adjust input field for expanded mode
        if entry_widget:
            entry_widget.config(font=("JetBrains Mono", 14, "bold"))  # Larger font
            # Update input padding for expanded mode
            entry_widget.pack_configure(padx=(1, 4), pady=0, ipady=0)
    else:
        # Compact mode - icon points northwest (up-left) 
        size_toggle_btn.config(text="⇱")  # Northwest arrow
        # Reset to default height
        for console in consoles.values():
            console.config(height=8)   # Original height for compact mode
        # Reset input field to default
        if entry_widget:
            entry_widget.config(font=("JetBrains Mono", 12, "bold"))  # Default font
            # Reset input padding to default
            entry_widget.pack_configure(padx=(2, 5), pady=0, ipady=0)


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
        # Check for Ctrl+Shift+S for toggling size
        elif hasattr(key, 'char') and key.char == 's' and \
             key.ctrl and key.shift:
            root.after(0, lambda: toggle_size(root))
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

def scroll_console(console, direction, smooth=True):
    """Scroll console content smoothly"""
    if smooth:
        # Smooth scrolling - multiple small steps
        steps = 10
        scroll_amount = 1
        delay = 20  # milliseconds between steps
        
        def smooth_scroll_step(step):
            if step < steps:
                if direction == "up":
                    console.yview_scroll(-scroll_amount, "units")
                elif direction == "down":
                    console.yview_scroll(scroll_amount, "units")
                console.after(delay, lambda: smooth_scroll_step(step + 1))
        
        smooth_scroll_step(0)
    else:
        # Original scrolling
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

# Global reference for entry widget and consoles
entry_widget = None
consoles = {}
active_mode_name = "bash" # Start with bash

def get_active_console():
    """Helper to get the currently visible console widget"""
    return consoles.get(active_mode_name)

def start_app():
    global entry_widget, consoles, active_mode_name, size_toggle_btn
    
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
        print("Using pynput for global hotkeys:")
        print("  Ctrl+Shift+M to toggle visibility")
        print("  Ctrl+Shift+S to toggle size")  
        print("  Escape to exit")
    else:
        try:
            simple_keyboard.add_hotkey('ctrl+shift+m', lambda: toggle_window(root))
            simple_keyboard.add_hotkey('ctrl+shift+s', lambda: toggle_size(root))
            print("Using 'keyboard' library for global hotkeys:")
            print("  Ctrl+Shift+M to toggle visibility")
            print("  Ctrl+Shift+S to toggle size")
        except Exception as e:
            print(f"Warning: Could not set global hotkey: {e}")
        
        root.bind_all("<Escape>", lambda e: root.destroy())

    place_bottom_right(root)
    
    # Get current theme
    THEME = get_current_theme()
    
    # Main container
    main_frame = tk.Frame(root, bg=THEME["bg"])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    # INTEGRATED HEADER: Drag handle + Mode + Status + Size toggle in one line
    header_frame = tk.Frame(main_frame, bg=THEME["border"], height=26)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)
    
    # Drag handle (small circle)
    drag_handle = tk.Label(
        header_frame, text="●", bg=THEME["border"], fg=THEME["accent"],
        font=("Fira Code", 12), width=2, cursor="fleur"
    )
    drag_handle.pack(side=tk.LEFT, pady=3)
    
    # Bind drag events to the handle
    drag_handle.bind("<Button-1>", start_drag)
    drag_handle.bind("<B1-Motion>", on_drag)
    
    # Mode + Status combined label
    mode_status_label = tk.Label(
        header_frame, text="[BASH] Ready", bg=THEME["border"], fg=THEME["text"],
        font=("Fira Code", 10), anchor="w"
    )
    mode_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4), pady=3)
    
    # Size toggle button (compact indicator)
    size_toggle_btn = tk.Label(
        header_frame, text="⇱", bg=THEME["border"], fg=THEME["dim"],
        font=("Fira Code", 10), cursor="hand2", width=2
    )
    size_toggle_btn.pack(side=tk.RIGHT, pady=3, padx=(0, 4))
    size_toggle_btn.bind("<Button-1>", lambda e: toggle_size(root))
    
    # Separator line
    separator = tk.Frame(main_frame, bg=THEME["border"], height=1)
    separator.pack(fill=tk.X)
    
    # Console area (no scrollbar, clean look)
    console_frame = tk.Frame(main_frame, bg=THEME["console_bg"])
    console_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
    console_frame.grid_rowconfigure(0, weight=1)
    console_frame.grid_columnconfigure(0, weight=1)

    # Create a console for each mode
    for mode_name in ["bash", "chat", "notes", "music"]:
        console = tk.Text(
            console_frame, height=8, bg=THEME["console_bg"], fg=THEME["text"],
            insertbackground=THEME["accent"], bd=0, highlightthickness=0,
            font=("Cascadia Code", 10), wrap=tk.WORD,
            selectbackground=THEME["accent"], selectforeground=THEME["bg"],
            padx=6, pady=8, cursor="arrow",
            spacing1=2, spacing3=1
        )
        # Configure text tags for each console
        console.tag_config("success", foreground=THEME["success"])
        console.tag_config("warning", foreground=THEME["warning"])
        console.tag_config("error", foreground=THEME["error"])
        console.tag_config("accent", foreground=THEME["accent"])
        console.tag_config("dim", foreground=THEME["dim"])
        
        # Disable editing and manage focus
        console.bind("<Key>", lambda e: "break")
        console.bind("<Button-1>", lambda e, entry=entry_widget: force_focus_to_entry(e, entry))

        consoles[mode_name] = console
        # Place console in grid, it will be hidden until lifted
        console.grid(row=0, column=0, sticky="nsew")

    # Bottom separator
    separator2 = tk.Frame(main_frame, bg=THEME["border"], height=1)
    separator2.pack(fill=tk.X)
    
    # FULL-WIDTH INPUT AREA - ENHANCED
    input_frame = tk.Frame(main_frame, bg=THEME["console_bg"], height=35)
    input_frame.pack(fill=tk.X)
    input_frame.pack_propagate(False)

    # Prompt symbol
    prompt_label = tk.Label(
        input_frame, text=">", bg=THEME["console_bg"], fg=THEME["accent"], 
        font=("JetBrains Mono", 14, "bold")
    )
    prompt_label.pack(side=tk.LEFT, padx=(2, 2), pady=1)

    # Entry field (full width) - ENHANCED
    entry = tk.Entry(
        input_frame, bg=THEME["console_bg"], fg=THEME["text"],
        insertbackground=THEME["accent"], bd=0, highlightthickness=0,
        font=("JetBrains Mono", 12, "bold"), selectbackground=THEME["accent"],
        selectforeground=THEME["bg"], insertwidth=3
    )
    entry.pack(fill=tk.X, expand=True, padx=(2, 15), pady=0, ipady=0)
    
    # Store global reference
    entry_widget = entry
    
    # Set initial focus
    entry.focus_set()
    
    # Override console click to focus entry
    for console in consoles.values():
        console.bind("<Button-1>", lambda e, entry=entry: force_focus_to_entry(e, entry))
    
    # Bind events
    entry.bind("<Return>", lambda e: on_enter(entry, get_active_console, mode_status_label))
    entry.bind("<Control-Up>", lambda e: on_up(entry))
    entry.bind("<Control-Down>", lambda e: on_down(entry))
    
    # Pass the new active_mode_name variable to toggle_mode
    def mode_toggle_handler(event):
        global active_mode_name
        active_mode_name = toggle_mode(consoles, mode_status_label, prompt_label, THEME)
        return "break"
    entry.bind("<Control-m>", mode_toggle_handler)
    
    # Console navigation
    entry.bind("<Up>", lambda e: scroll_console(get_active_console(), "up"))
    entry.bind("<Down>", lambda e: scroll_console(get_active_console(), "down"))
    
    # Theme switching
    entry.bind("<Control-t>", lambda e: cycle_theme(get_active_console(), mode_status_label, entry))
    
    # Window size toggle
    entry.bind("<Control-s>", lambda e: toggle_size(root))
    
    # Force focus on window activation
    root.bind("<FocusIn>", lambda e: entry.focus_set())
    
    # Initialize modes
    notes_core.load_notes()
    
    # Welcome message in BASH console
    consoles["bash"].insert(tk.END, ">> Mini Player Ready\n", "accent")
    consoles["bash"].insert(tk.END, f"   Theme: {THEME['name']}\n", "dim")
    consoles["bash"].insert(tk.END, "   Modes: BASH → CHAT → NOTES → MUSIC\n", "dim")
    consoles["bash"].insert(tk.END, "   Ctrl+M=modes • Ctrl+T=themes • Ctrl+S=size • ↑↓=scroll\n", "dim")
    consoles["bash"].insert(tk.END, "   Global: Ctrl+Shift+M=toggle • Ctrl+Shift+S=resize\n", "dim")
    consoles["bash"].see(tk.END)

    # Initial content for other consoles
    notes_core.display_notes(consoles["notes"])
    # A placeholder for music, can be expanded
    consoles["music"].insert(tk.END, ">> Music Mode\n", "accent")
    consoles["music"].insert(tk.END, "   Type 'help' for commands\n", "dim")
    
    # Lift the initial console to the top
    consoles[active_mode_name].lift()
    
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