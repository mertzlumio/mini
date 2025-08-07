import os
import sys
import subprocess
import platform

# --- Configuration ---
VENV_DIR = ".venv"
APP_DIR = os.path.dirname(os.path.abspath(__file__)) # Directory where this script is
MAIN_APP_PATH = os.path.join(APP_DIR, "__main__.py")

# Required Python packages
REQUIRED_PACKAGES = [
    "python-dotenv",
    # pynput and python-xlib are preferred for global hotkeys on Linux
    # keyboard is a fallback and generally works well on Windows/macOS
    "pynput",
    "python-xlib" # For pynput on Linux (Xorg)
]

# --- Helper Functions ---

def print_status(message):
    """Prints a status message to the console."""
    print(f"\n--- {message} ---")

def run_command(command, cwd=None, check=True):
    """Runs a shell command and prints its output."""
    try:
        result = subprocess.run(command, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Command not found. Make sure '{command[0]}' is in your PATH.")
        sys.exit(1)

def get_python_executable():
    """Determines the correct Python executable path."""
    if platform.system() == "Windows":
        return "python" # On Windows, 'python' usually points to the installed Python
    else:
        # Try 'python3' first, then 'python'
        try:
            subprocess.run(["python3", "--version"], check=True, capture_output=True)
            return "python3"
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(["python", "--version"], check=True, capture_output=True)
                return "python"
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Error: Python (python3 or python) not found in your PATH.")
                sys.exit(1)

# --- Main Setup and Run Logic ---

def setup_and_run():
    print_status("Starting Mini Player Setup and Launch")

    # 1. Check for Python
    base_python = get_python_executable()
    print(f"Detected base Python executable: {base_python}")

    # 2. Virtual Environment Setup
    venv_path = os.path.join(APP_DIR, VENV_DIR)
    if not os.path.exists(venv_path):
        print_status(f"Creating virtual environment at {venv_path}")
        run_command([base_python, "-m", "venv", VENV_DIR], cwd=APP_DIR)
    else:
        print_status("Virtual environment already exists.")

    # Determine venv Python executable
    if platform.system() == "Windows":
        venv_python_executable = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        venv_python_executable = os.path.join(venv_path, "bin", "python")

    if not os.path.exists(venv_python_executable):
        print(f"Error: Virtual environment Python executable not found at {venv_python_executable}")
        sys.exit(1)

    # 3. Install Required Packages
    print_status("Installing/Updating required Python packages...")
    pip_install_command = [venv_python_executable, "-m", "pip", "install"] + REQUIRED_PACKAGES
    run_command(pip_install_command, cwd=APP_DIR)
    print("All Python packages installed.")

    # 4. Global Hotkey Setup Guidance (OS-specific)
    print_status("Global Hotkey Setup Guidance")
    if platform.system() == "Linux":
        print("On Linux, global hotkeys can be tricky due to display server permissions.")
        print("The application tries to use 'pynput' first, which often works without root if 'python-xlib' is installed.")
        print("However, if you still face 'permission denied' or 'couldn't connect to display' errors:")
        print("  a) Ensure your user is part of the 'input' group: `sudo usermod -aG input $USER` (then log out/in).")
        print("  b) Temporarily grant display access to root (if running with sudo): `xhost +si:localuser:root` (from your regular user's terminal). Remember to revoke with `xhost -si:localuser:root` after use.")
        print("  c) If 'keyboard' library is used as a fallback and fails, running the app with `sudo` might be required:")
        print(f"     `sudo {venv_python_executable} {MAIN_APP_PATH}`")
        print("     (Remember the security implications of running GUI apps as root).")
        print("  d) Check your desktop environment's own hotkey settings for conflicts with Ctrl+Shift+M.")
    elif platform.system() == "Darwin": # macOS
        print("On macOS, applications often require 'Accessibility' permissions to capture global hotkeys.")
        print("If the hotkey (Ctrl+Shift+M) doesn't work, you might need to:")
        print("  Go to System Settings (or System Preferences) -> Privacy & Security -> Accessibility.")
        print("  Add your Terminal application (or Python executable) to the list and grant it permission.")
    elif platform.system() == "Windows":
        print("On Windows, global hotkeys with 'keyboard' or 'pynput' should generally work out-of-the-box.")
        print("If not, ensure no other application is already using Ctrl+Shift+M.")
    else:
        print("Unsupported operating system for specific hotkey guidance.")

    # 5. Launch the Application
    print_status("Launching Mini Player...")
    print("Press Ctrl+Shift+M to toggle the window visibility.")
    print("Press Escape to exit the application (globally if pynput is used, or locally if keyboard is used).")
    
    # Execute the main application using the virtual environment's Python
    # This needs to be run in the foreground to keep the app alive
    run_command([venv_python_executable, MAIN_APP_PATH], cwd=APP_DIR)

    print_status("Mini Player exited.")

if __name__ == "__main__":
    setup_and_run()
