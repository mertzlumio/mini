import tkinter as tk
from utils import place_bottom_right
from handlers import on_enter, on_up, on_down, toggle_mode, display_notes
from modes.notes import load_notes

# Clean UI theme
THEME = {
    "bg": "#0d1117",           # Dark background
    "console_bg": "#161b22",   # Console background  
    "entry_bg": "#21262d",     # Entry background
    "text": "#f0f6fc",         # Main text
    "accent": "#58a6ff",       # Accent color (blue)
    "success": "#3fb950",      # Success (green)
    "warning": "#d29922",      # Warning (yellow)
    "error": "#f85149",        # Error (red)
    "border": "#30363d",       # Border color
    "dim": "#7d8590"           # Dimmed text
}

def start_app():
    root = tk.Tk()
    root.overrideredirect(True)
    root.title("Mini Player")
    root.resizable(False, False)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.95)  # Slight transparency
    
    place_bottom_right(root)
    
    # Main container with padding
    main_frame = tk.Frame(root, bg=THEME["bg"])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    # Status bar showing current mode
    status_frame = tk.Frame(main_frame, bg=THEME["border"], height=24)
    status_frame.pack(fill=tk.X)
    status_frame.pack_propagate(False)
    
    mode_label = tk.Label(
        status_frame,
        text="[BASH]",
        bg=THEME["border"],
        fg=THEME["accent"],
        font=("Consolas", 8, "bold"),
        anchor="w"
    )
    mode_label.pack(side=tk.LEFT, padx=8, pady=2)
    
    status_label = tk.Label(
        status_frame,
        text="Ready",
        bg=THEME["border"], 
        fg=THEME["text"],
        font=("Consolas", 8),
        anchor="e"
    )
    status_label.pack(side=tk.RIGHT, padx=8, pady=2)
    
    # Console area with scrollbar
    console_frame = tk.Frame(main_frame, bg=THEME["console_bg"])
    console_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=1)
    
    # Custom scrollbar
    scrollbar = tk.Scrollbar(console_frame, width=12)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2), pady=2)
    
    console = tk.Text(
        console_frame,
        height=8,
        bg=THEME["console_bg"],
        fg=THEME["text"], 
        insertbackground=THEME["accent"],
        bd=0,
        highlightthickness=0,
        font=("Cascadia Code", 9),
        wrap=tk.WORD,
        yscrollcommand=scrollbar.set,
        selectbackground=THEME["accent"],
        selectforeground=THEME["bg"],
        padx=8,
        pady=6
    )
    console.pack(fill=tk.BOTH, expand=True, padx=(8, 0), pady=2)
    scrollbar.config(command=console.yview)
    
    # Configure colored text tags
    console.tag_config("success", foreground=THEME["success"])
    console.tag_config("warning", foreground=THEME["warning"]) 
    console.tag_config("error", foreground=THEME["error"])
    console.tag_config("accent", foreground=THEME["accent"])
    console.tag_config("dim", foreground=THEME["dim"])
    
    console.bind("<Key>", lambda e: "break")
    console.bind("<Button-1>", lambda e: entry.focus())
    
    # Entry area with prompt indicator
    entry_frame = tk.Frame(main_frame, bg=THEME["bg"])
    entry_frame.pack(fill=tk.X, pady=(1, 0))
    
    # Visual prompt
    prompt_label = tk.Label(
        entry_frame,
        text=">",
        bg=THEME["bg"],
        fg=THEME["accent"], 
        font=("Cascadia Code", 10, "bold")
    )
    prompt_label.pack(side=tk.LEFT, padx=(8, 4), pady=4)
    
    entry = tk.Entry(
        entry_frame,
        bg=THEME["entry_bg"],
        fg=THEME["text"],
        insertbackground=THEME["accent"],
        bd=0,
        highlightthickness=1,
        highlightcolor=THEME["accent"],
        highlightbackground=THEME["border"],
        font=("Cascadia Code", 9),
        selectbackground=THEME["accent"],
        selectforeground=THEME["bg"]
    )
    entry.pack(fill=tk.X, side=tk.RIGHT, padx=(0, 8), pady=4)
    entry.focus()
    
    # Enhanced bindings
    entry.bind("<Return>", lambda e: on_enter(entry, console, mode_label, status_label))
    entry.bind("<Up>", lambda e: on_up(entry))
    entry.bind("<Down>", lambda e: on_down(entry))
    entry.bind("<Tab>", lambda e: "break")
    entry.bind("<Control-m>", lambda e: toggle_mode(entry, console, mode_label, status_label, prompt_label))
    entry.bind("<Control-l>", lambda e: clear_console(console))
    
    root.bind_all("<Escape>", lambda e: root.destroy())
    root.bind_all("<Control-q>", lambda e: root.destroy())
    
    # Hover effects for better UX
    def on_entry_focus_in(e):
        entry.config(highlightthickness=2)
        
    def on_entry_focus_out(e):
        entry.config(highlightthickness=1)
        
    entry.bind("<FocusIn>", on_entry_focus_in)
    entry.bind("<FocusOut>", on_entry_focus_out)
    
    def enforce_focus():
        if root.focus_get() != entry:
            entry.focus()
        root.after(1000, enforce_focus)
    
    enforce_focus()
    load_notes()
    
    # Welcome message with better formatting
    console.insert(tk.END, ">> Mini Player Ready\n", "accent")
    console.insert(tk.END, "Ctrl+M: Switch mode | Ctrl+L: Clear | Esc: Quit\n", "dim")
    console.insert(tk.END, "-" * 40 + "\n", "dim")
    
    display_notes(console)
    console.see(tk.END)
    
    root.mainloop()

def clear_console(console):
    """Clear console with a clean message"""
    console.delete(1.0, tk.END)
    console.insert(tk.END, "Console cleared\n", "dim")
    return "break"