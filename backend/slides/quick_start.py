#!/usr/bin/env python3
"""
CONFUCIUS LECTURE SUMMARIZER - QUICK START GUIDE

This guide helps you get started with the video generation pipeline.
"""

import os
import sys

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_section(title):
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print('─' * 70 + "\n")

def check_environment():
    """Check if the environment is properly set up."""
    print_header("🔍 ENVIRONMENT CHECK")
    
    issues = []
    
    # Check Python version
    import sys
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (need 3.8+)")
        issues.append("Python version too old")
    
    # Check FFmpeg
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✅ FFmpeg installed")
    except:
        print("❌ FFmpeg not installed")
        issues.append("Install FFmpeg with: brew install ffmpeg")
    
    # Check for .env file
    from pathlib import Path
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found (will use environment variables)")
    
    # Load environment variables (will try .env file first)
    from env_loader import load_env_file
    load_env_file()
    
    # Check environment variables
    if os.environ.get("ELEVENLABS_API_KEY"):
        print("✅ ELEVENLABS_API_KEY set")
    else:
        print("❌ ELEVENLABS_API_KEY not set")
        issues.append("Create .env file or set ELEVENLABS_API_KEY")
    
    if os.environ.get("GEMINI_API_KEY"):
        print("✅ GEMINI_API_KEY set")
    else:
        print("❌ GEMINI_API_KEY not set")
        issues.append("Create .env file or set GEMINI_API_KEY")
    
    # Check Python packages
    required_packages = ["elevenlabs", "PIL", "google.generativeai"]
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} package installed")
        except ImportError:
            print(f"❌ {package} package not installed")
            issues.append(f"Install with: pip install -r requirements.txt")
            break
    
    return issues

def print_usage_guide():
    """Print usage instructions."""
    print_header("📖 USAGE GUIDE")
    
    print_section("🎯 FULL PIPELINE (Recommended)")
    print("Run everything in one command:")
    print("  python3 pipeline.py")
    print()
    print("This will:")
    print("  1. Render slides to PNG images")
    print("  2. Generate Confucius-style audio narration with ElevenLabs")
    print("  3. Stitch slides + audio into final video with FFmpeg")
    
    print_section("🔧 INDIVIDUAL STEPS")
    print("If you need more control, run steps individually:")
    print()
    print("Step 1: Generate slides from transcript")
    print("  python3 slides_generator.py")
    print("  → Creates: generated_slides.json")
    print()
    print("Step 2: Render slides to PNG images")
    print("  python3 slides_renderer.py")
    print("  → Creates: rendered_slides/slide_01.png, slide_02.png, ...")
    print()
    print("Step 3: Generate audio narration")
    print("  python3 audio_generator.py")
    print("  → Creates: generated_audio/audio_01.mp3, audio_02.mp3, ...")
    print()
    print("Step 4: Stitch video")
    print("  python3 video_stitcher.py")
    print("  → Creates: final_output/final_video.mp4")
    
    print_section("🎙️  ELEVENLABS VOICE CONFIGURATION")
    print("The Confucius voice is configured in audio_generator.py:")
    print()
    print("Current settings:")
    print("  • Voice: Adam (deep, authoritative)")
    print("  • Model: eleven_multilingual_v2")
    print("  • Stability: 0.7 (calm, steady)")
    print("  • Similarity Boost: 0.8 (consistent)")
    print()
    print("To see all available voices:")
    print("  1. Open audio_generator.py")
    print("  2. Uncomment: # get_available_voices()")
    print("  3. Run: python3 audio_generator.py")
    print()
    print("To change voice:")
    print("  1. Edit VOICE_CONFIG in audio_generator.py")
    print("  2. Update voice_id to your preferred voice")
    
    print_section("📁 OUTPUT STRUCTURE")
    print("After running the pipeline, you'll have:")
    print()
    print("slides/")
    print("├── generated_slides.json           # Slide content (input)")
    print("├── rendered_slides/                # PNG images")
    print("│   ├── slide_01.png")
    print("│   ├── slide_02.png")
    print("│   └── ...")
    print("├── generated_audio/                # MP3 audio files")
    print("│   ├── audio_01.mp3")
    print("│   ├── audio_02.mp3")
    print("│   └── ...")
    print("├── video_segments/                 # Individual video clips")
    print("│   ├── segment_01.mp4")
    print("│   ├── segment_02.mp4")
    print("│   └── ...")
    print("└── final_output/                   # Final video ✨")
    print("    └── confucius_lecture_summary.mp4")
    
    print_section("⚙️  CUSTOMIZATION OPTIONS")
    print("You can customize various aspects:")
    print()
    print("1. Slide appearance (slides_renderer.py):")
    print("   • Background color")
    print("   • Font sizes and styles")
    print("   • Layout and positioning")
    print()
    print("2. Voice settings (audio_generator.py):")
    print("   • Voice selection")
    print("   • Speech rate and pitch")
    print("   • Stability and similarity")
    print()
    print("3. Video quality (video_stitcher.py):")
    print("   • Video codec settings")
    print("   • Audio bitrate")
    print("   • Output filename")
    
    print_section("🐛 TROUBLESHOOTING")
    print("Common issues and solutions:")
    print()
    print("Issue: 'FFmpeg not found'")
    print("  → Install: brew install ffmpeg")
    print()
    print("Issue: 'ELEVENLABS_API_KEY not set'")
    print("  → Create .env file in backend/ directory:")
    print("    cp ../.env.example ../.env")
    print("    # Edit ../.env and add your API keys")
    print("  → Or set environment variable:")
    print("    export ELEVENLABS_API_KEY='your-key-here'")
    print()
    print("Issue: 'Import error: elevenlabs'")
    print("  → Install: pip install -r ../requirements.txt")
    print()
    print("Issue: 'Font not found' error")
    print("  → macOS uses different font paths")
    print("  → Edit slides_renderer.py and use system fonts")
    print()
    print("Issue: Video segments don't match audio length")
    print("  → FFmpeg -shortest flag handles this automatically")
    print("  → Each segment will be exactly as long as its audio")
    
    print_section("💡 PRO TIPS")
    print("• Test with a small number of slides first (2-3)")
    print("• Audio generation takes ~5-10 seconds per slide")
    print("• Video stitching is very fast (<10 seconds total)")
    print("• Keep speaker_notes concise for better pacing")
    print("• Use natural, conversational language for best TTS results")
    print("• The Confucius theme works best with philosophical content")

def print_api_info():
    """Print API setup information."""
    print_header("🔑 API SETUP")
    
    print("This project uses two APIs:")
    print()
    print("1. ElevenLabs API (Text-to-Speech)")
    print("   • Get your API key: https://elevenlabs.io/")
    print("   • Used for: Confucius-style narration")
    print()
    print("2. Google Gemini API (Slide Generation)")
    print("   • Get your API key: https://makersuite.google.com/app/apikey")
    print("   • Used for: Generating slide content from transcripts")
    print()
    print("Setup with .env file (RECOMMENDED):")
    print("   1. Copy the example: cp ../env.example ../.env")
    print("   2. Edit ../.env and add your API keys")
    print("   3. Run your scripts - keys will load automatically!")
    print()
    print("Alternative - Environment variables:")
    print("   export ELEVENLABS_API_KEY='your-key'")
    print("   export GEMINI_API_KEY='your-key'")

def main():
    """Main function."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║         🎓 CONFUCIUS LECTURE SUMMARIZER - QUICK START            ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Check environment
    issues = check_environment()
    
    if issues:
        print("\n⚠️  Please fix the following issues before proceeding:\n")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print()
        return
    
    print("\n✅ Environment is ready!")
    
    # Print guides
    print_api_info()
    print_usage_guide()
    
    print_header("🚀 READY TO START!")
    print("Quick start:")
    print("  cd slides")
    print("  python3 pipeline.py")
    print()

if __name__ == "__main__":
    main()
