import os
import tkinter as tk
from dotenv import load_dotenv 
load_dotenv()
from tkinter import scrolledtext
from datetime import datetime
import types
from jarvis_whisper import Jarvis
from threading import Thread
import time

porcupine_thread = None
wakeword_active = False

ROOT_BG = "#0f1720"
USER_COLOR = "#9be15d"
JARVIS_COLOR = "#6aa6ff"
TIME_FMT = "%H:%M"

jarvis = Jarvis(
    use_online_stt=True,
    use_offline_stt=True,
    typed_fallback=True,
    gemini_api_key=os.getenv("GEMINI_API_KEY")
)

root = tk.Tk()
root.title("Jarvis — Chat")
root.geometry("800x650")
root.configure(bg=ROOT_BG)

chat = scrolledtext.ScrolledText(
    root, wrap=tk.WORD, font=("Consolas", 12), bg="#07101A", fg="#E6EEF3"
)
chat.configure(state="disabled")
chat.pack(padx=12, pady=(12, 6), fill=tk.BOTH, expand=True)


bottom = tk.Frame(root, bg=ROOT_BG)
bottom.pack(fill=tk.X, padx=12, pady=12)

entry = tk.Entry(
    bottom, font=("Consolas", 13), bg="#0b1a1f", fg="#E6EEF3", insertbackground="white"
)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 8))

send_btn = tk.Button(
    bottom, text="Send", width=10, bg="#1f6feb", fg="white", font=("Segoe UI", 10, "bold")
)
send_btn.pack(side=tk.LEFT, padx=(0, 8))

mic_btn = tk.Button(
    bottom, text="Speak", width=10, bg="#1f6feb", fg="white", font=("Segoe UI", 10, "bold")
)
mic_btn.pack(side=tk.LEFT)

wake_btn = tk.Button(
    bottom, text="Wake Word", width=12, bg="#3b82f6", fg="white", font=("Segoe UI", 10, "bold")
)
wake_btn.pack(side=tk.LEFT, padx=(8, 0))

status_label = tk.Label(root, text="Ready", bg=ROOT_BG, fg="#9fb3c8", font=("Segoe UI", 9))
status_label.pack(anchor="w", padx=14, pady=(0, 8))


def gui_append(sender: str, message: str, color: str) -> None:
    def _insert():
        ts = datetime.now().strftime(TIME_FMT)
        chat.configure(state="normal")
        chat.insert(tk.END, f"[{ts}] {sender}: ", ("sender",))
        chat.tag_config("sender", foreground=color)
        chat.insert(tk.END, message + "\n\n")
        chat.configure(state="disabled")
        chat.see(tk.END)
    root.after(0, _insert)

def gui_set_status(text: str) -> None:
    root.after(0, lambda: status_label.config(text=text))

def gui_type_reply(sender: str, message: str, color: str, speed: float = 0.015) -> None:
    ts = datetime.now().strftime(TIME_FMT)
    def start_typing():
        chat.configure(state="normal")
        chat.insert(tk.END, f"[{ts}] {sender}: ")
        chat.tag_add(f"tag_{ts}", "end-1c linestart", "end-1c")
        chat.tag_config(f"tag_{ts}", foreground=color)
        chat.configure(state="disabled")
        chat.see(tk.END)
        type_char(0)

    def type_char(idx: int):
        if idx >= len(message):
            chat.configure(state="normal")
            chat.insert(tk.END, "\n\n")
            chat.configure(state="disabled")
            chat.see(tk.END)
            return
        chat.configure(state="normal")
        chat.insert(tk.END, message[idx])
        chat.configure(state="disabled")
        chat.see(tk.END)
        delay = 5 if len(message) > 100 else int(speed * 1000)
        root.after(delay, lambda: type_char(idx + 1))

    root.after(0, start_typing)

_original_speak = jarvis.speak

def gui_speak(self, text: str):
    if text:
        def _speak_worker():
            try:
                _original_speak(text)
            except Exception as e:
                gui_append("Jarvis", f"TTS error: {e}", JARVIS_COLOR)
        Thread(target=_speak_worker, daemon=True).start()

jarvis.speak = types.MethodType(gui_speak, jarvis)

def process_text_input(text: str) -> None:
    text = text.strip()
    if not text:
        return
    gui_append("You", text, USER_COLOR)
    exit_triggers = ["exit", "quit", "shutdown", "goodbye", "bye", "band karo", "stop jarvis"]

    if any(trigger in text.lower() for trigger in exit_triggers):
        reply = "Goodbye! Shutting down system."
        gui_type_reply("Jarvis", reply, JARVIS_COLOR)
        jarvis.speak(reply)
        root.after(3000, root.destroy)
        return

    try:
        if hasattr(jarvis, "execute_basic_command"):
            command_reply = jarvis.execute_basic_command(text)
            if command_reply:
                gui_type_reply("Jarvis", command_reply, JARVIS_COLOR)
                jarvis.speak(command_reply)
                return
    except Exception as e:
        gui_append("System", f"Command Error: {e}", "#ff6666")

    gui_set_status("Thinking...")
    def _ai_worker():
        reply = "AI error."
        try:
            if hasattr(jarvis, "ai_chat"):
                reply = jarvis.ai_chat(text)
            else:
                reply = "Jarvis AI chat method missing."
        except Exception as e:
            reply = f"AI Error: {e}"
        
        gui_type_reply("Jarvis", str(reply), JARVIS_COLOR)
        jarvis.speak(reply)
        gui_set_status("Ready")

    Thread(target=_ai_worker, daemon=True).start()


def on_send(_event=None) -> None:
    txt = entry.get().strip()
    entry.delete(0, tk.END)
    if txt:
        Thread(target=process_text_input, args=(txt,), daemon=True).start()

send_btn.config(command=on_send)
root.bind("<Return>", on_send)

def on_mic_tap() -> None:
    mic_btn.config(state="disabled", text="Listening...")
    gui_set_status("Listening...")

    def _listen_worker():
        try:
            was_wake_active = wakeword_active
            if was_wake_active:
                stop_wakeword_listener()

            heard = jarvis.hybrid_stt()
            
            gui_set_status("")
            if not heard:
                gui_append("System", "Didn't catch that.", "#9fb3c8")
            else:
                process_text_input(heard)
            if was_wake_active:
                root.after(1000, start_wakeword_listener)

        except Exception as e:
            gui_append("System", f"Mic Error: {e}", "#ff6666")
        finally:
            root.after(0, lambda: mic_btn.config(state="normal", text="🎤 Speak"))
            root.after(0, lambda: gui_set_status("Ready"))

    Thread(target=_listen_worker, daemon=True).start()

mic_btn.config(command=on_mic_tap)

def on_wake_toggle():
    global wakeword_active
    if not wakeword_active:
        wake_btn.config(text="Stop Wake", bg="#ef4444")
        start_wakeword_listener()
    else:
        wake_btn.config(text="Wake Word", bg="#3b82f6")
        stop_wakeword_listener()

wake_btn.config(command=on_wake_toggle)

def start_wakeword_listener():
    global porcupine_thread, wakeword_active
    if wakeword_active: return

    if not hasattr(jarvis, "porcupine") or jarvis.porcupine is None:
        gui_append("System", "Porcupine unavailable.", "#ff6666")
        return

    wakeword_active = True
    gui_set_status("Wake Mode: Listening for 'Jarvis'...")

    def _wake_worker():
        while wakeword_active:
            try:
                if jarvis.recorder:
                    pcm = jarvis.recorder.read()
                    if jarvis.porcupine and jarvis.porcupine.process(pcm) >= 0:
                        gui_append("System", "Wake word detected!", "#9be15d")
                        try:
                            jarvis.recorder.stop()
                        except: pass

                        heard = jarvis.record_command_continuous()
                        try:
                            jarvis.recorder.start()
                        except: pass

                        text, _ = jarvis.transcribe_command(heard)
                        if text.strip():
                            process_text_input(text)
                        
            except Exception as e:
                print(f"Wake Loop Error: {e}")
                time.sleep(1)
    
    porcupine_thread = Thread(target=_wake_worker, daemon=True)
    porcupine_thread.start()

def stop_wakeword_listener():
    global wakeword_active
    wakeword_active = False
    gui_append("System", "Wake word stopped.", "#9fb3c8")

gui_append("System", "Jarvis Initialized. Type or Speak.", "#9fb3c8")
root.mainloop()