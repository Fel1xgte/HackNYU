import json
import os
import sys
import re
# import base64  <- No longer needed
from openai import OpenAI
from config import Config
from env_loader import get_api_key

# ================================
# CONFIG
# ================================
API_KEY_ENV_VAR = "OPENROUTER_API_KEY"

# TEXT MODEL (slide JSON generation)
TEXT_MODEL = "nvidia/nemotron-4-340b-instruct"

# IMAGE MODEL (PNG slide generation)
# --- REMOVED ---
# IMAGE_MODEL = "black-forest-labs/flux-dev"
# The 'slides.py' script now handles image generation.

# ================================
# GLOBAL SLIDESHOW SUPER PROMPT (your design spec)
# ================================
GLOBAL_DESIGN_PROMPT = r"""
[ YOUR FULL JSON DESIGN SPEC HERE ]
(This is still used by the TEXT_MODEL to generate the JSON)
"""


# ================================
# INIT OPENROUTER CLIENT
# ================================
def create_client():
    api_key = get_api_key(API_KEY_ENV_VAR, required=True)
    if not api_key:
        print(f"❌ ERROR: Missing environment variable: {API_KEY_ENV_VAR}")
        return None

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


# ================================
# CLEAN JSON RESPONSE
# ================================
def clean_json_response(raw):
    m = re.search(r'```json\s*([\s\S]*?)```', raw)
    if m:
        return m.group(1)

    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        return m.group(0)

    return raw.strip()


# ================================
# 1. TEXT GENERATION (JSON SLIDE)
# ================================
def generate_slide_json(client, ocr_text, speech_text, caption):
    prompt = f"""
You are a world-class instructional designer and slide architect.

Follow this global slide design specification:
{GLOBAL_DESIGN_PROMPT}

Now generate ONE slide in JSON based on:

OCR:
{ocr_text}

Speech:
{speech_text}

Caption:
{caption}

Return ONLY JSON:
{{
  "title": "...",
  "key_message": "...",
  "points": ["...", "..."],
  "speaker_notes": "..."
}}
"""

    try:
        res = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "You generate clean slide JSON following the global design prompt."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = res.choices[0].message.content
        cleaned = clean_json_response(content)
        return json.loads(cleaned)

    except Exception as e:
        print("❌ JSON generation error:", e)
        return {
            "title": "Error",
            "key_message": "",
            "points": [],
            "speaker_notes": str(e)
        }


# ================================
# 2. IMAGE GENERATION (PNG SLIDE)
# ================================
# --- REMOVED ---
# The 'generate_slide_png' function was removed.
# 'slides.py' is now responsible for this.


# ================================
# MAIN PIPELINE
# ================================
def process_transcript(client, data):
    audio_segments = data.get("audio_segments", [])
    frames = data.get("visual_keyframes", [])

    slides = [f for f in frames if f.get("kind") == "slide"]
    slides.sort(key=lambda x: x["time_sec"])

    result_json = []

    for i, kf in enumerate(slides):
        start = kf["time_sec"]
        end = slides[i+1]["time_sec"] if i + 1 < len(slides) else float("inf")

        speech_text = " ".join(
            seg["text"]
            for seg in audio_segments
            if start <= seg["start_sec"] < end
        )

        ocr = kf.get("ocr_text", "")
        caption = kf.get("caption", "")

        print(f"\n➡️ Slide {i+1}: generating JSON…")
        slide_json = generate_slide_json(client, ocr, speech_text, caption)
        slide_json["slide_number"] = i + 1
        result_json.append(slide_json)

        # --- REMOVED ---
        # The call to generate_slide_png(...) was removed.
        # print(f"➡️ Slide {i+1}: generating PNG…")
        # generate_slide_png(client, slide_json, i + 1)

    return {"slides": result_json}


# ================================
# ENTRY POINT
# ================================
def main():
    client = create_client()
    if not client:
        print("❌ Failed to create OpenRouter client. Check API key.", file=sys.stderr)
        raise EnvironmentError("Failed to create OpenRouter client.")

    if not os.path.exists(Config.INPUT_JSON_PATH):
        print(f"❌ Error: Input file not found: {Config.INPUT_JSON_PATH}", file=sys.stderr)
        print("   (Did video_decoder.py fail to run?)", file=sys.stderr)
        raise FileNotFoundError(f"{Config.INPUT_JSON_PATH} not found.")

    with open(Config.INPUT_JSON_PATH) as f:
        data = json.load(f)

    output = process_transcript(client, data)

    with open(Config.OUTPUT_SLIDES_JSON, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ JSON saved → {Config.OUTPUT_SLIDES_JSON}")
    # --- REMOVED ---
    # print(f"🖼️ PNG slides saved → {OUTPUT_IMG_DIR}/")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error in transcript_condenser: {e}", file=sys.stderr)
        sys.exit(1)