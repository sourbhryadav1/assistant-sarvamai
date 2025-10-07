import os
import sounddevice as sd
import numpy as np
import wave
import dotenv
from sarvamai import SarvamAI
import threading
import queue

# --- Configuration ---
dotenv.load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# Initialize the Sarvam AI client for STT
sarvam_client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 8000
DTYPE = 'int16'

# Transcription logic settings
PAUSE_DURATION_SECONDS = 2.0
SILENCE_THRESHOLD = 5000  # Adjust this based on your microphone's sensitivity
TEMP_AUDIO_FILE = "temp_input.wav"

# --- Global State ---
audio_buffer = []
is_speaking = False
silent_chunks_count = 0
stt_result_queue = queue.Queue() # Thread-safe queue to hold transcription result
stop_listening_event = threading.Event() # Event to stop the audio stream

def transcribe_and_queue(filename):
    """Sends audio for transcription and puts the result in a queue."""
    print("\n[INFO] Pause detected. Transcribing speech...")
    try:
        with open(filename, "rb") as f:
            response = sarvam_client.speech_to_text.translate(file=f, model="saaras:v2.5")
        stt_result_queue.put(response) # Put the successful transcription in the queue
    except Exception as e:
        print(f"[ERROR] Could not transcribe: {e}")
        stt_result_queue.put(None) # Put None to signal an error

def save_and_transcribe():
    """Saves buffered audio and starts the transcription thread."""
    global audio_buffer
    if not audio_buffer:
        stt_result_queue.put(None)
        return

    full_audio_data = np.concatenate(audio_buffer, axis=0)
    audio_buffer = []

    with wave.open(TEMP_AUDIO_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(full_audio_data.tobytes())

    threading.Thread(target=transcribe_and_queue, args=(TEMP_AUDIO_FILE,)).start()

def audio_callback(indata, frames, time, status):
    """Callback function for the audio stream to detect voice activity."""
    global audio_buffer, is_speaking, silent_chunks_count

    if status:
        print(f"[WARNING] Audio status error: {status}")

    volume_rms = np.sqrt(np.mean(indata.astype(np.float64)**2))
    is_sound = volume_rms > SILENCE_THRESHOLD

    if is_sound:
        if not is_speaking:
            print("[INFO] Speaking detected...", end="", flush=True)
            is_speaking = True
        silent_chunks_count = 0
        audio_buffer.append(indata.copy())
    elif is_speaking:
        print(".", end="", flush=True)
        silent_chunks_count += 1
        num_pause_blocks = int((PAUSE_DURATION_SECONDS * SAMPLE_RATE) / BLOCK_SIZE)

        if silent_chunks_count > num_pause_blocks:
            is_speaking = False
            silent_chunks_count = 0
            save_and_transcribe()
            stop_listening_event.set() # Signal the main loop to stop listening

def listen_and_transcribe():
    """
    Starts listening to the microphone and blocks until a transcription is returned.
    """
    global audio_buffer, is_speaking, silent_chunks_count
    # Reset state for the new listening session
    audio_buffer = []
    is_speaking = False
    silent_chunks_count = 0
    stop_listening_event.clear()
    
    # Clear the queue in case there are old results
    while not stt_result_queue.empty():
        stt_result_queue.get()

    print("\n" + "="*50)
    print("[INFO] Listening... Speak when you're ready.")
    
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=CHANNELS,
        dtype=DTYPE,
        callback=audio_callback
    ):
        stop_listening_event.wait() # Wait until the callback signals to stop

    # Block until the transcription thread puts a result in the queue
    transcription = stt_result_queue.get()
    return transcription
