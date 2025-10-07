import os
import dotenv

# Import functions from our separate modules
from stt import listen_and_transcribe
from tts import speak
from conversation_manager import ConversationManager

# --- Universal Configuration ---
dotenv.load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

if not SARVAM_API_KEY:
    raise ValueError("SARVAM_API_KEY not set.")

if __name__ == "__main__":
    print("JobsUPI Voice Assistant")


    # Initialize the conversation manager
    manager = ConversationManager()

    try:
        # --- Start the conversation ---
        initial_message = manager.start_conversation()
        print(f">> Bot: {initial_message}")
        speak(initial_message)

        # --- Loop until the conversation is complete ---
        while not manager.is_complete:
            # Listen for user's voice and get transcription
            stt_response = listen_and_transcribe()

            if not stt_response or not stt_response.transcript:
                print("[WARNING] No valid transcription received. Asking again.")
                speak("I didn't catch that. Could you please repeat?")
                continue

            user_text = stt_response.transcript
            print(f"\n>> You: {user_text}")

            # Process the response and get the next bot message
            bot_response = manager.process_user_response(user_text)

            # Speak the bot's next message
            print(f">> Bot: {bot_response}")
            speak(bot_response)
        
        print("\n[INFO] Conversation complete. Exiting program.")

    except KeyboardInterrupt:
        print("\n[INFO] Exiting program.")
    except Exception as e:
        print(f"An unexpected error occurred in the main loop: {e}")

