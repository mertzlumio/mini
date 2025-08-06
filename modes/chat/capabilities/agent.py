# modes/chat/capabilities/agent.py
import json
from tkinter import END
from . import task_manager, web_search, file_reader
from ..api_client import call_mistral_api

# Tool registry - maps tool names to actual functions
TOOL_REGISTRY = {
    "add_task_to_notes": task_manager.add_task_to_notes,
    "search_web": web_search.search_web,
    "read_file": file_reader.read_file,
    "list_available_files": file_reader.list_available_files,
}

def handle_agent_response(response, history, console, status_label):
    """
    Handles the agentic logic - deciding what to do with AI responses.
    This is where the autonomous decision-making happens.
    """
    history.append(response)
    
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
        execute_autonomous_tool(tool_call, history, console)
    
    # Get AI's final response after autonomous tool usage
    console.insert(END, "💬 Agent formulating response...\n", "dim")
    final_response = call_mistral_api(history)
    history.append(final_response)
    
    final_content = final_response.get("content", "Task completed autonomously.")
    console.insert(END, f"AI: {final_content}\n")

def execute_autonomous_tool(tool_call, history, console):
    """
    Execute a tool that the AI autonomously decided to use.
    This demonstrates the agentic behavior.
    """
    tool_id = tool_call.get("id")
    function_info = tool_call.get("function", {})
    tool_name = function_info.get("name")
    
    console.insert(END, f"  → Agent executing: {tool_name}\n", "dim")
    
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
            
            # Add result to conversation history
            history.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": str(result)
            })
            
        except Exception as e:
            console.insert(END, f"  ❌ Agent tool error: {str(e)}\n", "error")
            history.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": f"Error: {str(e)}"
            })
    else:
        console.insert(END, f"  ❌ Agent: Unknown tool {tool_name}\n", "error")
        history.append({
            "role": "tool",
            "tool_call_id": tool_id,
            "name": tool_name,
            "content": f"Error: Tool '{tool_name}' not available."
        })