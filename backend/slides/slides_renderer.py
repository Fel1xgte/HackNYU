from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import json

OUTPUT_DIR = "rendered_slides"

# Create folder if not exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def render_slide(slide, index):
    """
    Render a single slide into a PNG image.
    slide: dict containing title, points, etc.
    index: slide number (1-based)
    """
    width = 1920
    height = 1080

    # Create black background
    img = Image.new("RGB", (width, height), color="#111111")
    draw = ImageDraw.Draw(img)

    # Load fonts (system fonts)
    title_font = ImageFont.truetype("Arial Bold.ttf", 80)
    point_font = ImageFont.truetype("Arial.ttf", 48)

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
    """
    with open(slides_json_path, "r") as f:
        data = json.load(f)

    slides = data["slides"]

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
