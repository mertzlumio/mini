import os
from tkinter import END
from .audio_engine import get_audio_engine, PlaybackState
from .playlist import get_playlist_manager

def handle_command(cmd, console):
    """Main command handler for music mode"""
    audio_engine = get_audio_engine()
    playlist_manager = get_playlist_manager()
    
    if not audio_engine.is_available():
        console.insert(END, "❌ Audio engine not available. Install pygame: pip install pygame\n", "error")
        return
    
    cmd_lower = cmd.lower().strip()
    parts = cmd.split()
    
    # Playback control commands
    if cmd_lower in ("play", "start"):
        handle_play_command(audio_engine, playlist_manager, console)
        
    elif cmd_lower in ("pause", "stop"):
        handle_pause_stop_command(cmd_lower, audio_engine, console)
        
    elif cmd_lower == "resume":
        handle_resume_command(audio_engine, console)
        
    elif cmd_lower in ("next", "skip", ">>"):
        handle_next_command(audio_engine, playlist_manager, console)
        
    elif cmd_lower in ("prev", "previous", "back", "<<"):
        handle_previous_command(audio_engine, playlist_manager, console)
        
    # Volume control
    elif cmd_lower.startswith("vol") or cmd_lower.startswith("volume"):
        handle_volume_command(parts, audio_engine, console)
        
    # Playlist management
    elif cmd_lower.startswith("add"):
        handle_add_command(parts, playlist_manager, console)
        
    elif cmd_lower in ("playlist", "list", "queue", "ls"):
        display_playlist(playlist_manager, audio_engine, console)
        
    elif cmd_lower.startswith("play "):
        # Play specific track: "play 5" or "play song name"
        handle_play_specific_command(parts[1:], audio_engine, playlist_manager, console)
        
    elif cmd_lower.startswith(("rm ", "remove ", "del ")):
        handle_remove_command(parts[1:], playlist_manager, console)
        
    elif cmd_lower in ("clear", "empty"):
        handle_clear_command(playlist_manager, console)
        
    # Search
    elif cmd_lower.startswith(("find ", "search ")):
        handle_search_command(parts[1:], playlist_manager, console)
        
    # Mode toggles
    elif cmd_lower in ("shuffle", "random"):
        handle_shuffle_command(playlist_manager, console)
        
    elif cmd_lower in ("repeat", "loop"):
        handle_repeat_command(playlist_manager, console)
        
    # Status and info
    elif cmd_lower in ("status", "info", "current"):
        display_status(audio_engine, playlist_manager, console)
        
    elif cmd_lower in ("help", "?"):
        show_music_help(console)
        
    else:
        console.insert(END, f"❓ Unknown music command: {cmd}\n", "warning")
        console.insert(END, "Type 'help' for available commands\n", "dim")

def handle_play_command(audio_engine, playlist_manager, console):
    """Handle play command"""
    current_track = playlist_manager.get_current_track()
    
    if not current_track:
        # No track selected, try to play first track
        if playlist_manager.tracks:
            current_track = playlist_manager.jump_to_track(0)
        else:
            console.insert(END, "📭 No tracks in playlist. Add some music first!\n", "warning")
            console.insert(END, "Use: add ~/Music or add song.mp3\n", "dim")
            return
    
    if audio_engine.get_state() == PlaybackState.PAUSED and audio_engine.get_current_track() == current_track.path:
        # Resume paused track
        if audio_engine.play():
            console.insert(END, f"▶️  Resumed: {current_track.title}\n", "success")
        else:
            console.insert(END, "❌ Failed to resume playback\n", "error")
    else:
        # Load and play new track
        if audio_engine.load_track(current_track.path):
            if audio_engine.play():
                console.insert(END, f"▶️  Playing: {current_track.title}\n", "success")
                console.insert(END, f"   Artist: {current_track.artist}\n", "dim")
            else:
                console.insert(END, "❌ Failed to start playback\n", "error")
        else:
            console.insert(END, f"❌ Failed to load: {current_track.title}\n", "error")

def handle_pause_stop_command(command, audio_engine, console):
    """Handle pause/stop commands"""
    current_state = audio_engine.get_state()
    
    if command == "pause":
        if current_state == PlaybackState.PLAYING:
            if audio_engine.pause():
                track_info = audio_engine.get_track_info()
                console.insert(END, f"⏸️  Paused: {track_info.get('name', 'Unknown')}\n", "accent")
            else:
                console.insert(END, "❌ Failed to pause\n", "error")
        else:
            console.insert(END, "ℹ️  Nothing playing to pause\n", "dim")
    
    elif command == "stop":
        if current_state in (PlaybackState.PLAYING, PlaybackState.PAUSED):
            if audio_engine.stop():
                console.insert(END, "⏹️  Stopped playback\n", "accent")
            else:
                console.insert(END, "❌ Failed to stop\n", "error")
        else:
            console.insert(END, "ℹ️  Nothing playing to stop\n", "dim")

def handle_resume_command(audio_engine, console):
    """Handle resume command"""
    if audio_engine.get_state() == PlaybackState.PAUSED:
        if audio_engine.play():
            track_info = audio_engine.get_track_info()
            console.insert(END, f"▶️  Resumed: {track_info.get('name', 'Unknown')}\n", "success")
        else:
            console.insert(END, "❌ Failed to resume\n", "error")
    else:
        console.insert(END, "ℹ️  Nothing paused to resume\n", "dim")

def handle_next_command(audio_engine, playlist_manager, console):
    """Handle next track command"""
    next_track = playlist_manager.next_track()
    
    if next_track:
        if audio_engine.load_track(next_track.path):
            if audio_engine.play():
                console.insert(END, f"⏭️  Next: {next_track.title}\n", "success")
                console.insert(END, f"   Artist: {next_track.artist}\n", "dim")
            else:
                console.insert(END, "❌ Failed to play next track\n", "error")
        else:
            console.insert(END, f"❌ Failed to load next track: {next_track.title}\n", "error")
    else:
        console.insert(END, "🔚 End of playlist\n", "dim")
        audio_engine.stop()

def handle_previous_command(audio_engine, playlist_manager, console):
    """Handle previous track command"""
    prev_track = playlist_manager.previous_track()
    
    if prev_track:
        if audio_engine.load_track(prev_track.path):
            if audio_engine.play():
                console.insert(END, f"⏮️  Previous: {prev_track.title}\n", "success")
                console.insert(END, f"   Artist: {prev_track.artist}\n", "dim")
            else:
                console.insert(END, "❌ Failed to play previous track\n", "error")
        else:
            console.insert(END, f"❌ Failed to load previous track: {prev_track.title}\n", "error")
    else:
        console.insert(END, "🔚 Beginning of playlist\n", "dim")

def handle_volume_command(parts, audio_engine, console):
    """Handle volume control commands"""
    if len(parts) < 2:
        current_vol = audio_engine.volume
        console.insert(END, f"🔊 Current volume: {current_vol}%\n", "accent")
        console.insert(END, "Usage: vol <0-100>\n", "dim")
        return
    
    try:
        volume = int(parts[1])
        if audio_engine.set_volume(volume):
            console.insert(END, f"🔊 Volume set to {audio_engine.volume}%\n", "success")
        else:
            console.insert(END, "❌ Failed to set volume\n", "error")
    except ValueError:
        console.insert(END, "❌ Volume must be a number (0-100)\n", "error")

def handle_add_command(parts, playlist_manager, console):
    """Handle add track/folder commands"""
    if len(parts) < 2:
        console.insert(END, "Usage: add <file/folder path>\n", "warning")
        console.insert(END, "Examples:\n", "dim")
        console.insert(END, "  add ~/Music\n", "dim")
        console.insert(END, "  add song.mp3\n", "dim")
        console.insert(END, "  add /path/to/album\n", "dim")
        return
    
    path = " ".join(parts[1:])
    path = os.path.expanduser(path)  # Expand ~ to home directory
    
    if os.path.isfile(path):
        # Single file
        if playlist_manager.add_track(path):
            track_name = os.path.basename(path)
            console.insert(END, f"➕ Added: {track_name}\n", "success")
        else:
            console.insert(END, f"❌ Failed to add: {path}\n", "error")
            console.insert(END, f"   (File not found or unsupported format)\n", "dim")
    
    elif os.path.isdir(path):
        # Folder
        console.insert(END, f"🔍 Scanning folder: {path}\n", "dim")
        added_count = playlist_manager.add_folder(path)
        if added_count > 0:
            console.insert(END, f"➕ Added {added_count} tracks from folder\n", "success")
        else:
            console.insert(END, f"❌ No supported audio files found in folder\n", "warning")
    
    else:
        console.insert(END, f"❌ Path not found: {path}\n", "error")

def handle_play_specific_command(parts, audio_engine, playlist_manager, console):
    """Handle play specific track command (by index or name)"""
    if not parts:
        handle_play_command(audio_engine, playlist_manager, console)
        return
    
    query = " ".join(parts)
    
    # Try to parse as track number first
    try:
        track_index = int(query) - 1  # Convert to 0-based
        track = playlist_manager.jump_to_track(track_index)
        if track:
            if audio_engine.load_track(track.path) and audio_engine.play():
                console.insert(END, f"▶️  Playing #{track_index + 1}: {track.title}\n", "success")
            else:
                console.insert(END, f"❌ Failed to play track #{track_index + 1}\n", "error")
        else:
            console.insert(END, f"❌ Track #{track_index + 1} not found\n", "error")
    except ValueError:
        # Not a number, search by name
        matches = playlist_manager.find_tracks(query)
        if matches:
            if len(matches) == 1:
                # Single match, play it
                index, track = matches[0]
                playlist_manager.jump_to_track(index)
                if audio_engine.load_track(track.path) and audio_engine.play():
                    console.insert(END, f"▶️  Playing: {track.title}\n", "success")
                else:
                    console.insert(END, f"❌ Failed to play: {track.title}\n", "error")
            else:
                # Multiple matches, show options
                console.insert(END, f"🔍 Multiple matches for '{query}':\n", "accent")
                for i, (idx, track) in enumerate(matches[:5]):  # Show max 5
                    console.insert(END, f"  {idx + 1}. {track.title} - {track.artist}\n")
                console.insert(END, "Use track number to play specific song\n", "dim")
        else:
            console.insert(END, f"❌ No tracks found matching '{query}'\n", "error")

def handle_remove_command(parts, playlist_manager, console):
    """Handle remove track command"""
    if not parts:
        console.insert(END, "Usage: rm <track number>\n", "warning")
        console.insert(END, "Example: rm 3\n", "dim")
        return
    
    try:
        track_index = int(parts[0]) - 1  # Convert to 0-based
        if playlist_manager.remove_track(track_index):
            console.insert(END, f"🗑️  Removed track #{track_index + 1}\n", "success")
        else:
            console.insert(END, f"❌ Track #{track_index + 1} not found\n", "error")
    except ValueError:
        console.insert(END, "❌ Track number must be a number\n", "error")

def handle_clear_command(playlist_manager, console):
    """Handle clear playlist command"""
    track_count = len(playlist_manager.tracks)
    if track_count > 0:
        playlist_manager.clear_playlist()
        console.insert(END, f"🗑️  Cleared {track_count} tracks from playlist\n", "success")
    else:
        console.insert(END, "📭 Playlist is already empty\n", "dim")

def handle_search_command(parts, playlist_manager, console):
    """Handle search tracks command"""
    if not parts:
        console.insert(END, "Usage: find <search term>\n", "warning")
        return
    
    query = " ".join(parts)
    matches = playlist_manager.find_tracks(query)
    
    if matches:
        console.insert(END, f"🔍 Found {len(matches)} tracks matching '{query}':\n", "accent")
        for idx, track in matches:
            console.insert(END, f"  {idx + 1}. {track.title} - {track.artist}\n")
    else:
        console.insert(END, f"❌ No tracks found matching '{query}'\n", "error")

def handle_shuffle_command(playlist_manager, console):
    """Handle shuffle toggle command"""
    playlist_manager.set_shuffle(not playlist_manager.shuffle_enabled)
    status = "enabled" if playlist_manager.shuffle_enabled else "disabled"
    icon = "🔀" if playlist_manager.shuffle_enabled else "➡️"
    console.insert(END, f"{icon} Shuffle {status}\n", "accent")

def handle_repeat_command(playlist_manager, console):
    """Handle repeat toggle command"""
    playlist_manager.set_repeat(not playlist_manager.repeat_enabled)
    status = "enabled" if playlist_manager.repeat_enabled else "disabled"
    icon = "🔁" if playlist_manager.repeat_enabled else "⏹️"
    console.insert(END, f"{icon} Repeat {status}\n", "accent")

def display_playlist(playlist_manager, audio_engine, console):
    """Display current playlist"""
    tracks = playlist_manager.tracks
    
    if not tracks:
        console.insert(END, "📭 Playlist is empty\n", "dim")
        console.insert(END, "Add music with: add ~/Music\n", "dim")
        return
    
    console.insert(END, f"🎵 Playlist ({len(tracks)} tracks):\n", "accent")
    
    current_track_path = audio_engine.get_current_track()
    current_index = playlist_manager.current_index
    
    # Show up to 10 tracks around current position
    start_idx = max(0, current_index - 5)
    end_idx = min(len(tracks), start_idx + 10)
    
    if start_idx > 0:
        console.insert(END, f"   ... ({start_idx} more above)\n", "dim")
    
    for i in range(start_idx, end_idx):
        track = tracks[i]
        prefix = "▶️ " if i == current_index else "   "
        
        # Format duration if available
        duration_str = ""
        if track.duration > 0:
            minutes = int(track.duration // 60)
            seconds = int(track.duration % 60)
            duration_str = f" ({minutes}:{seconds:02d})"
        
        console.insert(END, f"{prefix}{i + 1}. {track.title} - {track.artist}{duration_str}\n")
    
    if end_idx < len(tracks):
        console.insert(END, f"   ... ({len(tracks) - end_idx} more below)\n", "dim")
    
    # Show playlist status
    status_parts = []
    if playlist_manager.shuffle_enabled:
        status_parts.append("🔀 Shuffle")
    if playlist_manager.repeat_enabled:
        status_parts.append("🔁 Repeat")
    
    if status_parts:
        console.insert(END, f"Status: {' | '.join(status_parts)}\n", "dim")

def display_status(audio_engine, playlist_manager, console):
    """Display current playback status"""
    state = audio_engine.get_state()
    track_info = audio_engine.get_track_info()
    current_track = playlist_manager.get_current_track()
    
    # Playback status
    state_icons = {
        PlaybackState.PLAYING: "▶️",
        PlaybackState.PAUSED: "⏸️", 
        PlaybackState.STOPPED: "⏹️",
        PlaybackState.LOADING: "⏳"
    }
    
    icon = state_icons.get(state, "❓")
    console.insert(END, f"{icon} Status: {state.value.title()}\n", "accent")
    
    if current_track:
        console.insert(END, f"🎵 Track: {current_track.title}\n")
        console.insert(END, f"👤 Artist: {current_track.artist}\n")
        
        # Position info
        if state != PlaybackState.STOPPED:
            position = audio_engine.get_position()
            duration = audio_engine.get_duration()
            
            pos_min, pos_sec = divmod(int(position), 60)
            dur_min, dur_sec = divmod(int(duration), 60) if duration > 0 else (0, 0)
            
            console.insert(END, f"⏱️  Time: {pos_min}:{pos_sec:02d}", "dim")
            if duration > 0:
                console.insert(END, f" / {dur_min}:{dur_sec:02d}")
            console.insert(END, "\n")
    
    # Playlist info
    playlist_info = playlist_manager.get_playlist_info()
    console.insert(END, f"📋 Playlist: {playlist_info['current_index'] + 1}/{playlist_info['total_tracks']}\n", "dim")
    console.insert(END, f"🔊 Volume: {audio_engine.volume}%\n", "dim")

def show_music_help(console):
    """Display music mode help"""
    help_text = """
🎵 Music Player Commands:

Playback Control:
  play              - Play current/first track
  play <number>     - Play specific track by number
  play <name>       - Search and play track by name
  pause             - Pause playback
  resume            - Resume paused track
  stop              - Stop playback
  next, >>          - Next track
  prev, <<          - Previous track

Volume:
  vol <0-100>       - Set volume (0-100)
  vol               - Show current volume

Playlist Management:
  add <path>        - Add file or folder
  playlist, list    - Show playlist
  rm <number>       - Remove track by number
  clear             - Clear entire playlist
  find <term>       - Search tracks

Modes:
  shuffle           - Toggle shuffle mode
  repeat            - Toggle repeat mode

Info:
  status            - Show playback status
  help              - Show this help

Examples:
  add ~/Music
  play 5
  vol 50
  find beethoven
"""
    console.insert(END, help_text, "dim")