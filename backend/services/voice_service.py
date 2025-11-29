import os
from openai import AsyncOpenAI
import io

class VoiceService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Transcribe audio using Whisper."""
        # Create a file-like object from bytes
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav" # OpenAI API needs a filename

        transcript = await self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text

    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using OpenAI TTS."""
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content

# Singleton instance
voice_service = VoiceService()
