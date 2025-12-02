import edge_tts
import asyncio
import tempfile
import os
import re
from gtts import gTTS

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
        Fallback to gTTS if edge-tts fails (e.g. 403 error on cloud).
        """
        if not text or not text.strip():
            return b""
            
        # Clean text before generating audio
        clean_text = self.clean_text(text)
        if not clean_text:
            return b""
            
        # Try Edge TTS first
        try:
            communicate = edge_tts.Communicate(clean_text, self.voice)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_path = tmp_file.name
            
            await communicate.save(tmp_path)
            
            with open(tmp_path, "rb") as f:
                data = f.read()
            
            print(f"EdgeTTS Success: Generated {len(data)} bytes")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return data
            
        except Exception as e:
            print(f"EdgeTTS failed: {e}. Switching to gTTS fallback...")
            
            # Fallback to gTTS
            try:
                # Run gTTS in a separate thread to avoid blocking asyncio loop
                loop = asyncio.get_event_loop()
                def _gtts_generate():
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        gtts_path = tmp_file.name
                    tts = gTTS(text=clean_text, lang='en')
                    tts.save(gtts_path)
                    with open(gtts_path, "rb") as f:
                        gtts_data = f.read()
                    if os.path.exists(gtts_path):
                        os.remove(gtts_path)
                    return gtts_data
                
                data = await loop.run_in_executor(None, _gtts_generate)
                print(f"gTTS Success: Generated {len(data)} bytes")
                return data
                
            except Exception as e2:
                print(f"gTTS fallback failed: {e2}")
                return b""
