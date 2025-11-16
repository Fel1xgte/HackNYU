# -*- coding: utf-8 -*-
"""
slides.py

This script now reads the JSON output from transcript_condenser.py
and generates high-quality slide images using the Gemini 2.5 model.
"""

import os
import json
import base64
import requests
import sys
from config import Config
from env_loader import get_api_key

# ================== CONFIG ==================
# 1. API Key is now loaded securely
OPENROUTER_API_KEY = get_api_key("OPENROUTER_API_KEY", required=True)

MODEL_NAME = "google/gemini-2.5-flash-image-preview"
ASPECT_RATIO = "16:9"

# 2. Output directory is now linked to your config
OUTPUT_DIR = str(Config.RENDERED_SLIDES_DIR)
# This directory is already created by config.py
# os.makedirs(OUTPUT_DIR, exist_ok=True)


# ================== JSON Input Removed ==================
# The hardcoded SLIDESHOW_JSON variable has been removed.
# This script will now load 'generated_slides.json' from your workspace.


# ================== Helper: JSON -> prompt ==================
def slide_to_prompt(slide: dict, index: int, total: int) -> str:
    """
    Build a natural language prompt for a slide image.
    This is adapted from your original file but uses a hardcoded theme
    and only the fields available from transcript_condenser's output.
    """
    
    # Theme is now hardcoded, as it's no longer in the input JSON
    theme = {
      "vibe": "clean, modern, business-learning hybrid",
      "colors": "#0F172A, #1D4ED8, #FACC15, #F9FAFB",
      "font_style": "sans-serif, large headings, generous white space",
      "layout_principles": "1 idea per slide; Strong visual anchor; Consistent titles"
    }

    # Data from generated_slides.json
    title = slide.get("title", "Untitled")
    key_message = slide.get("key_message", "")
    # Use "points" (from transcript_condenser) not "bullets"
    bullets = slide.get("points", [])
    bullets_text = "\n".join(f"- {b}" for b in bullets)
    
    # Use speaker_notes (from transcript_condenser)
    speaker_notes = slide.get("speaker_notes", "")
    speaker_notes_text = f"Speaker notes for intent: {speaker_notes}"


    prompt = f"""
You are a world-class presentation designer.

Generate a SINGLE 16:9 slide image for slide {index} of {total}.
The slide should be flat artwork (no UI chrome, no extra borders).

Global theme:
- Vibe: {theme.get("vibe")}
- Colors: {theme.get("colors")}
- Font style: {theme.get("font_style")}
- Layout principles: {theme.get("layout_principles")}

Slide spec:
- Title: {title}
- Key message: {key_message}

Body bullets (these are the on-slide text, keep them concise and legible):
{bullets_text}

Design requirements:
- Clean, modern, educational look.
- High contrast with the given color palette.
- Plenty of white space.
- Title consistent across slides (position & style).
- Bullets aligned as a column.
- No watermarks, no logos, no extra text besides title, subtitle, and bullets.
- {speaker_notes_text} (Use this for INSPIRATION ONLY. DO NOT render this text on the slide).

Output: a single, well-composed 16:9 slide image.
"""
    return prompt.strip()

# ================== Core OpenRouter call + saving ==================

def call_openrouter_image(prompt: str, aspect_ratio: str = "16:9") -> str:
    """
    Call OpenRouter to generate an image from a text prompt.
    Returns a data URL: 'data:image/png;base64,...'
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost", # Added for compliance
        "X-Title": "ConfuciusSummarizer" # Added for compliance
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": aspect_ratio
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()

        if not result.get("choices"):
            raise RuntimeError("No choices returned from OpenRouter.")

        message = result["choices"][0]["message"]
        images = message.get("images")
        if not images:
            raise RuntimeError("No images field in response.")

        data_url = images[0]["image_url"]["url"]
        if not data_url.startswith("data:image"):
            raise RuntimeError("Unexpected image URL format (expected data URL).")

        return data_url
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error: {e}", file=sys.stderr)
        if e.response:
            print(f"   Response: {e.response.text}", file=sys.stderr)
        raise e


def save_data_url_to_file(data_url: str, filepath: str) -> None:
    """
    Save 'data:image/png;base64,...' URL to a binary file.
    """
    try:
        header, b64_data = data_url.split(",", 1)
        binary = base64.b64decode(b64_data)
        with open(filepath, "wb") as f:
            f.write(binary)
    except Exception as e:
        print(f"❌ Error saving image file: {e}", file=sys.stderr)
        raise e

# ================== Main execution ==================

def main():
    """
    Main function to load the slide JSON and generate all images.
    """
    input_json_path = str(Config.OUTPUT_SLIDES_JSON)
    if not os.path.exists(input_json_path):
        print(f"❌ Error: Input JSON not found: {input_json_path}", file=sys.stderr)
        print("   (Did transcript_condenser.py run successfully?)", file=sys.stderr)
        raise FileNotFoundError(f"{input_json_path} not found.")

    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    slides_data = data.get("slides", [])
    if not slides_data:
        print("⚠️ Warning: No slides found in JSON file.", file=sys.stderr)
        return

    total = len(slides_data)
    print(f"Loaded {total} slides from {input_json_path}.")
    
    filenames = []
    for idx, slide in enumerate(slides_data, start=1):
        print(f"\n=== Generating slide {idx}/{total}: {slide.get('title')} ===")
        
        try:
            prompt = slide_to_prompt(slide, idx, total)
            data_url = call_openrouter_image(prompt, aspect_ratio=ASPECT_RATIO)

            filename = os.path.join(OUTPUT_DIR, f"slide_{idx:02d}.png")
            save_data_url_to_file(data_url, filename)
            filenames.append(filename)

            print(f"Saved: {filename}")
            
        except Exception as e:
            print(f"❌ FAILED to generate slide {idx}: {e}", file=sys.stderr)


    print("\nDone. Generated files in {OUTPUT_DIR}:")
    for f in filenames:
        print(f"- {f}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error in slides.py: {e}", file=sys.stderr)
        sys.exit(1)