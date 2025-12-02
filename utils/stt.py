from faster_whisper import WhisperModel
import io

class STTEngine:
    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        """
        Initializes the Faster Whisper model.
        Args:
            model_size: 'tiny', 'base', 'small', 'medium', 'large-v2'
            device: 'cpu' or 'cuda' (if GPU available)
            compute_type: 'int8', 'float16', 'float32'
        """
        print(f"Loading Faster Whisper model: {model_size} on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Faster Whisper model loaded.")

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes audio bytes to text.
        """
        # faster-whisper accepts a file-like object
        audio_file = io.BytesIO(audio_bytes)
        
        segments, info = self.model.transcribe(audio_file, beam_size=5)
        
        text = ""
        for segment in segments:
            text += segment.text + " "
            
        return text.strip()
