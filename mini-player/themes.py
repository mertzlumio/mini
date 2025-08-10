# themes.py - Updated with minimal TUI theme

# Minimal TUI theme - clean, professional
MINIMAL_THEME = {
    "name": "Minimal TUI",
    "bg": "#1a1a1a",           # Dark background
    "console_bg": "#1a1a1a",   # Same as bg for seamless look
    "entry_bg": "#1a1a1a",     # Same as bg
    "text": "#ffffff",         # Pure white default text
    "accent": "#00ff88",       # Single accent color (green)
    "success": "#00ff88",      # Same as accent
    "warning": "#ffaa00",      # Amber warning
    "error": "#ff4444",        # Red error
    "border": "#333333",       # Subtle borders/separators
    "dim": "#666666",          # Dimmed text
    "mode_config": {
        "bash": {"symbol": "[BASH]", "color": "#ffffff", "prompt": ">"},
        "chat": {"symbol": "[CHAT]", "color": "#00ff88", "prompt": ">"}, 
        "notes": {"symbol": "[NOTE]", "color": "#ffffff", "prompt": ">"},
        "music": {"symbol": "[MUSIC]", "color": "#ffaa00", "prompt": ">"}
    }
}

# Modern theme (your original)
MODERN_THEME = {
    "name": "Modern Dark",
    "bg": "#0d1117",           
    "console_bg": "#161b22",   
    "entry_bg": "#21262d",     
    "text": "#f0f6fc",         
    "accent": "#58a6ff",       
    "success": "#3fb950",      
    "warning": "#d29922",      
    "error": "#f85149",        
    "border": "#30363d",       
    "dim": "#7d8590",          
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
    "bg": "#000000",           
    "console_bg": "#000000",   
    "entry_bg": "#000000",     
    "text": "#00ff00",         
    "accent": "#00ffff",       
    "success": "#00ff00",      
    "warning": "#ffff00",      
    "error": "#ff0000",        
    "border": "#00ff00",       
    "dim": "#008000",          
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
    "bg": "#1a0f00",           
    "console_bg": "#1a0f00",   
    "entry_bg": "#1a0f00",     
    "text": "#ffb000",         
    "accent": "#ffd700",       
    "success": "#ffb000",      
    "warning": "#ff8c00",      
    "error": "#ff4500",        
    "border": "#ffb000",       
    "dim": "#cc8800",          
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
    "bg": "#000000",           
    "console_bg": "#000000",   
    "entry_bg": "#000000",     
    "text": "#00ff41",         
    "accent": "#41ff00",       
    "success": "#00ff41",      
    "warning": "#ffff00",      
    "error": "#ff0040",        
    "border": "#00ff41",       
    "dim": "#008020",          
    "mode_config": {
        "bash": {"symbol": "[BASH]", "color": "#00ff41", "prompt": ">>"},
        "chat": {"symbol": "[CHAT]", "color": "#41ff00", "prompt": ">>"}, 
        "notes": {"symbol": "[NOTE]", "color": "#00ff41", "prompt": ">>"},
        "music": {"symbol": "[MUSIC]", "color": "#ffff00", "prompt": ">>"}
    }
}

# All available themes
THEMES = {
    "minimal": MINIMAL_THEME,  # New default
    "modern": MODERN_THEME,
    "ascii": ASCII_THEME,
    "amber": AMBER_THEME,
    "matrix": MATRIX_THEME
}

# Current theme (changed to minimal)
current_theme = "minimal"

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