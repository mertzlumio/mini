# modes/chat/capabilities/task_manager.py
from modes.notes import core as notes_core

def add_task_to_notes(task_content: str):
    """
    The actual implementation for adding a task to the notes file.
    It calls the core function from the notes mode.
    """
    if not isinstance(task_content, str):
        return "Error: The task content must be a string."
        
    notes_core.add_note(task_content)
    return f"Successfully added the task '{task_content}' to your notes."
