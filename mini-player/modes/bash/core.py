import subprocess
import os
import platform
import shlex

# List of known TUI applications that need a real terminal
INTERACTIVE_COMMANDS = {
    'nvim', 'vim', 'vi', 'nano', 'emacs', 'pico',
    'nmtui', 'htop', 'top', 'less', 'more', 'man',
    'ssh', 'mosh', 'tmux', 'screen', 'ranger', 'mc'
}

def open_in_new_terminal(command):
    """Opens a command in a new terminal window, OS-compatibly."""
    system = platform.system()
    try:
        if system == "Linux":
            # Try common terminal emulators on Linux
            terminals = ['gnome-terminal', 'konsole', 'xfce4-terminal', 'terminator', 'xterm']
            for terminal in terminals:
                try:
                    # Use -- to ensure arguments are passed to the command, not the terminal
                    subprocess.Popen([terminal, '-e', f"bash -c '{command}; exec bash'"])
                    return f"✅ Opened '{command}' in a new {terminal} window."
                except FileNotFoundError:
                    continue
            return "⚠️ Could not find a known terminal emulator to open the command."
        elif system == "Windows":
            subprocess.Popen(f'start cmd /c "{command}"', shell=True)
            return f"✅ Opened '{command}' in a new Command Prompt window."
        elif system == "Darwin": # macOS
            # Use osascript to run command in a new Terminal.app window
            script = f'tell app "Terminal" to do script "{command}"'
            subprocess.Popen(['osascript', '-e', script])
            return f"✅ Opened '{command}' in a new Terminal window."
        else:
            return f"⚠️ Unsupported OS for opening new terminals: {system}"
    except Exception as e:
        return f"⚠️ Failed to open new terminal: {str(e)}"

def handle_command(cmd, current_dir):
    """Handles bash commands by detecting their type."""
    cmd = cmd.strip()
    if not cmd:
        return "", current_dir

    # 1. Handle 'cd' command separately as it's a shell builtin
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

    # Use shlex to safely parse the command
    try:
        parts = shlex.split(cmd)
        base_command = parts[0]
    except ValueError:
        return "⚠️ Error: Unmatched quotes in command.", current_dir

    # 2. Detect interactive TUI commands
    if base_command in INTERACTIVE_COMMANDS:
        output = open_in_new_terminal(cmd)
        return output, current_dir

    # 3. Detect background processes (ending with '&')
    if cmd.endswith('&'):
        try:
            # Run without waiting and don't capture output
            subprocess.Popen(parts[:-1], cwd=current_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"✅ Started process '{cmd[:-1].strip()}' in the background.", current_dir
        except Exception as e:
            return f"⚠️ Failed to start background process: {str(e)}", current_dir

    # 4. Handle simple, synchronous commands
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            stderr=subprocess.STDOUT, 
            stdout=subprocess.PIPE,
            text=True, 
            cwd=current_dir,
            timeout=60 # Add a timeout to prevent indefinite hangs
        )
        output = result.stdout
        if not output.strip():
            return "(Command executed with no output)", current_dir
        return output, current_dir
    except subprocess.CalledProcessError as e:
        return e.output, current_dir
    except subprocess.TimeoutExpired:
        return "⚠️ Command timed out after 60 seconds.", current_dir
    except FileNotFoundError:
        return f"⚠️ Command not found: '{base_command}'", current_dir
    except Exception as e:
        return f"⚠️ An unexpected error occurred: {str(e)}", current_dir
