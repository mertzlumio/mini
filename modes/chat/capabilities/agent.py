# Updated modes/chat/capabilities/agent.py - Now with Real Mistral Vision!
import json
from tkinter import END
from . import task_manager, web_search, file_reader, memory_tools, visual_assistant
from ..api_client import call_mistral_api, call_mistral_vision_api, supports_vision

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
    # Visual analysis tools
    "capture_screen_context": visual_assistant.capture_screen_context,
    "get_screen_dimensions": visual_assistant.get_screen_dimensions,
    "analyze_screen_region": visual_assistant.analyze_screen_region
}

def handle_agent_response(response, session_history, console, status_label):
    """
    Enhanced agent handler with REAL Mistral Vision support
    """
    # Check if AI decided to use tools
    tool_calls = response.get("tool_calls")
    
    if not tool_calls:
        # Simple response - no autonomous action needed
        content = response.get("content", "I'm not sure how to respond.")
        console.insert(END, f"AI: {content}\n")
        return
    
    # AI autonomously decided to use tools
    console.insert(END, "🛠️ Agent using tools...\n", "accent")
    
    # Track if we captured any visual content and store the image data
    captured_image_data = None
    visual_tool_used = False
    
    # Execute all tool calls the AI requested
    for tool_call in tool_calls:
        tool_result = execute_autonomous_tool(tool_call, console)
        # Add tool result to session history
        session_history.append(tool_result)
        
        # Check if this was a visual capture tool and extract image data
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
    
    # Now get AI's final response - use vision API if we captured visual content
    if visual_tool_used and captured_image_data and supports_vision():
        console.insert(END, "👁️ Analyzing visual content with Mistral Vision...\n", "dim")
        
        try:
            # Use the vision API with the captured screenshot
            final_response = call_mistral_vision_api(session_history[:-len(tool_calls)], captured_image_data)
            console.insert(END, "✅ Visual analysis complete!\n", "success")
            
        except Exception as e:
            console.insert(END, f"⚠️ Vision analysis failed: {str(e)}\n", "warning")
            console.insert(END, "💬 Falling back to text-only response...\n", "dim")
            # Fallback to regular API call
            working_history = session_history.copy()
            final_response = call_mistral_api(working_history)
    else:
        # Regular response for non-visual tools or when vision not available
        if visual_tool_used and not supports_vision():
            console.insert(END, "⚠️ Vision not available with current model, providing text response...\n", "warning")
        
        console.insert(END, "💬 Agent formulating response...\n", "dim")
        working_history = session_history.copy()
        final_response = call_mistral_api(working_history)
    
    # Add final response to session history
    session_history.append(final_response)
    
    final_content = final_response.get("content", "Task completed autonomously.")
    console.insert(END, f"AI: {final_content}\n")

def execute_autonomous_tool(tool_call, console):
    """
    Execute a tool that the AI autonomously decided to use.
    Enhanced with better visual tool feedback.
    """
    tool_id = tool_call.get("id")
    function_info = tool_call.get("function", {})
    tool_name = function_info.get("name")
    
    console.insert(END, f"  → Agent executing: {tool_name}\n", "dim")
    
    tool_result = {
        "role": "tool",
        "tool_call_id": tool_id,
        "name": tool_name,
        "content": ""
    }
    
    if tool_name in TOOL_REGISTRY:
        try:
            # Parse arguments and execute tool autonomously
            arguments = json.loads(function_info.get("arguments", "{}"))
            tool_function = TOOL_REGISTRY[tool_name]
            
            # Special handling for visual tools
            if tool_name == "capture_screen_context":
                region = arguments.get("region")
                if region and len(region) == 4:
                    result = tool_function(region=tuple(region), save_screenshot=arguments.get("save_screenshot", True))
                else:
                    result = tool_function(save_screenshot=arguments.get("save_screenshot", True))
                console.insert(END, f"  📸 Screen captured for analysis\n", "success")
                
            elif tool_name == "analyze_screen_region":
                result = tool_function(
                    arguments.get("x1"), arguments.get("y1"),
                    arguments.get("x2"), arguments.get("y2")
                )
                console.insert(END, f"  🎯 Region captured for analysis\n", "success")
                
            elif tool_name == "get_screen_dimensions":
                result = tool_function()
                console.insert(END, f"  📏 Screen dimensions retrieved\n", "success")
                
            else:
                # Regular tool execution
                result = tool_function(**arguments)
                
                # Show appropriate feedback
                if tool_name == "add_task_to_notes":
                    console.insert(END, f"  ✓ Task added: {arguments.get('task_content', '')[:30]}...\n", "success")
                elif tool_name == "search_web":
                    console.insert(END, f"  🔍 Web search: {arguments.get('query', '')[:30]}...\n", "success")
                elif tool_name == "remember_fact":
                    console.insert(END, f"  🧠 Fact stored in memory\n", "success")
                elif tool_name == "recall_information":
                    console.insert(END, f"  🔍 Memory searched\n", "success")
            
            tool_result["content"] = str(result)
            
        except Exception as e:
            console.insert(END, f"  ❌ Tool error: {str(e)}\n", "error")
            tool_result["content"] = f"Error: {str(e)}"
    else:
        console.insert(END, f"  ❌ Unknown tool: {tool_name}\n", "error")
        tool_result["content"] = f"Error: Tool '{tool_name}' not available."
    
    return tool_result