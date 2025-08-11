# modes/chat/capabilities/visual_assistant.py
import os
import base64
import time
from datetime import datetime
from PIL import ImageGrab, Image
import io

from config import SCREENSHOTS_DIR

class VisualAssistant:
    def __init__(self, screenshots_dir=SCREENSHOTS_DIR):
        self.screenshots_dir = screenshots_dir
        os.makedirs(screenshots_dir, exist_ok=True)
        self.last_screenshot = None
        self.last_screenshot_time = None
    
    def take_screenshot(self, region=None, save=True, quality=85):
        """
        Take a screenshot optimized for API usage
        Args:
            region: tuple (x1, y1, x2, y2) for specific region, None for full screen
            save: bool, whether to save to file
            quality: int, JPEG quality (1-100) for compression
        Returns:
            dict with image data and metadata
        """
        try:
            # Take screenshot
            if region:
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()
            
            # Resize if too large (API limits)
            max_dimension = 1024  # Reasonable size for API
            if screenshot.width > max_dimension or screenshot.height > max_dimension:
                ratio = min(max_dimension / screenshot.width, max_dimension / screenshot.height)
                new_size = (int(screenshot.width * ratio), int(screenshot.height * ratio))
                screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Save if requested
            if save:
                screenshot.save(filepath, "PNG", optimize=True)
            
            # Convert to base64 for API usage (use JPEG for smaller size)
            buffer = io.BytesIO()
            # Convert to RGB if RGBA (for JPEG)
            if screenshot.mode == 'RGBA':
                screenshot = screenshot.convert('RGB')
            screenshot.save(buffer, format='JPEG', quality=quality, optimize=True)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Cache for potential reuse
            self.last_screenshot = img_base64
            self.last_screenshot_time = time.time()
            
            return {
                "success": True,
                "filepath": filepath if save else None,
                "filename": filename,
                "base64": img_base64,
                "size": screenshot.size,
                "timestamp": timestamp,
                "file_size_kb": round(len(img_base64) * 3 / 4 / 1024, 2)  # Approx base64 to bytes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_cached_screenshot(self, max_age_seconds=30):
        """Get last screenshot if recent enough"""
        if (self.last_screenshot and self.last_screenshot_time and 
            time.time() - self.last_screenshot_time <= max_age_seconds):
            return self.last_screenshot
        return None
    
    def take_region_screenshot(self, x1, y1, x2, y2, save=True):
        """Take screenshot of specific region"""
        return self.take_screenshot(region=(x1, y1, x2, y2), save=save)

# Global instance
_visual_assistant = None

def get_visual_assistant():
    """Get or create visual assistant instance"""
    global _visual_assistant
    if _visual_assistant is None:
        _visual_assistant = VisualAssistant()
    return _visual_assistant

def capture_screen_context(region=None, save_screenshot=True):
    """
    Capture screen context for AI analysis
    
    Args:
        region: Optional region tuple (x1, y1, x2, y2)
        save_screenshot: Whether to save screenshot to disk
        
    Returns:
        str: Result message for the AI
    """
    try:
        assistant = get_visual_assistant()
        result = assistant.take_screenshot(region=region, save=save_screenshot, quality=75)
        
        if result["success"]:
            return f"✅ Screen captured ({result['file_size_kb']}KB, {result['size'][0]}x{result['size'][1]}). Image ready for analysis."
        else:
            return f"❌ Failed to capture screenshot: {result['error']}"
            
    except Exception as e:
        return f"❌ Error capturing screen: {str(e)}"

def get_screen_dimensions():
    """Get current screen dimensions"""
    try:
        screenshot = ImageGrab.grab()
        width, height = screenshot.size
        return f"Screen dimensions: {width}x{height} pixels"
    except Exception as e:
        return f"Error getting screen dimensions: {str(e)}"

def analyze_screen_region(x1, y1, x2, y2):
    """Capture and prepare analysis for a specific screen region"""
    try:
        assistant = get_visual_assistant()
        result = assistant.take_region_screenshot(x1, y1, x2, y2, save=True)
        
        if result["success"]:
            return f"✅ Region captured ({x1},{y1} to {x2},{y2}) - {result['file_size_kb']}KB. Ready for analysis."
        else:
            return f"❌ Failed to capture region: {result['error']}"
    except Exception as e:
        return f"❌ Error capturing region: {str(e)}"