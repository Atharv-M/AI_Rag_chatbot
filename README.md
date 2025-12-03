# Genova Gemini - AI RAG Chatbot

Genova Gemini is a powerful, interactive chatbot application built with Streamlit. It leverages Google's Gemini Pro LLM and Retrieval-Augmented Generation (RAG) to provide accurate, context-aware responses based on your uploaded documents. The application also features robust voice interaction capabilities.

## 🌟 Features

-   **🧠 Advanced LLM**: Powered by Google's **Gemini Pro** for high-quality text generation.
-   **📚 RAG Engine**:
    -   Uses **ChromaDB** for efficient vector storage.
    -   **Sentence Transformers** (`all-MiniLM-L6-v2`) for local embeddings.
    -   Supports **PDF, TXT, CSV, and DOCX** document uploads for context.
-   **🗣️ Voice Interaction**:
    -   **Speech-to-Text (STT)**: Integrated **Faster Whisper** for fast and accurate local transcription.
    -   **Text-to-Speech (TTS)**: High-quality **Edge TTS** (primary) with **gTTS** fallback for natural-sounding voice responses.
-   **⚡ Real-time Streaming**: Streamlit-based UI for a responsive chat experience.
-   **🐳 Dev Container Ready**: Includes a `.devcontainer` configuration for instant, consistent development environments using VS Code or GitHub Codespaces.

## 🛠️ Prerequisites

-   **Python 3.11+**
-   **FFmpeg** (Required for audio processing)
    -   *Mac*: `brew install ffmpeg`
    -   *Linux*: `sudo apt install ffmpeg`
    -   *Windows*: Download and add to PATH.

## 🚀 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Atharv-M/AI_Rag_chatbot.git
    cd genova-gemini
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables**:
    -   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    -   Open `.env` and add your Google Gemini API Key:
        ```env
        GEMINI_API_KEY=your_actual_api_key_here
        GEMINI_MODEL=gemini-pro
        ```

## 🏃‍♂️ Usage

Run the Streamlit application:

```bash
streamlit run main.py
```

The application will open in your default web browser (usually at `http://localhost:8501`).

### Using the Chatbot
1.  **Upload Documents**: Use the sidebar to upload PDF, TXT, CSV, or DOCX files. The RAG engine will index them automatically.
2.  **Chat**: Type your message in the text input or use the **Voice** input to speak.
3.  **Listen**: The assistant will respond with text and automatically generate audio playback.

## 📦 Development Container

This project includes a `.devcontainer` folder. If you are using VS Code:
1.  Install the **Dev Containers** extension.
2.  Open the project folder in VS Code.
3.  Click "Reopen in Container" when prompted (or use the Command Palette).

This will set up a fully isolated environment with all dependencies and tools pre-installed.
