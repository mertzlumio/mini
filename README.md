# 🧮 Mini-Player

A lightweight, always-on-top, multi-mode terminal-style GUI built with `tkinter`. Perfect for quickly executing shell commands, chatting with an AI assistant (Mistral), or managing your personal notes.

---

## 🚀 Features

- 🔁 **Mode switching**: 
  - `bash` – Run shell commands.
  - `chat` – Ask questions to Mistral's LLM.
  - `notes` – Maintain a TODO-style personal notes list.

- 🧠 **Mistral AI Chat Integration**:
  - Sends input to Mistral API in `chat` mode.
  - API key is securely handled via `config.py` or `.env`.

- 📒 **Notes**:
  - Notes are saved locally.
  - File path is defined in `config.py`.

- 🔐 **Minimal UI**:
  - Resizable and always-on-top.
  - Bottom-right auto-placement.
  - Keyboard-controlled:  
    - `Ctrl+M` to toggle mode  
    - `Esc` to quit  
    - `↑ / ↓` to cycle history

---

## 🧾 Setup

### 1. Clone the Repo

```bash
git clone https://github.com/mertzlumio/mini.git
cd mini

2. Install Dependencies

Only standard libraries (tkinter, subprocess, os, etc.) are used.

For Mistral support:

pip install requests

3. config.py

Edit config.py to set your Mistral API key and notes path:

# config.py
import os

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") or "your-api-key-here"
MISTRAL_MODEL = "mistral-medium"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

NOTES_FILE = os.path.expanduser("~/.local/share/mini-console/notes.txt")

    You can also set the MISTRAL_API_KEY using an environment variable.

    NOTES_FILE path can be customized for portability.

📦 Run It

python __main__.py

Use the input bar for commands, and watch the console print output or responses.
🧹 .gitignore Tip

Make sure to exclude sensitive or system files:

# .gitignore
__pycache__/
*.log
.env
*.txt

📜 License

MIT License.
🙋‍♂️ Author

Maintained by @YourUsername.


---

Let me know if you want:
- A badge (e.g. Python version, license)
- A screenshot preview
- Dark/light mode toggle for the README

I can also help you auto-generate a GitHub release or Python package structure later.
