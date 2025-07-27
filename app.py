import tkinter as tk
from utils import place_bottom_right
from handlers import on_enter, on_up, on_down, toggle_mode, display_notes
from modes.notes import load_notes
import os

# --- Centralized Window Configuration ---
APP_WIDTH = 400
APP_HEIGHT = 200
APP_MARGIN = 10
# ----------------------------------------

def start_app():
    root = tk.Tk()
    root.overrideredirect(True)
    root.title("Mini Console")
    # REMOVED: root.geometry("500x80") - Dimensions are now handled by place_bottom_right
    root.resizable(False, False)
    root.attributes('-topmost', True)

    # Pass the defined dimensions to the utility function
    place_bottom_right(root, width=APP_WIDTH, height=APP_HEIGHT, margin=APP_MARGIN)

    console = tk.Text(root, height=8, bg="#1e1e1e", fg="#dcdcdc", insertbackground="#dcdcdc", bd=0, highlightthickness=0)
    console.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 0))
    console.bind("<Key>", lambda e: "break")
    console.bind("<Button-1>", lambda e: entry.focus())

    entry = tk.Entry(root, bg="#202020", fg="#ffffff", insertbackground="#ffffff", bd=0, highlightthickness=0)
    entry.pack(fill=tk.X, padx=5, pady=(0, 2))
    entry.focus()

    entry.bind("<Return>", lambda e: on_enter(entry, console))
    entry.bind("<Up>", lambda e: on_up(entry))
    entry.bind("<Down>", lambda e: on_down(entry))
    entry.bind("<Tab>", lambda e: "break")
    entry.bind("<Control-m>", lambda e: toggle_mode(entry, console))
    root.bind_all("<Escape>", lambda e: root.destroy())

    def enforce_focus():
        # This ensures the entry widget always has focus, useful for an overlay console
        if root.focus_get() != entry:
            entry.focus()
        root.after(500, enforce_focus) # Check every 500ms

    enforce_focus() # Start the focus enforcement loop
    load_notes()    # Assuming this loads initial notes data
    display_notes(console) # Assuming this displays the notes in the console
    root.mainloop() # Start the Tkinter event loop