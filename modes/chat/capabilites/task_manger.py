"""
Task Management Capability - Handles task detection and integration with notes
"""
import re
from tkinter import END

class TaskCapability:
    def __init__(self):
        self.name = "task_manager"
    
    def detect_task_intent(self, prompt):
        """Smart task detection using regex patterns"""
        task_patterns = [
            r'\b(?:remind me to|i need to|i have to|todo:|task:)\s+(.+)',
            r'\b(?:add task|add to list|remember to)\s+(.+)',
            r'\b(?:deadline|due by|meeting at|appointment)\s+(.+)',
            r'\b(?:buy|pick up|get|purchase)\s+(.+)',
            r'\b(?:call|email|contact)\s+(.+)'
        ]
        
        for pattern in task_patterns:
            match = re.search(pattern, prompt.lower())
            if match:
                return match.group(1).strip()
        
        return None
    
    def add_task(self, task_content, console):
        """Add task to notes and display feedback"""
        try:
            # Import notes functionality
            from modes.notes import core as notes_core
            
            # Add the task
            notes_core.add_note(task_content)
            
            # Display feedback
            console.insert(END, f"[+] Added task: {task_content}\n", "success")
            console.insert(END, "\nTODO List Updated:\n", "accent")
            
            # Show updated notes
            self._display_notes_preview(console, notes_core)
            
        except ImportError:
            console.insert(END, "[!] Notes system not available\n", "warning")
    
    def _display_notes_preview(self, console, notes_core):
        """Display a preview of current notes"""
        notes = notes_core.get_notes()
        if not notes:
            console.insert(END, "  (no tasks yet)\n", "dim")
            return
            
        # Show last 3 tasks
        preview_notes = notes[-3:] if len(notes) > 3 else notes
        
        for i, note in enumerate(preview_notes, 1):
            if len(notes) > 3 and i == 1:
                console.insert(END, f"  ... ({len(notes)-3} more)\n", "dim")
            console.insert(END, f"  {len(notes)-len(preview_notes)+i}. {note}\n")
        
        console.insert(END, f"\nTotal: {len(notes)} task{'s' if len(notes) != 1 else ''}\n", "dim")
    
    def get_capability_prompt(self):
        """Get prompt text for this capability"""
        return """
TASK DETECTION:
Look for anything that sounds like:
- Something to do: "I need to buy groceries", "finish the report"
- Appointments: "doctor visit Thursday", "meeting at 3pm"
- Deadlines: "presentation due tomorrow", "project deadline Friday"
- Reminders: "call mom", "pick up dry cleaning"
- Commitments: "promised to help Sarah", "agreed to review the document"

If you detect a task, include it in the "task" field of your JSON response.
"""