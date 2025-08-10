import os
import sys
import subprocess
import platform

# --- Configuration ---
VENV_DIR = ".venv"
APP_DIR = os.path.dirname(os.path.abspath(__file__))  # Root directory where this script is
MAIN_APP_PATH = os.path.join(APP_DIR, "mini-player", "__main__.py")  # Main entry point
REQUIREMENTS_FILE = os.path.join(APP_DIR, "requirements.txt")

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
        return "python"
    else:
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

    # 3. Install Required Packages from requirements.txt
    if os.path.exists(REQUIREMENTS_FILE):
        print_status("Installing/Updating required Python packages...")
        run_command([venv_python_executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE], cwd=APP_DIR)
        print("All Python packages installed.")
    else:
        print(f"Warning: {REQUIREMENTS_FILE} not found. Skipping package installation.")

    # 4. Global Hotkey Setup Guidance (OS-specific)
    print_status("Global Hotkey Setup Guidance")
    if platform.system() == "Linux":
        print("On Linux, global hotkeys can be tricky due to display server permissions...")
        print("Ensure your user is in the 'input' group or run with `sudo` if necessary.")
    elif platform.system() == "Darwin":
        print("On macOS, add your Terminal/Python to Accessibility permissions if hotkeys don't work.")
    elif platform.system() == "Windows":
        print("On Windows, hotkeys should work out of the box unless another app is using them.")

    # 5. Launch the Application
    print_status("Launching Mini Player...")
    print("Press Ctrl+Shift+M to toggle window visibility.")
    print("Press Escape to exit.")

    run_command([venv_python_executable, "__main__.py"], cwd=os.path.join(APP_DIR, "mini-player"))
    print_status("Mini Player exited.")

if __name__ == "__main__":
    setup_and_run()
