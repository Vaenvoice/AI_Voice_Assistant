🚀 AI Voice Assistant (Jarvis) — Python + Gemini + Offline STT

Your personal offline + online AI voice assistant with:

✔ Wake-word activation (“Hey Jarvis”)
✔ Online Google STT
✔ Offline Vosk STT
✔ Gemini AI chat responses
✔ GUI Chat Window (Tkinter)
✔ Intent classification (ML model)
✔ Notes, jokes, time/date, search, websites, AI chat

⸻

📁 Project Structure
AI_Voice_Assistant/
│
├── assistant.py        # Runs Jarvis (voice mode)
├── gui.py              # GUI chat mode
├── jarvis.py           # Main assistant class
├── utils.py
├── train_intent.py
│
├── models/            
├── data/               # Contains training data (intents)
│
├── config.example.py   # Example config
├── requirements.txt
└── README.md
🔐 API Keys

Create a new file:

config.py

(Do NOT upload to GitHub.)

GEMINI_API_KEY = "YOUR_API_KEY_HERE"

Your .gitignore already contains:
config.py

🔧 Installation

1. Clone the repo
git clone https://github.com/Vaenvoice/AI_Voice_Assistant.git
cd AI_Voice_Assistant

2. Install dependencies
pip install -r requirements.txt

3. Setup your config
cp config.example.py config.py

Open config.py and paste your Gemini API key.

⸻

🗣 Offline STT (Vosk)

Download Vosk English model:
https://alphacephei.com/vosk/models
Download:
vosk-model-small-en-us-0.15
Extract → place folder inside project root:
AI_Voice_Assistant/vosk-model-small-en-us-0.15/

🧠 Training your intent model

Run:
python train_intent.py

This will produce a new file:
models/intent_pipeline.pkl

You must generate this yourself — it is not included in GitHub.

⸻

▶ Running Jarvis (Voice Mode)
python assistant.py

Say: “Hey Jarvis”
Then: ask anything.

💬 Running Jarvis GUI (Chat Mode)
python gui.py 
