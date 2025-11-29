import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

class VectorStoreService:
    def __init__(self):
        self.client = None

    def _get_client(self):
        if self.client is None:
            url = os.getenv("QDRANT_URL")
            api_key = os.getenv("QDRANT_API_KEY")
            
            if not url:
                # Fallback to local disk storage
                # Use a path that works on both Windows and Linux
                storage_path = os.path.join(os.getcwd(), "qdrant_data")
                os.makedirs(storage_path, exist_ok=True)
                self.client = QdrantClient(path=storage_path)
            else:
                self.client = QdrantClient(url=url, api_key=api_key)
        return self.client

    def create_collection(self, collection_name: str, vector_size: int = 384):
        """Create a collection. Recreates it if it exists to ensure correct vector size."""
        client = self._get_client()
        # Use recreate_collection to delete and create in one call
        # This ensures we always have the correct vector size
        try:
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
        except Exception:
            # If recreate fails, try create (in case collection doesn't exist)
            if not client.collection_exists(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )

    def upsert_vectors(self, collection_name: str, points: List[PointStruct]):
        """Upsert vectors into the collection."""
        self._get_client().upsert(
            collection_name=collection_name,
            points=points
        )

    def search(self, collection_name: str, query_vector: List[float], limit: int = 5, score_threshold: Optional[float] = None) -> List[Any]:
        """Search for similar vectors using query_points API."""
        client = self._get_client()
        
        # query_points accepts query_vector directly as list[float] or as query parameter
        # It also supports limit and score_threshold as direct parameters
        results = client.query_points(
            collection_name=collection_name,
            query=query_vector,  # Can pass vector directly
            limit=limit,
            score_threshold=score_threshold
        )
        
        return results.points

# Singleton instance
vector_store_service = VectorStoreService()
