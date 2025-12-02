import edge_tts
import asyncio
import tempfile
import os
import re

class AudioStreamer:
    def __init__(self, voice: str = "en-US-AriaNeural"):
        self.voice = voice

    def clean_text(self, text: str) -> str:
        """
        Removes markdown and other artifacts from text for better TTS.
        """
        # Remove bold/italic markers (**text**, *text*)
        text = re.sub(r'\*\*|__', '', text)
        text = re.sub(r'\*|_', '', text)
        
        # Remove code blocks (`text`)
        text = re.sub(r'`', '', text)
        
        # Remove headers (### Header)
        text = re.sub(r'#+', '', text)
        
        # Remove brackets/citations [Source: ...]
        text = re.sub(r'\[.*?\]', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    async def generate_audio(self, text: str) -> bytes:
        """
        Generates audio using edge-tts and returns bytes.
        Uses a temporary file to ensure complete generation before reading.
        """
        if not text or not text.strip():
            return b""
            
        # Clean text before generating audio
        clean_text = self.clean_text(text)
        if not clean_text:
            return b""
            
        communicate = edge_tts.Communicate(clean_text, self.voice)
        
        # Create a temporary file
        # We close it immediately so edge-tts can open and write to it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            await communicate.save(tmp_path)
            
            with open(tmp_path, "rb") as f:
                data = f.read()
                
            return data
        except Exception as e:
            print(f"EdgeTTS generation error: {e}")
            # Return empty bytes on error instead of raising, to avoid crashing app
            return b""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
