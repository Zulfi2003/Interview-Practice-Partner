import speech_recognition as sr
import wave
import os

class Config:
    channels = 2
    sample_width = 2
    sample_rate = 44100

def save_wav_file(file_path, wav_bytes):
    """Save audio bytes to a WAV file"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(Config.channels)
            wav_file.setsampwidth(Config.sample_width)
            wav_file.setframerate(Config.sample_rate)
            wav_file.writeframes(wav_bytes)
        return True
    except Exception as e:
        print(f"Error saving WAV file: {e}")
        return False

def transcribe(file_path):
    """Transcribe audio file using Google Speech Recognition
    
    Returns:
        tuple: (success: bool, text: str)
        - If successful: (True, transcribed_text)
        - If failed: (False, error_message)
    """
    try:
        # Check if file exists and has content
        if not os.path.exists(file_path):
            return (False, "Audio file not found")
        
        if os.path.getsize(file_path) < 100:  # Too small to be valid audio
            return (False, "Audio file is too small or empty")
        
        recognizer = sr.Recognizer()
        
        # Adjust for ambient noise
        with sr.AudioFile(file_path) as source:
            # Optional: adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
        # Attempt transcription
        text = recognizer.recognize_google(audio_data)
        
        if text and text.strip():
            return (True, text)
        else:
            return (False, "No speech detected in audio")
            
    except sr.UnknownValueError:
        return (False, "Could not understand the audio. Please speak clearly and try again.")
    except sr.RequestError as e:
        return (False, f"Speech recognition service error: {e}")
    except Exception as e:
        print(f"Unexpected error in transcribe: {e}")
        return (False, "An unexpected error occurred during transcription")
