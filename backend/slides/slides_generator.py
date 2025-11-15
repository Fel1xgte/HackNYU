import json
import os
import sys
import re
from google import genai



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
    """

    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        print(f"❌ ERROR: {API_KEY_ENV_VAR} is not set.", file=sys.stderr)
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
    """
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

    audio_segments = data.get("audio_segments", [])
    keyframes = data.get("visual_keyframes", [])

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
    client = create_gemini_client()
    if not client:
        sys.exit(1)

    data = json.load(open(INPUT_JSON_PATH, "r"))

    result = process_transcript_to_slides(client, data)

    with open(OUTPUT_JSON_PATH, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ DONE → slides saved to {OUTPUT_JSON_PATH}\n")


if __name__ == "__main__":
    main()
