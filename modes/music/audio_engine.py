import pygame
import threading
import time
import os
from enum import Enum
from typing import Optional, Callable

class PlaybackState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"

class AudioEngine:
    """
    Pygame-based audio engine for music playback
    Supports MP3, WAV, OGG formats with threading for non-blocking operation
    """
    
    def __init__(self):
        self.initialized = False
        self.current_track = None
        self.state = PlaybackState.STOPPED
        self.volume = 70  # 0-100
        self.position = 0.0  # Current position in seconds
        self.duration = 0.0  # Track duration in seconds
        self.position_thread = None
        self.position_running = False
        
        # Callbacks
        self.on_track_finished = None
        self.on_state_changed = None
        self.on_position_changed = None
        
        self._initialize_pygame()
    
    def _initialize_pygame(self):
        """Initialize pygame mixer"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.initialized = True
            print("Audio engine initialized successfully")
        except Exception as e:
            print(f"Failed to initialize audio engine: {e}")
            self.initialized = False
    
    def is_available(self) -> bool:
        """Check if audio engine is ready"""
        return self.initialized
    
    def load_track(self, file_path: str) -> bool:
        """
        Load an audio track for playback
        Returns True if successful, False otherwise
        """
        if not self.initialized:
            return False
        
        if not os.path.exists(file_path):
            print(f"Audio file not found: {file_path}")
            return False
        
        try:
            self._set_state(PlaybackState.LOADING)
            pygame.mixer.music.load(file_path)
            self.current_track = file_path
            self.position = 0.0
            self.duration = self._get_track_duration(file_path)
            self._set_state(PlaybackState.STOPPED)
            return True
        except Exception as e:
            print(f"Failed to load track: {e}")
            self._set_state(PlaybackState.STOPPED)
            return False
    
    def play(self, start_pos: float = 0.0) -> bool:
        """
        Start playback from specified position (in seconds)
        """
        if not self.initialized or not self.current_track:
            return False
        
        try:
            if self.state == PlaybackState.PAUSED:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.play(start=start_pos)
                self.position = start_pos
            
            self._set_state(PlaybackState.PLAYING)
            self._start_position_tracking()
            return True
        except Exception as e:
            print(f"Failed to start playback: {e}")
            return False
    
    def pause(self) -> bool:
        """Pause playback"""
        if not self.initialized or self.state != PlaybackState.PLAYING:
            return False
        
        try:
            pygame.mixer.music.pause()
            self._set_state(PlaybackState.PAUSED)
            self._stop_position_tracking()
            return True
        except Exception as e:
            print(f"Failed to pause playback: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop playback and reset position"""
        if not self.initialized:
            return False
        
        try:
            pygame.mixer.music.stop()
            self.position = 0.0
            self._set_state(PlaybackState.STOPPED)
            self._stop_position_tracking()
            return True
        except Exception as e:
            print(f"Failed to stop playback: {e}")
            return False
    
    def set_volume(self, volume: int) -> bool:
        """
        Set playback volume (0-100)
        """
        if not self.initialized:
            return False
        
        try:
            volume = max(0, min(100, volume))  # Clamp to 0-100
            pygame_volume = volume / 100.0
            pygame.mixer.music.set_volume(pygame_volume)
            self.volume = volume
            return True
        except Exception as e:
            print(f"Failed to set volume: {e}")
            return False
    
    def seek(self, position: float) -> bool:
        """
        Seek to specific position in seconds
        Note: pygame doesn't support seeking directly, so this reloads the track
        """
        if not self.initialized or not self.current_track:
            return False
        
        if position < 0 or position > self.duration:
            return False
        
        was_playing = self.state == PlaybackState.PLAYING
        
        try:
            self.stop()
            if self.load_track(self.current_track):
                if was_playing:
                    return self.play(position)
                else:
                    self.position = position
                    return True
        except Exception as e:
            print(f"Failed to seek: {e}")
            return False
    
    def get_position(self) -> float:
        """Get current playback position in seconds"""
        return self.position
    
    def get_duration(self) -> float:
        """Get track duration in seconds"""
        return self.duration
    
    def get_state(self) -> PlaybackState:
        """Get current playback state"""
        return self.state
    
    def get_current_track(self) -> Optional[str]:
        """Get currently loaded track path"""
        return self.current_track
    
    def get_track_info(self) -> dict:
        """Get information about current track"""
        if not self.current_track:
            return {}
        
        filename = os.path.basename(self.current_track)
        name, ext = os.path.splitext(filename)
        
        return {
            "path": self.current_track,
            "filename": filename,
            "name": name,
            "format": ext.upper()[1:] if ext else "Unknown",
            "duration": self.duration,
            "position": self.position,
            "state": self.state.value
        }
    
    def _get_track_duration(self, file_path: str) -> float:
        """
        Get track duration - simplified version
        For more accurate duration, could use mutagen library
        """
        try:
            # This is a rough estimation method
            # In a full implementation, you'd use mutagen or similar
            # For now, return a default duration
            return 180.0  # 3 minutes default
        except Exception:
            return 0.0
    
    def _set_state(self, new_state: PlaybackState):
        """Internal state setter with callback"""
        old_state = self.state
        self.state = new_state
        
        if self.on_state_changed and old_state != new_state:
            try:
                self.on_state_changed(old_state, new_state)
            except Exception as e:
                print(f"State change callback error: {e}")
    
    def _start_position_tracking(self):
        """Start background thread for position tracking"""
        if self.position_thread and self.position_running:
            return
        
        self.position_running = True
        self.position_thread = threading.Thread(target=self._position_tracker, daemon=True)
        self.position_thread.start()
    
    def _stop_position_tracking(self):
        """Stop position tracking thread"""
        self.position_running = False
        if self.position_thread:
            self.position_thread.join(timeout=1.0)
    
    def _position_tracker(self):
        """Background thread for tracking playback position"""
        while self.position_running and self.state == PlaybackState.PLAYING:
            if pygame.mixer.music.get_busy():
                self.position += 0.1
                
                # Check if track finished
                if self.duration > 0 and self.position >= self.duration:
                    self.position = self.duration
                    self._set_state(PlaybackState.STOPPED)
                    if self.on_track_finished:
                        try:
                            self.on_track_finished()
                        except Exception as e:
                            print(f"Track finished callback error: {e}")
                    break
                
                # Position callback
                if self.on_position_changed:
                    try:
                        self.on_position_changed(self.position)
                    except Exception as e:
                        print(f"Position callback error: {e}")
                        
            else:
                # Track finished naturally
                self._set_state(PlaybackState.STOPPED)
                if self.on_track_finished:
                    try:
                        self.on_track_finished()
                    except Exception as e:
                        print(f"Track finished callback error: {e}")
                break
            
            time.sleep(0.1)
        
        self.position_running = False
    
    def cleanup(self):
        """Cleanup resources"""
        self._stop_position_tracking()
        if self.initialized:
            try:
                pygame.mixer.quit()
            except Exception as e:
                print(f"Cleanup error: {e}")
        
        self.initialized = False

# Global audio engine instance
_audio_engine = None

def get_audio_engine() -> AudioEngine:
    """Get or create global audio engine instance"""
    global _audio_engine
    if _audio_engine is None:
        _audio_engine = AudioEngine()
    return _audio_engine

def cleanup_audio_engine():
    """Cleanup global audio engine"""
    global _audio_engine
    if _audio_engine:
        _audio_engine.cleanup()
        _audio_engine = None