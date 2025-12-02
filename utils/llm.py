# utils/llm.py
import asyncio
from typing import Optional

# Depending on your environment install:
# pip install google-generativeai
try:
    import google.generativeai as genai
except Exception:
    genai = None

class GeminiLLM:
    def __init__(self, api_key: str, model: str = "text-bison-001"):
        if not genai:
            raise RuntimeError("google-generativeai library not installed. pip install google-generativeai")
        self.api_key = api_key
        self.model = model
        genai.configure(api_key=api_key)

    async def generate(self, prompt: str, pdf_context: Optional[str] = None) -> str:
        # If PDF context is provided, prepend it to the prompt
        if pdf_context:
            system_message = f"""You are a helpful assistant. Below is content from uploaded documents. Please use this content to answer the user's questions accurately.

--- DOCUMENT CONTENT ---
{pdf_context}
--- END OF DOCUMENT CONTENT ---

Now, answer the user's question based ONLY on the document content above.
If the answer is not found in the provided documents, you must respond with exactly: "I don't know based on the provided documents."
Do not hallucinate or use outside knowledge.

User Question: {prompt}"""
            effective_prompt = system_message
        else:
            effective_prompt = prompt
        
        loop = asyncio.get_event_loop()
        def _call():
            try:
                # Use GenerativeModel API which exposes generate_content
                model_obj = genai.GenerativeModel(self.model)
                resp = model_obj.generate_content(contents=[{"parts": [{"text": effective_prompt}]}], stream=False)
                # prefer convenience property
                if getattr(resp, 'text', None):
                    return resp.text
                # parse candidates -> content -> parts
                if getattr(resp, 'candidates', None):
                    c = resp.candidates[0]
                    cont = getattr(c, 'content', None)
                    if cont and getattr(cont, 'parts', None):
                        parts = cont.parts
                        if parts and getattr(parts[0], 'text', None):
                            return parts[0].text
                # fallback to dictionary or repr
                try:
                    return resp.to_dict()
                except Exception:
                    return str(resp)
            except Exception as e:
                # fallback for older SDKs or errors
                try:
                    resp = genai.generate_text(model=self.model, text=effective_prompt)
                    return getattr(resp, 'text', str(resp))
                except Exception as e2:
                    return f'LLM call failed: {e} | {e2}'
        return await loop.run_in_executor(None, _call)

    async def transcribe_bytes(self, audio_bytes: bytes) -> str:
        loop = asyncio.get_event_loop()
        def _call():
            try:
                # Try using Gemini's audio transcription
                resp = genai.audio.speech_to_text(content=audio_bytes)
                text = getattr(resp, 'text', str(resp))
                if text and text.strip():
                    return text
            except Exception as e:
                print(f"STT via Gemini failed: {e}")
            
            # Fallback: return a default message indicating audio was received
            # In production, integrate Google Cloud Speech-to-Text API
            print(f"Warning: Could not transcribe audio ({len(audio_bytes)} bytes). Using fallback.")
            return "[Audio received but transcription not available - please use text mode]"
        
        return await loop.run_in_executor(None, _call)

    async def partial_transcribe_bytes(self, audio_bytes: bytes) -> Optional[str]:
        return None
