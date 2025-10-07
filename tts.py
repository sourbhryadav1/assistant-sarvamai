import tempfile
from sarvamai import SarvamAI
import os
import dotenv
import base64
from pydub import AudioSegment
from pydub.playback import play

dotenv.load_dotenv()

# Initialize the client once
try:
    client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))
except Exception as e:
    client = None
    print(f"[ERROR] Failed to initialize SarvamAI client: {e}")

def speak_text(text: str, language_code: str = 'en-IN'):
    """
    Converts text to speech for a given language and plays it.
    """
    if not client:
        print("[ERROR] TTS client not initialized. Cannot speak.")
        return
    if not text:
        print("[WARNING] speak_text called with empty string.")
        return

    print(f"[INFO] Generating speech for text: '{text}' in language: {language_code}")
    try:
        response = client.text_to_speech.convert(
            text=text,
            target_language_code=language_code,
            speaker = 'anushka',
            model='bulbul:v2'
        )

        audio_bytes = base64.b64decode(response.audios[0])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        audio = AudioSegment.from_file(temp_path)
        play(audio)
        os.remove(temp_path)

    except Exception as e:
        print(f"[ERROR] An error occurred during text-to-speech conversion or playback: {e}")

