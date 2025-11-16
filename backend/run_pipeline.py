import os
import sys
import hashlib
from pathlib import Path
from importlib import reload

# Import your scripts (after we modify them)
import video_decoder
import transcript_condenser
import slides  # <-- 1. 就像这样导入
import audio_generator
import video_stitcher

from config import Config

def get_video_hash(video_path: Path) -> str:
    """
    Calculate hash of video file to detect changes.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        str: SHA256 hash of the video file, or empty string if file doesn't exist
    """
    if not video_path.exists():
        return ""
    
    try:
        hash_sha256 = hashlib.sha256()
        with open(video_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"⚠️  Warning: Could not calculate video hash: {e}", file=sys.stderr)
        return ""

def cleanup_old_files():
    """
    Clean up old generated files to ensure fresh pipeline execution.
    Removes: slides JSON, audio files, video segments, final video.
    """
    print("[PIPELINE] 🧹 Cleaning up old generated files...")
    
    cleaned_count = 0
    
    # 1. Clean up slides JSON
    slides_json = Config.OUTPUT_SLIDES_JSON
    if slides_json.exists():
        try:
            slides_json.unlink()
            print(f"   ✅ Deleted: {slides_json}")
            cleaned_count += 1
        except Exception as e:
            print(f"   ⚠️  Warning: Could not delete {slides_json}: {e}", file=sys.stderr)
    
    # 2. Clean up audio files
    audio_dir = Config.GENERATED_AUDIO_DIR
    if audio_dir.exists():
        for audio_file in audio_dir.glob("*.mp3"):
            try:
                audio_file.unlink()
                print(f"   ✅ Deleted: {audio_file.name}")
                cleaned_count += 1
            except Exception as e:
                print(f"   ⚠️  Warning: Could not delete {audio_file}: {e}", file=sys.stderr)
    
    # 3. Clean up video segments
    segments_dir = Config.VIDEO_SEGMENTS_DIR
    if segments_dir.exists():
        for segment_file in segments_dir.glob("segment_*.mp4"):
            try:
                segment_file.unlink()
                print(f"   ✅ Deleted: {segment_file.name}")
                cleaned_count += 1
            except Exception as e:
                print(f"   ⚠️  Warning: Could not delete {segment_file}: {e}", file=sys.stderr)
        
        # Also delete concat list if it exists
        concat_list = segments_dir / "concat_list.txt"
        if concat_list.exists():
            try:
                concat_list.unlink()
                print(f"   ✅ Deleted: {concat_list.name}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not delete {concat_list}: {e}", file=sys.stderr)
    
    # 4. Clean up final video
    final_video = Config.FINAL_OUTPUT_DIR / Config.FINAL_VIDEO_NAME
    if final_video.exists():
        try:
            final_video.unlink()
            print(f"   ✅ Deleted: {final_video.name}")
            cleaned_count += 1
        except Exception as e:
            print(f"   ⚠️  Warning: Could not delete {final_video}: {e}", file=sys.stderr)
    
    if cleaned_count > 0:
        print(f"[PIPELINE] ✅ Cleanup complete: {cleaned_count} file(s) removed")
    else:
        print("[PIPELINE] ℹ️  No old files to clean up")

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
        
        # 0.5. Detect new video upload and cleanup old files
        input_video_path = Config.WORKSPACE_DIR / "input_video.mp4"
        video_hash_file = Config.WORKSPACE_DIR / ".video_hash"
        
        current_hash = get_video_hash(input_video_path)
        previous_hash = ""
        
        if video_hash_file.exists():
            previous_hash = video_hash_file.read_text().strip()
        
        # If video hash changed or doesn't exist, it's a new upload - cleanup
        if current_hash and current_hash != previous_hash:
            print("[PIPELINE] 🔍 New video detected - cleaning up old files...")
            cleanup_old_files()
            # Save new hash
            if current_hash:
                video_hash_file.write_text(current_hash)
        elif not current_hash:
            print("[PIPELINE] ⚠️  Warning: Input video not found, skipping cleanup")
        
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
        reload(audio_generator)  # Force reload to get latest changes
        try:
            audio_paths = audio_generator.main()
            if not audio_paths:
                raise Exception("No audio files were generated. Check ElevenLabs API quota.")
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "quota_exceeded" in error_msg.lower():
                status_file.write_text(f"pipeline_failed: ElevenLabs API quota exceeded. Please check your account and add credits.")
            raise
        
        # 5. Stitch Video
        status_file.write_text("stitching_video")
        print("[PIPELINE] Step 5: Stitching final video...")
        
        reload(video_stitcher)  # Force reload to get latest changes
        final_video = video_stitcher.main()
        
        # Verify video was created
        final_video_path = Config.FINAL_OUTPUT_DIR / Config.FINAL_VIDEO_NAME
        if not final_video_path.exists():
            raise Exception(f"Video file was not created: {final_video_path}")
        
        # 6. Complete
        status_file.write_text("complete")
        print("[PIPELINE] Task complete!")

    except Exception as e:
        # If any step fails, write the error to the status file
        error_message = f"pipeline_failed: {str(e)}"
        print(f"[PIPELINE] ERROR: {error_message}", file=sys.stderr)
        status_file.write_text(error_message)