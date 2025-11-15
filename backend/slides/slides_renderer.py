"""
Slide Renderer for Confucius Lecture Summarizer

This module renders slide content from JSON into PNG images.
It creates professional-looking slides with titles and bullet points.

Functions:
    render_slide: Render a single slide to PNG
    render_slides_from_json: Render all slides from JSON file

Usage:
    from slides_renderer import render_slides_from_json
    slide_paths = render_slides_from_json("generated_slides.json")
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import sys
import json

OUTPUT_DIR = "rendered_slides"

# Create folder if not exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def render_slide(slide, index):
    """
    Render a single slide into a PNG image.
    
    Args:
        slide (dict): Dictionary containing 'title' and 'points' keys
        index (int): Slide number (1-based) for filename generation
    
    Returns:
        str: Path to the saved PNG file
    
    Raises:
        Exception: If image rendering or saving fails
    """
    width = 1920
    height = 1080

    # Create black background
    img = Image.new("RGB", (width, height), color="#111111")
    draw = ImageDraw.Draw(img)

    # Load fonts with fallback mechanism for cross-platform compatibility
    try:
        # Try to load Arial Bold (works on macOS and Windows)
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 80)
    except (OSError, IOError):
        try:
            # Fallback to Helvetica on macOS
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
        except (OSError, IOError):
            # Final fallback to default font
            print("⚠️  Warning: Using default font for title", file=sys.stderr)
            title_font = ImageFont.load_default()
    
    try:
        # Try to load Arial (works on macOS and Windows)
        point_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 48)
    except (OSError, IOError):
        try:
            # Fallback to Helvetica on macOS
            point_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except (OSError, IOError):
            # Final fallback to default font
            print("⚠️  Warning: Using default font for points", file=sys.stderr)
            point_font = ImageFont.load_default()

    # Title
    draw.text((100, 100), slide["title"], font=title_font, fill="white")

    # Draw bullet points
    y = 250
    for p in slide["points"]:
        wrapped = textwrap.fill(p, width=40)
        draw.text((150, y), "• " + wrapped, font=point_font, fill="#DDDDDD")
        y += 120

    # Save image
    output_path = f"{OUTPUT_DIR}/slide_{index:02d}.png"
    img.save(output_path)

    return output_path


def render_slides_from_json(slides_json_path):
    """
    Load slide JSON file and create PNG slides for all entries.
    
    Args:
        slides_json_path (str): Path to JSON file containing slide data
    
    Returns:
        list: List of paths to generated PNG files
    
    Raises:
        FileNotFoundError: If slides JSON file doesn't exist
        json.JSONDecodeError: If JSON file is invalid
        KeyError: If required 'slides' key is missing
    """
    try:
        with open(slides_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Slides JSON file not found: {slides_json_path}", file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file {slides_json_path}: {e}", file=sys.stderr)
        raise

    if "slides" not in data:
        print(f"❌ Error: 'slides' key not found in JSON file", file=sys.stderr)
        raise KeyError("'slides' key missing from JSON data")
    
    slides = data["slides"]
    
    if not slides:
        print("⚠️  Warning: No slides found in JSON file", file=sys.stderr)
        return []

    print(f"Rendering {len(slides)} slides...")

    output_paths = []
    for i, slide in enumerate(slides, start=1):
        path = render_slide(slide, i)
        print(f" → Slide {i} saved to {path}")
        output_paths.append(path)

    print("\n✨ ALL SLIDES RENDERED!")
    return output_paths


if __name__ == "__main__":
    render_slides_from_json("generated_slides.json")
