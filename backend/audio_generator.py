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
import time
import subprocess
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def write_status(status: str):
    """Write status to status.txt for frontend polling"""
    status_file = Path("workspace/status.txt")
    status_file.write_text(status)
    print(f"📊 Status: {status}")


def get_voice_settings() -> VoiceSettings:
    """
    Get optimized voice settings for fast-paced, concise narration.
    
    Returns:
        VoiceSettings: Configured voice settings object
    """
    return VoiceSettings(
        stability=Config.VOICE_STABILITY,
        similarity_boost=Config.VOICE_SIMILARITY,
        style=Config.VOICE_STYLE,
        use_speaker_boost=Config.VOICE_SPEAKER_BOOST
    )


def speed_up_audio(audio_path: str, speed_multiplier: float = 1.15) -> bool:
    """
    Speed up audio file using FFmpeg atempo filter.
    
    Args:
        audio_path (str): Path to the audio file to speed up
        speed_multiplier (float): Speed multiplier (e.g., 1.15 for 15% faster)
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Create temporary output path
    temp_path = audio_path.replace('.mp3', '_temp.mp3')
    
    try:
        # FFmpeg command to speed up audio
        # atempo filter accepts values between 0.5 and 2.0
        # For values > 2.0, we chain multiple atempo filters
        if speed_multiplier <= 2.0:
            atempo_filter = f"atempo={speed_multiplier}"
        else:
            # Chain multiple filters for speeds > 2.0
            num_filters = int(speed_multiplier / 2.0) + 1
            atempo_filter = ",".join(["atempo=2.0"] * num_filters)
            # Adjust last filter for remainder
            remainder = speed_multiplier / (2.0 ** num_filters)
            if remainder > 1.0:
                atempo_filter += f",atempo={remainder}"
        
        command = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i", audio_path,
            "-af", atempo_filter,
            "-c:a", "libmp3lame",  # MP3 codec
            "-b:a", "192k",  # Audio bitrate
            temp_path
        ]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Replace original with sped-up version
        os.replace(temp_path, audio_path)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Warning: Could not speed up audio {audio_path}: {e.stderr}", file=sys.stderr)
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return False
    except Exception as e:
        print(f"   ⚠️  Warning: Error speeding up audio {audio_path}: {e}", file=sys.stderr)
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return False


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


def generate_slide_audio(slide_text: str, output_filename: str, max_retries: int = 3) -> Optional[str]:
    """
    Generate audio narration for a single slide using ElevenLabs TTS.
    
    This function converts text to speech with a voice optimized for
    philosophical and educational content (deep, authoritative, calm).
    
    Args:
        slide_text (str): The speaker notes text to convert to speech
        output_filename (str): Name of the output audio file (e.g., 'audio_01.mp3')
        max_retries (int): Maximum number of retry attempts for rate limit errors
    
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
    output_path = str(Config.GENERATED_AUDIO_DIR / output_filename)
    
    # Clean up any existing invalid file first
    if os.path.exists(output_path):
        try:
            if not validate_audio_file(output_path):
                os.remove(output_path)
        except Exception:
            pass
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                # Exponential backoff for retries (2s, 4s, 8s)
                wait_time = 2 ** attempt
                print(f"   ⏳ Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            
            print(f"🎙️  Generating audio: {output_filename}")
            
            # Validate input - CRITICAL SAFETY CHECK
            if not slide_text or slide_text.strip() == "":
                print(f"   ❌ ERROR: Empty text provided for {output_filename}", file=sys.stderr)
                print(f"   This will cause TTS to fail. Check your slide data!", file=sys.stderr)
                return None
            
            # Check for minimum text length
            if len(slide_text.strip()) < 10:
                print(f"   ⚠️  WARNING: Very short text ({len(slide_text)} chars) for {output_filename}", file=sys.stderr)
            
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
            with open(output_path, "wb") as audio_file:
                for chunk in audio_generator:
                    if chunk:
                        audio_file.write(chunk)
            
            # Validate generated file
            if not validate_audio_file(output_path):
                print(f"   ❌ Generated audio file is invalid: {output_path}", file=sys.stderr)
                # Delete invalid file
                try:
                    os.remove(output_path)
                except Exception:
                    pass
                if attempt < max_retries - 1:
                    continue
                return None
            
            file_size_kb = os.path.getsize(output_path) / 1024
            print(f"   ✅ Audio saved: {output_path} ({file_size_kb:.1f} KB)")
            
            # Apply speed adjustment for faster pacing
            # Use getattr with default to handle cases where config hasn't been reloaded
            speed_multiplier = getattr(Config, 'AUDIO_SPEED_MULTIPLIER', 1.15)
            if speed_multiplier > 1.0:
                print(f"   ⚡ Speeding up audio by {speed_multiplier:.2f}x...")
                if speed_up_audio(output_path, speed_multiplier):
                    print(f"   ✅ Audio speed adjusted successfully")
                else:
                    print(f"   ⚠️  Speed adjustment failed, using original audio")
            
            return output_path
        
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error (429)
            is_rate_limit = "429" in error_str or "too_many_concurrent_requests" in error_str.lower()
            # Check if it's a quota exceeded error (401 with quota_exceeded)
            is_quota_exceeded = "401" in error_str and ("quota_exceeded" in error_str.lower() or "quota" in error_str.lower())
            
            # Clean up any partial/invalid file
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            
            if is_quota_exceeded:
                # Quota exceeded - don't retry, it won't help
                print(f"   ❌ QUOTA EXCEEDED for {output_filename}: {error_str}", file=sys.stderr)
                print(f"   ⚠️  ElevenLabs API quota has been exceeded. Please check your account or upgrade your plan.", file=sys.stderr)
                return None
            elif is_rate_limit and attempt < max_retries - 1:
                # Rate limit error - will retry with backoff
                print(f"   ⚠️  Rate limit error for {output_filename}: {error_str}", file=sys.stderr)
                continue
            else:
                # Other error or max retries reached
                print(f"   ❌ Error generating audio for {output_filename}: {error_str}", file=sys.stderr)
                if attempt == max_retries - 1:
                    return None
    
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
        
        print(f"\n🎵 Generating audio for {len(slides)} slides IN PARALLEL with Confucius-style voice...\n")
        
        def generate_audio_for_slide(i: int, slide: dict, total: int) -> Optional[str]:
            """Generate audio for a single slide - can run in parallel"""
            write_status(f"generating_audio:audio_{i}_of_{total}")
            
            speaker_notes = slide.get("speaker_notes", "")
            
            if not speaker_notes or speaker_notes.strip() == "":
                print(f"⚠️  Warning: Slide {i} has no speaker notes, skipping...", file=sys.stderr)
                return None
            
            output_filename = f"audio_{i:02d}.mp3"
            return generate_slide_audio(speaker_notes, output_filename)
        
        audio_paths = []
        failed_count = 0
        
        # Use ThreadPoolExecutor with max 2 workers (ElevenLabs API limit: 2 concurrent requests)
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit all tasks
            future_to_idx = {
                executor.submit(generate_audio_for_slide, i, slide, len(slides)): i
                for i, slide in enumerate(slides, start=1)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    audio_path = future.result()
                    if audio_path:
                        audio_paths.append(audio_path)
                    else:
                        failed_count += 1
                        print(f"❌ Failed to generate audio for slide {idx}", file=sys.stderr)
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error generating audio for slide {idx}: {str(e)}", file=sys.stderr)
        
        # Summary
        print(f"\n{'='*70}")
        print(f"✅ Successfully generated {len(audio_paths)} audio files")
        if failed_count > 0:
            print(f"❌ Failed to generate {failed_count} audio files")
            # Check if all failures were due to quota
            if len(audio_paths) == 0 and failed_count == len(slides):
                print(f"\n⚠️  WARNING: All audio generation failed!")
                print(f"   This may be due to ElevenLabs API quota being exceeded.")
                print(f"   Please check your ElevenLabs account and ensure you have sufficient credits.")
        print(f"{'='*70}\n")
        
        # Return audio paths even if some failed (partial success)
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


def main():
    """
    Main function for generating audio for all slides.
    Can be called from other scripts or run standalone.
    """
    print("=" * 70)
    print("🎙️  CONFUCIUS AUDIO GENERATOR")
    print("=" * 70)
    
    json_path = str(Config.OUTPUT_SLIDES_JSON)
    
    if not os.path.exists(json_path):
        print(f"\n❌ Error: {json_path} not found!", file=sys.stderr)
        print("   Please run slides_generator.py first", file=sys.stderr)
        raise FileNotFoundError(f"{json_path} not found")
    
    audio_paths = generate_all_slide_audios(json_path)
    
    if audio_paths:
        print(f"\n✨ Audio generation complete!")
        print(f"📁 Output directory: {Config.GENERATED_AUDIO_DIR}")
        print(f"📊 Generated {len(audio_paths)} audio file(s)")
        return audio_paths
    else:
        print(f"\n❌ Audio generation failed - no audio files were generated!")
        print(f"⚠️  This may be due to:")
        print(f"   1. ElevenLabs API quota exceeded (check your account)")
        print(f"   2. Invalid API key")
        print(f"   3. Network issues")
        print(f"   4. Empty or invalid slide content")
        raise Exception("Audio generation failed: No audio files were generated. Check ElevenLabs API quota and account status.")


if __name__ == "__main__":
    """
    Command-line entry point for standalone execution.
    Generates audio for all slides in generated_slides.json.
    """
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
