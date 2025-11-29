import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from backend.services.voice_service import voice_service

@pytest.mark.asyncio
async def test_transcribe_audio():
    # Mock AsyncOpenAI client
    with patch("backend.services.voice_service.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_transcript = MagicMock()
        mock_transcript.text = "Hello world"
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcript)
        mock_openai.return_value = mock_client
        
        # Replace the client
        original_client = voice_service.client
        voice_service.client = mock_client
        
        audio_bytes = b"fake_audio_data"
        result = await voice_service.transcribe_audio(audio_bytes)
        
        assert result == "Hello world"
        mock_client.audio.transcriptions.create.assert_called_once()
        
        # Restore original client
        voice_service.client = original_client

@pytest.mark.asyncio
async def test_text_to_speech():
    # Mock AsyncOpenAI client
    with patch("backend.services.voice_service.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = b"fake_audio_content"
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Replace the client
        original_client = voice_service.client
        voice_service.client = mock_client
        
        text = "Hello world"
        result = await voice_service.text_to_speech(text)
        
        assert result == b"fake_audio_content"
        mock_client.audio.speech.create.assert_called_once()
        
        # Restore original client
        voice_service.client = original_client
