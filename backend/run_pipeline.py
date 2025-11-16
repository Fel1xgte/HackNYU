import os
import sys
from pathlib import Path

# Import your scripts (after we modify them)
import video_decoder
import transcript_condenser
import slides  # <-- 1. 就像这样导入
import audio_generator
import video_stitcher

from config import Config

def run_pipeline_task(status_file: Path):
    """
    This is the function that runs in the background.
    It executes your full pipeline, step-by-step,
    and updates the status file.
    """
    try:
        # 0. Initialize: Create all directories from config
        status_file.write_text("initializing")
        print("[PIPELINE] Initializing directories...")
        Config.create_directories()
        
        # 1. Decode Video -> JSON
        status_file.write_text("decoding_video")
        print("[PIPELINE] Step 1: Decoding video to JSON...")
        video_decoder.main()
        
        # 2. Condense JSON -> Slide JSON (Text ONLY)
        status_file.write_text("generating_slide_text")
        print("[PIPELINE] Step 2: Generating slide text (JSON)...")
        transcript_condenser.main()
        
        # 3. Generate Slide Images (PNGs) - NEW STEP
        status_file.write_text("generating_slide_images")
        print("[PIPELINE] Step 3: Generating slide images (PNGs)...")
        slides.main() # <-- 2. 在这里调用
        
        # 4. Generate Audio
        status_file.write_text("generating_audio")
        print("[PIPELINE] Step 4: Generating audio...")
        audio_generator.main()
        
        # 5. Stitch Video
        status_file.write_text("stitching_video")
        print("[PIPELINE] Step 5: Stitching final video...")
        video_stitcher.main()
        
        # 6. Complete
        status_file.write_text("complete")
        print("[PIPELINE] Task complete!")

    except Exception as e:
        # If any step fails, write the error to the status file
        error_message = f"pipeline_failed: {str(e)}"
        print(f"[PIPELINE] ERROR: {error_message}", file=sys.stderr)
        status_file.write_text(error_message)