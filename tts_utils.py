import os
from gtts import gTTS
import tempfile
import hashlib

def synthesize_speech(text, lang='en'):
    """
    Synthesizes speech from text using gTTS (Google Text-to-Speech)
    and saves it to a temporary MP3 file with a unique name.
    """
    try:
        # Create a unique filename based on the text content
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        output_path = os.path.join(tempfile.gettempdir(), f"speech_{text_hash}.mp3")
        
        # Only generate if file doesn't exist (cache)
        if not os.path.exists(output_path):
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
        
        return output_path
    except Exception as e:
        print(f"Error in speech synthesis: {e}")
        # Return None to indicate error
        return None
