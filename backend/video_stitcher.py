"""
Video Stitcher for Confucius Lecture Summarizer

This module stitches PNG slide images and MP3 audio files into MP4 videos using FFmpeg.
It creates individual video segments and concatenates them into a final video.

Key Features:
    - FFmpeg-based video generation
    - Static slides with synchronized audio
    - Fast rendering (~5-10 seconds total)
    - H.264 encoding for universal compatibility
    - Web-optimized output with faststart flag

Functions:
    check_ffmpeg: Verify FFmpeg installation
    create_video_segment: Create a single video segment from image + audio
    concatenate_video_segments: Merge all segments into final video
    stitch_slides_to_video: Complete pipeline for video generation
    get_file_paths_from_directories: Helper to auto-discover files

Usage:
    from video_stitcher import stitch_slides_to_video
    video_path = stitch_slides_to_video(slide_paths, audio_paths, "output.mp4")
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from config import Config

# Directories are now controlled by Config
# VIDEO_SEGMENTS_DIR = "video_segments"
# FINAL_OUTPUT_DIR = "final_output"
# TARGET_VIDEO_DURATION = 90

# Directories are created by config.py on import
# os.makedirs(VIDEO_SEGMENTS_DIR, exist_ok=True)
# os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)


def get_audio_duration(audio_path):
    """
    Get the duration of an audio file in seconds.
    
    Args:
        audio_path (str): Path to the audio file
    
    Returns:
        float: Duration in seconds, or 0 if failed
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️  Warning: Could not get duration for {audio_path}: {e}", file=sys.stderr)
        return 0


def check_ffmpeg():
    """
    Check if FFmpeg is installed and available.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("✅ FFmpeg is installed and ready")
        return True
    except FileNotFoundError:
        print("❌ ERROR: FFmpeg is not installed!", file=sys.stderr)
        print("   Install with: brew install ffmpeg (macOS)", file=sys.stderr)
        return False
    except subprocess.CalledProcessError:
        print("❌ ERROR: FFmpeg check failed", file=sys.stderr)
        return False


def create_video_segment(slide_image_path, audio_path, segment_index, duration=None, output_dir=None):
    """
    Create a video segment from a slide image and audio file.
    
    Args:
        slide_image_path (str): Path to the slide PNG image
        audio_path (str): Path to the audio MP3 file
        segment_index (int): Index of the segment (1-based)
        duration (float): Optional duration in seconds (overrides audio duration)
        output_dir (str): Directory to save the segment (defaults to Config)
    
    Returns:
        str: Path to the generated video segment, or None if failed
    """
    if output_dir is None:
        output_dir = str(Config.VIDEO_SEGMENTS_DIR)

    try:
        output_filename = f"segment_{segment_index:02d}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"🎬 Creating video segment {segment_index}...")
        print(f"   Slide: {slide_image_path}")
        print(f"   Audio: {audio_path}")
        if duration:
            print(f"   Duration: {duration:.2f} seconds")
        
        # FFmpeg command
        command = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-loop", "1",  # Loop the image
            "-i", slide_image_path,  # Input image
            "-i", audio_path,  # Input audio
            "-c:v", "libx264",  # Video codec
            "-tune", "stillimage",  # Optimize for still images
            "-c:a", "aac",  # Audio codec
            "-b:a", "192k",  # Audio bitrate
            "-pix_fmt", "yuv420p",  # Pixel format
        ]
        
        # Add duration and audio speed adjustment if specified
        if duration:
            audio_dur = get_audio_duration(audio_path)
            if audio_dur > 0 and audio_dur != duration:
                speed = audio_dur / duration
                # atempo only accepts 0.5-2.0, so chain multiple if needed
                if 0.5 <= speed <= 2.0:
                    command.extend(["-af", f"atempo={speed}"])
                elif speed < 0.5:
                    command.extend(["-af", "atempo=0.5,atempo=" + str(speed/0.5)])
                else:  # speed > 2.0
                    command.extend(["-af", "atempo=2.0,atempo=" + str(speed/2.0)])
            command.extend(["-t", str(duration)])
        else:
            command.append("-shortest")  # Duration matches shortest input (audio)
        
        command.extend([
            "-movflags", "+faststart",  # Enable fast start for web playback
            output_path
        ])
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        print(f"   ✅ Segment created: {output_path}")
        return output_path
    
    except subprocess.CalledProcessError as e:
        print(f"   ❌ FFmpeg error for segment {segment_index}:", file=sys.stderr)
        print(f"   {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"   ❌ Error creating segment {segment_index}: {e}", file=sys.stderr)
        return None


def concatenate_video_segments(segment_paths, output_filename="final_video.mp4"):
    """
    Concatenate all video segments into a single final video.
    
    Args:
        segment_paths (list): List of paths to video segments
        output_filename (str): Name of the final output video file
    
    Returns:
        str: Path to the final video, or None if failed
    """
    try:
        if not segment_paths:
            print("❌ No video segments to concatenate", file=sys.stderr)
            return None
        
        print(f"\n🎞️  Concatenating {len(segment_paths)} video segments...")
        
        # Create concat list file for FFmpeg
        concat_list_path = os.path.join(Config.VIDEO_SEGMENTS_DIR, "concat_list.txt")
        
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for segment_path in segment_paths:
                # Use absolute paths for FFmpeg concat
                abs_path = os.path.abspath(segment_path)
                # Escape single quotes in paths for FFmpeg
                abs_path = abs_path.replace("'", "'\\''")
                f.write(f"file '{abs_path}'\n")
        
        print(f"   Created concat list: {concat_list_path}")
        
        output_path = os.path.join(Config.FINAL_OUTPUT_DIR, output_filename)
        
        # FFmpeg concat command
        command = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "concat",  # Concat demuxer
            "-safe", "0",  # Allow absolute paths
            "-i", concat_list_path,  # Input concat list
            "-c:v", "copy",  # Copy video stream (no re-encoding)
            "-c:a", "aac",  # Re-encode audio for compatibility
            "-b:a", "192k",  # Audio bitrate
            "-movflags", "+faststart",  # Enable fast start
            output_path
        ]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        print(f"   ✅ Final video created: {output_path}")
        
        # Get video info
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"   📊 File size: {file_size:.2f} MB")
        
        return output_path
    
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg concatenation error:", file=sys.stderr)
        print(f"   {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Error concatenating videos: {e}", file=sys.stderr)
        return None


def stitch_slides_to_video(slide_image_paths, audio_paths, output_filename="final_video.mp4"):
    """
    Complete pipeline: Create video segments and concatenate them.
    
    Args:
        slide_image_paths (list): List of paths to slide PNG images
        audio_paths (list): List of paths to audio MP3 files
        output_filename (str): Name of the final output video
    
    Returns:
        str: Path to the final video, or None if failed
    """
    try:
        if len(slide_image_paths) != len(audio_paths):
            print(f"❌ Mismatch: {len(slide_image_paths)} slides but {len(audio_paths)} audio files", file=sys.stderr)
            return None
        
        if not slide_image_paths:
            print("❌ No slides to process", file=sys.stderr)
            return None
        
        print(f"\n🎬 Starting video stitching pipeline...")
        print(f"   Slides: {len(slide_image_paths)}")
        print(f"   Audio files: {len(audio_paths)}")
        print(f"   Target duration: {Config.TARGET_VIDEO_DURATION} seconds")
        print()
        
        # Check FFmpeg
        if not check_ffmpeg():
            return None
        
        # Calculate total audio duration and segment durations
        audio_durations = []
        for audio_path in audio_paths:
            if os.path.exists(audio_path):
                duration = get_audio_duration(audio_path)
                audio_durations.append(duration)
            else:
                audio_durations.append(0)
        
        total_audio_duration = sum(audio_durations)
        
        # Calculate proportional durations to fit TARGET_VIDEO_DURATION
        if total_audio_duration > 0:
            ratio = Config.TARGET_VIDEO_DURATION / total_audio_duration
            segment_durations = [(d * ratio) for d in audio_durations]
            print(f"📊 Original audio duration: {total_audio_duration:.2f}s → Compressed to: {Config.TARGET_VIDEO_DURATION}s")
            print(f"   Compression ratio: {ratio:.2f}x\n")
        else:
            # Fallback: equal distribution
            segment_durations = [Config.TARGET_VIDEO_DURATION / len(audio_paths)] * len(audio_paths)
            print(f"⚠️  Could not detect audio durations, using equal distribution\n")
        
        # Create video segments
        segment_paths = []
        
        for i, (slide_path, audio_path, duration) in enumerate(zip(slide_image_paths, audio_paths, segment_durations), start=1):
            # Verify files exist
            if not os.path.exists(slide_path):
                print(f"⚠️  Warning: Slide image not found: {slide_path}", file=sys.stderr)
                continue
            
            if not os.path.exists(audio_path):
                print(f"⚠️  Warning: Audio file not found: {audio_path}", file=sys.stderr)
                continue
            
            segment_path = create_video_segment(slide_path, audio_path, i, duration=duration)
            
            if segment_path:
                segment_paths.append(segment_path)
            else:
                print(f"⚠️  Warning: Failed to create segment {i}, skipping...", file=sys.stderr)
        
        if not segment_paths:
            print("❌ No video segments were created successfully", file=sys.stderr)
            return None
        
        # Concatenate segments
        final_video_path = concatenate_video_segments(segment_paths, output_filename)
        
        if final_video_path:
            print(f"\n✨ SUCCESS! Final video ready: {final_video_path}")
            return final_video_path
        else:
            print("\n❌ Failed to create final video", file=sys.stderr)
            return None
    
    except Exception as e:
        print(f"❌ Unexpected error in video stitching: {e}", file=sys.stderr)
        return None


def get_file_paths_from_directories():
    """
    Helper function to automatically find slide and audio files from directories.
    
    Returns:
        tuple: (slide_paths, audio_paths) - Lists of sorted file paths
    
    Raises:
        FileNotFoundError: If directories don't exist
    """
    slide_dir = str(Config.RENDERED_SLIDES_DIR)
    audio_dir = str(Config.GENERATED_AUDIO_DIR)
    
    # Check if directories exist
    if not os.path.exists(slide_dir):
        print(f"⚠️  Warning: Directory '{slide_dir}' not found", file=sys.stderr)
        return [], []
    
    if not os.path.exists(audio_dir):
        print(f"⚠️  Warning: Directory '{audio_dir}' not found", file=sys.stderr)
        return [], []
    
    try:
        # Get sorted slide paths (e.g., slide_01.png, slide_02.png)
        slide_paths = sorted([
            os.path.join(slide_dir, f) 
            for f in os.listdir(slide_dir) 
            if f.endswith('.png') and not f.startswith('.')
        ])
        
        # Get sorted audio paths (e.g., audio_01.mp3, audio_02.mp3)
        audio_paths = sorted([
            os.path.join(audio_dir, f) 
            for f in os.listdir(audio_dir) 
            if f.endswith('.mp3') and not f.startswith('.')
        ])
        
        return slide_paths, audio_paths
    
    except Exception as e:
        print(f"❌ Error reading directories: {e}", file=sys.stderr)
        return [], []


if __name__ == "__main__":
    # When run directly, automatically find and process files
    try:
        slide_paths, audio_paths = get_file_paths_from_directories()
        
        if not slide_paths:
            print(f"❌ No slide images found in '{Config.RENDERED_SLIDES_DIR}' directory", file=sys.stderr)
            sys.exit(1)
        
        if not audio_paths:
            print(f"❌ No audio files found in '{Config.GENERATED_AUDIO_DIR}' directory", file=sys.stderr)
            sys.exit(1)
        
        final_video = stitch_slides_to_video(
            slide_paths, 
            audio_paths, 
            output_filename=Config.FINAL_VIDEO_NAME
        )
        
        if final_video:
            print(f"\n🎉 Video generation complete!")
            print(f"📁 Location: {os.path.abspath(final_video)}")
            sys.exit(0)
        else:
            print("\n❌ Video generation failed!")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)