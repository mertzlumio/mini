import json
from tkinter import END
from . import task_manager, web_search, file_reader, memory_tools, visual_assistant
from . import bash_executor
from ..utils.api_client import call_mistral_vision_api, supports_vision

# Tool registry - maps tool names to actual functions
TOOL_REGISTRY = {
    "add_task_to_notes": task_manager.add_task_to_notes,
    "search_web": web_search.search_web,
    "read_file": file_reader.read_file,
    "list_available_files": file_reader.list_available_files,
    "remember_fact": memory_tools.remember_fact,
    "recall_information": memory_tools.recall_information,
    "update_preference": memory_tools.update_preference,
    "get_memory_stats": memory_tools.get_memory_stats,
    "capture_screen_context": visual_assistant.capture_screen_context,
    "get_screen_dimensions": visual_assistant.get_screen_dimensions,
    "analyze_screen_region": visual_assistant.analyze_screen_region,
    "execute_bash_command": bash_executor.execute_bash_command,
    "get_current_directory": bash_executor.get_current_directory,
    "change_directory": bash_executor.change_directory,
    "get_bash_command_history": bash_executor.get_bash_command_history,
}

def handle_agent_response(response, console):
    """
    Executes tool calls requested by the AI and returns the results.
    Now includes vision API integration for visual tools.
    """
    tool_calls = response.get("tool_calls")
    if not tool_calls:
        return []

    # Track if we used visual tools and capture image data
    captured_image_data = None
    visual_tool_used = False
    tool_results = []
    
    # Execute all tool calls
    for tool_call in tool_calls:
        tool_result = execute_autonomous_tool(tool_call, console)
        tool_results.append(tool_result)
        
        # Check if this was a visual capture tool
        tool_name = tool_call.get("function", {}).get("name", "")
        if tool_name in ["capture_screen_context", "analyze_screen_region"]:
            visual_tool_used = True
            # Get the screenshot data from the visual assistant
            try:
                from .visual_assistant import get_visual_assistant
                assistant = get_visual_assistant()
                cached_screenshot = assistant.get_cached_screenshot(max_age_seconds=60)
                if cached_screenshot:
                    captured_image_data = cached_screenshot
            except Exception as e:
                console.insert(END, f"⚠️ Failed to get screenshot data: {str(e)}\n", "warning")
    
    # If visual tools were used and we have image data, call vision API
    if visual_tool_used and captured_image_data and supports_vision():
        try:
            console.insert(END, "🔍 Analyzing visual content with Mistral Vision...\n", "dim")
            
            # Create a simple context for vision analysis
            vision_context = [
                {
                    "role": "user", 
                    "content": "I've captured my screen. Please analyze what you see and provide insights about the visual content."
                }
            ]
            
            # Call vision API with the captured screenshot
            vision_response = call_mistral_vision_api(vision_context, captured_image_data)
            
            # Create a tool result that includes the vision analysis
            vision_tool_result = {
                "role": "tool",
                "tool_call_id": f"vision_analysis_{len(tool_results)}",
                "name": "vision_analysis",
                "content": f"Vision Analysis: {vision_response.get('content', 'Visual analysis completed.')}"
            }
            
            tool_results.append(vision_tool_result)
            console.insert(END, "✅ Visual analysis complete!\n", "success")
            
        except Exception as e:
            console.insert(END, f"⚠️ Vision analysis failed: {str(e)}\n", "warning")
            # Add a fallback tool result
            fallback_result = {
                "role": "tool",
                "tool_call_id": f"vision_fallback_{len(tool_results)}",
                "name": "vision_analysis",
                "content": "Vision analysis failed due to API error. Screenshot was captured successfully but detailed visual analysis is not available."
            }
            tool_results.append(fallback_result)
    
    elif visual_tool_used and not supports_vision():
        console.insert(END, "⚠️ Vision not available with current model\n", "warning")
        # Add a tool result explaining the limitation
        no_vision_result = {
            "role": "tool",
            "tool_call_id": f"no_vision_{len(tool_results)}",
            "name": "vision_analysis", 
            "content": "Screenshot captured successfully, but vision analysis is not available with the current model configuration."
        }
        tool_results.append(no_vision_result)
    
    return tool_results

def execute_autonomous_tool(tool_call, console):
    """
    Execute a single tool that the AI autonomously decided to use.
    """
    tool_id = tool_call.get("id")
    function_info = tool_call.get("function", {})
    tool_name = function_info.get("name")
    
    tool_result = {
        "role": "tool",
        "tool_call_id": tool_id,
        "name": tool_name,
        "content": ""
    }
    
    if tool_name in TOOL_REGISTRY:
        try:
            arguments = json.loads(function_info.get("arguments", "{}"))
            tool_function = TOOL_REGISTRY[tool_name]
            
            # Enhanced UI Feedback
            if tool_name == "execute_bash_command":
                command = arguments.get('command', '')
                console.insert(END, f"  🖥️  Executing: {command}\n", "accent")
            elif tool_name == "capture_screen_context":
                region = arguments.get("region")
                if region:
                    console.insert(END, f"  📸 Capturing screen region\n", "success")
                else:
                    console.insert(END, f"  📸 Capturing full screen\n", "success")
            elif tool_name == "analyze_screen_region":
                console.insert(END, f"  🎯 Analyzing specific screen region\n", "success")
            elif tool_name == "search_web":
                query = arguments.get('query', '')[:30]
                console.insert(END, f"  🌐 Web search: {query}...\n", "success")
            elif tool_name == "read_file":
                filename = arguments.get('filename', '')[:30]
                console.insert(END, f"  📄 Reading file: {filename}...\n", "success")
            else:
                console.insert(END, f"  🛠️  Executing: {tool_name}\n", "dim")

            # Execute the tool with special handling for visual tools
            if tool_name in ["capture_screen_context", "analyze_screen_region"]:
                if tool_name == "capture_screen_context":
                    region = arguments.get("region")
                    if region and len(region) == 4:
                        result = tool_function(region=tuple(region), save_screenshot=arguments.get("save_screenshot", True))
                    else:
                        result = tool_function(save_screenshot=arguments.get("save_screenshot", True))
                elif tool_name == "analyze_screen_region":
                    result = tool_function(
                        arguments.get("x1"), arguments.get("y1"),
                        arguments.get("x2"), arguments.get("y2")
                    )
            else:
                result = tool_function(**arguments)
            
            tool_result["content"] = str(result)
            
        except Exception as e:
            console.insert(END, f"  ❌ Tool error: {str(e)}\n", "error")
            tool_result["content"] = f"Error: {str(e)}"
    else:
        console.insert(END, f"  ❌ Unknown tool: {tool_name}\n", "error")
        tool_result["content"] = f"Error: Tool '{tool_name}' not available."
    
    return tool_result