import os
import base64
import time
from datetime import datetime
from PIL import ImageGrab, Image
import io

class VisualAssistant:
    def __init__(self, screenshots_dir="screenshots"):
        self.screenshots_dir = screenshots_dir
        os.makedirs(screenshots_dir, exist_ok=True)
    
    def take_screenshot(self, region=None, save=True):
        """
        Take a screenshot
        Args:
            region: tuple (x1, y1, x2, y2) for specific region, None for full screen
            save: bool, whether to save to file
        Returns:
            dict with image path, base64 data, and metadata
        """
        try:
            # Take screenshot
            if region:
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Save if requested
            if save:
                screenshot.save(filepath)
            
            # Convert to base64 for API usage
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "filepath": filepath if save else None,
                "filename": filename,
                "base64": img_base64,
                "size": screenshot.size,
                "timestamp": timestamp
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_screen_info(self):
        """Get screen dimensions and info"""
        try:
            # Get screen size using PIL
            screenshot = ImageGrab.grab()
            width, height = screenshot.size
            
            return {
                "success": True,
                "width": width,
                "height": height,
                "total_pixels": width * height
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def take_region_screenshot(self, x1, y1, x2, y2, save=True):
        """Take screenshot of specific region"""
        return self.take_screenshot(region=(x1, y1, x2, y2), save=save)
    
    def list_screenshots(self, limit=10):
        """List recent screenshots"""
        try:
            files = os.listdir(self.screenshots_dir)
            screenshot_files = [f for f in files if f.startswith('screenshot_') and f.endswith('.png')]
            screenshot_files.sort(reverse=True)  # Most recent first
            
            recent_files = screenshot_files[:limit]
            
            result = []
            for filename in recent_files:
                filepath = os.path.join(self.screenshots_dir, filename)
                stat = os.stat(filepath)
                result.append({
                    "filename": filename,
                    "filepath": filepath,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return {
                "success": True,
                "screenshots": result,
                "total_count": len(screenshot_files)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_old_screenshots(self, keep_days=7):
        """Remove screenshots older than specified days"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (keep_days * 24 * 60 * 60)
            
            files = os.listdir(self.screenshots_dir)
            removed_count = 0
            
            for filename in files:
                if filename.startswith('screenshot_') and filename.endswith('.png'):
                    filepath = os.path.join(self.screenshots_dir, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        removed_count += 1
            
            return {
                "success": True,
                "removed_count": removed_count,
                "message": f"Removed {removed_count} old screenshots"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }