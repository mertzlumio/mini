#!/usr/bin/env python3
"""
Test script for visual assistant capabilities
Run this to verify screenshot functionality works before integrating
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path so we can import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from modes.chat.capabilities.visual_assistant import get_visual_assistant
    print("✅ Visual assistant module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import visual assistant: {e}")
    sys.exit(1)

def test_screenshot_functionality():
    """Test basic screenshot functionality"""
    print("\n🧪 Testing visual assistant functionality...")
    
    assistant = get_visual_assistant()
    
    # Test 1: Full screen capture
    print("📸 Testing full screen capture...")
    result = assistant.take_screenshot(save=True, quality=85)
    
    if result["success"]:
        print(f"✅ Screenshot taken successfully!")
        print(f"   - Size: {result['size'][0]}x{result['size'][1]} pixels")
        print(f"   - File size: ~{result['file_size_kb']}KB")
        print(f"   - Saved to: {result['filepath']}")
        print(f"   - Base64 length: {len(result.get('base64', ''))} characters")
    else:
        print(f"❌ Screenshot failed: {result['error']}")
        return False
    
    # Test 2: Screen dimensions
    print("\n📏 Testing screen dimensions...")
    try:
        from modes.chat.capabilities.visual_assistant import get_screen_dimensions
        dimensions = get_screen_dimensions()
        print(f"✅ {dimensions}")
    except Exception as e:
        print(f"❌ Failed to get dimensions: {e}")
    
    # Test 3: Region capture (small region in top-left)
    print("\n🎯 Testing region capture (200x200 from top-left)...")
    region_result = assistant.take_region_screenshot(0, 0, 200, 200, save=True)
    
    if region_result["success"]:
        print(f"✅ Region captured successfully!")
        print(f"   - Size: {region_result['size'][0]}x{region_result['size'][1]} pixels")
        print(f"   - File size: ~{region_result['file_size_kb']}KB")
        print(f"   - Saved to: {region_result['filepath']}")
    else:
        print(f"❌ Region capture failed: {region_result['error']}")
    
    print("\n🎉 Visual assistant test completed!")
    print(f"📁 Screenshots saved in: {assistant.screenshots_dir}")
    
    return True

def test_capability_functions():
    """Test the capability functions that would be called by the agent"""
    print("\n🔧 Testing capability function wrappers...")
    
    try:
        from modes.chat.capabilities.visual_assistant import capture_screen_context, analyze_screen_region
        
        # Test capture_screen_context
        print("📸 Testing capture_screen_context...")
        result1 = capture_screen_context(save_screenshot=True)
        print(f"   Result: {result1}")
        
        # Test analyze_screen_region  
        print("🎯 Testing analyze_screen_region...")
        result2 = analyze_screen_region(100, 100, 300, 300)
        print(f"   Result: {result2}")
        
        print("✅ Capability functions working correctly!")
        
    except Exception as e:
        print(f"❌ Capability function test failed: {e}")
        return False
    
    return True

def main():
    print("🖼️  Visual Assistant Test Suite")
    print("=" * 40)
    
    # Test dependencies
    try:
        from PIL import ImageGrab
        print("✅ PIL/Pillow is available")
    except ImportError:
        print("❌ PIL/Pillow not found. Install with: pip install Pillow")
        return
    
    # Run tests
    if test_screenshot_functionality() and test_capability_functions():
        print("\n🎊 All tests passed! Visual assistant is ready to use.")
        print("\n💡 You can now use phrases like:")
        print("   - 'What am I looking at?'")
        print("   - 'Help me with this screen'") 
        print("   - 'Can you see what's displayed?'")
        print("   - 'Analyze what's on my screen'")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()