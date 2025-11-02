"""
Text-to-Speech Service using OpenAI TTS or ElevenLabs
Converts text responses to natural-sounding audio
"""

import logging
from typing import Optional
import base64

import openai
from core.config import settings

logger = logging.getLogger(__name__)


class Synthesizer:
    """
    Handles text-to-speech synthesis with fallback providers
    """
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.provider = "openai"  # or "elevenlabs"
        self.default_voice = settings.OPENAI_TTS_VOICE
        
        # Initialize ElevenLabs if API key provided
        if settings.ELEVENLABS_API_KEY:
            self.provider = "elevenlabs"
            self.elevenlabs_api_key = settings.ELEVENLABS_API_KEY
            self.elevenlabs_voice_id = settings.ELEVENLABS_VOICE_ID
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """
        Convert text to speech
        
        Args:
            text: Text to synthesize
            voice: Voice ID or name (provider-specific)
            speed: Speech speed (0.25 to 4.0)
        
        Returns:
            Audio bytes (MP3 format) or None if failed
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for synthesis")
            return None
        
        try:
            if self.provider == "elevenlabs":
                return await self._synthesize_elevenlabs(text, voice, speed)
            else:
                return await self._synthesize_openai(text, voice, speed)
                
        except Exception as e:
            logger.error(f"Synthesis failed with {self.provider}: {e}")
            
            # Fallback to OpenAI if ElevenLabs fails
            if self.provider == "elevenlabs":
                logger.info("Falling back to OpenAI TTS")
                try:
                    return await self._synthesize_openai(text, voice, speed)
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
            
            return None
    
    async def _synthesize_openai(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """
        Synthesize using OpenAI TTS API
        """
        try:
            response = await self.openai_client.audio.speech.create(
                model=settings.OPENAI_TTS_MODEL,
                voice=voice or self.default_voice,
                input=text,
                speed=speed,
            )
            
            audio_bytes = response.content
            logger.info(f"OpenAI TTS successful: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            return None
    
    async def _synthesize_elevenlabs(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """
        Synthesize using ElevenLabs API (higher quality)
        """
        try:
            import httpx
            
            voice_id = voice or self.elevenlabs_voice_id
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "xi-api-key": self.elevenlabs_api_key,
                "Content-Type": "application/json",
            }
            
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "speed": speed,
                },
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"ElevenLabs TTS successful: {len(response.content)} bytes")
                    return response.content
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            return None
    
    async def synthesize_stream(self, text: str, chunk_size: int = 1024):
        """
        Stream synthesis for long texts
        """
        # Note: Streaming TTS requires chunked responses
        # This is a simplified implementation
        audio_bytes = await self.synthesize(text)
        if audio_bytes:
            for i in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[i:i + chunk_size]


# Global synthesizer instance
synthesizer = Synthesizer()