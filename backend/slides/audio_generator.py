"""
Audio Generator for Confucius Lecture Summarizer

This module generates audio narration for slides using ElevenLabs Text-to-Speech API.
It uses a Confucius-appropriate voice (deep, authoritative) for philosophical content.

Key Features:
    - ElevenLabs TTS integration with custom voice settings
    - Optimized for ancient philosopher narration style
    - Batch processing of multiple slides
    - Error handling and progress tracking

Functions:
    generate_slide_audio: Generate audio for a single slide
    generate_all_slide_audios: Generate audio for all slides from JSON
    get_available_voices: List all available ElevenLabs voices

Usage:
    from audio_generator import generate_all_slide_audios
    audio_paths = generate_all_slide_audios("generated_slides.json")
"""

import os
import sys
import json
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from env_loader import get_api_key

# Initialize ElevenLabs client
# API key will be automatically loaded from .env file or environment variables
ELEVENLABS_API_KEY = get_api_key("ELEVENLABS_API_KEY", required=True)

if not ELEVENLABS_API_KEY:
    sys.exit(1)

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Output directory for audio files
AUDIO_OUTPUT_DIR = "generated_audio"
os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)

# Voice configuration for ancient Chinese philosopher theme
# Using a voice that sounds wise, aged, and authoritative
VOICE_CONFIG = {
    "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - deep, authoritative voice
    "model_id": "eleven_multilingual_v2",
    "voice_settings": VoiceSettings(
        stability=0.7,  # Higher stability for calm, steady narration
        similarity_boost=0.8,  # Maintain voice consistency
        style=0.4,  # Moderate expressiveness
        use_speaker_boost=True
    )
}


def generate_slide_audio(slide_text, output_filename):
    """
    Generate audio narration for a single slide using ElevenLabs TTS.
    
    Args:
        slide_text (str): The speaker notes text to convert to speech
        output_filename (str): Name of the output audio file (e.g., 'audio_01.mp3')
    
    Returns:
        str: Full path to the generated audio file
    """
    try:
        print(f"🎙️  Generating audio: {output_filename}")
        
        # Generate audio using ElevenLabs
        audio_generator = client.text_to_speech.convert(
            voice_id=VOICE_CONFIG["voice_id"],
            optimize_streaming_latency="0",
            output_format="mp3_44100_128",
            text=slide_text,
            model_id=VOICE_CONFIG["model_id"],
            voice_settings=VOICE_CONFIG["voice_settings"]
        )
        
        # Save audio to file
        output_path = os.path.join(AUDIO_OUTPUT_DIR, output_filename)
        
        with open(output_path, "wb") as audio_file:
            for chunk in audio_generator:
                audio_file.write(chunk)
        
        print(f"   ✅ Audio saved: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"   ❌ Error generating audio for {output_filename}: {e}", file=sys.stderr)
        raise


def generate_all_slide_audios(slides_json_path):
    """
    Generate audio files for all slides from the JSON file.
    
    Args:
        slides_json_path (str): Path to the generated_slides.json file
    
    Returns:
        list: List of paths to generated audio files
    """
    try:
        with open(slides_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        slides = data.get("slides", [])
        
        if not slides:
            print("❌ No slides found in JSON file", file=sys.stderr)
            return []
        
        print(f"\n🎵 Generating audio for {len(slides)} slides with Confucius-style voice...\n")
        
        audio_paths = []
        
        for i, slide in enumerate(slides, start=1):
            speaker_notes = slide.get("speaker_notes", "")
            
            if not speaker_notes:
                print(f"⚠️  Warning: Slide {i} has no speaker notes, skipping...")
                continue
            
            output_filename = f"audio_{i:02d}.mp3"
            
            try:
                audio_path = generate_slide_audio(speaker_notes, output_filename)
                audio_paths.append(audio_path)
            except Exception as e:
                print(f"❌ Failed to generate audio for slide {i}: {e}", file=sys.stderr)
                # Create a placeholder or skip
                continue
        
        print(f"\n✅ Successfully generated {len(audio_paths)} audio files!")
        return audio_paths
    
    except FileNotFoundError:
        print(f"❌ Error: Could not find slides JSON file: {slides_json_path}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in file: {slides_json_path}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return []


def get_available_voices():
    """
    List all available ElevenLabs voices to help choose the best one.
    Useful for finding voices that sound like Confucius.
    """
    try:
        print("\n🎤 Available ElevenLabs Voices:\n")
        
        voices = client.voices.get_all()
        
        for voice in voices.voices:
            print(f"   • {voice.name}")
            print(f"     ID: {voice.voice_id}")
            print(f"     Description: {voice.description or 'No description'}")
            print(f"     Category: {voice.category}")
            print()
        
        return voices.voices
    
    except Exception as e:
        print(f"❌ Error fetching voices: {e}", file=sys.stderr)
        return []


if __name__ == "__main__":
    # If run directly, generate audio for all slides
    SLIDES_JSON = "generated_slides.json"
    
    # Uncomment to see available voices
    # get_available_voices()
    
    audio_files = generate_all_slide_audios(SLIDES_JSON)
    
    if audio_files:
        print(f"\n✨ Audio generation complete! Generated {len(audio_files)} files.")
    else:
        print("\n❌ Audio generation failed!")
        sys.exit(1)
