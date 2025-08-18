# --- Centralized Window Configuration ---
APP_WIDTH = 240
APP_HEIGHT = 320
APP_MARGIN = 10

# Expanded mode dimensions
EXPANDED_WIDTH = 380  # Wider than default
EXPANDED_MARGIN = 20  # More margin for expanded mode
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

def get_expanded_dimensions(root):
    """Get dimensions for expanded (full-height) mode"""
    root.update_idletasks()
    screen_height = root.winfo_screenheight()
    
    # Full height minus margins for taskbar/dock
    expanded_height = screen_height - (EXPANDED_MARGIN * 2)
    
    return EXPANDED_WIDTH, expanded_height

def place_expanded_window(root):
    """Position window in expanded (full-height) mode at bottom-right"""
    expanded_width, expanded_height = get_expanded_dimensions(root)
    
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    x = screen_width - expanded_width - EXPANDED_MARGIN
    y = EXPANDED_MARGIN  # Start from top margin
    
    root.geometry(f"{expanded_width}x{expanded_height}+{x}+{y}")

def toggle_window_size(root, is_expanded=False):
    """
    Toggle between default and expanded window size
    Returns: new expanded state (boolean)
    """
    if is_expanded:
        # Switch to default size
        place_bottom_right(root)
        return False
    else:
        # Switch to expanded size
        place_expanded_window(root)
        return True