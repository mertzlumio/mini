# themes.py - Modular theme system for Mini-Player

# Default modern theme (your current one)
MODERN_THEME = {
    "name": "Modern Dark",
    "bg": "#0d1117",           # Dark background
    "console_bg": "#161b22",   # Console background  
    "entry_bg": "#21262d",     # Entry background
    "text": "#f0f6fc",         # Main text
    "accent": "#58a6ff",       # Accent color (blue)
    "success": "#3fb950",      # Success (green)
    "warning": "#d29922",      # Warning (yellow)
    "error": "#f85149",        # Error (red)
    "border": "#30363d",       # Border color
    "dim": "#7d8590",          # Dimmed text
    "mode_config": {
        "bash": {"symbol": "[BASH]", "color": "#f0f6fc", "prompt": ">"},
        "chat": {"symbol": "[CHAT]", "color": "#58a6ff", "prompt": ">"}, 
        "notes": {"symbol": "[NOTE]", "color": "#3fb950", "prompt": ">"},
        "music": {"symbol": "[MUSIC]", "color": "#d29922", "prompt": ">"}
    }
}

# ASCII Terminal theme
ASCII_THEME = {
    "name": "ASCII Terminal",
    "bg": "#000000",           # Pure black background
    "console_bg": "#000000",   # Black console
    "entry_bg": "#000000",     # Black input area
    "text": "#00ff00",         # Classic terminal green
    "accent": "#00ffff",       # Cyan for highlights/mode
    "success": "#00ff00",      # Bright green for success
    "warning": "#ffff00",      # Yellow for warnings
    "error": "#ff0000",        # Red for errors
    "border": "#00ff00",       # Green borders
    "dim": "#008000",          # Darker green for dimmed text
    "mode_config": {
        "bash": {"symbol": "┌─ BASH ─┐", "color": "#00ff00", "prompt": "├►"},
        "chat": {"symbol": "┌─ CHAT ─┐", "color": "#00ffff", "prompt": "├►"}, 
        "notes": {"symbol": "┌─ NOTE ─┐", "color": "#00ff00", "prompt": "├►"},
        "music": {"symbol": "┌─ MUSIC ─┐", "color": "#ffff00", "prompt": "├►"}
    }
}

# Retro amber theme
AMBER_THEME = {
    "name": "Retro Amber",
    "bg": "#1a0f00",           # Dark brown background
    "console_bg": "#1a0f00",   # Dark brown console
    "entry_bg": "#1a0f00",     # Dark brown input
    "text": "#ffb000",         # Amber text
    "accent": "#ffd700",       # Gold accent
    "success": "#ffb000",      # Amber success
    "warning": "#ff8c00",      # Orange warning
    "error": "#ff4500",        # Red-orange error
    "border": "#ffb000",       # Amber borders
    "dim": "#cc8800",          # Dimmed amber
    "mode_config": {
        "bash": {"symbol": "[BASH]", "color": "#ffb000", "prompt": "▶"},
        "chat": {"symbol": "[CHAT]", "color": "#ffd700", "prompt": "▶"}, 
        "notes": {"symbol": "[NOTE]", "color": "#ffb000", "prompt": "▶"},
        "music": {"symbol": "[MUSIC]", "color": "#ff8c00", "prompt": "▶"}
    }
}

# Matrix theme
MATRIX_THEME = {
    "name": "Matrix",
    "bg": "#000000",           # Black background
    "console_bg": "#000000",   # Black console
    "entry_bg": "#000000",     # Black input
    "text": "#00ff41",         # Matrix green
    "accent": "#41ff00",       # Bright matrix green
    "success": "#00ff41",      # Matrix green
    "warning": "#ffff00",      # Yellow warning
    "error": "#ff0040",        # Matrix red
    "border": "#00ff41",       # Matrix green borders
    "dim": "#008020",          # Dimmed matrix green
    "mode_config": {
        "bash": {"symbol": "[BASH]", "color": "#00ff41", "prompt": ">>"},
        "chat": {"symbol": "[CHAT]", "color": "#41ff00", "prompt": ">>"}, 
        "notes": {"symbol": "[NOTE]", "color": "#00ff41", "prompt": ">>"},
        "music": {"symbol": "[MUSIC]", "color": "#ffff00", "prompt": ">>"}
    }
}

# All available themes
THEMES = {
    "modern": MODERN_THEME,
    "ascii": ASCII_THEME,
    "amber": AMBER_THEME,
    "matrix": MATRIX_THEME
}

# Current theme (can be changed)
current_theme = "modern"

def get_current_theme():
    """Get the currently active theme"""
    return THEMES[current_theme]

def switch_theme(theme_name):
    """Switch to a different theme"""
    global current_theme
    if theme_name in THEMES:
        current_theme = theme_name
        return True
    return False

def get_available_themes():
    """Get list of available theme names"""
    return list(THEMES.keys())

def get_theme_info():
    """Get info about current theme"""
    theme = get_current_theme()
    return f"Current theme: {theme['name']}"