# gui.py
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
from datetime import datetime
import types
import time

from jarvis import Jarvis
from utils import clean_text
from config import GEMINI_API_KEY
# -----------------------
# Create Jarvis instance
# -----------------------
jarvis = Jarvis(
    use_online_stt=True,
    use_offline_stt=True,
    typed_fallback=True,
    gemini_api_key= GEMINI_API_KEY  # if you use genai client, pass your key here; otherwise keep None
)

# Keep reference to original speak (so TTS still works)
_original_speak = jarvis.speak

# -----------------------
# GUI setup
# -----------------------
ROOT_BG = "#0f1720"
USER_COLOR = "#9be15d"
JARVIS_COLOR = "#6aa6ff"
TIME_FMT = "%H:%M"

root = tk.Tk()
root.title("Jarvis — Chat")
root.geometry("720x600")
root.configure(bg=ROOT_BG)

# Chat area
chat = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 12), bg="#07101A", fg="#E6EEF3")
chat.configure(state="disabled")
chat.pack(padx=12, pady=(12,6), fill=tk.BOTH, expand=True)

# Bottom frame with input + buttons
bottom = tk.Frame(root, bg=ROOT_BG)
bottom.pack(fill=tk.X, padx=12, pady=12)

entry = tk.Entry(bottom, font=("Consolas", 13), bg="#0b1a1f", fg="#E6EEF3", insertbackground="white")
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,8))

send_btn = tk.Button(bottom, text="Send", width=10, bg="#1f6feb", fg="white", font=("Segoe UI", 10, "bold"))
send_btn.pack(side=tk.LEFT, padx=(0,8))

mic_btn = tk.Button(bottom, text="🎤 Speak", width=10, bg="#1f6feb", fg="white", font=("Segoe UI", 10, "bold"))
mic_btn.pack(side=tk.LEFT)

status_label = tk.Label(root, text="", bg=ROOT_BG, fg="#9fb3c8", font=("Segoe UI", 9))
status_label.pack(anchor="w", padx=14, pady=(0,8))

# -----------------------
# GUI helpers (thread-safe)
# -----------------------
def gui_append(sender: str, message: str, color: str):
    """Schedule insertion into chat (thread-safe)."""
    def _insert():
        ts = datetime.now().strftime(TIME_FMT)
        chat.configure(state="normal")
        chat.insert(tk.END, f"[{ts}] {sender}: ", ("sender",))
        chat.tag_config("sender", foreground=color)
        chat.insert(tk.END, message + "\n\n")
        chat.configure(state="disabled")
        chat.see(tk.END)
    root.after(0, _insert)

def gui_set_status(text: str):
    root.after(0, lambda: status_label.config(text=text))

# -----------------------
# Typing animation helper
# -----------------------
def gui_type_reply(sender: str, message: str, color: str, speed=0.015):
    """Show message char-by-char in chat (runs in GUI thread via after)."""
    ts = datetime.now().strftime(TIME_FMT)
    def start():
        chat.configure(state="normal")
        chat.insert(tk.END, f"[{ts}] {sender}: ")
        chat.tag_add(f"tag_{ts}", "end-1c linestart", "end-1c")
        chat.tag_config(f"tag_{ts}", foreground=color)
        chat.configure(state="disabled")
        chat.see(tk.END)
        # begin typing loop
        _type_char(0, "")
    def _type_char(idx, built):
        if idx >= len(message):
            chat.configure(state="normal")
            chat.insert(tk.END, "\n\n")
            chat.configure(state="disabled")
            chat.see(tk.END)
            return
        # insert next character
        chat.configure(state="normal")
        chat.insert(tk.END, message[idx])
        chat.configure(state="disabled")
        chat.see(tk.END)
        root.after(int(speed*1000), lambda: _type_char(idx+1, built + message[idx]))
    root.after(0, start)

# -----------------------
# Bind Jarvis.speak to GUI output + original TTS
# -----------------------
def gui_speak(self, text: str):
    if text:
        gui_append("Jarvis", text, JARVIS_COLOR)
    # still call original to keep TTS behavior
    try:
        _original_speak(text)
    except Exception:
        pass

jarvis.speak = types.MethodType(gui_speak, jarvis)

# -----------------------
# Core processing
# -----------------------
def process_text_input(text: str):
    text = text.strip()
    if not text:
        return
    gui_append("You", text, USER_COLOR)

    # predict intent
    cleaned = clean_text(text)
    try:
        intent = jarvis.model.predict([cleaned])[0]
    except Exception:
        intent = "unknown"

    # if recognized intent that is not 'unknown' and not AI chat, handle directly
    non_ai_intents = {"time", "date", "joke", "take_note", "note", "open_website", "search_web",
                      "search", "smalltalk_greeting", "greeting", "system_exit", "exit", "quit"}
    if intent in non_ai_intents and intent != "unknown":
        # Let jarvis handle (it will call speak -> routed to GUI)
        try:
            jarvis.handle_intent(intent, text)
        except Exception as e:
            # fallback to AI if handler fails
            gui_set_status("Intent handler error, falling back to AI...")
            reply = jarvis.ai_chat(text) if hasattr(jarvis, "ai_chat") else "AI not available."
            gui_type_reply("Jarvis", reply, JARVIS_COLOR)
    else:
        # Use AI chat (either unknown or explicit ask_ai)
        gui_set_status("Thinking...")
        # run AI in background
        def _ai_worker():
            try:
                if hasattr(jarvis, "ai_chat"):
                    reply = jarvis.ai_chat(text)
                else:
                    reply = "Gemini/AI not configured."
            except Exception as exc:
                reply = f"AI error: {exc}"
            gui_set_status("")
            # animate reply
            gui_type_reply("Jarvis", reply, JARVIS_COLOR)
            # speak after typing (call TTS directly)
            try:
                _original_speak(reply)
            except:
                pass
        Thread(target=_ai_worker, daemon=True).start()

# -----------------------
# Send button / Enter
# -----------------------
def on_send(_event=None):
    txt = entry.get().strip()
    entry.delete(0, tk.END)
    Thread(target=process_text_input, args=(txt,), daemon=True).start()

send_btn.config(command=on_send)
root.bind("<Return>", on_send)

# -----------------------
# Tap-to-speak (Option B)
# -----------------------
def on_mic_tap():
    # disable button while working
    mic_btn.config(state="disabled", text="Listening...")
    gui_set_status("Listening...")
    def _listen_worker():
        try:
            # call hybrid_stt with safe defaults
            heard = jarvis.hybrid_stt()
            gui_set_status("")
            if not heard:
                gui_append("Jarvis", "Sorry, I didn't catch that.", JARVIS_COLOR)
            else:
                # show user text then process
                gui_append("You", heard, USER_COLOR)
                process_text_input(heard)
        except Exception as e:
            gui_append("Jarvis", f"Listening error: {e}", JARVIS_COLOR)
        finally:
            root.after(0, lambda: mic_btn.config(state="normal", text="🎤 Speak"))
            root.after(0, lambda: gui_set_status(""))
    Thread(target=_listen_worker, daemon=True).start()

mic_btn.config(command=on_mic_tap)

# disable mic button if no mic available
if jarvis.mic is None:
    mic_btn.config(state="disabled", text="No Mic")

# -----------------------
# Start GUI
# -----------------------
gui_append("System", "Jarvis is ready. Type or tap 🎤 to speak.", "#9fb3c8")
root.mainloop()