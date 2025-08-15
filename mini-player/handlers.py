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
is_chat_first_visit = True # Track first visit to chat mode
is_ai_replying = False # State lock for chat mode

def toggle_mode(consoles, mode_status_label, prompt_label, theme=None):
    """Switch to the next mode and lift its console to the top."""
    global mode_index, mode, is_chat_first_visit
    mode_index = (mode_index + 1) % len(modes)
    mode = modes[mode_index]
    
    # Get the active console and lift it
    active_console = consoles.get(mode)
    if active_console:
        active_console.lift()
    
    # Get current theme config
    if theme is None:
        theme = get_current_theme()
    
    config = theme["mode_config"][mode]
    
    # Update UI elements for the new mode
    mode_status_label.config(text=f"{config['symbol']} Ready", fg=config['color'])
    prompt_label.config(text=config['prompt'], fg=config['color'])
    
    # Refresh content or show welcome message
    if mode == "notes":
        display_notes(active_console)
    elif mode == "music":
        display_music_status(active_console)
    elif mode == "chat" and is_chat_first_visit:
        if active_console:
            active_console.insert(END, ">> Mini here... what do we do today?\n", "accent")
        is_chat_first_visit = False # Ensure message only appears once per session
    
    if active_console:
        active_console.see(END)
        
    return mode # Return the new mode name


def update_status(mode_status_label, status_text, mode_override=None):
    """Update the status part of the integrated label"""
    global mode
    current_mode = mode_override or mode
    theme = get_current_theme()
    config = theme["mode_config"][current_mode]
    
    # Update with mode + status
    mode_status_label.config(text=f"{config['symbol']} {status_text}", fg=config['color'])

def on_ai_reply_complete():
    """Callback to reset the AI replying state."""
    global is_ai_replying
    is_ai_replying = False

def on_enter(entry, get_active_console, mode_status_label):
    """Dispatches command to the active mode's console."""
    global history, history_index, current_dir, mode, is_ai_replying
    
    # For chat mode, check the state lock
    if mode == "chat" and is_ai_replying:
        # Optionally provide feedback that the AI is busy
        # For now, we just ignore the input
        return

    cmd = entry.get().strip()
    if not cmd:
        return

    console = get_active_console() # Get the currently visible console
    if not console:
        print("Error: No active console found.")
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
        is_ai_replying = True # Lock the state
        # Pass the callback to the handler
        chat_core.handle_command(cmd, console, mode_status_label, entry, on_ai_reply_complete)
            
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
    console.delete('1.0', END) # Clear previous content
    notes = notes_core.get_notes()
    if not notes:
        console.insert(END, "  (no tasks yet)\n", "dim")
        return
        
    for i, note in enumerate(notes, 1):
        console.insert(END, f"  {i}. {note}\n")
    
    console.insert(END, f"\nTotal: {len(notes)} task{'s' if len(notes) != 1 else ''}\n", "dim")

def display_music_status(console):
    """Display music player status"""
    console.delete('1.0', END) # Clear previous content
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
        
        console.insert(END, ">> Music Player Ready\n", "accent")
        
        if current_track:
            console.insert(END, f"Current: {current_track.title}\n", "dim")
            console.insert(END, f"Status: {state.value.title()}\n", "dim")
        
        track_count = playlist_info['total_tracks']
        if track_count > 0:
            console.insert(END, f"Playlist: {track_count} track{'s' if track_count != 1 else ''}\n", "dim")
        else:
            console.insert(END, "Playlist empty - use 'add ~/Music'\n", "dim")
            
        console.insert(END, "\nType 'help' for commands\n", "dim")
        
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
