from modes import chat, bash, notes as notes_mode
from tkinter import END
import os

history = []
history_index = -1
current_dir = os.getcwd()
modes = ["bash", "chat", "notes"]
mode_index = 0
mode = modes[mode_index]

# Mode colors and symbols
MODE_CONFIG = {
    "bash": {"symbol": "[BASH]", "color": "#f0f6fc"},
    "chat": {"symbol": "[CHAT]", "color": "#58a6ff"}, 
    "notes": {"symbol": "[NOTE]", "color": "#3fb950"}
}

def toggle_mode(entry, console, mode_label, status_label, prompt_label):
    """Enhanced mode switching with visual feedback"""
    global mode_index, mode
    mode_index = (mode_index + 1) % len(modes)
    mode = modes[mode_index]
    
    # Update mode display
    config = MODE_CONFIG[mode]
    mode_label.config(text=config['symbol'])
    prompt_label.config(fg=config['color'])
    status_label.config(text=f"Switched to {mode}")
    
    # Visual feedback in console
    console.insert(END, f"\n>> Mode: {config['symbol']}\n", "accent")
    
    if mode == "notes":
        display_notes(console)
    
    console.see(END)
    return "break"

def on_enter(entry, console, mode_label, status_label):
    """Clean command processing with better visual feedback"""
    global history, history_index, current_dir, mode
    
    cmd = entry.get().strip()
    if not cmd:
        return

    # Add to history
    history.append(cmd)
    history_index = len(history)
    
    # Show command with clean formatting
    console.insert(END, f"\n> {cmd}\n", "dim")
    
    # Update status
    status_label.config(text="Processing...")

    # Execute based on mode
    if mode == "bash":
        output, current_dir = bash.run_bash_command(cmd, current_dir)
        console.insert(END, output + "\n")
        
    elif mode == "chat":
        if cmd.lower() in ("/new", "/reset"):
            chat.clear_history()
            console.insert(END, "✨ New chat session started.\n", "accent")
            status_label.config(text="Ready")
            entry.delete(0, END)
            return

        status_label.config(text="Thinking...")
        response_data = chat.call_mistral(cmd)
        
        # Main response
        output = response_data.get("response", "Sorry, something went wrong.")
        console.insert(END, f"AI: {output}\n")
        
        # Handle task addition
        if "task" in response_data:
            task = response_data["task"]
            notes_mode.add_note(task)
            console.insert(END, f"[+] Added task: {task}\n", "success")
            console.insert(END, "\nTODO List Updated:\n", "accent")
            display_notes(console)
            
    elif mode == "notes":
        # Handle special commands
        if cmd.lower().startswith(("rm ", "remove ", "del ", "delete ")):
            # Extract identifier (everything after the command)
            parts = cmd.split(maxsplit=1)
            if len(parts) > 1:
                identifier = parts[1]
                success, message, removed_note = notes_mode.remove_note(identifier)
                
                if success:
                    console.insert(END, f"[✓] {message}\n", "success")
                else:
                    console.insert(END, f"[!] {message}\n", "warning")
                
                console.insert(END, "\nUpdated TODO List:\n", "accent")
                display_notes(console)
            else:
                console.insert(END, "[!] Usage: rm <number> or rm <text>\n", "warning")
                console.insert(END, "Examples: 'rm 1', 'rm groceries'\n", "dim")
                
        elif cmd.lower() in ("clear", "clear all", "reset"):
            count = notes_mode.clear_all_notes()
            console.insert(END, f"[✓] Cleared {count} tasks\n", "success")
            console.insert(END, "\nTODO List (empty):\n", "accent")
            display_notes(console)
            
        elif cmd.lower() in ("list", "show", "ls"):
            console.insert(END, "\nYour TODO List:\n", "accent")
            display_notes(console)
            
        elif cmd.lower() in ("help", "?"):
            show_notes_help(console)
            
        else:
            # Regular note addition
            notes_mode.add_note(cmd)
            console.insert(END, f"[+] Added: {cmd}\n", "success")
            console.insert(END, "\nYour TODO List:\n", "accent")
            display_notes(console)

    # Reset status and clean up
    status_label.config(text="Ready")
    console.see(END)
    entry.delete(0, END)
    
    # Keep console manageable (max 100 lines)
    lines = console.get(1.0, END).count('\n')
    if lines > 100:
        console.delete(1.0, "10.0")

def show_notes_help(console):
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

def display_notes(console):
    """Clean notes display with numbering"""
    notes = notes_mode.get_notes()
    if not notes:
        console.insert(END, "  (no tasks yet)\n", "dim")
        return
        
    for i, note in enumerate(notes, 1):
        console.insert(END, f"  {i}. {note}\n")
    
    # Show total count
    console.insert(END, f"\nTotal: {len(notes)} task{'s' if len(notes) != 1 else ''}\n", "dim")

def on_up(entry):
    """Navigate command history up"""
    global history_index
    if history and history_index > 0:
        history_index -= 1
        entry.delete(0, END)
        entry.insert(0, history[history_index])
    return "break"

def on_down(entry):
    """Navigate command history down"""
    global history_index
    if history:
        if history_index < len(history) - 1:
            history_index += 1
            entry.delete(0, END)
            entry.insert(0, history[history_index])
        else:
            history_index = len(history)
            entry.delete(0, END)
    return "break"