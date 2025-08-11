from tkinter import END
import os
from modes.bash import core as bash_core
from modes.chat import core as chat_core
from modes.notes import core as notes_core
from modes.music import core as music_core
from themes import get_current_theme

history = []
history_index = -1
current_dir = os.getcwd()
modes = ["bash", "chat", "notes", "music"]
mode_index = 0
mode = modes[mode_index]

def toggle_mode(entry, console, mode_status_label, status_label, prompt_label, theme=None):
    """Enhanced mode switching for integrated header"""
    global mode_index, mode
    mode_index = (mode_index + 1) % len(modes)
    mode = modes[mode_index]
    
    # Get current theme config
    if theme is None:
        theme = get_current_theme()
    
    config = theme["mode_config"][mode]
    
    # Update integrated mode/status label
    mode_status_label.config(text=f"{config['symbol']} Ready", fg=config['color'])
    prompt_label.config(text=config['prompt'], fg=config['color'])
    
    console.insert(END, f"\n>> Mode: {config['symbol']}\n", "accent")
    
    if mode == "notes":
        display_notes(console)
    elif mode == "music":
        display_music_status(console)
    
    console.see(END)
    return "break"

def update_status(mode_status_label, status_text, mode_override=None):
    """Update the status part of the integrated label"""
    global mode
    current_mode = mode_override or mode
    theme = get_current_theme()
    config = theme["mode_config"][current_mode]
    
    # Update with mode + status
    mode_status_label.config(text=f"{config['symbol']} {status_text}", fg=config['color'])

def on_enter(entry, console, mode_status_label, status_label):
    """Dispatches command with integrated status updates"""
    global history, history_index, current_dir, mode
    
    cmd = entry.get().strip()
    if not cmd:
        return

    # Check for theme commands first
    if cmd.startswith("/theme "):
        theme_name = cmd.split(maxsplit=1)[1]
        from themes import switch_theme, get_available_themes
        if switch_theme(theme_name):
            console.insert(END, f"\n> {cmd}\n", "dim")
            console.insert(END, f"🎨 Switched to {theme_name} theme\n", "accent")
            console.insert(END, "Restart app to see full theme changes\n", "dim")
        else:
            console.insert(END, f"\n> {cmd}\n", "dim")
            themes_list = ", ".join(get_available_themes())
            console.insert(END, f"❌ Unknown theme. Available: {themes_list}\n", "error")
        console.see(END)
        entry.delete(0, END)
        return
    
    if cmd == "/themes":
        console.insert(END, f"\n> {cmd}\n", "dim")
        from themes import get_available_themes, get_theme_info
        console.insert(END, f"{get_theme_info()}\n", "accent")
        themes_list = ", ".join(get_available_themes())
        console.insert(END, f"Available themes: {themes_list}\n", "dim")
        console.insert(END, "Usage: /theme <name> (restart to apply)\n", "dim")
        console.see(END)
        entry.delete(0, END)
        return

    history.append(cmd)
    history_index = len(history)
    
    console.insert(END, f"\n> {cmd}\n", "dim")
    
    if mode == "bash":
        update_status(mode_status_label, "Running...")
        output, new_dir = bash_core.handle_command(cmd, current_dir)
        current_dir = new_dir
        console.insert(END, output + "\n")
        update_status(mode_status_label, "Ready")
        
    elif mode == "chat":
        # Chat handler manages its own status updates
        chat_core.handle_command(cmd, console, mode_status_label, entry)
            
    elif mode == "notes":
        update_status(mode_status_label, "Processing...")
        notes_core.handle_command(cmd, console)
        update_status(mode_status_label, "Ready")
        
    elif mode == "music":
        update_status(mode_status_label, "Processing...")
        music_core.handle_command(cmd, console)
        update_status(mode_status_label, "Ready")

    console.see(END)
    entry.delete(0, END)

def display_notes(console):
    """Clean notes display - theme-agnostic"""
    notes = notes_core.get_notes()
    if not notes:
        console.insert(END, "  (no tasks yet)\n", "dim")
        return
        
    for i, note in enumerate(notes, 1):
        console.insert(END, f"  {i}. {note}\n")
    
    console.insert(END, f"\nTotal: {len(notes)} task{'s' if len(notes) != 1 else ''}\n", "dim")

def display_music_status(console):
    """Display music player status"""
    try:
        from modes.music.audio_engine import get_audio_engine
        from modes.music.playlist import get_playlist_manager
        
        audio_engine = get_audio_engine()
        playlist_manager = get_playlist_manager()
        
        if not audio_engine.is_available():
            console.insert(END, "🎵 Music Player (pygame required)\n", "warning")
            console.insert(END, "  Install: pip install pygame\n", "dim")
            return
        
        # Show quick status
        state = audio_engine.get_state()
        current_track = playlist_manager.get_current_track()
        playlist_info = playlist_manager.get_playlist_info()
        
        console.insert(END, f"Music Player Ready\n", "accent")
        
        if current_track:
            console.insert(END, f"Current: {current_track.title}\n", "dim")
            console.insert(END, f"Status: {state.value.title()}\n", "dim")
        
        track_count = playlist_info['total_tracks']
        if track_count > 0:
            console.insert(END, f"Playlist: {track_count} track{'s' if track_count != 1 else ''}\n", "dim")
        else:
            console.insert(END, "Playlist empty - use 'add ~/Music'\n", "dim")
            
        console.insert(END, "Type 'help' for commands\n", "dim")
        
    except ImportError as e:
        console.insert(END, "Music Player (dependencies missing)\n", "warning")
        console.insert(END, f"Error: {str(e)}\n", "dim")
    except Exception as e:
        console.insert(END, "Music Player (initialization error)\n", "error")
        console.insert(END, f"Error: {str(e)}\n", "dim")

def on_up(entry):
    global history_index
    if history and history_index > 0:
        history_index -= 1
        entry.delete(0, END)
        entry.insert(0, history[history_index])
    return "break"

def on_down(entry):
    global history_index
    if history:
        if history_index < len(history) - 1:
            history_index += 1
            entry.delete(0, END)
            entry.insert(0, history[history_index])
        else:
            history_index = len(history)
            entry.delete(0, END)
    return "break"