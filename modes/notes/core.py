"""
Notes mode - Simple file-based task management
"""
import os
from tkinter import END
from config import NOTES_FILE

# Module-level state
notes = []

def load_notes():
    """Load notes from file"""
    global notes
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            notes = [line.strip() for line in f if line.strip()]

def save_notes():
    """Save notes to file"""
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        for note in notes:
            f.write(note + "\n")

def add_note(note):
    """Add a new note"""
    notes.append(note)
    save_notes()
    return note

def remove_note(identifier):
    """Remove a note by index or text match"""
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
    """Get all notes"""
    return notes

def get_notes_count():
    """Get number of notes"""
    return len(notes)

def handle_input(user_input, console):
    """Handle notes mode input"""
    cmd = user_input.strip()
    
    # Handle special commands
    if cmd.lower().startswith(("rm ", "remove ", "del ", "delete ")):
        # Extract identifier (everything after the command)
        parts = cmd.split(maxsplit=1)
        if len(parts) > 1:
            identifier = parts[1]
            success, message, removed_note = remove_note(identifier)
            
            if success:
                console.insert(END, f"[✓] {message}\n", "success")
            else:
                console.insert(END, f"[!] {message}\n", "warning")
            
            console.insert(END, "\nUpdated TODO List:\n", "accent")
            _display_notes(console)
        else:
            console.insert(END, "[!] Usage: rm <number> or rm <text>\n", "warning")
            console.insert(END, "Examples: 'rm 1', 'rm groceries'\n", "dim")
            
    elif cmd.lower() in ("clear", "clear all", "reset"):
        count = clear_all_notes()
        console.insert(END, f"[✓] Cleared {count} tasks\n", "success")
        console.insert(END, "\nTODO List (empty):\n", "accent")
        _display_notes(console)
        
    elif cmd.lower() in ("list", "show", "ls"):
        console.insert(END, "\nYour TODO List:\n", "accent")
        _display_notes(console)
        
    elif cmd.lower() in ("help", "?"):
        _show_help(console)
        
    else:
        # Regular note addition
        add_note(cmd)
        console.insert(END, f"[+] Added: {cmd}\n", "success")
        console.insert(END, "\nYour TODO List:\n", "accent")
        _display_notes(console)

def _display_notes(console):
    """Display notes in console"""
    notes = get_notes()
    if not notes:
        console.insert(END, "  (no tasks yet)\n", "dim")
        return
        
    for i, note in enumerate(notes, 1):
        console.insert(END, f"  {i}. {note}\n")
    
    # Show total count
    console.insert(END, f"\nTotal: {len(notes)} task{'s' if len(notes) != 1 else ''}\n", "dim")

def _show_help(console):
    """Display help for notes mode"""
    help_text = """
Notes Mode Commands:
  <task>          - Add new task
  rm <number>     - Remove task by number (e.g., 'rm 1')
  rm <text>       - Remove task by partial text match
  list            - Show all tasks
  clear           - Remove all tasks
  help            - Show this help
  
Examples:
  > Buy groceries
  > rm 1
  > rm groceries
  > clear
"""
    console.insert(END, help_text, "dim")

def on_mode_enter(console):
    """Called when entering notes mode"""
    console.insert(END, "\nYour TODO List:\n", "accent")
    _display_notes(console)