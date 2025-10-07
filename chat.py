import os
import requests
import dotenv

# --- Configuration ---
dotenv.load_dotenv()
API_KEY = os.getenv("SARVAM_API_KEY")
API_URL = "https://api.sarvam.ai/v1/chat/completions"
MODEL = "sarvam-m" 

def chat_with_sarvam(chat_history):
    """
    Sends a chat history to the Sarvam AI API and returns the response.
    """
    if not API_KEY:
        print("Error: SARVAM_API_KEY is not set.")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = { "model": MODEL, "messages": chat_history, "temperature": 0.2, "max_tokens": 50 }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        response_data = response.json()
        ai_message = response_data['choices'][0]['message']['content']
        return ai_message.strip()
    except requests.exceptions.RequestException as req_err:
        print(f"[Error] A request error occurred: {req_err}")
    except Exception as e:
        print(f"[Error] An unexpected error occurred: {e}")
        
    return None

