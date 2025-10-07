import os
import requests
import dotenv

# Load environment variables
dotenv.load_dotenv()
API_KEY = os.getenv("SARVAM_API_KEY")
API_URL = "https://api.sarvam.ai/translate"

def translate_text(text: str, target_language_code: str) -> str:
    """
    Translates the given text to the target language using Sarvam AI.

    Args:
        text: The text to be translated.
        target_language_code: The language code to translate to (e.g., 'hi-IN').

    Returns:
        The translated text, or the original text if translation fails.
    """
    if not API_KEY:
        print("[ERROR] SARVAM_API_KEY not set for translation.")
        return text

    headers = {
        "api-subscription-key": API_KEY,
    }

    json = {
        "input": text,
        "source_language_code": "en-IN", # our source text is always English
        "target_language_code": target_language_code
    }

    try:
        response = requests.post(API_URL, headers=headers, json=json, timeout=20)
        response.raise_for_status()
        response_data = response.json()
        # print(f"[DEBUG] Translation response data: {response_data}")
        
        translated_text = response_data.get('translated_text')
        if translated_text:
            print(f"[INFO] Translation successful: '{text}' -> '{translated_text}'")
            return translated_text
        else:
            print(f"[WARNING] Translation response did not contain output.")
            return text # Fallback to original text

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Translation API call failed: {e}")
        return text # Fallback to original text

# Example usage:
# translated = translate_text("Hello, how are you?", "hi-IN")
# print(translated)