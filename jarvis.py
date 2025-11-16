# jarvis.py
import os
import json
import joblib
import webbrowser
import traceback
import time

import speech_recognition as sr
import pyttsx3

from utils import (
    clean_text,
    tell_joke,
    get_time,
    get_date,
    get_summary,
    check_internet,
    write_note,
)

# Optional imports for Vosk (offline fallback)
try:
    from vosk import Model as VoskModel, KaldiRecognizer
    VOSK_AVAILABLE = True
except Exception:
    VOSK_AVAILABLE = False

# Gemini imports
try:
    from google import genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

MODEL_PATH = os.path.join("models", "intent_pipeline.pkl")
VOSK_MODEL_DIR = "vosk-model-small-en-us-0.15"


class Jarvis:
    def __init__(self, use_online_stt=True, use_offline_stt=True, typed_fallback=False, gemini_api_key=None):
        # Flags
        self.use_online_stt = use_online_stt
        self.use_offline_stt = use_offline_stt
        self.typed_fallback = typed_fallback

        # Load ML Intent Model
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Intent model not found at {MODEL_PATH}")
        self.model = joblib.load(MODEL_PATH)

        # TTS
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 160)

        # Recognizer
        self.recognizer = sr.Recognizer()

        # Microphone
        self.mic = None
        try:
            self.mic = sr.Microphone()
            print("Microphone initialized (default device).")
        except Exception:
            self.mic = None
            print("No microphone detected. Voice mode disabled.")

        # Vosk offline
        self.vosk_recognizer = None
        if self.use_offline_stt and VOSK_AVAILABLE and os.path.isdir(VOSK_MODEL_DIR):
            try:
                vosk_model = VoskModel(VOSK_MODEL_DIR)
                self.vosk_recognizer = KaldiRecognizer(vosk_model, 16000)
                print("Vosk model loaded for offline fallback.")
            except Exception:
                self.vosk_recognizer = None

        # Runtime flags
        self.voice_mode = bool(self.mic)
        self.wake_words = ["hey jarvis", "jarvis"]

        # Gemini AI client
        self.gemini = None
        if GEMINI_AVAILABLE and gemini_api_key:
            try:
                self.gemini = genai.Client(api_key=gemini_api_key)
                print("Gemini client initialized.")
            except Exception as e:
                print("Failed to init Gemini:", e)

        print("Jarvis ready.\n")

    # -------------------------
    # TTS
    # -------------------------
    def speak(self, text: str):
        if not text:
            return
        print("Jarvis:", text)
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:
            print("TTS failed.")

    # -------------------------
    # Gemini AI Chat
    # -------------------------
    def ai_chat(self, prompt: str) -> str:
        if not self.gemini:
            return "Gemini AI not available."
        try:
            chat = self.gemini.chats.create(model="gemini-2.5-flash")
            resp = chat.send_message(prompt)
            return resp.text
        except Exception as e:
            return f"Gemini AI error: {e}"

    # -------------------------
    # Google STT
    # -------------------------
    def listen_google(self, timeout=5, phrase_time_limit=6) -> str:
        if self.mic is None:
            return ""
        with self.mic as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.35)
            except Exception:
                pass
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            except Exception:
                return ""
        try:
            return self.recognizer.recognize_google(audio).lower()
        except Exception:
            return ""

    # -------------------------
    # Vosk STT
    # -------------------------
    def listen_vosk(self, timeout=5, phrase_time_limit=6) -> str:
        if not self.vosk_recognizer or self.mic is None:
            return ""
        with self.mic as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
            except:
                pass
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            except Exception:
                return ""
        try:
            data = audio.get_raw_data()
            if self.vosk_recognizer.AcceptWaveform(data):
                return json.loads(self.vosk_recognizer.Result()).get("text", "").lower()
            else:
                return json.loads(self.vosk_recognizer.PartialResult()).get("partial", "").lower()
        except:
            return ""

    # -------------------------
    # Hybrid STT
    # -------------------------
    def hybrid_stt(self):
        if self.mic is None:
            return input("Type command: ").lower() if self.typed_fallback else ""
        if self.use_online_stt and check_internet():
            try:
                return self.listen_google()
            except:
                return self.listen_vosk() if self.use_offline_stt else ""
        elif self.use_offline_stt:
            return self.listen_vosk()
        return ""

    # -------------------------
    # Wake word detection
    # -------------------------
    def listen_for_wake_word(self):
        if not self.voice_mode:
            return
        self.speak("Waiting for wake word.")
        while True:
            text = self.hybrid_stt()
            if any(w in text for w in self.wake_words):
                self.speak("Yes?")
                return
            time.sleep(0.2)

    # -------------------------
    # Listen & process
    # -------------------------
    def listen_and_process(self):
        self.speak("I'm listening.")
        command = self.hybrid_stt()
        if not command:
            if self.typed_fallback:
                command = input("Type command: ").strip().lower()
            else:
                self.speak("I didn't catch that.")
                return

        print("You:", command)
        cleaned = clean_text(command)
        try:
            intent = self.model.predict([cleaned])[0]
        except:
            intent = "unknown"

        self.handle_intent(intent, command)

    # -------------------------
    # Intent router
    # -------------------------
    def handle_intent(self, intent, text):
        if intent == "time":
            self.speak(get_time())
        elif intent == "date":
            self.speak(get_date())
        elif intent.startswith("open"):
            url = "https://www.google.com"
            if "youtube" in text:
                url = "https://www.youtube.com"
            elif "google" in text:
                url = "https://www.google.com"
            elif "instagram" in text:
                url = "https://www.instagram.com"
            webbrowser.open(url)
            self.speak("Opening website.")
        elif intent in ("search_web", "search"):
            q = text.replace("search", "").strip()
            url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
            webbrowser.open(url)
            self.speak(f"Searching Google for {q}")
        elif intent == "joke":
            self.speak(tell_joke())
        elif intent in ("take_note", "note"):
            self.speak(write_note(text))
        elif intent in ("ask_ai", "wikipedia", "unknown"):
            # fallback to Gemini AI
            reply = self.ai_chat(text)
            self.speak(reply)
        elif intent in ("smalltalk_greeting", "greeting"):
            self.speak("Hello Pragyan, how can I help you?")
        elif intent in ("system_exit", "exit", "quit"):
            self.speak("Goodbye!")
            raise SystemExit()
        else:
            # unknown -> search web
            self.speak("I didn't fully understand that. Searching Google.")
            webbrowser.open("https://www.google.com/search?q=" + text.replace(" ", "+"))

    # -------------------------
    # Main run loop
    # -------------------------
    def run(self):
        self.speak("Jarvis online.")
        while True:
            if self.voice_mode:
                self.listen_for_wake_word()
                self.listen_and_process()
            elif self.typed_fallback:
                cmd = input("Type command (or 'exit'): ").strip().lower()
                if cmd in ("exit", "quit", "bye"):
                    self.speak("Goodbye!")
                    break
                cleaned = clean_text(cmd)
                try:
                    intent = self.model.predict([cleaned])[0]
                except:
                    intent = "unknown"
                self.handle_intent(intent, cmd)
            else:
                self.speak("No input mode available. Exiting.")
                break