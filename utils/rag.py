import chromadb
from chromadb.utils import embedding_functions
import os
from typing import List, Optional

class RAGEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.chroma_client = chromadb.Client() # Ephemeral client
        
        # Use Sentence Transformers for local embeddings
        # This will download the model on first use
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        
        self.collection = self.chroma_client.create_collection(
            name="pdf_context",
            embedding_function=self.embedding_fn,
            get_or_create=True
        )

    def split_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        """
        Splits text into chunks based on word count.
        """
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            start += chunk_size - overlap
        return chunks

    def index_document(self, text: str, filename: str):
        """
        Splits text into chunks and indexes them in ChromaDB.
        """
        # NOTE: We no longer clear the collection here to allow multiple documents.
        
        chunks = self.split_text(text)
        if not chunks:
            return

        # Create unique IDs for chunks
        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "chunk_id": i} for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"Indexed {len(chunks)} chunks for {filename}")

    def clear_database(self):
        """
        Clears the entire database.
        """
        try:
            self.chroma_client.delete_collection("pdf_context")
        except:
            pass
        
        self.collection = self.chroma_client.create_collection(
            name="pdf_context",
            embedding_function=self.embedding_fn,
            get_or_create=True
        )

    def retrieve(self, query: str, n_results: int = 5) -> str:
        """
        Retrieves relevant context for a query.
        """
        if self.collection.count() == 0:
            return ""

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )
        
        # Combine retrieved documents
        if results['documents'] and results['documents'][0]:
            # Add source info to context
            context_parts = []
            for i, doc in enumerate(results['documents'][0]):
                source = results['metadatas'][0][i].get('source', 'Unknown')
                context_parts.append(f"[Source: {source}]\n{doc}")
            
            return "\n\n".join(context_parts)
        return ""
