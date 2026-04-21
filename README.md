<h1 align="center"><b>AI Voice Assistant</b></h1>

<p align="justify">
  A desktop-based AI assistant that uses <b><a href="https://ai.google.dev/">Google Gemini</a></b> for intelligence, <b><a href="https://openai.com/index/whisper/">OpenAI Whisper</a></b> for speech recognition, and <b><a href="https://picovoice.ai/platform/porcupine">Porcupine</a></b> for wake-word detection. <br>Built with Python and Tkinter, it features a modern dark-mode GUI and supports offline system control commands.
</p>

<br>

## **📌 Project Overview**

<p align="justify">This project is a personal AI assistant designed to run on a local machine. It combines the accuracy of cloud-based LLMs (Gemini) with efficient local wake-word detection. Users can interact via voice or text to get answers, control their PC, or launch applications through a clean, responsive interface.
</p>

<br>

## **🧪 Features**

* **Hybrid Speech Recognition:** Uses **Porcupine** for instant wake-word detection ("Jarvis") and **OpenAI Whisper** for high-accuracy command transcription.
* **Intelligent Conversations:** Powered by **Google Gemini 1.5 Flash** for human-like, context-aware responses.
* **Modern GUI:** A dark-themed **Tkinter** interface with real-time typing effects and status indicators.
* **System Control:** Offline commands to open apps (Notepad, Calculator), websites (YouTube, Google), and check time/date.
* **Voice Feedback:** Natural-sounding Text-to-Speech using **Edge TTS**.
* **Multithreading:** Non-blocking UI ensures the assistant listens and speaks without freezing the application.

<br>

## **💻 Tech Stack**

* **Programming Language:** Python
* **AI Model (LLM):** Google Gemini (via `google-genai`)
* **Speech-to-Text (STT):** OpenAI Whisper (Local Model)
* **Wake Word:** Picovoice Porcupine
* **Text-to-Speech (TTS):** Edge TTS
* **GUI Framework:** Tkinter (Customized)
* **Audio Handling:** SoundDevice, PvRecorder, PyDub

<br>

## **📁 Folder Structure**

```bash
AI_Voice_Assistant/
├── gui.py                  
├── jarvis_whisper.py       
├── requirements.txt        
├── .env                    
├── wakewords/
│   └── jarvis.ppn          
└── README.md                

```
## **🚀 Getting Started**
1.&nbsp;Clone the Repository

```bash
git clone [https://github.com/YourUsername/AI_Voice_Assistant.git](https://github.com/YourUsername/AI_Voice_Assistant.git)
cd AI_Voice_Assistant
```
2.&nbsp;Set Up a Virtual Environment
<br>For Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```
For macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3.&nbsp;Install Dependencies

#### <b>Note: You must have <a href="https://www.ffmpeg.org/download.html">FFmpeg</a> installed on your system for audio processing.</b>
```bash
pip install -r requirements.txt
```
4.&nbsp;Configure API Keys
<br>Create a file named `.env` in the root folder and add your keys:

```bash
GEMINI_API_KEY=your_google_gemini_key_here
PORCUPINE_ACCESS_KEY=your_picovoice_access_key_here
PPN_PATH=wakewords/jarvis.ppn
```

5.&nbsp;Run the Application

```bash
python gui.py
```
## **📊 How it Works**
Wake Mode: The system runs in a low-power loop listening for the keyword "Jarvis" using Porcupine.

Listening: Once triggered (or if the "Speak" button is pressed), it records audio and transcribes it using Whisper.

Routing:

Offline Commands: If the text matches a system command (e.g., "`Open Calculator`"), it executes immediately.

AI Query: If no command matches, the text is sent to Google Gemini.

Response: The AI's text response is displayed in the GUI and spoken aloud via Edge TTS.

## **🛠 Troubleshooting**
FFmpeg Error: If the app crashes when trying to speak or listen, ensure FFmpeg is added to your system PATH.

Wake Word Issues: Ensure your jarvis.ppn file matches your OS (Windows/Linux/Mac). You can download platform-specific files from the [Picovoice Console](https://picovoice.ai/platform/porcupine).

## **📄 License**
This project is licensed under the MIT License.

## **📬 Contact**
For any inquiries or contributions, please contact:
<br>[Vaenvoice](https://github.com/Vaenvoice)
<br>[proxybinder](https://github.com/proxybinder)
