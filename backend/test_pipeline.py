#!/usr/bin/env python3
"""
Quick test to verify the pipeline can generate slides from existing decoded_video.json
"""

import json

# Load the decoded video
with open('workspace/decoded_video.json', 'r') as f:
    data = json.load(f)

frames = data.get("visual_keyframes", [])
audio_segments = data.get("audio_segments", [])

print(f"📊 Pipeline Test Results:")
print(f"   Total frames: {len(frames)}")
print(f"   Total audio segments: {len(audio_segments)}")

# Check frames with substantial OCR
frames_with_text = [f for f in frames if len(f.get("ocr_text", "").strip()) > 20]
print(f"   Frames with OCR text (>20 chars): {len(frames_with_text)}")

# Simulate what transcript_condenser does NOW (after fix)
slides = frames  # Using all frames
slides.sort(key=lambda x: x["time_sec"])

print(f"   Slides to be processed: {len(slides)}")

if slides:
    print(f"\n✅ Pipeline should work! It will generate {len(slides)} slides")
    print(f"\nFirst 3 slides will have:")
    for i, slide in enumerate(slides[:3], 1):
        print(f"\n   Slide {i}:")
        print(f"      Time: {slide['time_sec']}s")
        print(f"      OCR: {slide['ocr_text'][:80]}...")
else:
    print(f"\n❌ No slides to process!")
