import speech_recognition as sr
import edge_tts
import asyncio
import ctypes
import os
import time
import sounddevice as sd
import scipy.io.wavfile as wav
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

import threading
import queue
import re
import numpy as np

# Dual Queue Architecture: Text -> [Generator] -> AudioPath -> [Player]
# Initialize Windows Multimedia Library (MCI) for zero-dependency playback
winmm = ctypes.windll.winmm

# Audio Management State
text_queue = queue.Queue()
audio_queue = queue.Queue()
_stop_event = threading.Event()
_is_speaking_lock = threading.Lock()
_is_speaking = False

TEMP_DIR = "temp_audio"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
else:
    # Cleanup old files from previous sessions
    for f in os.listdir(TEMP_DIR):
        try: os.remove(os.path.join(TEMP_DIR, f))
        except: pass

def _tts_generator_worker():
    """Consumes text chunks and generates audio files in the background."""
    while True:
        try:
            task = text_queue.get()
            if task is None: break
            text, voice = task
            
            # Use unique filenames in temp directory
            audio_file = os.path.join(TEMP_DIR, f"speech_{int(time.time() * 1000000)}.mp3")
            
            async def _generate():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(audio_file)
            
            try:
                asyncio.run(_generate())
                if os.path.exists(audio_file):
                    audio_queue.put(audio_file)
            except Exception as e:
                print(f"TTS Gen Error: {e}")
                
            text_queue.task_done()
        except Exception as e:
            print(f"Generator Worker Error: {e}")

def _tts_player_worker():
    """Consumes audio files and plays them using Windows MCI for interruption support."""
    global _is_speaking
    while True:
        try:
            audio_file = audio_queue.get()
            if audio_file is None: break
            
            if _stop_event.is_set():
                audio_queue.task_done()
                try: os.remove(audio_file)
                except: pass
                continue

            if os.path.exists(audio_file):
                try:
                    with _is_speaking_lock:
                        _is_speaking = True
                    
                    # MCI Player (Non-blocking and interruptible)
                    # We use an alias 'mymp3' to control the stream
                    abs_path = os.path.abspath(audio_file)
                    winmm.mciSendStringW(f'open "{abs_path}" type mpegvideo alias mymp3', None, 0, None)
                    winmm.mciSendStringW('play mymp3', None, 0, None)
                    
                    # To check if it's still playing, we use 'status mymp3 mode'
                    # which returns 'playing', 'stopped', etc.
                    buffer = ctypes.create_unicode_buffer(64)
                    while True:
                        winmm.mciSendStringW('status mymp3 mode', buffer, 64, None)
                        if buffer.value != 'playing' or _stop_event.is_set():
                            winmm.mciSendStringW('stop mymp3', None, 0, None)
                            winmm.mciSendStringW('close mymp3', None, 0, None)
                            break
                        time.sleep(0.01)
                        
                except Exception as e:
                    print(f"Playback Error: {e}")
                finally:
                    with _is_speaking_lock:
                        _is_speaking = False
                    try:
                        os.remove(audio_file)
                    except:
                        pass
            
            audio_queue.task_done()
        except Exception as e:
            print(f"Player Worker Error: {e}")

# Control Functions
def stop_speaking():
    """Immediately stops all speech and clears queues."""
    _stop_event.set()
    winmm.mciSendStringW('stop mymp3', None, 0, None)
    winmm.mciSendStringW('close mymp3', None, 0, None)
    
    # Clear both queues
    with text_queue.mutex:
        text_queue.queue.clear()
    with audio_queue.mutex:
        audio_queue.queue.clear()
        
    time.sleep(0.05) # Brief wait for workers to sync
    _stop_event.clear()

def is_currently_speaking():
    """Returns True if JARVIS is playing audio."""
    with _is_speaking_lock:
        return _is_speaking

# Start background threads
threading.Thread(target=_tts_generator_worker, daemon=True).start()
threading.Thread(target=_tts_player_worker, daemon=True).start()

def speak(text, voice="en-GB-RyanNeural"):
    """Splits text into ~20 word chunks and queues them for pre-generation and playback."""
    # Clean text
    text = text.replace("ACTION:TYPE_TEXT:", "").replace("*", "").replace("#", "").strip()
    if not text: return
    
    # Split text into words
    words = text.split()
    chunk_size = 35
    
    # Create chunks of approximately 35 words
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    # Put chunks into the generator queue
    for chunk in chunks:
        text_queue.put((chunk, voice))

def listen(duration=5, on_energy_change=None):
    """Listen to microphone dynamically using sounddevice and transcribe using Groq Whisper.
    Calls 'on_energy_change(energy_percent)' if provided for GUI feedback."""
    fs = 44100
    chunk_duration = 0.1 # Faster updates for smoother UI (was 0.5)
    chunk_samples = int(fs * chunk_duration)
    
    recording = []
    silence_duration = 0
    has_spoken = False
    elapsed_time = 0
    
    # User's strict parameters:
    silence_timeout = 4.0        # How long to wait after they stop speaking before processing
    give_up_timeout = duration   # How long to wait for them to START speaking
    energy_threshold = 150       # Amplitude RMS cutoff
    
    filename = "temp_recording.wav"
    
    try:
        with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
            while True:
                chunk, _ = stream.read(chunk_samples)
                recording.append(chunk.copy())
                elapsed_time += chunk_duration
                
                # Calculate volume energy (RMS)
                energy = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                
                # Update GUI if callback provided
                if on_energy_change:
                    # Normalize energy to 0.0 - 1.0 (approximate range)
                    norm_energy = min(1.0, energy / 1000.0) 
                    on_energy_change(norm_energy)
                
                if energy > energy_threshold:
                    has_spoken = True
                    silence_duration = 0
                else:
                    if has_spoken:
                        silence_duration += chunk_duration
                        
                # End Conditions
                if has_spoken and silence_duration >= silence_timeout:
                    break
                if not has_spoken and elapsed_time >= give_up_timeout:
                    if on_energy_change: on_energy_change(0)
                    return ""
                if elapsed_time >= 30: 
                    break
                    
        if on_energy_change: on_energy_change(0) # Reset energy
                    
        audio_data = np.concatenate(recording, axis=0)
        wav.write(filename, fs, audio_data)
        
        try:
            with open(filename, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=("temp_recording.wav", file.read()),
                    model="whisper-large-v3",
                    language="en",
                    response_format="text"
                )
            text = str(transcription).strip()
        except Exception as e:
            print(f"Groq API Error: {e}")
            text = ""
                
        try:
            os.remove(filename)
        except:
            pass
            
        if text.strip() and len(text) > 3:
            print(f"[DEBUG MIC] I heard: '{text}'")
        return text.lower()
        
    except Exception as e:
        print(f"ERROR LISTENING: {str(e)}")
        return ""
