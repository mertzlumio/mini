import os
import json
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from config import CHAT_HISTORY_DIR

@dataclass
class Track:
    """Represents a music track"""
    path: str
    filename: str
    title: str
    artist: str = "Unknown Artist"
    album: str = "Unknown Album"
    duration: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "filename": self.filename,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    
    @classmethod
    def from_file(cls, file_path: str):
        """Create track from file path with basic metadata"""
        path = Path(file_path)
        filename = path.name
        title = path.stem
        
        # Try to extract artist and title from filename
        # Common patterns: "Artist - Title.mp3", "Title - Artist.mp3"
        if " - " in title:
            parts = title.split(" - ", 1)
            if len(parts) == 2:
                # Assume "Artist - Title" format
                artist, title = parts[0].strip(), parts[1].strip()
            else:
                artist = "Unknown Artist"
        else:
            artist = "Unknown Artist"
        
        return cls(
            path=str(path),
            filename=filename,
            title=title,
            artist=artist
        )

class PlaylistManager:
    """Manages playlists and track collections"""
    
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
    
    def __init__(self):
        # Create music data directory
        self.music_dir = os.path.join(CHAT_HISTORY_DIR, 'music')
        os.makedirs(self.music_dir, exist_ok=True)
        
        self.playlist_file = os.path.join(self.music_dir, 'playlist.json')
        self.state_file = os.path.join(self.music_dir, 'player_state.json')
        
        # Playlist state
        self.tracks: List[Track] = []
        self.current_index = -1
        self.shuffle_enabled = False
        self.repeat_enabled = False
        self.shuffle_history: List[int] = []
        
        # Load saved data
        self.load_playlist()
        self.load_state()
    
    def add_track(self, file_path: str) -> bool:
        """Add a single track to playlist"""
        if not os.path.exists(file_path):
            return False
        
        # Check if file is supported audio format
        ext = Path(file_path).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            return False
        
        # Check if already in playlist
        if any(track.path == file_path for track in self.tracks):
            return False
        
        track = Track.from_file(file_path)
        self.tracks.append(track)
        self.save_playlist()
        return True
    
    def add_folder(self, folder_path: str) -> int:
        """
        Add all supported audio files from folder recursively
        Returns number of files added
        """
        if not os.path.exists(folder_path):
            return 0
        
        added_count = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if self.add_track(file_path):
                    added_count += 1
        
        return added_count
    
    def remove_track(self, index: int) -> bool:
        """Remove track by index"""
        if 0 <= index < len(self.tracks):
            removed_track = self.tracks.pop(index)
            
            # Adjust current index if needed
            if index < self.current_index:
                self.current_index -= 1
            elif index == self.current_index:
                # Current track was removed
                if self.current_index >= len(self.tracks):
                    self.current_index = len(self.tracks) - 1
            
            self.save_playlist()
            return True
        return False
    
    def clear_playlist(self):
        """Clear all tracks"""
        self.tracks.clear()
        self.current_index = -1
        self.shuffle_history.clear()
        self.save_playlist()
    
    def get_current_track(self) -> Optional[Track]:
        """Get currently selected track"""
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    
    def next_track(self) -> Optional[Track]:
        """Move to next track based on shuffle/repeat settings"""
        if not self.tracks:
            return None
        
        if self.shuffle_enabled:
            return self._next_shuffle_track()
        else:
            return self._next_sequential_track()
    
    def previous_track(self) -> Optional[Track]:
        """Move to previous track"""
        if not self.tracks:
            return None
        
        if self.shuffle_enabled:
            return self._previous_shuffle_track()
        else:
            return self._previous_sequential_track()
    
    def jump_to_track(self, index: int) -> Optional[Track]:
        """Jump to specific track by index"""
        if 0 <= index < len(self.tracks):
            self.current_index = index
            self.save_state()
            return self.tracks[index]
        return None
    
    def find_tracks(self, query: str) -> List[tuple]:
        """
        Find tracks matching query (search in title, artist, filename)
        Returns list of (index, track) tuples
        """
        results = []
        query_lower = query.lower()
        
        for i, track in enumerate(self.tracks):
            if (query_lower in track.title.lower() or 
                query_lower in track.artist.lower() or 
                query_lower in track.filename.lower()):
                results.append((i, track))
        
        return results
    
    def get_playlist_info(self) -> dict:
        """Get comprehensive playlist information"""
        total_duration = sum(track.duration for track in self.tracks)
        
        return {
            "total_tracks": len(self.tracks),
            "current_index": self.current_index,
            "current_track": self.get_current_track().to_dict() if self.get_current_track() else None,
            "total_duration": total_duration,
            "shuffle_enabled": self.shuffle_enabled,
            "repeat_enabled": self.repeat_enabled,
            "supported_formats": list(self.SUPPORTED_FORMATS)
        }
    
    def set_shuffle(self, enabled: bool):
        """Enable/disable shuffle mode"""
        self.shuffle_enabled = enabled
        if enabled:
            self.shuffle_history.clear()
        self.save_state()
    
    def set_repeat(self, enabled: bool):
        """Enable/disable repeat mode"""
        self.repeat_enabled = enabled
        self.save_state()
    
    def _next_sequential_track(self) -> Optional[Track]:
        """Get next track in sequential order"""
        if self.current_index + 1 < len(self.tracks):
            self.current_index += 1
        elif self.repeat_enabled:
            self.current_index = 0
        else:
            # End of playlist
            return None
        
        self.save_state()
        return self.tracks[self.current_index]
    
    def _previous_sequential_track(self) -> Optional[Track]:
        """Get previous track in sequential order"""
        if self.current_index > 0:
            self.current_index -= 1
        elif self.repeat_enabled:
            self.current_index = len(self.tracks) - 1
        else:
            # Beginning of playlist
            return None
        
        self.save_state()
        return self.tracks[self.current_index]
    
    def _next_shuffle_track(self) -> Optional[Track]:
        """Get next track in shuffle mode"""
        if len(self.tracks) <= 1:
            return self.get_current_track()
        
        # Add current track to history
        if self.current_index >= 0:
            self.shuffle_history.append(self.current_index)
        
        # Get unplayed tracks
        unplayed = [i for i in range(len(self.tracks)) 
                   if i not in self.shuffle_history and i != self.current_index]
        
        if not unplayed:
            if self.repeat_enabled:
                # Reset shuffle history and start over
                self.shuffle_history.clear()
                unplayed = [i for i in range(len(self.tracks)) if i != self.current_index]
            else:
                # End of shuffle playlist
                return None
        
        # Pick random unplayed track
        self.current_index = random.choice(unplayed)
        self.save_state()
        return self.tracks[self.current_index]
    
    def _previous_shuffle_track(self) -> Optional[Track]:
        """Get previous track from shuffle history"""
        if self.shuffle_history:
            self.current_index = self.shuffle_history.pop()
            self.save_state()
            return self.tracks[self.current_index]
        return None
    
    def save_playlist(self):
        """Save playlist to file"""
        try:
            data = {
                "tracks": [track.to_dict() for track in self.tracks],
                "created": "Generated by Mini Player"
            }
            
            with open(self.playlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Failed to save playlist: {e}")
    
    def load_playlist(self):
        """Load playlist from file"""
        try:
            if os.path.exists(self.playlist_file):
                with open(self.playlist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.tracks = [Track.from_dict(track_data) 
                              for track_data in data.get("tracks", [])]
                
                # Validate that files still exist
                valid_tracks = []
                for track in self.tracks:
                    if os.path.exists(track.path):
                        valid_tracks.append(track)
                
                if len(valid_tracks) != len(self.tracks):
                    self.tracks = valid_tracks
                    self.save_playlist()  # Save cleaned playlist
                    
        except Exception as e:
            print(f"Failed to load playlist: {e}")
            self.tracks = []
    
    def save_state(self):
        """Save player state (current track, shuffle, repeat)"""
        try:
            state_data = {
                "current_index": self.current_index,
                "shuffle_enabled": self.shuffle_enabled,
                "repeat_enabled": self.repeat_enabled,
                "shuffle_history": self.shuffle_history
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save player state: {e}")
    
    def load_state(self):
        """Load player state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                self.current_index = state_data.get("current_index", -1)
                self.shuffle_enabled = state_data.get("shuffle_enabled", False)
                self.repeat_enabled = state_data.get("repeat_enabled", False)
                self.shuffle_history = state_data.get("shuffle_history", [])
                
                # Validate current index
                if self.current_index >= len(self.tracks):
                    self.current_index = len(self.tracks) - 1
                    
        except Exception as e:
            print(f"Failed to load player state: {e}")

# Global playlist manager instance
_playlist_manager = None

def get_playlist_manager() -> PlaylistManager:
    """Get or create global playlist manager instance"""
    global _playlist_manager
    if _playlist_manager is None:
        _playlist_manager = PlaylistManager()
    return _playlist_manager