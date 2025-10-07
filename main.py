import time
from stt import listen_and_transcribe
from tts import speak_text
from conversation_manager import ConversationManager

def main():
    print("-----------------------------------------------Sarvam AI Voice Assistant Started------------------------------------------------")


    conversation = ConversationManager()

    # Start the conversation
    initial_prompt = conversation.start_conversation()
    speak_text(initial_prompt, conversation.user_language_code) # Use default language for the first prompt

    while not conversation.is_complete:
        try:
            # Listen and Transcribe
            user_input_response = listen_and_transcribe()
            if not user_input_response:
                print("[WARNING] STT returned no result. Listening again.")
                continue
            
            user_text = user_input_response.transcript
            print(f">> You: {user_text}")

            # Process with Conversation Manager 
            ai_response = conversation.process_user_response(user_text)

            # Speak the response (passing the CURRENT language)
            speak_text(ai_response, conversation.user_language_code)

        except KeyboardInterrupt:
            print("\n[INFO] Exiting program.")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            break

    print("-----------------------------------------------Conversation Finished------------------------------------------------")



if __name__ == "__main__":
    main()

