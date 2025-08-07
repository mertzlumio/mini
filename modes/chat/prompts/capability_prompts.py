# Updated modes/chat/prompts/capability_prompts.py

# Enhanced tool definitions for Mistral API with memory capabilities
MISTRAL_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file to understand capabilities, configurations, or documentation. Useful for self-discovery and understanding available features.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string", 
                        "description": "Path to the file to read. Can read from modes/chat/capabilities/, modes/chat/prompts/, config/, or docs/ directories."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_files", 
            "description": "List files in a directory that can be read for information discovery.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to list files from (default: modes/chat/capabilities/)"
                    }
                },
                "required": []
            }
        }
    },
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
                        "description": "The specific content of the task or note to be added."
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
    },
    # New memory tools
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Store important information in long-term memory for future recall. Use when the user shares personal info, preferences, or important facts that should be remembered across sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact_content": {
                        "type": "string",
                        "description": "The specific fact or information to remember"
                    },
                    "importance": {
                        "type": "number",
                        "description": "Importance score from 0.0 to 1.0 (default: 0.7)",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "tags": {
                        "type": "string", 
                        "description": "Comma-separated tags for easier recall (e.g., 'work,project,python')"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context about when/why this is important"
                    }
                },
                "required": ["fact_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_information",
            "description": "Search long-term memory for relevant information. Use when you need to find previously stored facts, preferences, or context about the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant memories"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (1-10, default: 5)",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_preference", 
            "description": "Store or update a user preference for future reference. Use when the user expresses how they like things done or configured.",
            "parameters": {
                "type": "object",
                "properties": {
                    "preference_key": {
                        "type": "string",
                        "description": "Name/key for the preference (e.g., 'coding_style', 'communication_tone')"
                    },
                    "preference_value": {
                        "type": "string", 
                        "description": "The preference value or description"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context about this preference"
                    }
                },
                "required": ["preference_key", "preference_value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory_stats",
            "description": "Get statistics about the memory system state. Useful for understanding how much information is stored.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
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
    },
    "memory_system": {
        "name": "remember_fact",
        "description": "Store important information in long-term memory for future sessions.",
        "parameters": [
            {"name": "fact_content", "type": "string", "description": "The fact to remember"},
            {"name": "importance", "type": "number", "description": "Importance from 0.0-1.0"},
            {"name": "tags", "type": "string", "description": "Comma-separated tags"}
        ]
    },
    "memory_recall": {
        "name": "recall_information", 
        "description": "Search long-term memory for relevant information.",
        "parameters": [
            {"name": "query", "type": "string", "description": "Search query for memories"}
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