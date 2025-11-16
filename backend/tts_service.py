"""
TTS Service for Confucius Voice Q&A

This module provides text-to-speech functionality using ElevenLabs API
with caching support.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from config import Config
from env_loader import get_api_key


# Cache directory for TTS audio files
CACHE_DIR = Path("workspace/tts_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Global client instance
_client: Optional[ElevenLabs] = None


def get_tts_client() -> Optional[ElevenLabs]:
    """Get or initialize ElevenLabs client."""
    global _client
    if _client is None:
        api_key = get_api_key("ELEVENLABS_API_KEY", required=False)
        if api_key:
            _client = ElevenLabs(api_key=api_key)
    return _client


def get_text_hash(text: str) -> str:
    """Generate hash for text to use as cache key."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_cached_audio_path(text: str) -> Path:
    """Get path for cached audio file."""
    text_hash = get_text_hash(text)
    return CACHE_DIR / f"{text_hash}.mp3"


def text_to_speech(
    text: str,
    voice_id: Optional[str] = None
) -> Optional[str]:
    """
    Convert text to speech using ElevenLabs API with caching.
    
    Args:
        text: Text to convert to speech (must be non-empty)
        voice_id: Optional voice ID (defaults to Config.VOICE_ID)
    
    Returns:
        Path to audio file, or None if generation failed
    
    Raises:
        ValueError: If text is empty or invalid
        Exception: If API call fails
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    # Validate text length
    MAX_TEXT_LENGTH = 5000
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Text too long. Maximum {MAX_TEXT_LENGTH} characters.")
    
    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check cache first
    cached_path = get_cached_audio_path(text)
    if cached_path.exists():
        file_size = cached_path.stat().st_size
        if file_size > 0:
            return str(cached_path)
        else:
            # Remove invalid cached file
            try:
                cached_path.unlink()
            except Exception:
                pass
    
    # Generate audio
    client = get_tts_client()
    if not client:
        print("⚠️  ElevenLabs client not available")
        return None
    
    try:
        voice_settings = VoiceSettings(
            stability=Config.VOICE_STABILITY,
            similarity_boost=Config.VOICE_SIMILARITY,
            style=Config.VOICE_STYLE,
            use_speaker_boost=Config.VOICE_SPEAKER_BOOST
        )
        
        # Generate audio with error handling
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id or Config.VOICE_ID,
            optimize_streaming_latency="0",
            output_format=Config.AUDIO_OUTPUT_FORMAT,
            text=text.strip(),
            model_id=Config.VOICE_MODEL,
            voice_settings=voice_settings
        )
        
        # Save to cache with error handling
        try:
            with open(cached_path, "wb") as audio_file:
                bytes_written = 0
                for chunk in audio_generator:
                    if chunk:
                        audio_file.write(chunk)
                        bytes_written += len(chunk)
            
            # Validate generated file
            if cached_path.exists():
                file_size = cached_path.stat().st_size
                if file_size > 0:
                    return str(cached_path)
                else:
                    # Remove invalid file
                    try:
                        cached_path.unlink()
                    except Exception:
                        pass
                    print("⚠️  Generated audio file is empty")
                    return None
            else:
                print("⚠️  Audio file was not created")
                return None
                
        except IOError as io_error:
            print(f"⚠️  File I/O error: {io_error}")
            # Clean up partial file
            if cached_path.exists():
                try:
                    cached_path.unlink()
                except Exception:
                    pass
            return None
        
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️  TTS API error: {error_msg}")
        
        # Clean up partial file on error
        if cached_path.exists():
            try:
                cached_path.unlink()
            except Exception:
                pass
        
        return None

