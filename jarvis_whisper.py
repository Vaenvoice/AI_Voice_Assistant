import os
import sys
import platform
import queue
import time
import tempfile
import asyncio
import wave
import webbrowser
import subprocess
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
import edge_tts
import whisper
from dotenv import load_dotenv
from google import genai
from threading import Thread

try:
    import pvporcupine
    from pvrecorder import PvRecorder
    PV_AVAILABLE = True
except ImportError:
    PV_AVAILABLE = False

class Jarvis:
    def __init__(self, gemini_api_key=None, use_porcupine=True, use_online_stt=False, use_offline_stt=True, typed_fallback=False):
        load_dotenv()
        self.use_online_stt = use_online_stt
        self.use_offline_stt = use_offline_stt
        self.typed_fallback = typed_fallback
        
        self.SAMPLE_RATE = 16000
        self.CHANNELS = 1
        self.BLOCK_SIZE = 1024
        self.MIN_SPEECH_RMS = 500
        self.SILENCE_FRAMES = 30
        self.COMMAND_MAX_DURATION = 20
        self.SILENCE_TIMEOUT = 15

        self.audio_queue = queue.Queue()
        self.use_porcupine = use_porcupine

        self.gemini_client = None
        if gemini_api_key:
            self.gemini_client = genai.Client(api_key=gemini_api_key)

        print("Loading Whisper model: small...")
        self.whisper_model = whisper.load_model("small")
        print("Whisper loaded.")

        self.porcupine = None
        self.recorder = None
        self.PORCUPINE_PPN = os.getenv("PPN_PATH", "wakewords/jarvis.ppn")
        self.PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", None)

        if self.use_porcupine:
            self.init_porcupine()

    def callback(self, indata, frames, time_, status):
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(indata.copy())

    def record_audio(self, duration):
        recorded = []
        with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=self.CHANNELS,
                            blocksize=self.BLOCK_SIZE, callback=self.callback):
            start_time = time.time()
            while time.time() - start_time < duration:
                recorded.append(self.audio_queue.get())
        audio_np = np.concatenate(recorded, axis=0)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(temp_file.name, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())
        return temp_file.name

    def speak(self, text, lang="en"):
        if not text or not str(text).strip():
            return

        text = str(text).strip()

        for char in text:
            if char in ['\u09f0', '\u09f1']:
                lang = "as"
                break

            if '\u0980' <= char <= '\u09ff': 
                lang = "bn"
                if '\u09f0' in text or '\u09f1' in text: 
                    lang = "as"
                break
            
            if '\u0b00' <= char <= '\u0b7f':
                lang = "or"
                break

            if '\u0900' <= char <= '\u097f': 
                if lang == "en":
                    lang = "hi" 
                break
            
            if '\u0a00' <= char <= '\u0a7f': 
                lang = "pa"
                break
            
            if '\u0a80' <= char <= '\u0aff': 
                lang = "gu"
                break
            
            if '\u0b80' <= char <= '\u0bff': 
                lang = "ta"
                break
            
            if '\u0c00' <= char <= '\u0c7f': 
                lang = "te"
                break
            
            if '\u0c80' <= char <= '\u0cff': 
                lang = "kn"
                break
            
            if '\u0d00' <= char <= '\u0d7f': 
                lang = "ml"
                break

            if '\u0600' <= char <= '\u06ff':
                lang = "ur"
                break

        try:
            voice_map = {
                "en": "en-IN-AaravNeural",
                "hi": "hi-IN-MadhurNeural",   
                "bn": "bn-IN-BashkarNeural",  
                "pa": "pa-IN-OjasNeural",     
                "gu": "gu-IN-NiranjanNeural", 
                "ta": "ta-IN-ValluvarNeural", 
                "te": "te-IN-MohanNeural",    
                "kn": "kn-IN-GaganNeural",    
                "ml": "ml-IN-MidhunNeural",   
                "mr": "mr-IN-ManoharNeural",  
                "ur": "ur-IN-SalmanNeural",   
                "as": "as-IN-PriyomNeural",   
                "ne": "ne-NP-SagarNeural",      
                "or": "or-IN-SubhasNeural",     
                "sa": "hi-IN-MadhurNeural",    
                "kok": "hi-IN-MadhurNeural",   
                "mai": "hi-IN-MadhurNeural",   
                "doi": "hi-IN-MadhurNeural",   
                "brx": "hi-IN-MadhurNeural",   
                "sd": "hi-IN-MadhurNeural",    
                "mni": "bn-IN-BashkarNeural",  
            }
            
            voice = voice_map.get(lang[:2], "en-IN-AaravNeural")

            communicate = edge_tts.Communicate(text, voice)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file.close()

            if platform.system() == "Windows":
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) #type: ignore

            asyncio.run(communicate.save(temp_file.name))

            try:
                audio = AudioSegment.from_mp3(temp_file.name)
                samples = np.array(audio.get_array_of_samples())
                if audio.channels == 2:
                    samples = samples.reshape((-1, 2))
                sd.play(samples, samplerate=audio.frame_rate)
                sd.wait()
            except Exception as play_error:
                print(f"Playback Error: {play_error}")

            try:
                os.unlink(temp_file.name)
            except:
                pass

        except Exception as e:
            print(f"TTS Error: {e}")

    def transcribe_command(self, file_path):
        result = self.whisper_model.transcribe(
            file_path,
            language=None,     
            fp16=False,       
            initial_prompt="The user speaks with an Indian accent. Hello Jarvis."
        )
        text = str(result.get("text", "")).strip()
        lang = result.get("language", "en")

        print(f"Detected Language: {lang} | Text: {text}")

        return text, lang

    def ai_chat(self, prompt):
        return self.ask_gemini(prompt)

    def ask_gemini(self, prompt):
        if not self.gemini_client:
            return f"[Gemini not initialized] You said: {prompt}"
        try:
            from datetime import datetime
            now = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
            sys_instruction = (
                f"Current System Time: {now}. "
                "You are Jarvis, a helpful AI assistant. "
                "Keep answers concise and human-like. "
                "If asked for time/date, use the System Time provided above."
            )
            
            chat = self.gemini_client.chats.create(
                model="gemini-2.5-flash",
                config=genai.types.GenerateContentConfig(
                    system_instruction=sys_instruction
                )
            )
            resp = chat.send_message(prompt)
            return resp.text
        except Exception as e:
            return f"[Gemini error] {e}"

    def init_porcupine(self):
        if not PV_AVAILABLE or not self.PORCUPINE_ACCESS_KEY or not os.path.exists(self.PORCUPINE_PPN):
            self.use_porcupine = False
            print("Porcupine disabled (Key/File missing).")
            return

        self.porcupine = pvporcupine.create(
            access_key=self.PORCUPINE_ACCESS_KEY,
            keyword_paths=[self.PORCUPINE_PPN]
        )
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.recorder.start()
        print("Porcupine initialized.")

    def record_command_continuous(self):
        print("Listening for command...")
        recorded = []
        silence_counter = 0
        speech_started = False
        start_time = time.time()

        with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=self.CHANNELS,
                            blocksize=self.BLOCK_SIZE, callback=self.callback):
            while True:
                if time.time() - start_time > self.COMMAND_MAX_DURATION:
                    break
                data = self.audio_queue.get()
                rms = np.sqrt(np.mean(data**2)) * 32767
                if rms > self.MIN_SPEECH_RMS:
                    speech_started = True
                    silence_counter = 0
                else:
                    if speech_started:
                        silence_counter += 1
                recorded.append(data)
                if speech_started and (silence_counter >= self.SILENCE_FRAMES or time.time() - start_time > self.SILENCE_TIMEOUT):
                    break

        audio_np = np.concatenate(recorded, axis=0)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(temp.name, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())
        return temp.name

    def execute_basic_command(self, text):
        text = text.lower().strip()
        def check(keywords):
            return any(k in text for k in keywords)

        if check(["time", "समय", "samay", "baj rahe"]):
            from datetime import datetime
            return f"The current time is {datetime.now().strftime('%I:%M %p')}."
        
        elif check(["date", "tariq", "tarikh", "तारीख", "din", "aaj kya hai"]):
            from datetime import datetime
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."

        elif check(["open youtube", "youtube kholo", "यूट्यूब खोलो", "youtube chalao"]):
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube..."
        
        elif check(["open google", "google kholo", "गूगल खोलो"]):
            webbrowser.open("https://www.google.com")
            return "Opening Google..."

        elif check(["open facebook", "facebook kholo", "फेसबुक खोलो"]):
            webbrowser.open("https://www.facebook.com")
            return "Opening Facebook..."
            
        elif check(["open instagram", "instagram kholo", "इंस्टाग्राम खोलो"]):
            webbrowser.open("https://www.instagram.com")
            return "Opening Instagram..."

        elif check(["open notepad", "notepad kholo", "नोटपैड खोलो"]):
            try:
                subprocess.Popen("notepad.exe")
                return "Opening Notepad."
            except:
                return "I couldn't find Notepad."

        elif check(["open calculator", "calculator kholo", "hisab kitab", "कैलकुलेटर"]):
            try:
                subprocess.Popen("calc.exe")
                return "Opening Calculator."
            except:
                return "I couldn't open the calculator."
        
        return None

    def hybrid_stt(self):
        try:
            path = self.record_command_continuous()
            txt, _ = self.transcribe_command(path)
            os.unlink(path)
            return txt
        except:
            return ""