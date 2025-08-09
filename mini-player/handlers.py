from tkinter import END
import os
from modes.bash import core as bash_core
from modes.chat import core as chat_core
from modes.notes import core as notes_core
from modes.music import core as music_core

history = []
history_index = -1
current_dir = os.getcwd()
modes = ["bash", "chat", "notes", "music"]
mode_index = 0
mode = modes[mode_index]

# Mode colors and symbols
MODE_CONFIG = {
    "bash": {"symbol": "[BASH]", "color": "#f0f6fc"},
    "chat": {"symbol": "[CHAT]", "color": "#58a6ff"}, 
    "notes": {"symbol": "[NOTE]", "color": "#3fb950"},
    "music": {"symbol": "[MUSIC]", "color": "#d29922"}
}

def toggle_mode(entry, console, mode_label, status_label, prompt_label):
    """Enhanced mode switching with visual feedback"""
    global mode_index, mode
    mode_index = (mode_index + 1) % len(modes)
    mode = modes[mode_index]
    
    config = MODE_CONFIG[mode]
    mode_label.config(text=config['symbol'])
    prompt_label.config(fg=config['color'])
    status_label.config(text=f"Switched to {mode}")
    
    console.insert(END, f"\n>> Mode: {config['symbol']}\n", "accent")
    
    if mode == "notes":
        display_notes(console)
    elif mode == "music":
        display_music_status(console)
    
    console.see(END)
    return "break"

def on_enter(entry, console, mode_label, status_label):
    """Dispatches command to the active mode's handler."""
    global history, history_index, current_dir, mode
    
    cmd = entry.get().strip()
    if not cmd:
        return

    history.append(cmd)
    history_index = len(history)
    
    console.insert(END, f"\n> {cmd}\n", "dim")
    
    if mode == "bash":
        output, new_dir = bash_core.handle_command(cmd, current_dir)
        current_dir = new_dir
        console.insert(END, output + "\n")
        status_label.config(text="Ready")
        
    elif mode == "chat":
        chat_core.handle_command(cmd, console, status_label, entry)
            
    elif mode == "notes":
        notes_core.handle_command(cmd, console)
        status_label.config(text="Ready")
        
    elif mode == "music":
        music_core.handle_command(cmd, console)
        status_label.config(text="Ready")

    console.see(END)
    entry.delete(0, END)

def display_notes(console):
    """Clean notes display with numbering"""
    notes = notes_core.get_notes()
    if not notes:
        console.insert(END, "  (no tasks yet)\n", "dim")
        return
        
    for i, note in enumerate(notes, 1):
        console.insert(END, f"  {i}. {note}\n")
    
    console.insert(END, f"\nTotal: {len(notes)} task{'s' if len(notes) != 1 else ''}\n", "dim")

def display_music_status(console):
    """Display music player status when switching to music mode"""
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
        
        console.insert(END, f"🎵 Music Player Ready\n", "accent")
        
        if current_track:
            console.insert(END, f"  Current: {current_track.title}\n", "dim")
            console.insert(END, f"  Status: {state.value.title()}\n", "dim")
        
        track_count = playlist_info['total_tracks']
        if track_count > 0:
            console.insert(END, f"  Playlist: {track_count} track{'s' if track_count != 1 else ''}\n", "dim")
        else:
            console.insert(END, "  Playlist empty - use 'add ~/Music'\n", "dim")
            
        console.insert(END, "  Type 'help' for commands\n", "dim")
        
    except ImportError as e:
        console.insert(END, "🎵 Music Player (dependencies missing)\n", "warning")
        console.insert(END, f"  Error: {str(e)}\n", "dim")
    except Exception as e:
        console.insert(END, "🎵 Music Player (initialization error)\n", "error")
        console.insert(END, f"  Error: {str(e)}\n", "dim")

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