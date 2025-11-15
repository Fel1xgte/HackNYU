import os
import json
from PIL import Image, ImageDraw, ImageFont
import textwrap

OUTPUT_DIR = "rendered_slides_minimalist_clean"
os.makedirs(OUTPUT_DIR, exist_ok=True)

WIDTH = 1920
HEIGHT = 1080

TITLE_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf" 
BODY_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"   

COLOR_BACKGROUND = (255, 255, 255)  
COLOR_PRIMARY = (30, 30, 30)        
COLOR_SECONDARY = (90, 90, 90)      
COLOR_ACCENT = (0, 47, 167)         


def get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# Cover Slide
def draw_cover_slide(title, subtitle, index):
    bg = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BACKGROUND)
    draw = ImageDraw.Draw(bg)

    title_font = ImageFont.truetype(TITLE_FONT_PATH, 180)
    subtitle_font = ImageFont.truetype(BODY_FONT_PATH, 70)

    # Automatically wrap title to prevent horizontal overflow
    wrapped_title = textwrap.fill(title, width=15)
    
    w_block, h_block = get_text_size(draw, wrapped_title, title_font)
    
    # Calculate starting Y to center the block
    start_y = HEIGHT / 2 - h_block / 2 - 100 

    draw.text(((WIDTH - w_block) / 2, start_y),
              wrapped_title, fill=COLOR_PRIMARY, font=title_font, align="center")

    if subtitle:
        subtitle_y = start_y + h_block + 50
        
        w2, h2 = get_text_size(draw, subtitle, subtitle_font)
        draw.text(((WIDTH - w2) / 2, subtitle_y),
                  subtitle, fill=COLOR_SECONDARY, font=subtitle_font)

    # Minimal accent line at the bottom
    draw.line((WIDTH/2 - 200, HEIGHT - 100, WIDTH/2 + 200, HEIGHT - 100), fill=COLOR_ACCENT, width=5)

    out = f"{OUTPUT_DIR}/slide_{index:02d}.png"
    bg.save(out)
    return out


# Content Slide
def draw_content_slide(title, points, index):
    bg = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BACKGROUND)
    draw = ImageDraw.Draw(bg)

    title_font = ImageFont.truetype(TITLE_FONT_PATH, 70) # ENHANCEMENT: Smaller title to prevent overflow
    bullet_font = ImageFont.truetype(BODY_FONT_PATH, 65) 

    draw.text((120, 100), title, fill=COLOR_PRIMARY, font=title_font)

    # Accent line slightly shorter
    draw.line((120, 200, WIDTH - 120, 200), fill=COLOR_ACCENT, width=5)

    y = 280
    LEFT_MARGIN = 150 
    BULLET_OFFSET = 50

    for p in points:
        wrapped = textwrap.fill(p, width=45) 
        
        # Accent color bullet
        draw.text((LEFT_MARGIN, y), "•", fill=COLOR_ACCENT, font=bullet_font)
        
        # Primary color text
        draw.text((LEFT_MARGIN + BULLET_OFFSET, y), wrapped, fill=COLOR_PRIMARY, font=bullet_font)
        
        line_height = get_text_size(draw, "M", bullet_font)[1]
        # ENHANCEMENT: Increased vertical space for breathability
        y += line_height * (wrapped.count('\n') + 2.2) 
        
        if y > HEIGHT - 100:
            break

    out = f"{OUTPUT_DIR}/slide_{index:02d}.png"
    bg.save(out)
    return out


# Message Slide
def draw_message_slide(msg, index):
    bg = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BACKGROUND)
    draw = ImageDraw.Draw(bg)

    msg_font = ImageFont.truetype(TITLE_FONT_PATH, 120) 
    
    wrapped = textwrap.fill(msg, width=15)
    
    w, h = get_text_size(draw, wrapped, msg_font)
    
    draw.text(((WIDTH - w)/2, (HEIGHT - h)/2),
              wrapped, fill=COLOR_PRIMARY, font=msg_font, align="center")
    
    # Simple brackets using accent color
    draw.text((WIDTH/2 - w/2 - 100, HEIGHT/2 - h/2 - 20), "“", fill=COLOR_ACCENT, font=msg_font)
    draw.text((WIDTH/2 + w/2 + 50, HEIGHT/2 + h/2 - 100), "”", fill=COLOR_ACCENT, font=msg_font)

    out = f"{OUTPUT_DIR}/slide_{index:02d}.png"
    bg.save(out)
    return out


def choose_template(slide, index):
    title = slide.get("title", "Untitled Section")
    points = slide.get("points", []) 

    if index == 1:
        subtitle = points[0] if points else ""
        return draw_cover_slide(title, subtitle, index)

    if len(points) == 1:
        return draw_message_slide(points[0], index)

    return draw_content_slide(title, points, index)


def render_slides(slides_json="slide_plan.json"):
    print("\nLoading slide_plan.json...")
    try:
        with open(slides_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File '{slides_json}' not found. Please ensure the file exists.")
        return
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from '{slides_json}'. Please check the format.")
        return
    
    slides = data.get("slides", [])

    print(f"Generating {len(slides)} modern minimalist slides into '{OUTPUT_DIR}' folder...\n")

    for i, slide in enumerate(slides, 1):
        print(f" -> Slide {i}: {slide.get('title', 'No Title')}")
        choose_template(slide, i)

    print(f"\nDONE! All slides saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    render_slides()