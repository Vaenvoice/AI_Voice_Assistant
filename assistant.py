from jarvis import Jarvis
from config import GEMINI_API_KEY

if __name__ == "__main__":
    jarvis = Jarvis(
        use_online_stt=True,
        use_offline_stt=True,
        typed_fallback=True,
        gemini_api_key= GEMINI_API_KEY
    )

    jarvis.run()