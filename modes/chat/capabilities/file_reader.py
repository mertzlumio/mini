import os
import json

def read_file(file_path: str):
    """
    Read and return the contents of a file.
    Can read text files, JSON files, and configuration files.
    """
    if not isinstance(file_path, str):
        return "Error: File path must be a string."
    
    try:
        # Security check - only allow reading from certain directories
        allowed_dirs = [
            'modes/chat/capabilities/',
            'modes/chat/prompts/', 
            'config/',
            'docs/',
            './'  # Current directory for config files
        ]
        
        # Check if file path starts with allowed directory
        if not any(file_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
            return f"Error: Access denied to {file_path}. Only allowed directories: {', '.join(allowed_dirs)}"
        
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # If it's a JSON file, try to format it nicely
        if file_path.endswith('.json'):
            try:
                json_data = json.loads(content)
                return json.dumps(json_data, indent=2)
            except json.JSONDecodeError:
                return content  # Return raw content if JSON parsing fails
        
        return content
        
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_available_files(directory: str = "modes/chat/capabilities/"):
    """
    List files in a directory that the agent can read
    """
    if not isinstance(directory, str):
        return "Error: Directory path must be a string."
    
    try:
        if not os.path.exists(directory):
            return f"Error: Directory not found: {directory}"
        
        files = []
        for filename in os.listdir(directory):
            if filename.endswith(('.py', '.json', '.txt', '.md')):
                files.append(filename)
        
        if files:
            return f"Available files in {directory}:\n" + "\n".join(f"- {f}" for f in sorted(files))
        else:
            return f"No readable files found in {directory}"
            
    except Exception as e:
        return f"Error listing files: {str(e)}"