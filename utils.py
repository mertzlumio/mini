import os

def place_bottom_right(root, width=500, height=80, margin=10):
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = screen_width - width - margin
    y = screen_height - height - margin
    root.geometry(f"{width}x{height}+{x}+{y}")
