import os
from config import NOTES_FILE

notes = []

def load_notes():
    global notes
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            notes = [line.strip() for line in f if line.strip()]

def save_notes():
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        for note in notes:
            f.write(note + "\n")

def add_note(note):
    notes.append(note)
    save_notes()
    return note

def remove_note(identifier):
    """
    Remove a note by index (1-based) or by partial text match
    Returns: (success: bool, message: str, removed_note: str or None)
    """
    if not notes:
        return False, "No tasks to remove", None
    
    # Try to parse as index first
    try:
        index = int(identifier) - 1  # Convert to 0-based
        if 0 <= index < len(notes):
            removed_note = notes.pop(index)
            save_notes()
            return True, f"Removed task #{identifier}", removed_note
        else:
            return False, f"Task #{identifier} not found (1-{len(notes)} available)", None
    except ValueError:
        # Not a number, try partial text match
        identifier_lower = identifier.lower()
        matches = []
        
        for i, note in enumerate(notes):
            if identifier_lower in note.lower():
                matches.append((i, note))
        
        if len(matches) == 1:
            # Exact match found
            index, note = matches[0]
            removed_note = notes.pop(index)
            save_notes()
            return True, f"Removed: {removed_note}", removed_note
        elif len(matches) > 1:
            # Multiple matches - show options
            match_list = "\n".join([f"  {i+1}. {note}" for i, note in matches])
            return False, f"Multiple matches found:\n{match_list}\nUse number to remove specific task", None
        else:
            return False, f"No task found matching '{identifier}'", None

def clear_all_notes():
    """Clear all notes"""
    global notes
    count = len(notes)
    notes = []
    save_notes()
    return count

def get_notes():
    return notes

def get_notes_count():
    return len(notes)