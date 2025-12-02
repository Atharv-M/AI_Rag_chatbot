import streamlit as st
import os
import asyncio
import edge_tts
import tempfile
from dotenv import load_dotenv
from utils.llm import GeminiLLM
from utils.rag import RAGEngine
from utils.stt import STTEngine
from utils.audio import AudioStreamer
import PyPDF2
from io import BytesIO
import docx
import csv

# Initialize utils
@st.cache_resource
def get_audio_streamer():
    return AudioStreamer()

audio_streamer = get_audio_streamer()

# Load environment variables
load_dotenv()

# Initialize utils
@st.cache_resource
def get_llm():
    return GeminiLLM(api_key=os.getenv("GEMINI_API_KEY"), model=os.getenv("GEMINI_MODEL"))



@st.cache_resource
def get_rag_engine():
    # No API key needed for local embeddings
    return RAGEngine(model_name="all-MiniLM-L6-v2")

@st.cache_resource
def get_stt_engine():
    # Use Faster Whisper (local)
    # Using 'tiny' for speed on typical machines, 'base' is better accuracy
    return STTEngine(model_size="tiny", device="cpu", compute_type="int8")

llm = get_llm()
rag_engine = get_rag_engine()
stt_engine = get_stt_engine()

# Page Config
st.set_page_config(
    page_title="Genova Gemini",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for Input Alignment
st.markdown("""
<style>
    /* Align the bottom of the columns */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }
    
    /* Optional: Make audio input look more like a button if needed, 
       but primarily this ensures text input and audio widget sit at same baseline */
    .stAudioInput {
        margin-top: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

# Sidebar - Document Upload
with st.sidebar:
    st.title("📄 Document Context")
    
    # Initialize indexed files list if not present
    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = set()

    uploaded_files = st.file_uploader(
        "Upload Documents", 
        type=["pdf", "txt", "csv", "docx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.indexed_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        text = ""
                        # PDF Processing
                        if uploaded_file.name.endswith('.pdf'):
                            pdf_reader = PyPDF2.PdfReader(uploaded_file)
                            for page in pdf_reader.pages:
                                text += page.extract_text() + "\n"
                        
                        # TXT Processing
                        elif uploaded_file.name.endswith('.txt'):
                            text = uploaded_file.read().decode("utf-8")
                            
                        # CSV Processing
                        elif uploaded_file.name.endswith('.csv'):
                            # Read as text for simplicity, or use csv module
                            content = uploaded_file.read().decode("utf-8")
                            text = content # Treat CSV as raw text for now
                            
                        # DOCX Processing
                        elif uploaded_file.name.endswith('.docx'):
                            doc = docx.Document(uploaded_file)
                            text = "\n".join([para.text for para in doc.paragraphs])
                        
                        if text:
                            # Index document using RAG Engine
                            rag_engine.index_document(text, uploaded_file.name)
                            st.session_state.indexed_files.add(uploaded_file.name)
                            st.toast(f"Indexed {uploaded_file.name}", icon="✅")
                            
                    except Exception as e:
                        st.error(f"Error reading {uploaded_file.name}: {e}")
    
    # Display Indexed Files
    if st.session_state.indexed_files:
        st.markdown("### 📚 Indexed Documents")
        for f in st.session_state.indexed_files:
            st.text(f"• {f}")
            
        if st.button("Clear Database", type="primary"):
            rag_engine.clear_database()
            st.session_state.indexed_files = set()
            st.session_state.pdf_name = None # Legacy cleanup
            st.rerun()

# Main Chat Interface
st.title("🤖 Genova Assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format="audio/mpeg", autoplay=False)

# Helper function to process input
async def process_input(user_input, is_audio=False):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Retrieving context & Thinking..."):
            # Retrieve relevant context if PDF is loaded
            context = None
            # Retrieve relevant context if documents are indexed
            context = None
            if st.session_state.indexed_files:
                context = rag_engine.retrieve(user_input)
            
            response_text = await llm.generate(user_input, pdf_context=context)
            st.markdown(response_text)
        
        # Generate Audio
        with st.spinner("Generating Audio..."):
            try:
                audio_bytes = await audio_streamer.generate_audio(response_text)
                
                if audio_bytes:
                    # Use audio/mpeg for MP3 compatibility
                    st.audio(audio_bytes, format="audio/mpeg", autoplay=True)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response_text,
                        "audio": audio_bytes
                    })
                else:
                    st.warning("TTS generated no audio.")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response_text
                    })

            except Exception as e:
                print(f"DEBUG: TTS Error details: {e}")
                st.error("TTS Error occurred:")
                st.exception(e)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text
                })

# Input Area
# Use columns to place Audio and Text side-by-side
input_container = st.container()

with input_container:
    col1, col2 = st.columns([1, 8])
    
    with col1:
        # Audio Input
        audio_value = st.audio_input("Voice", label_visibility="collapsed")
    
    with col2:
        # Text Input with callback
        def submit_text():
            if st.session_state.chat_input_text:
                asyncio.run(process_input(st.session_state.chat_input_text))
                st.session_state.chat_input_text = ""

        st.text_input(
            "Message", 
            key="chat_input_text", 
            on_change=submit_text, 
            placeholder="Type your message here...", 
            label_visibility="collapsed"
        )

# Logic to handle Audio Input (Text is handled by callback)
if audio_value:
    audio_bytes = audio_value.read()
    
    if "last_audio_bytes" not in st.session_state or st.session_state.last_audio_bytes != audio_bytes:
        st.session_state.last_audio_bytes = audio_bytes
        
        with st.spinner("Transcribing..."):
            # Use local STT engine
            try:
                transcript = stt_engine.transcribe(audio_bytes)
                if transcript and transcript.strip():
                    asyncio.run(process_input(transcript, is_audio=True))
                else:
                    st.warning("Could not understand audio.")
            except Exception as e:
                st.error(f"STT Error: {e}")
