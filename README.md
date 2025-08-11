# 🧮 Mini-Player

A compact, always-on-top utility window that packs powerful features into a minimal interface. Switch seamlessly between bash commands, AI chat, note-taking, and music playback - all from one tiny, keyboard-driven window.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

---

## ✨ What Makes Mini-Player Special

**🪟 Tiny but Mighty** - A small window that stays out of your way but gives you instant access to powerful tools

**🎛️ Four Modes, One Interface** - Seamlessly switch between different modes without opening new applications

**🤖 Meet Mini** - Your personal AI assistant with memory, web search, visual analysis, and extensible capabilities

**⚡ Lightning Fast** - Global hotkeys and keyboard-first design for maximum productivity

---

## 🚀 Core Features

### 🔄 **Multi-Mode Interface**
- **`BASH`** → Execute shell commands directly
- **`CHAT`** → Interact with Mini, your AI assistant
- **`NOTES`** → Quick todo list and note management  
- **`MUSIC`** → Control music playback and playlists

Switch modes instantly with `Ctrl+M` - no mouse needed!

### 🧠 **Mini: Your AI Assistant**
Mini isn't just a chatbot - it's a capable assistant with:

- **🧠 Long-term Memory** - Remembers facts, preferences, and conversations across sessions
- **🌐 Web Search** - Gets real-time information from the internet
- **👁️ Visual Analysis** - Can see and analyze your screen when you ask "what am I looking at?"
- **📝 Smart Task Management** - Automatically adds tasks when you mention them
- **🔧 Extensible Tools** - File reading, system integration, and more

### 🎵 **Music Mode**
- Play local music files
- Playlist management
- Playback controls (play/pause/skip)
- Volume control
- Supports common audio formats

### 📋 **Notes Mode**
- Quick task addition and removal
- Persistent local storage
- Simple numbered list interface
- Perfect for capture-and-go workflows

### ⌨️ **Keyboard-First Design**
- `Ctrl+M` - Switch modes
- `Ctrl+Shift+M` - Toggle window visibility (global hotkey)
- `↑/↓` - Command history navigation
- `Esc` - Exit application

---

## 🛠️ Quick Setup

### 1. **Clone & Navigate**
```bash
git clone https://github.com/mertzlumio/mini.git
cd mini
```

### 2. **Configure Your AI**
Create a `.env` file in the root directory:

```env
# Required: Your Mistral AI API key
MISTRAL_API_KEY=your-mistral-api-key-here

# Optional: Customize behavior
MISTRAL_MODEL=mistral-medium
MISTRAL_VISION_MODEL=pixtral-large-latest
NOTES_FILE=~/notes.txt
DEBUG=false
```

**Get your API key:** [Mistral AI Console](https://console.mistral.ai/)

### 3. **One-Command Setup**
```bash
python setup_and_run.py
```

This script automatically:
- Creates a virtual environment
- Installs all dependencies
- Configures global hotkeys
- Launches Mini-Player

---

## 🎮 How to Use

1. **Launch Mini-Player** - Run `python setup_and_run.py` or use `Ctrl+Shift+M` if already running
2. **Switch Modes** - Press `Ctrl+M` to cycle through BASH → CHAT → NOTES → MUSIC
3. **Start Typing** - Each mode has its own command interface
4. **Stay Productive** - The window stays on top and out of your way

### 💬 Chat with Mini

```
> hello Mini
Mini: Hello! I'm Mini, your AI assistant. I can help you with tasks, 
answer questions, analyze your screen, search the web, and remember 
things for future conversations. What can I help you with?

> what's the weather in Tokyo?
🛠️ Searching web for current weather...
Mini: The weather in Tokyo today is partly cloudy with temperatures 
around 22°C (72°F)...

> remember that I prefer dark themes
✅ Remembered: User prefers dark themes

> what am I looking at?
📸 Analyzing screen...
Mini: I can see you have a code editor open with a Python file. 
The code appears to be...
```

### 🎵 Music Mode Examples

```
> add ~/Music
✅ Added 45 tracks to playlist

> play
🎵 Now playing: Song Title - Artist

> next
⏭️ Skipped to: Next Song Title

> volume 70
🔊 Volume set to 70%
```

---

## 🔧 Advanced Features

### 🧠 **Mini's Memory System**
- **Facts**: Automatically stores important information
- **Preferences**: Remembers how you like things done
- **Search**: Query past conversations with `/search <query>`
- **Stats**: View memory stats with `/memory`

### 👁️ **Visual Analysis**
Ask Mini about your screen:
- "What am I looking at?"
- "Help me understand this interface"
- "Can you see what's displayed here?"

Mini will capture and analyze your screen content intelligently.

### 🛠️ **Extensible Tool System**
Mini can:
- Read files and documentation
- Execute system commands (when appropriate)
- Search the web for current information
- Manage your tasks and notes
- Remember context between sessions

---

## 🎨 Interface Preview

```
┌─────────────────────────────────────┐
│ [CHAT]                       Ready  │
├─────────────────────────────────────┤
│ > hello Mini                        │
│                                     │
│ Mini: Hello! I'm ready to assist    │
│ you. I can help with commands,      │
│ questions, tasks, and more.         │
│                                     │
│ Modes: BASH → CHAT → NOTES → MUSIC │
│ Ctrl+M to switch modes              │
│                                     │
│ > █                                 │
└─────────────────────────────────────┘
```
![Mini-Player Console Interface](https://github.com/mertzlumio/mini/screenshots)
---

## 📋 Requirements

- **Python 3.7+**
- **Dependencies**: Automatically installed by setup script
  - `python-dotenv` - Environment configuration
  - `requests` - API communication
  - `Pillow` - Screenshot functionality
  - `pynput` - Global hotkeys
  - `pygame` - Music playback (optional)

---

## 🗂️ Project Structure

```
mini/
├── 📄 README.md                   # You are here
├── 📄 requirements.txt            # Python dependencies  
├── 📄 setup_and_run.py           # One-command setup
├── 📄 .env                       # Your configuration
├── 📁 mini-player/               # Main application code
│   ├── 🐍 __main__.py            # Entry point
│   ├── 🐍 app.py                 # Main GUI application
│   ├── 🐍 config.py              # Configuration handling
│   └── 📁 modes/                 # Mode implementations
│       ├── 📁 bash/              # Shell command mode
│       ├── 📁 chat/              # AI assistant mode  
│       ├── 📁 notes/             # Note-taking mode
│       └── 📁 music/             # Music player mode
└── 📁 .venv/                     # Virtual environment
```

---

## 🤝 Contributing

Mini-Player is designed to be extensible! Want to add a new mode or enhance Mini's capabilities?

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 🎯 Ideas for Contributions
- New modes (calculator, timer, clipboard manager)
- Enhanced AI capabilities  
- Better music format support
- Plugin system
- Themes and customization
- Mobile companion app

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙋‍♂️ Author

**Mertz Lumio** ([@mertzlumio](https://github.com/mertzlumio))

Built with ❤️ for productivity enthusiasts who love minimal, powerful tools.

---

## ⭐ Show Your Support

If Mini-Player helps boost your productivity, give it a star! ⭐

**Questions?** Open an issue or reach out - Mini-Player is built for the community.

---

*Mini-Player: Big capabilities, tiny footprint.* 🚀