"""
Slide Generator for Confucius Lecture Summarizer

This module generates slide content from transcript data using Google Gemini AI.
It processes audio segments and visual keyframes to create structured slide content
with titles, bullet points, and speaker notes.

Key Features:
    - Google Gemini AI integration for content generation
    - Automatic JSON response cleaning and parsing
    - Transcript-to-slide conversion with timing information
    - Error handling and fallback mechanisms

Functions:
    create_gemini_client: Initialize Gemini API client
    clean_json_response: Extract JSON from AI responses
    generate_slide_content: Generate content for a single slide
    process_transcript_to_slides: Convert full transcript to slides
    main: Command-line entry point

Usage:
    python3 slides_generator.py
"""

import json
import os
import sys
import re
from google import genai
from env_loader import get_api_key



API_KEY_ENV_VAR = "GEMINI_API_KEY"
MODEL_NAME = "gemini-2.5-flash"   # or "gemini-1.5-pro"
INPUT_JSON_PATH = "sample_transcript.json"
OUTPUT_JSON_PATH = "generated_slides.json"


# ------------------------------------------------------
# Gemini Client Initialization
# ------------------------------------------------------

def create_gemini_client():
    """
    Initializes the latest Gemini Client (2025 version).
    API key will be automatically loaded from .env file or environment variables.
    """

    api_key = get_api_key(API_KEY_ENV_VAR, required=True)
    if not api_key:
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        print(f"✨ Gemini client initialized: {MODEL_NAME}")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize Gemini client: {e}", file=sys.stderr)
        return None


# ------------------------------------------------------
# Response Cleaning
# ------------------------------------------------------

def clean_json_response(raw):
    """
    Removes ```json wrappers and extracts the raw JSON string.
    
    Args:
        raw (str): Raw response text from Gemini API
    
    Returns:
        str: Cleaned JSON string ready for parsing
    """
    if not raw:
        return "{}"
    
    m = re.search(r'```json\s*([\s\S]*?)```', raw)
    if m:
        return m.group(1)

    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        return m.group(0)

    return raw.strip()


# ------------------------------------------------------
# Core LLM Call
# ------------------------------------------------------

def generate_slide_content(client, ocr_text, speech_text, caption):
    """
    Calls Gemini 2.5 API to produce title + points + speaker_notes.
    
    Args:
        client: Initialized Gemini client
        ocr_text (str): Text extracted from slide images via OCR
        speech_text (str): Transcribed speech from audio
        caption (str): Visual description of the slide
    
    Returns:
        dict: Slide content with 'title', 'points', and 'speaker_notes' keys
    """

    if not client:
        return {
            "title": "LLM Init Failed",
            "points": [],
            "speaker_notes": "Gemini client not available."
        }

    prompt = f"""
You are an instructional designer. Create a clean slide.

[OCR Text]
{ocr_text}

[Speech Transcript]
{speech_text}

[Visual Caption]
{caption}

Return ONLY JSON:
{{
  "title": "...",
  "points": ["...", "..."],
  "speaker_notes": "..."
}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        raw_text = response.text
        cleaned = clean_json_response(raw_text)
        return json.loads(cleaned)

    except Exception as e:
        print(f"❌ Parse Error: {e}", file=sys.stderr)
        return {
            "title": "Parse Error",
            "points": [],
            "speaker_notes": "Failed to parse JSON."
        }


# ------------------------------------------------------
# Build Slides From Transcript
# ------------------------------------------------------

def process_transcript_to_slides(client, data):
    """
    Convert transcript data into structured slides.
    
    Args:
        client: Initialized Gemini client
        data (dict): Transcript data with 'audio_segments' and 'visual_keyframes'
    
    Returns:
        dict: Dictionary with 'slides' key containing list of slide objects
    """
    if not data:
        print("❌ Error: No transcript data provided", file=sys.stderr)
        return {"slides": []}

    audio_segments = data.get("audio_segments", [])
    keyframes = data.get("visual_keyframes", [])
    
    if not keyframes:
        print("⚠️  Warning: No visual keyframes found in transcript data", file=sys.stderr)
        return {"slides": []}

    slides = [kf for kf in keyframes if kf.get("kind") == "slide"]
    slides.sort(key=lambda x: x["time_sec"])

    final_slides = []

    for i, kf in enumerate(slides):
        start = kf["time_sec"]
        end = slides[i+1]["time_sec"] if i+1 < len(slides) else float("inf")

        speech_chunks = [
            seg["text"] for seg in audio_segments
            if start <= seg["start_sec"] < end
        ]
        speech_text = " ".join(speech_chunks) or "(no transcript)"

        ocr_text = kf.get("ocr_text", "")
        caption = kf.get("caption", "")

        print(f"➡️ Generating Slide {i+1}...")

        slide = generate_slide_content(client, ocr_text, speech_text, caption)
        slide["slide_number"] = i + 1
        slide["source_frame"] = kf.get("image_path")

        final_slides.append(slide)

    return { "slides": final_slides }


# ------------------------------------------------------
# Entrypoint
# ------------------------------------------------------

def main():
    """
    Main entry point for slide generation.
    Loads transcript data, generates slides, and saves to JSON.
    """
    try:
        client = create_gemini_client()
        if not client:
            print("❌ Failed to initialize Gemini client", file=sys.stderr)
            sys.exit(1)

        # Load input data with proper error handling
        if not os.path.exists(INPUT_JSON_PATH):
            print(f"❌ Error: Input file not found: {INPUT_JSON_PATH}", file=sys.stderr)
            sys.exit(1)
        
        with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Process transcript to slides
        result = process_transcript_to_slides(client, data)
        
        if not result.get("slides"):
            print("⚠️  Warning: No slides were generated", file=sys.stderr)

        # Save output with UTF-8 encoding
        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n✅ DONE → {len(result.get('slides', []))} slides saved to {OUTPUT_JSON_PATH}\n")
    
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
