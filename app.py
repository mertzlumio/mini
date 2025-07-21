import tkinter as tk
from utils import place_bottom_right
from handlers import on_enter, on_up, on_down, toggle_mode, display_notes
from modes.notes import load_notes
import os
def start_app():
    root = tk.Tk()
    root.overrideredirect(True)
    root.title("Mini Console")
    root.geometry("400x150")
    root.resizable(False, False)
    root.attributes('-topmost', True)
    place_bottom_right(root)

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
        if root.focus_get() != entry:
            entry.focus()
        root.after(500, enforce_focus)

    enforce_focus()
    load_notes()
    display_notes(console)
    root.mainloop()
