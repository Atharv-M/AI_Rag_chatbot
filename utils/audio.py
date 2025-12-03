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
        # Remove code blocks (`text`)
        # Remove headers (### Header)
        # Remove brackets/citations [Source: ...]
        # Remove URLs
        text = re.sub(r'\*\*|__', '', text)
        text = re.sub(r'\*|_', '', text)
        text = re.sub(r'`', '', text)
        text = re.sub(r'#+', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'http\S+', '', text)
        
        
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
                    
                    # Generate slow audio
                    tts = gTTS(text=clean_text, lang='en')
                    tts.save(gtts_path)
                    
                    # Speed up audio using pydub
                    try:
                        from pydub import AudioSegment
                        audio = AudioSegment.from_mp3(gtts_path)
                        # Speed up by 1.3x
                        fast_audio = audio.speedup(playback_speed=1.2)
                        
                        # Export to buffer
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fast_tmp:
                            fast_path = fast_tmp.name
                            
                        fast_audio.export(fast_path, format="mp3")
                        
                        with open(fast_path, "rb") as f:
                            gtts_data = f.read()
                            
                        if os.path.exists(fast_path):
                            os.remove(fast_path)
                            
                    except Exception as e_pydub:
                        print(f"Pydub speedup failed: {e_pydub}. Using normal speed.")
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
