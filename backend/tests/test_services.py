import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from backend.services.embedding_service import embedding_service
from backend.services.database_service import database_service
from backend.services.vector_store_service import vector_store_service

@patch("backend.services.embedding_service.SentenceTransformer")
def test_embedding_service(mock_sentence_transformer):
    # Mock the model instance and its encode method
    # Need to return a numpy array-like object with tolist() method
    import numpy as np
    mock_model = mock_sentence_transformer.return_value
    mock_array = np.array([0.1] * 384)  # Updated for all-MiniLM-L6-v2 (384 dimensions)
    mock_model.encode.return_value = mock_array
    
    # Reset the model cache
    embedding_service.model = None
    
    text = "This is a test sentence."
    embedding = embedding_service.embed_text(text)
    
    assert len(embedding) == 384  # Updated for all-MiniLM-L6-v2
    assert isinstance(embedding, list)
    mock_sentence_transformer.assert_called_once()
    mock_model.encode.assert_called_with(text)

def test_database_service():
    # Use a temporary file-based DB for testing (more reliable than :memory:)
    import sqlite3
    import json
    import os
    import tempfile
    
    # Create a fresh database service instance for testing
    from backend.services.database_service import DatabaseService
    
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        tmp_db_path = tmp_file.name
    
    try:
        # Create a test instance with temporary database
        test_db = DatabaseService.__new__(DatabaseService)
        test_db.db_path = tmp_db_path
        # Initialize the database
        test_db.init_db()
        
        interview_id = test_db.create_interview("John Doe", "Resume content", "Job Description")
        assert interview_id is not None
        
        interview = test_db.get_interview(interview_id)
        assert interview['candidate_name'] == "John Doe"
        assert interview['status'] == "pending"
        
        test_db.update_matching_results(interview_id, 85.5, ["Python", "FastAPI"])
        interview = test_db.get_interview(interview_id)
        assert interview['match_score'] == 85.5
        matched_skills = json.loads(interview['matched_skills']) if isinstance(interview['matched_skills'], str) else interview['matched_skills']
        assert "Python" in matched_skills
    finally:
        # Clean up temporary database file
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)

@patch("backend.services.vector_store_service.QdrantClient")
def test_vector_store_service(mock_qdrant):
    # Mock Qdrant client
    mock_client_instance = MagicMock()
    mock_client_instance.collection_exists.return_value = False
    mock_qdrant.return_value = mock_client_instance
    
    # Reset the client cache
    vector_store_service.client = None
    
    # Mock the _get_client method to return our mock
    original_get_client = vector_store_service._get_client
    vector_store_service._get_client = lambda: mock_client_instance
    
    vector_store_service.create_collection("test_collection")
    
    # Verify create_collection was called
    mock_client_instance.create_collection.assert_called_once()
    
    # Restore original method
    vector_store_service._get_client = original_get_client
