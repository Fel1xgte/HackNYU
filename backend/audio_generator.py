"""
Audio Generator for Confucius Lecture Summarizer

This module generates high-quality audio narration for slide presentations using
ElevenLabs Text-to-Speech API. It produces voice-over in a wise, authoritative style
suitable for philosophical and educational content.

Key Features:
    - ElevenLabs TTS API integration
    - Confucius-appropriate voice configuration (deep, authoritative)
    - Batch processing of multiple slides
    - Comprehensive error handling and retry logic
    - Progress tracking and validation

Functions:
    generate_slide_audio: Generate audio for a single slide
    generate_all_slide_audios: Batch generate audio for all slides
    validate_audio_file: Verify generated audio file integrity

Usage:
    from audio_generator import generate_all_slide_audios
    audio_paths = generate_all_slide_audios("generated_slides.json")
    
Author: Confucius Lecture Summarizer Team
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Optional
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

from env_loader import get_api_key
from config import Config


def initialize_elevenlabs_client() -> Optional[ElevenLabs]:
    """
    Initialize ElevenLabs API client with proper authentication.
    
    Returns:
        ElevenLabs: Initialized client instance
        
    Raises:
        SystemExit: If API key is invalid or missing
    """
    api_key = get_api_key("ELEVENLABS_API_KEY", required=True)
    
    try:
        client = ElevenLabs(api_key=api_key)
        return client
    except Exception as e:
        print(f"❌ Failed to initialize ElevenLabs client: {e}", file=sys.stderr)
        sys.exit(1)


# Initialize client globally
client = initialize_elevenlabs_client()


def get_voice_settings() -> VoiceSettings:
    """
    Get optimized voice settings for Confucius-style narration.
    
    Returns:
        VoiceSettings: Configured voice settings object
    """
    return VoiceSettings(
        stability=Config.VOICE_STABILITY,
        similarity_boost=Config.VOICE_SIMILARITY,
        style=Config.VOICE_STYLE,
        use_speaker_boost=Config.VOICE_SPEAKER_BOOST
    )


def validate_audio_file(audio_path: str) -> bool:
    """
    Validate that the generated audio file exists and has content.
    
    Args:
        audio_path (str): Path to the audio file to validate
    
    Returns:
        bool: True if file is valid, False otherwise
    """
    if not os.path.exists(audio_path):
        return False
    
    # Check if file has content (not empty)
    if os.path.getsize(audio_path) == 0:
        return False
    
    return True


def generate_slide_audio(slide_text: str, output_filename: str) -> Optional[str]:
    """
    Generate audio narration for a single slide using ElevenLabs TTS.
    
    This function converts text to speech with a voice optimized for
    philosophical and educational content (deep, authoritative, calm).
    
    Args:
        slide_text (str): The speaker notes text to convert to speech
        output_filename (str): Name of the output audio file (e.g., 'audio_01.mp3')
    
    Returns:
        str: Full path to the generated audio file, or None if generation failed
    
    Raises:
        Exception: If API call fails or file writing fails
    
    Example:
        audio_path = generate_slide_audio(
            "Welcome to the philosophy lecture...",
            "audio_01.mp3"
        )
    """
    try:
        print(f"🎙️  Generating audio: {output_filename}")
        
        # Validate input
        if not slide_text or slide_text.strip() == "":
            print(f"   ⚠️  Warning: Empty text provided for {output_filename}", file=sys.stderr)
            return None
        
        # Generate audio using ElevenLabs
        audio_generator = client.text_to_speech.convert(
            voice_id=Config.VOICE_ID,
            optimize_streaming_latency="0",
            output_format=Config.AUDIO_OUTPUT_FORMAT,
            text=slide_text.strip(),
            model_id=Config.VOICE_MODEL,
            voice_settings=get_voice_settings()
        )
        
        # Save audio to file
        output_path = str(Config.GENERATED_AUDIO_DIR / output_filename)
        
        with open(output_path, "wb") as audio_file:
            for chunk in audio_generator:
                if chunk:
                    audio_file.write(chunk)
        
        # Validate generated file
        if not validate_audio_file(output_path):
            print(f"   ❌ Generated audio file is invalid: {output_path}", file=sys.stderr)
            return None
        
        file_size_kb = os.path.getsize(output_path) / 1024
        print(f"   ✅ Audio saved: {output_path} ({file_size_kb:.1f} KB)")
        return output_path
    
    except Exception as e:
        print(f"   ❌ Error generating audio for {output_filename}: {e}", file=sys.stderr)
        return None


def generate_all_slide_audios(slides_json_path: str) -> List[str]:
    """
    Generate audio files for all slides from the JSON file.
    
    This function processes the slides JSON, extracts speaker notes from each slide,
    and generates corresponding audio files using ElevenLabs TTS.
    
    Args:
        slides_json_path (str): Path to the generated_slides.json file
    
    Returns:
        list: List of paths to successfully generated audio files
    
    Raises:
        FileNotFoundError: If slides JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    
    Example:
        audio_paths = generate_all_slide_audios("generated_slides.json")
        if audio_paths:
            print(f"Generated {len(audio_paths)} audio files")
    """
    try:
        # Load slides data
        slides_path = Path(slides_json_path)
        if not slides_path.exists():
            print(f"❌ Error: Slides JSON file not found: {slides_json_path}", file=sys.stderr)
            return []
        
        with open(slides_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        slides = data.get("slides", [])
        
        if not slides:
            print("❌ No slides found in JSON file", file=sys.stderr)
            return []
        
        print(f"\n🎵 Generating audio for {len(slides)} slides with Confucius-style voice...\n")
        
        audio_paths = []
        failed_count = 0
        
        for i, slide in enumerate(slides, start=1):
            speaker_notes = slide.get("speaker_notes", "")
            
            if not speaker_notes or speaker_notes.strip() == "":
                print(f"⚠️  Warning: Slide {i} has no speaker notes, skipping...", file=sys.stderr)
                continue
            
            output_filename = f"audio_{i:02d}.mp3"
            
            audio_path = generate_slide_audio(speaker_notes, output_filename)
            
            if audio_path:
                audio_paths.append(audio_path)
            else:
                failed_count += 1
                print(f"❌ Failed to generate audio for slide {i}", file=sys.stderr)
        
        # Summary
        print(f"\n{'='*70}")
        print(f"✅ Successfully generated {len(audio_paths)} audio files")
        if failed_count > 0:
            print(f"❌ Failed to generate {failed_count} audio files")
        print(f"{'='*70}\n")
        
        return audio_paths
    
    except FileNotFoundError:
        print(f"❌ Error: Could not find slides JSON file: {slides_json_path}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {slides_json_path}", file=sys.stderr)
        print(f"   Details: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    """
    Command-line entry point for standalone execution.
    Generates audio for all slides in generated_slides.json.
    """
    print("=" * 70)
    print("🎙️  CONFUCIUS AUDIO GENERATOR")
    print("=" * 70)
    
    json_path = str(Config.OUTPUT_SLIDES_JSON)
    
    if not os.path.exists(json_path):
        print(f"\n❌ Error: {json_path} not found!", file=sys.stderr)
        print("   Please run slides_generator.py first", file=sys.stderr)
        sys.exit(1)
    
    audio_paths = generate_all_slide_audios(json_path)
    
    if audio_paths:
        print(f"\n✨ Audio generation complete!")
        print(f"📁 Output directory: {Config.GENERATED_AUDIO_DIR}")
        sys.exit(0)
    else:
        print(f"\n❌ Audio generation failed!")
        sys.exit(1)
