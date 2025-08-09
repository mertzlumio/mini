import subprocess
import os

def handle_command(cmd, current_dir):
    """Handles bash commands."""
    if cmd.startswith("cd"):
        try:
            path = cmd.split(maxsplit=1)[1] if len(cmd.split()) > 1 else os.path.expanduser("~")
            new_dir = os.path.abspath(os.path.join(current_dir, path))
            if os.path.isdir(new_dir):
                return f"Changed directory to {new_dir}", new_dir
            else:
                return f"⚠️ Directory not found: {new_dir}", current_dir
        except Exception as e:
            return f"⚠️ Error: {str(e)}", current_dir
    else:
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True, cwd=current_dir)
            return output, current_dir
        except subprocess.CalledProcessError as e:
            return e.output, current_dir
        except subprocess.TimeoutExpired:
            return "⚠️ Command timed out.", current_dir
