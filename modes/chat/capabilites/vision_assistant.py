"""
Visual Assistant Capability - Screenshot and visual analysis
"""
import re
from screenshot import VisualAssistant

class VisualCapability:
    def __init__(self):
        self.name = "visual_assistant"
        self.visual_assistant = VisualAssistant()
        
        # Command patterns
        self.visual_patterns = {
            'screenshot': r'\b(screenshot|capture screen|take screen|screen shot)\b',
            'screen_info': r'\b(screen size|screen info|display info|resolution)\b',
            'region_screenshot': r'\b(capture region|region screenshot|crop screen)\b',
            'list_screenshots': r'\b(list screenshots|show screenshots|recent screens)\b',
            'cleanup': r'\b(cleanup screenshots|delete old screens|clean screens)\b'
        }
    
    def can_handle(self, user_input):
        """Check if this capability can handle the input"""
        user_input_lower = user_input.lower()
        
        for pattern in self.visual_patterns.values():
            if re.search(pattern, user_input_lower):
                return True
        return False
    
    def handle(self, user_input):
        """Handle visual commands"""
        command = self._detect_visual_command(user_input)
        
        if not command:
            return {"response": "I didn't understand that visual command."}
        
        try:
            if command == 'screenshot':
                result = self.visual_assistant.take_screenshot()
                if result['success']:
                    return {
                        "response": f"📸 Screenshot taken successfully!\nSaved as: {result['filename']}\nSize: {result['size'][0]}x{result['size'][1]}",
                        "screenshot_path": result['filepath'],
                        "visual_data": True
                    }
                else:
                    return {"response": f"❌ Failed to take screenshot: {result['error']}"}
            
            elif command == 'screen_info':
                result = self.visual_assistant.get_screen_info()
                if result['success']:
                    return {
                        "response": f"🖥️ Screen Information:\nResolution: {result['width']}x{result['height']}\nTotal pixels: {result['total_pixels']:,}"
                    }
                else:
                    return {"response": f"❌ Failed to get screen info: {result['error']}"}
            
            elif command == 'list_screenshots':
                result = self.visual_assistant.list_screenshots()
                if result['success']:
                    if result['screenshots']:
                        screenshot_list = "\n".join([
                            f"• {shot['filename']} ({shot['size_kb']}KB) - {shot['modified']}"
                            for shot in result['screenshots']
                        ])
                        return {
                            "response": f"📁 Recent Screenshots ({result['total_count']} total):\n{screenshot_list}"
                        }
                    else:
                        return {"response": "📁 No screenshots found."}
                else:
                    return {"response": f"❌ Failed to list screenshots: {result['error']}"}
            
            elif command == 'cleanup':
                result = self.visual_assistant.cleanup_old_screenshots()
                if result['success']:
                    return {"response": f"🧹 {result['message']}"}
                else:
                    return {"response": f"❌ Failed to cleanup: {result['error']}"}
            
            elif command == 'region_screenshot':
                # Extract coordinates if provided
                coords_match = re.search(r'(\d+)[,\s]+(\d+)[,\s]+(\d+)[,\s]+(\d+)', user_input)
                if coords_match:
                    x1, y1, x2, y2 = map(int, coords_match.groups())
                    result = self.visual_assistant.take_region_screenshot(x1, y1, x2, y2)
                    if result['success']:
                        return {
                            "response": f"📸 Region screenshot taken!\nArea: ({x1},{y1}) to ({x2},{y2})\nSaved as: {result['filename']}",
                            "screenshot_path": result['filepath'],
                            "visual_data": True
                        }
                    else:
                        return {"response": f"❌ Failed to take region screenshot: {result['error']}"}
                else:
                    return {
                        "response": "📐 To take a region screenshot, provide coordinates:\nExample: 'capture region 100 100 500 400'\nFormat: x1 y1 x2 y2"
                    }
            
        except Exception as e:
            return {"response": f"❌ Visual command error: {str(e)}"}
    
    def _detect_visual_command(self, prompt):
        """Detect which visual command is being requested"""
        prompt_lower = prompt.lower()
        
        for command, pattern in self.visual_patterns.items():
            if re.search(pattern, prompt_lower):
                return command
        
        return None
    
    def get_capability_prompt(self):
        """Get prompt text for this capability"""
        return """
VISUAL CAPABILITIES:
You can help with:
- Taking screenshots: "screenshot", "capture screen"
- Getting screen info: "screen size", "display info"
- Region screenshots: "capture region X Y X2 Y2"
- Managing screenshots: "list screenshots", "cleanup screenshots"

When users ask for visual tasks, mention these capabilities.
"""