"""
Bash mode - Terminal command execution
TODO: Upgrade to full PTY terminal emulator
"""
import subprocess
import os
from tkinter import END

# Module-level state
current_dir = os.getcwd()

def handle_input(user_input, console):
    """Handle bash command execution"""
    global current_dir
    
    cmd = user_input.strip()
    
    # Handle directory changes specially
    if cmd.startswith("cd"):
        _handle_cd_command(cmd, console)
    else:
        _execute_command(cmd, console)

def _handle_cd_command(cmd, console):
    """Handle directory change commands"""
    global current_dir
    
    try:
        path = cmd.split(maxsplit=1)[1] if len(cmd.split()) > 1 else os.path.expanduser("~")
        new_dir = os.path.abspath(os.path.join(current_dir, path))
        
        if os.path.isdir(new_dir):
            current_dir = new_dir
            console.insert(END, f"Changed directory to {new_dir}\n", "success")
        else:
            console.insert(END, f"⚠️ Directory not found: {new_dir}\n", "warning")
            
    except Exception as e:
        console.insert(END, f"⚠️ Error: {str(e)}\n", "error")

def _execute_command(cmd, console):
    """Execute shell command"""
    global current_dir
    
    try:
        # Execute command in current directory
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=current_dir,
            timeout=30  # 30 second timeout
        )
        
        # Display output
        if result.stdout:
            console.insert(END, result.stdout)
        
        if result.stderr:
            console.insert(END, result.stderr, "error")
            
        if result.returncode != 0:
            console.insert(END, f"\n[Exit code: {result.returncode}]\n", "warning")
            
    except subprocess.TimeoutExpired:
        console.insert(END, "⚠️ Command timed out (30s limit)\n", "warning")
    except Exception as e:
        console.insert(END, f"⚠️ Error executing command: {str(e)}\n", "error")

def get_current_directory():
    """Get current working directory"""
    return current_dir

def set_current_directory(path):
    """Set current working directory"""
    global current_dir
    if os.path.isdir(path):
        current_dir = path
        return True
    return False

def on_mode_enter(console):
    """Called when entering bash mode"""
    console.insert(END, f"Bash mode ready. Working directory: {current_dir}\n", "dim")
    console.insert(END, "Note: This will be upgraded to full PTY terminal soon.\n", "dim")

# Future PTY implementation notes:
# - Use pty module for true terminal emulation
# - Handle terminal control sequences (colors, cursor movement)
# - Support interactive programs (vim, top, etc.)
# - Proper signal handling (Ctrl+C, Ctrl+Z)
# - Terminal size management