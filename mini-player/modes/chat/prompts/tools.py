# Updated modes/chat/prompts/capability_prompts.py

# Enhanced tool definitions for Mistral API with memory AND visual capabilities
MISTRAL_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file with enhanced security and formatting. Can read Python, JSON, text, markdown, and config files. Provides helpful error messages and suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string", 
                        "description": "Path to the file to read. Can be relative (e.g., 'modes/chat/core.py') or use directory shortcuts."
                    },
                    "max_size_kb": {
                        "type": "integer",
                        "description": "Maximum file size to read in KB (default: 500). Prevents memory issues with large files.",
                        "default": 500
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
            "description": "List files in a directory with type information and sizes. Great for discovering what files are available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to list files from. Popular options: 'modes/chat/capabilities', 'modes/chat/prompts', 'modes', 'config', 'docs'",
                        "default": "modes/chat/capabilities"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to search subdirectories recursively",
                        "default": False
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files by name or content. Useful for finding specific functionality or code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to look for in filenames or file content"
                    },
                    "search_dirs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Directories to search in (optional, defaults to main directories)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_structure",
            "description": "Get an overview of the entire Mini-Player project structure. Useful for understanding the codebase organization.",
            "parameters": {
                "type": "object",
                "properties": {},
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
    # Memory tools
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
    },
    # Visual/Screen Analysis tools
    {
        "type": "function",
        "function": {
            "name": "capture_screen_context",
            "description": "Take a screenshot of the current screen for visual analysis. Use when user asks about what's on screen, needs help with visual content, or wants screen analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Optional region to capture as [x1, y1, x2, y2]. If not specified, captures full screen.",
                        "minItems": 4,
                        "maxItems": 4
                    },
                    "save_screenshot": {
                        "type": "boolean",
                        "description": "Whether to save the screenshot to disk (default: true)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_screen_dimensions",
            "description": "Get the current screen resolution and dimensions. Useful for understanding screen layout.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_screen_region",
            "description": "Capture and analyze a specific rectangular region of the screen. Useful when user wants to focus on a particular area.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x1": {"type": "integer", "description": "Left coordinate of region"},
                    "y1": {"type": "integer", "description": "Top coordinate of region"},
                    "x2": {"type": "integer", "description": "Right coordinate of region"},
                    "y2": {"type": "integer", "description": "Bottom coordinate of region"}
                },
                "required": ["x1", "y1", "x2", "y2"]
            }
        }
    },
    {
            "type": "function",
            "function": {
                "name": "execute_bash_command",
                "description": "Execute bash commands securely with built-in safety checks. Can run system commands, file operations, git commands, development tools, and more. Automatically handles directory context.",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute (e.g., 'ls -la', 'git status', 'python --version', 'find . -name \"*.py\"')"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Maximum execution time in seconds (default: 30)",
                            "default": 30
                        },
                        "safe_mode": {
                            "type": "boolean", 
                            "description": "Enable security restrictions to block dangerous commands (default: True)",
                            "default": True
                        }
                    },
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_current_directory",
                "description": "Get the current working directory and list its contents for context",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "change_directory", 
                "description": "Change the working directory for subsequent bash operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to change to (absolute or relative)"
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_bash_command_history",
                "description": "Show recent bash commands executed in this session",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of recent commands to show (default: 5)",
                            "default": 5
                        }
                    }
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
    },
    "visual_analysis": {
        "name": "capture_screen_context",
        "description": "Capture and analyze screen content for visual assistance.",
        "parameters": [
            {"name": "region", "type": "array", "description": "Optional screen region [x1,y1,x2,y2]"},
            {"name": "save_screenshot", "type": "boolean", "description": "Save to disk"}
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