"""
Configuration Module for Confucius Lecture Summarizer

Centralized configuration management for all components of the video generation pipeline.
This module provides a single source of truth for all configuration constants, paths,
and settings used throughout the application.

Constants:
    - Directory paths for input/output
    - API configuration settings
    - Video generation parameters
    - Voice and audio settings
    - FFmpeg encoding parameters

Usage:
    from config import Config
    client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
"""

import os
from pathlib import Path

class Config:
    """
    Centralized configuration class for the Confucius Lecture Summarizer.
    All paths, API keys, and parameters are defined here for easy maintenance.
    """
    
    # ============================================
    # Directory Structure
    # ============================================
    BASE_DIR = Path(__file__).parent
    
    # Central working directory for all dynamic files
    WORKSPACE_DIR = BASE_DIR / "workspace"
    
    # Input directories
    INPUT_JSON_PATH = WORKSPACE_DIR / "decoded_video.json"
    
    # Output directories
    OUTPUT_SLIDES_JSON = WORKSPACE_DIR / "generated_slides.json"
    RENDERED_SLIDES_DIR = WORKSPACE_DIR / "rendered_slides"
    GENERATED_AUDIO_DIR = WORKSPACE_DIR / "generated_audio"
    VIDEO_SEGMENTS_DIR = WORKSPACE_DIR / "video_segments"
    FINAL_OUTPUT_DIR = WORKSPACE_DIR / "final_output"
    FRAMES_DIR = WORKSPACE_DIR / "frames"
    
    # Ensure output directories exist
    @classmethod
    def create_directories(cls):
        """Create all required output directories if they don't exist."""
        for directory in [
            cls.WORKSPACE_DIR,
            cls.RENDERED_SLIDES_DIR,
            cls.GENERATED_AUDIO_DIR,
            cls.VIDEO_SEGMENTS_DIR,
            cls.FINAL_OUTPUT_DIR,
            cls.FRAMES_DIR
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    # ============================================
    # API Configuration
    # ============================================
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    
    # ============================================
    # Video Generation Settings
    # ============================================
    TARGET_VIDEO_DURATION = 90  # seconds
    FINAL_VIDEO_NAME = "confucius_lecture_summary.mp4"
    
    # Video encoding parameters
    VIDEO_WIDTH = 1920
    VIDEO_HEIGHT = 1080
    VIDEO_CODEC = "libx264"
    VIDEO_PIXEL_FORMAT = "yuv420p"
    
    # Audio encoding parameters
    AUDIO_CODEC = "aac"
    AUDIO_BITRATE = "192k"
    AUDIO_OUTPUT_FORMAT = "mp3_44100_128"
    
    # ============================================
    # ElevenLabs Voice Configuration
    # ============================================
    VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam - deep, authoritative
    VOICE_MODEL = "eleven_multilingual_v2"
    VOICE_STABILITY = 0.7  # Calm, steady narration
    VOICE_SIMILARITY = 0.8  # High consistency
    VOICE_STYLE = 0.4  # Moderate expressiveness
    VOICE_SPEAKER_BOOST = True
    
    # Audio speed adjustment for faster pacing
    AUDIO_SPEED_MULTIPLIER = 1.15  # 15% faster (1.15x speed) for more concise narration
    
    # ============================================
    # Google Gemini Configuration
    # ============================================
    # Available models: gemini-pro, gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp
    # Using 2.0-flash-exp for best balance of speed, quality, and improved reasoning
    GEMINI_MODEL = "gemini-2.0-flash-exp"  # Latest experimental model with enhanced capabilities
    
    # ============================================
    # Slide Rendering Settings
    # ============================================
    SLIDE_BACKGROUND_COLOR = "#111111"
    SLIDE_TITLE_COLOR = "white"
    SLIDE_TEXT_COLOR = "#DDDDDD"
    SLIDE_TITLE_FONT_SIZE = 80
    SLIDE_BODY_FONT_SIZE = 48
    SLIDE_TEXT_WRAP_WIDTH = 40
    
    # Font paths (with fallbacks)
    FONT_PATHS_TITLE = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    
    FONT_PATHS_BODY = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]


# Initialize directories on module import
Config.create_directories()