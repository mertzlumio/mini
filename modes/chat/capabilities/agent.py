import json
from tkinter import END
from . import task_manager, web_search, file_reader, memory_tools
from ..api_client import call_mistral_api

# Tool registry - maps tool names to actual functions
TOOL_REGISTRY = {
    "add_task_to_notes": task_manager.add_task_to_notes,
    "search_web": web_search.search_web,
    "read_file": file_reader.read_file,
    "list_available_files": file_reader.list_available_files,
    "remember_fact": memory_tools.remember_fact,
    "recall_information": memory_tools.recall_information,
    "update_preference": memory_tools.update_preference,
    "get_memory_stats": memory_tools.get_memory_stats
}

def handle_agent_response(response, session_history, console, status_label):
    """
    Handles the agentic logic - deciding what to do with AI responses.
    Now properly updates the session history.
    """
    # Note: The response is already added to session_history in core.py
    
    # Check if AI decided to use tools
    tool_calls = response.get("tool_calls")
    
    if not tool_calls:
        # Simple response - no autonomous action needed
        content = response.get("content", "I'm not sure how to respond.")
        console.insert(END, f"AI: {content}\n")
        return
    
    # AI autonomously decided to use tools
    console.insert(END, "🛠️ Agent using tools...\n", "accent")
    
    # Execute all tool calls the AI requested
    for tool_call in tool_calls:
        tool_result = execute_autonomous_tool(tool_call, console)
        # Add tool result to session history
        session_history.append(tool_result)
    
    # Get AI's final response after autonomous tool usage
    console.insert(END, "💬 Agent formulating response...\n", "dim")
    
    # Create a working copy for the API call
    working_history = session_history.copy()
    final_response = call_mistral_api(working_history)
    
    # Add final response to session history
    session_history.append(final_response)
    
    final_content = final_response.get("content", "Task completed autonomously.")
    console.insert(END, f"AI: {final_content}\n")

def execute_autonomous_tool(tool_call, console):
    """
    Execute a tool that the AI autonomously decided to use.
    Returns the tool result message for history.
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
            result = tool_function(**arguments)
            
            # Show autonomous action feedback
            if tool_name == "add_task_to_notes":
                console.insert(END, f"  ✓ Agent added task: {arguments.get('task_content', '')}\n", "success")
            elif tool_name == "search_web":
                console.insert(END, f"  🔍 Agent searched: {arguments.get('query', '')}\n", "success")
            
            tool_result["content"] = str(result)
            
        except Exception as e:
            console.insert(END, f"  ❌ Agent tool error: {str(e)}\n", "error")
            tool_result["content"] = f"Error: {str(e)}"
    else:
        console.insert(END, f"  ❌ Agent: Unknown tool {tool_name}\n", "error")
        tool_result["content"] = f"Error: Tool '{tool_name}' not available."
    
    return tool_result