# utils/llm.py
import asyncio
from typing import Optional

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
                
                model_obj = genai.GenerativeModel(self.model)
                resp = model_obj.generate_content(contents=[{"parts": [{"text": effective_prompt}]}], stream=False)
                
                # Checking for safety ratings or other blocks if text is not available
                try:
                    if resp.text:
                        return resp.text
                except ValueError:
                    
                    print(f"Response blocked. Safety ratings: {resp.prompt_feedback}")
                    return "I cannot answer this question because it violates safety policies."
                
                # Fallback parsing for complex responses
                if hasattr(resp, 'candidates') and resp.candidates:
                    c = resp.candidates[0]
                    if hasattr(c, 'content') and c.content:
                        if hasattr(c.content, 'parts') and c.content.parts:
                            return c.content.parts[0].text
                            
                return "I could not generate a response. Please try again."

            except Exception as e:
                print(f"LLM Generation Error: {e}")
                return f"Error generating response: {str(e)}"
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
            #  integrate Google Cloud Speech-to-Text API
            print(f"Warning: Could not transcribe audio ({len(audio_bytes)} bytes). Using fallback.")
            return "[Audio received but transcription not available - please use text mode]"
        
        return await loop.run_in_executor(None, _call)

    async def partial_transcribe_bytes(self, audio_bytes: bytes) -> Optional[str]:
        return None
