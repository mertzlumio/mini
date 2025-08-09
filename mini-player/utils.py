# --- Centralized Window Configuration ---
APP_WIDTH = 240
APP_HEIGHT = 320
APP_MARGIN = 10
# ----------------------------------------

def place_bottom_right(root, width=None, height=None, margin=None):
    """
    Position window at bottom-right of screen.
    Uses default values if parameters not provided.
    """
    # Use defaults if not specified
    width = width or APP_WIDTH
    height = height or APP_HEIGHT
    margin = margin or APP_MARGIN
    
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    x = screen_width - width - margin
    y = screen_height - height - margin
    
    root.geometry(f"{width}x{height}+{x}+{y}")