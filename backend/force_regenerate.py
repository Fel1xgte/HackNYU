#!/usr/bin/env python3
"""
Script to force regeneration of video with all 6 segments totaling 90 seconds.
This deletes old video files and segments to ensure fresh generation.
"""

import os
import shutil
from pathlib import Path
from config import Config

def cleanup_old_files():
    """Delete old video files and segments to force regeneration"""
    print("🧹 Cleaning up old video files...")
    
    # Delete final video
    final_video = Config.FINAL_OUTPUT_DIR / Config.FINAL_VIDEO_NAME
    if final_video.exists():
        print(f"   Deleting: {final_video}")
        os.remove(final_video)
    
    # Delete all video segments
    segments_dir = Config.VIDEO_SEGMENTS_DIR
    if segments_dir.exists():
        for segment_file in segments_dir.glob("segment_*.mp4"):
            print(f"   Deleting: {segment_file}")
            os.remove(segment_file)
        
        # Also delete concat list if it exists
        concat_list = segments_dir / "concat_list.txt"
        if concat_list.exists():
            os.remove(concat_list)
    
    print("✅ Cleanup complete!")
    print("\n📝 Next steps:")
    print("   1. Delete generated_slides.json to regenerate with new prompt")
    print("   2. Delete generated_audio/*.mp3 to regenerate audio with speed adjustment")
    print("   3. Run the pipeline again")
    print("\n   Or run: python3 force_regenerate.py --full")

def full_cleanup():
    """Delete slides and audio too for complete regeneration"""
    print("🧹 Full cleanup - deleting slides, audio, and video files...")
    
    # Delete slides JSON
    slides_json = Config.OUTPUT_SLIDES_JSON
    if slides_json.exists():
        print(f"   Deleting: {slides_json}")
        os.remove(slides_json)
    
    # Delete audio files
    audio_dir = Config.GENERATED_AUDIO_DIR
    if audio_dir.exists():
        for audio_file in audio_dir.glob("*.mp3"):
            print(f"   Deleting: {audio_file}")
            os.remove(audio_file)
    
    # Delete rendered slides (optional - comment out if you want to keep them)
    # slides_dir = Config.RENDERED_SLIDES_DIR
    # if slides_dir.exists():
    #     for slide_file in slides_dir.glob("slide_*.png"):
    #         print(f"   Deleting: {slide_file}")
    #         os.remove(slide_file)
    
    # Delete video files
    cleanup_old_files()
    
    print("\n✅ Full cleanup complete!")
    print("   Now run the pipeline to regenerate everything with:")
    print("   - New concise speaker notes (15s per slide)")
    print("   - Faster audio (1.15x speed)")
    print("   - All 6 segments totaling 90 seconds")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        full_cleanup()
    else:
        cleanup_old_files()


