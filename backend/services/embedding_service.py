import os
from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None

    def _get_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        embedding = self._get_model().encode(text)
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text strings."""
        embeddings = self._get_model().encode(texts)
        return embeddings.tolist()

# Singleton instance
embedding_service = EmbeddingService()
