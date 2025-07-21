import os
from config import NOTES_FILE

notes = []

def load_notes():
    global notes
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            notes = [line.strip() for line in f if line.strip()]

def save_notes():
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        for note in notes:
            f.write(note + "\n")

def add_note(note):
    notes.append(note)
    save_notes()
    return note

def get_notes():
    return notes
