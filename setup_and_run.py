import os
import sys
import subprocess
import platform
import re

# --- Configuration ---
VENV_DIR = ".venv"
APP_DIR = os.path.dirname(os.path.abspath(__file__))  # Root directory where this script is
MAIN_APP_PATH = os.path.join(APP_DIR, "mini-player", "__main__.py")  # Main entry point
REQUIREMENTS_FILE = os.path.join(APP_DIR, "requirements.txt")
ENV_PATH = os.path.join(APP_DIR, ".env")
ENV_EXAMPLE_PATH = os.path.join(APP_DIR, ".env.example")

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

def check_python_version():
    """Checks if the installed Python version meets the minimum requirement."""
    print_status("Checking Python version...")
    if sys.version_info < (3, 7):
        print(f"Error: Your Python version is {sys.version.split()[0]}.")
        print("This project requires Python 3.7 or higher.")
        sys.exit(1)
    else:
        print(f"Python version {sys.version.split()[0]} is compatible.")

def create_directories_from_env_example():
    """Reads .env.example and creates directories specified by _DIR variables."""
    if not os.path.exists(ENV_EXAMPLE_PATH):
        print(f"Warning: {ENV_EXAMPLE_PATH} not found. Cannot create directories.")
        return

    print_status("Creating necessary directories from .env.example")
    with open(ENV_EXAMPLE_PATH, "r") as f:
        for line in f:
            if "_DIR=" in line:
                match = re.search(r'_DIR="?(.+?)"?$', line)
                if match:
                    # Strip any quotes and whitespace
                    relative_path = match.group(1).strip('"\' \n')
                    # Split path and get the directory part if it's a file
                    if '.' in os.path.basename(relative_path):
                        dir_path = os.path.dirname(relative_path)
                    else:
                        dir_path = relative_path
                    
                    full_path = os.path.join(APP_DIR, dir_path)
                    if full_path and not os.path.exists(full_path):
                        try:
                            os.makedirs(full_path, exist_ok=True)
                            print(f"Created directory: {full_path}")
                        except OSError as e:
                            print(f"Error creating directory {full_path}: {e}")

# --- Main Setup and Run Logic ---

def setup_and_run():
    print_status("Starting Mini Player Setup and Launch")

    # 1. Check Python Version
    check_python_version()

    # 2. Check for Python
    base_python = get_python_executable()
    print(f"Detected base Python executable: {base_python}")

    # 3. Virtual Environment Setup
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

    # 4. Install Required Packages from requirements.txt
    if os.path.exists(REQUIREMENTS_FILE):
        print_status("Installing/Updating required Python packages...")
        run_command([venv_python_executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE], cwd=APP_DIR)
        print("All Python packages installed.")
    else:
        print(f"Warning: {REQUIREMENTS_FILE} not found. Skipping package installation.")

    # 5. Setting up .env with Mistral API Key
    if not os.path.exists(ENV_PATH):
        print_status("Setting up .env file...")
        mistral_api_key = input("Please enter your Mistral API Key: ")
        env_content = f"MISTRAL_API_KEY=\"{mistral_api_key}\"\n"
        
        # Check if .env.example exists and copy its contents
        if os.path.exists(ENV_EXAMPLE_PATH):
            print("Copying contents from .env.example...")
            with open(ENV_EXAMPLE_PATH, "r") as src:
                lines = src.readlines()
                for line in lines:
                    if not line.startswith("MISTRAL_API_KEY="):
                        env_content += line
        
        with open(ENV_PATH, "w") as dst:
            dst.write(env_content)
        
        print("Successfully created .env file.")
        print("Please ensure you configure any necessary paths in the .env file if required by the application.")

        # Create directories after creating .env
        create_directories_from_env_example()
    else:
        print_status(".env file already exists. Skipping creation.")
        # If .env exists, we should still create the directories for a smooth experience
        create_directories_from_env_example()

    # 6. Global Hotkey Setup Guidance (OS-specific)
    print_status("Global Hotkey Setup Guidance")
    if platform.system() == "Linux":
        print("On Linux, global hotkeys can be tricky due to display server permissions...")
        print("Ensure your user is in the 'input' group or run with `sudo` if necessary.")
    elif platform.system() == "Darwin":
        print("On macOS, add your Terminal/Python to Accessibility permissions if hotkeys don't work.")
    elif platform.system() == "Windows":
        print("On Windows, hotkeys should work out of the box unless another app is using them.")

    # 7. Launch the Application
    print_status("Launching Mini Player...")
    print("Press Ctrl+Shift+M to toggle window visibility.")
    print("Press Escape to exit.")

    run_command([venv_python_executable, "__main__.py"], cwd=os.path.join(APP_DIR, "mini-player"))
    print_status("Mini Player exited.")

if __name__ == "__main__":
    setup_and_run()