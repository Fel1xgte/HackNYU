import json
import os
import sys
import re
from google import genai


API_KEY_ENV_VAR = "GEMINI_API_KEY"
MODEL_NAME = "gemini-2.5-flash"

INPUT_JSON_PATH = "sample_transcript.json"
OUTPUT_JSON_PATH = "slide_plan.json"


# ------------------------------------------------------
# Gemini Client Initialization
# ------------------------------------------------------

def create_gemini_client():
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

def generate_slide_plan(client, full_transcript, course_title):
    """
    The real NotebookLM-style summarizer:
    Takes a long transcript → outputs 3–7 slides with title/points/speaker_notes.
    """

    prompt = f"""
You are an expert AI Tutor slide generator.

A long lecture transcript is provided below. Summarize it into a clear, short teaching slide deck that fits into a 1–2 minute explanation video.

TRANSCRIPT:
----------------
{full_transcript}
----------------

Your tasks:
1. Break the content into 3–7 slides.
2. For each slide, produce:
   - "title": short & clear
   - "points": 2–4 bullet points summarizing the key ideas
   - "speaker_notes": one short paragraph explaining the concept

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
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        raw_text = response.text
        cleaned = clean_json_response(raw_text)
        return json.loads(cleaned)

    except Exception as e:
        print(f"❌ JSON parse error: {e}", file=sys.stderr)
        return {
            "course_title": course_title,
            "slides": [
                {
                    "title": "Error Occurred",
                    "points": ["Model failed"],
                    "speaker_notes": "Parsing error occurred."
                }
            ]
        }



# ------------------------------------------------------
# Step 1: Merge Transcript
# ------------------------------------------------------

def load_full_transcript():
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
    client = create_gemini_client()
    if not client:
        sys.exit(1)

    print("📘 Loading transcript...")
    full_transcript, course_title = load_full_transcript()

    print("✨ Generating slide plan...")
    slide_plan = generate_slide_plan(client, full_transcript, course_title)

    with open(OUTPUT_JSON_PATH, "w") as f:
        json.dump(slide_plan, f, indent=2, ensure_ascii=False)

    print(f"\n✅ DONE → slide plan saved to {OUTPUT_JSON_PATH}\n")



if __name__ == "__main__":
    main()
