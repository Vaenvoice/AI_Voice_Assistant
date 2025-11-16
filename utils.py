# utils.py
import re
import datetime
import random
import socket

# -------------------------
# Clean text for ML model
# -------------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# -------------------------
# Jokes
# -------------------------
JOKES = [
    "Why don't programmers like nature? Too many bugs.",
    "Why do Java developers wear glasses? Because they don't C sharp.",
    "Debugging: Being the detective in a crime movie where you are also the murderer.",
    "Why did the computer go to the doctor? It had a virus!"
]

def tell_joke() -> str:
    return random.choice(JOKES)

# -------------------------
# Time & Date
# -------------------------
def get_time() -> str:
    return datetime.datetime.now().strftime("%I:%M %p")

def get_date() -> str:
    return datetime.datetime.now().strftime("%B %d, %Y")

# -------------------------
# Wikipedia summary (simple)
# -------------------------
def get_summary(topic: str) -> str:
    try:
        import wikipedia
        topic = topic.strip()
        if not topic:
            return "Please ask about a specific topic."
        return wikipedia.summary(topic, sentences=2)
    except Exception:
        return "I couldn't find information on that topic."

# -------------------------
# Internet check
# -------------------------
def check_internet(host="8.8.8.8", port=53, timeout=2) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

# -------------------------
# Notes
# -------------------------
def write_note(text: str) -> str:
    try:
        with open("memory/notes.txt", "a", encoding="utf-8") as f:
            f.write(text.strip() + "\n")
        return "Note saved."
    except Exception:
        return "Failed to save note."