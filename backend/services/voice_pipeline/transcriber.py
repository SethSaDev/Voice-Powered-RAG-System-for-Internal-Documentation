"""
Speech-to-Text Service using OpenAI Whisper
Converts audio input to text
"""

import logging
import base64
import tempfile
from typing import Optional, Union
from pathlib import Path

import openai
from core.config import settings

logger = logging.getLogger(__name__)


class Transcriber:
    """
    Handles audio transcription using Whisper API
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.WHISPER_MODEL
        self.sample_rate = settings.SAMPLE_RATE
    
    async def transcribe(self, audio_data: Union[bytes, str, Path]) -> Optional[str]:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Bytes, base64 string, or file path
        
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Handle different input formats
            if isinstance(audio_data, bytes):
                # Save bytes to temporary file
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_path = tmp_file.name
                
                result = await self._transcribe_file(tmp_path)
                Path(tmp_path).unlink()  # Cleanup
                return result
                
            elif isinstance(audio_data, str) and audio_data.startswith("data:audio"):
                # Handle base64 data URL
                import re
                base64_data = re.sub(r"^data:audio/\w+;base64,", "", audio_data)
                audio_bytes = base64.b64decode(base64_data)
                
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_path = tmp_file.name
                
                result = await self._transcribe_file(tmp_path)
                Path(tmp_path).unlink()
                return result
                
            elif isinstance(audio_data, (str, Path)):
                # Assume it's a file path
                return await self._transcribe_file(audio_data)
            
            else:
                logger.error(f"Unsupported audio data type: {type(audio_data)}")
                return None
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    async def _transcribe_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Transcribe audio file using Whisper API
        """
        try:
            with open(file_path, "rb") as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en",  # Auto-detect if not specified
                    response_format="text",
                )
            
            # Response is a string when response_format="text"
            transcript = response if isinstance(response, str) else response.text
            
            logger.info(f"Transcription successful: {len(transcript)} chars")
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            return None
    
    async def transcribe_stream(self, audio_chunks: list) -> Optional[str]:
        """
        Transcribe concatenated audio chunks
        Useful for streaming scenarios
        """
        combined_audio = b"".join(audio_chunks)
        return await self.transcribe(combined_audio)


# Global transcriber instance
transcriber = Transcriber()