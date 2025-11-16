import json
import os
import sys
import re
from pathlib import Path
import time
import google.generativeai as genai


API_KEY_ENV_VAR = "GEMINI_API_KEY"
MODEL_NAME = "gemini-2.5-flash"
API_TIMEOUT_SECONDS = 90  # Maximum wait time for Gemini API

INPUT_JSON_PATH = "./workspace/decoded_video.json"
OUTPUT_JSON_PATH = "./workspace/generated_slides.json"


def write_status(status: str):
    """Write status to status.txt for frontend polling"""
    status_file = Path("workspace/status.txt")
    status_file.write_text(status)
    print(f"📊 Status: {status}")


# ------------------------------------------------------
# Gemini Client Initialization
# ------------------------------------------------------

def create_gemini_client():
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        print(f"❌ ERROR: {API_KEY_ENV_VAR} is not set.", file=sys.stderr)
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL_NAME)
        print(f"✨ Gemini model initialized: {MODEL_NAME}")
        return model
    except Exception as e:
        print(f"❌ Failed to initialize Gemini model: {e}", file=sys.stderr)
        return None



# ------------------------------------------------------
# JSON Cleaner
# ------------------------------------------------------

def clean_json_response(raw):
    """
    Removes ```json ... ``` or extracts the first {...} block.
    """
    m = re.search(r'```json\s*([\s\S]*?)```', raw)
    if m:
        return m.group(1).strip()

    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        return m.group(0).strip()

    return raw.strip()



# ------------------------------------------------------
# LLM: Generate Slide Plan From Full Transcript
# ------------------------------------------------------

def generate_slide_plan(model, full_transcript, course_title):
    """
    The real NotebookLM-style summarizer:
    Takes a long transcript → outputs 6 slides with title/points/speaker_notes.
    """
    
    # Validate inputs
    if not full_transcript or full_transcript.strip() == "":
        raise ValueError("Empty transcript provided to generate_slide_plan")
    
    if len(full_transcript.strip()) < 100:
        print(f"⚠️  WARNING: Very short transcript ({len(full_transcript)} chars). Results may be poor.", file=sys.stderr)

    # Calculate target duration per slide (90 seconds total / 6 slides = 15 seconds per slide)
    TARGET_DURATION_PER_SLIDE = 15  # seconds
    NUM_SLIDES = 6

    prompt = f"""
You are an expert AI Tutor slide generator.

A long lecture transcript is provided below. Summarize it into a clear, concise teaching slide deck that fits into exactly 90 seconds of video narration.

TRANSCRIPT:
----------------
{full_transcript}
----------------

CRITICAL DURATION REQUIREMENT:
- The final video must be exactly 90 seconds total
- You must create exactly {NUM_SLIDES} slides
- Each slide's speaker_notes should result in approximately {TARGET_DURATION_PER_SLIDE} seconds of speech when spoken at a natural, fast-paced pace
- Write concise, direct speaker notes - prioritize key information only
- Be brief and engaging - aim for 2-3 sentences maximum per slide's speaker_notes
- The tone should be quick and fast-paced while remaining clear and educational

Your tasks:
1. Break the content into exactly {NUM_SLIDES} slides.
2. For each slide, produce:
   - "title": short & clear (3-6 words)
   - "points": 2–4 bullet points summarizing the key ideas (keep concise)
   - "speaker_notes": a brief, fast-paced paragraph (2-3 sentences max) that will take approximately {TARGET_DURATION_PER_SLIDE} seconds to speak

Return ONLY valid JSON:

{{
  "course_title": "{course_title}",
  "slides": [
    {{
      "title": "...",
      "points": ["...", "..."],
      "speaker_notes": "..."
    }}
  ]
}}
"""

    try:
        write_status("generating_slide_text:calling_ai_model")
        print("✨ Generating slide plan... (this may take 30-60 sec)")
        
        start_time = time.time()
        response = model.generate_content(prompt)
        elapsed = time.time() - start_time
        print(f"⏱️  API call completed in {elapsed:.1f} seconds")
        
        raw = response.text
        clean = clean_json_response(raw)
        data = json.loads(clean)
        
        # CRITICAL: Validate the LLM output structure
        if "slides" not in data:
            raise ValueError("LLM response missing 'slides' key")
        
        if not isinstance(data["slides"], list):
            raise ValueError("LLM 'slides' is not a list")
        
        if len(data["slides"]) == 0:
            raise ValueError("LLM generated 0 slides")
        
        # Validate each slide has required fields
        for i, slide in enumerate(data["slides"]):
            required_fields = ["title", "points", "speaker_notes"]
            for field in required_fields:
                if field not in slide:
                    raise ValueError(f"Slide {i+1} missing required field: {field}")
                if not slide[field]:
                    print(f"⚠️  WARNING: Slide {i+1} has empty {field}", file=sys.stderr)
        
        print(f"✅ Generated {len(data['slides'])} slides successfully")
        return data

    except Exception as e:
        error_msg = f"JSON parse error: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        write_status(f"error:slide_generation_failed:{str(e)[:100]}")
        return {
            "course_title": course_title,
            "slides": [
                {
                    "title": "Error Occurred",
                    "points": ["Model failed"],
                    "speaker_notes": f"Parsing error occurred: {str(e)}"
                }
            ]
        }



# ------------------------------------------------------
# Step 1: Merge Transcript
# ------------------------------------------------------

def load_full_transcript():
    write_status("generating_slide_text:loading_transcript")
    data = json.load(open(INPUT_JSON_PATH, "r"))
    audio_segments = data.get("audio_segments", [])

    # merge into one mega transcript string
    full_text = " ".join(seg["text"] for seg in audio_segments)

    # fallback title
    title = data.get("video", {}).get("metadata", {}).get("topic", "Lecture Summary")

    return full_text, title



# ------------------------------------------------------
# Main
# ------------------------------------------------------

def main():
    model = create_gemini_client()
    if not model:
        sys.exit(1)

    print("📘 Loading transcript...")
    full_transcript, course_title = load_full_transcript()

    write_status("generating_slide_text:calling_ai_model")
    print("✨ Generating slide plan... (this may take 30-60 sec)")
    generated_slides = generate_slide_plan(model, full_transcript, course_title)

    write_status("generating_slide_text:saving_slides")
    with open(OUTPUT_JSON_PATH, "w") as f:
        json.dump(generated_slides, f, indent=2, ensure_ascii=False)

    print(f"\n✅ DONE → slide plan saved to {OUTPUT_JSON_PATH}\n")


if __name__ == "__main__":
    main()