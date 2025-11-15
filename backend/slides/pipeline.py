"""
Main Pipeline Orchestrator for Confucius Lecture Summarizer

This module orchestrates the complete video generation pipeline:
1. Renders slides from JSON to PNG images
2. Generates audio narration using ElevenLabs TTS
3. Stitches slides and audio into a final MP4 video using FFmpeg

The pipeline includes comprehensive error handling, progress tracking,
and prerequisite validation to ensure smooth execution.

Functions:
    run_full_pipeline: Execute the complete video generation pipeline
    verify_prerequisites: Check all requirements before running

Usage:
    python3 pipeline.py
    
    Or programmatically:
    from pipeline import run_full_pipeline
    video_path = run_full_pipeline()
"""

import os
import sys
import json
from env_loader import load_env_file
from slides_renderer import render_slides_from_json
from audio_generator import generate_all_slide_audios
from video_stitcher import stitch_slides_to_video

# Load environment variables from .env file
load_env_file()

# Configuration
SLIDES_JSON = "generated_slides.json"
FINAL_VIDEO_NAME = "confucius_lecture_summary.mp4"


def run_full_pipeline():
    """
    Execute the complete pipeline:
    1. Render slides from JSON to PNG images
    2. Generate audio narration with ElevenLabs (Confucius voice)
    3. Stitch slides + audio into final video with FFmpeg
    
    Returns:
        str: Path to final video, or None if failed
    """
    print("=" * 70)
    print("🎓 CONFUCIUS LECTURE SUMMARIZER - FULL PIPELINE")
    print("=" * 70)
    print()
    
    # Check if slides JSON exists
    if not os.path.exists(SLIDES_JSON):
        print(f"❌ Error: {SLIDES_JSON} not found!", file=sys.stderr)
        print(f"   Please run slides_generator.py first to generate slides.", file=sys.stderr)
        return None
    
    # ============================================
    # STEP 1: Render Slides to PNG Images
    # ============================================
    print("📊 STEP 1: Rendering slides to PNG images...")
    print("-" * 70)
    
    try:
        slide_image_paths = render_slides_from_json(SLIDES_JSON)
        
        if not slide_image_paths:
            print("❌ Failed to render slides", file=sys.stderr)
            return None
        
        print(f"✅ Successfully rendered {len(slide_image_paths)} slides")
        print()
    
    except Exception as e:
        print(f"❌ Error rendering slides: {e}", file=sys.stderr)
        return None
    
    # ============================================
    # STEP 2: Generate Audio with ElevenLabs
    # ============================================
    print("🎙️  STEP 2: Generating Confucius-style narration with ElevenLabs...")
    print("-" * 70)
    
    try:
        audio_paths = generate_all_slide_audios(SLIDES_JSON)
        
        if not audio_paths:
            print("❌ Failed to generate audio files", file=sys.stderr)
            return None
        
        print(f"✅ Successfully generated {len(audio_paths)} audio files")
        print()
    
    except Exception as e:
        print(f"❌ Error generating audio: {e}", file=sys.stderr)
        return None
    
    # ============================================
    # STEP 3: Stitch Video with FFmpeg
    # ============================================
    print("🎬 STEP 3: Stitching slides and audio into final video...")
    print("-" * 70)
    
    try:
        final_video_path = stitch_slides_to_video(
            slide_image_paths, 
            audio_paths, 
            FINAL_VIDEO_NAME
        )
        
        if not final_video_path:
            print("❌ Failed to create final video", file=sys.stderr)
            return None
        
        print()
        print("=" * 70)
        print("✨ PIPELINE COMPLETE!")
        print("=" * 70)
        print()
        print(f"📹 Final Video: {os.path.abspath(final_video_path)}")
        
        # Get video duration estimate
        with open(SLIDES_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            num_slides = len(data.get("slides", []))
        
        print(f"📊 Statistics:")
        print(f"   • Number of slides: {num_slides}")
        print(f"   • Audio files: {len(audio_paths)}")
        print(f"   • Video segments: {num_slides}")
        
        file_size = os.path.getsize(final_video_path) / (1024 * 1024)
        print(f"   • File size: {file_size:.2f} MB")
        
        print()
        print("🎉 Your Confucius-narrated lecture summary is ready!")
        print()
        
        return final_video_path
    
    except Exception as e:
        print(f"❌ Error stitching video: {e}", file=sys.stderr)
        return None


def verify_prerequisites():
    """
    Verify all prerequisites are met before running pipeline.
    
    Returns:
        bool: True if all prerequisites met, False otherwise
    """
    issues = []
    
    # Check environment variables (will auto-load from .env if present)
    if not os.environ.get("ELEVENLABS_API_KEY"):
        issues.append("ELEVENLABS_API_KEY not found in .env file or environment variables")
    
    if not os.environ.get("GEMINI_API_KEY"):
        issues.append("GEMINI_API_KEY not found in .env file or environment variables")
    
    # Check if slides JSON exists
    if not os.path.exists(SLIDES_JSON):
        issues.append(f"{SLIDES_JSON} not found - run slides_generator.py first")
    
    # Check if FFmpeg is installed
    import subprocess
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        issues.append("FFmpeg not installed - install with 'brew install ffmpeg'")
    
    if issues:
        print("❌ Prerequisites not met:", file=sys.stderr)
        for issue in issues:
            print(f"   • {issue}", file=sys.stderr)
        print()
        return False
    
    return True


if __name__ == "__main__":
    # Verify prerequisites
    if not verify_prerequisites():
        print("\n💡 Setup Instructions:")
        print("   1. Install FFmpeg: brew install ffmpeg")
        print("   2. Install Python packages: pip install -r ../requirements.txt")
        print("   3. Create .env file in backend/ directory:")
        print("      cp ../.env.example ../.env")
        print("      # Edit ../.env and add your API keys")
        print("   4. Generate slides: python3 slides_generator.py")
        print("   5. Run this pipeline: python3 pipeline.py")
        print()
        sys.exit(1)
    
    # Run the full pipeline
    result = run_full_pipeline()
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
