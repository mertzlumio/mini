# modes/chat/prompts/capability_prompts.py

# Tool definitions for Mistral API
MISTRAL_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "add_task_to_notes",
            "description": "Adds a new task or item to the user's notes list. Use this when the user asks to be reminded of something, to add something to a list, or to create a note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_content": {
                        "type": "string",
                        "description": "The specific content of the task or note to be added. For example, 'Buy milk' or 'Call John at 5pm'."
                    }
                },
                "required": ["task_content"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "search_web",
            "description": "Performs a web search to find up-to-date information, answer questions about current events, or look up facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query. Should be a concise and effective search term."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Legacy format for documentation (if needed)
CAPABILITIES = {
    "task_manager": {
        "name": "add_task_to_notes",
        "description": "Adds a new task or item to the user's notes list. Use this when the user asks to be reminded of something, to add something to a list, or to create a note.",
        "parameters": [
            {"name": "task_content", "type": "string", "description": "The specific content of the task or note to be added. For example, 'Buy milk' or 'Call John at 5pm'."}
        ]
    },
    "web_search": {
        "name": "search_web",
        "description": "Performs a web search to find up-to-date information, answer questions about current events, or look up facts.",
        "parameters": [
            {"name": "query", "type": "string", "description": "The search query. Should be a concise and effective search term."}
        ]
    }
}

def get_mistral_tools():
    """Returns tool definitions in Mistral API format."""
    return MISTRAL_TOOL_DEFINITIONS

def get_capability_descriptions():
    """Returns a formatted string describing all available capabilities."""
    import json
    return json.dumps(CAPABILITIES, indent=2)