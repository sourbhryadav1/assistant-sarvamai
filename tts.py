import os
import tempfile
import base64
import dotenv
from sarvamai import SarvamAI
from pydub import AudioSegment
from pydub.playback import play

# --- Configuration ---
dotenv.load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# Initialize the Sarvam AI client for TTS
sarvam_client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

def speak(text_input):
    """Converts text to speech and plays it out loud."""
    if not text_input:
        print("[WARNING] TTS received empty text.")
        return

    print("[INFO] Converting AI response to speech...")
    try:
        response = sarvam_client.text_to_speech.convert(
            text=text_input,
            target_language_code='en-IN',
        )
        audio_bytes = base64.b64decode(response.audios[0])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        print("[INFO] Speaking...")
        audio = AudioSegment.from_file(temp_path)
        play(audio)
        os.remove(temp_path)
    except Exception as e:
        print(f"[ERROR] TTS failed: {e}")
