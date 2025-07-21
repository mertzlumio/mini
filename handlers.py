from modes import chat, bash, notes as notes_mode
from tkinter import END
import os

history = []
history_index = -1
current_dir = os.getcwd()
modes = ["bash", "chat", "notes"]
mode_index = 0
mode = modes[mode_index]

def toggle_mode(entry, console):
    global mode_index, mode
    mode_index = (mode_index + 1) % len(modes)
    mode = modes[mode_index]
    entry.config(bg="#202020" if mode == "bash" else ("#002b36" if mode == "chat" else "#1c1f26"))
    console.insert(END, f"🔁 Switched to {mode.upper()} mode\n")
    console.see(END)
    return "break"

def on_enter(entry, console):
    global history, history_index, current_dir, mode
    cmd = entry.get().strip()
    if not cmd:
        return

    history.append(cmd)
    history_index = len(history)
    console.insert(END, f"[{mode}] > {cmd}\n")

    if mode == "bash":
        output, current_dir = bash.run_bash_command(cmd, current_dir)
    elif mode == "chat":
        output = chat.call_mistral(cmd)
    elif mode == "notes":
        notes_mode.add_note(cmd)
        output = f"✅ Task added: {cmd}\n"
        console.insert(END, output)
        display_notes(console)
        entry.delete(0, END)
        return

    console.insert(END, output + "\n")
    console.see(END)
    entry.delete(0, END)

def display_notes(console):
    console.insert(END, "📝 TODO List:\n")
    for i, note in enumerate(notes_mode.get_notes(), 1):
        console.insert(END, f"  {i}. {note}\n")
    console.see(END)

def on_up(entry):
    global history_index
    if history:
        history_index = max(0, history_index - 1)
        entry.delete(0, END)
        entry.insert(0, history[history_index])
    return "break"

def on_down(entry):
    global history_index
    if history:
        history_index = min(len(history), history_index + 1)
        entry.delete(0, END)
        if history_index < len(history):
            entry.insert(0, history[history_index])
    return "break"
