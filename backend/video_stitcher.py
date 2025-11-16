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
import re
from pathlib import Path
from config import Config


def write_status(status: str):
    """Write status to status.txt for frontend polling"""
    status_file = Path("workspace/status.txt")
    status_file.write_text(status)
    print(f"📊 Status: {status}")

# Directories are now controlled by Config
# VIDEO_SEGMENTS_DIR = "video_segments"
# FINAL_OUTPUT_DIR = "final_output"
# TARGET_VIDEO_DURATION = 90

# Directories are created by config.py on import
# os.makedirs(VIDEO_SEGMENTS_DIR, exist_ok=True)
# os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)


def validate_audio_file(audio_path: str) -> bool:
    """
    Validate that an audio file exists, has content, and is a valid audio file.
    
    Args:
        audio_path (str): Path to the audio file to validate
    
    Returns:
        bool: True if file is valid, False otherwise
    """
    if not os.path.exists(audio_path):
        return False
    
    # Check if file has content (not empty)
    if os.path.getsize(audio_path) == 0:
        return False
    
    # Try to get duration - if this fails, the file is likely invalid
    duration = get_audio_duration(audio_path)
    if duration <= 0:
        return False
    
    return True


def get_audio_duration(audio_path, timeout=10):
    """
    Get the duration of an audio or video file in seconds.
    
    Args:
        audio_path (str): Path to the audio/video file
        timeout (int): Timeout in seconds for ffprobe command
    
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
            check=True,
            timeout=timeout
        )
        duration_str = result.stdout.strip()
        if duration_str:
            return float(duration_str)
        return 0
    except subprocess.TimeoutExpired:
        print(f"⚠️  Warning: ffprobe timed out for {audio_path}", file=sys.stderr)
        return 0
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
        
        write_status(f"stitching_video:segment_{segment_index}")
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
        
        write_status("stitching_video:merging_segments")
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
        write_status("stitching_video:starting")
        
        if len(slide_image_paths) != len(audio_paths):
            print(f"❌ Mismatch: {len(slide_image_paths)} slides but {len(audio_paths)} audio files", file=sys.stderr)
            write_status("stitching_video:failed:mismatch")
            return None
        
        if not slide_image_paths:
            print("❌ No slides to process", file=sys.stderr)
            write_status("stitching_video:failed:no_slides")
            return None
        
        print(f"\n🎬 Starting video stitching pipeline...")
        print(f"   Slides: {len(slide_image_paths)}")
        print(f"   Audio files: {len(audio_paths)}")
        print(f"   Target duration: {Config.TARGET_VIDEO_DURATION} seconds")
        print()
        
        # Check FFmpeg
        if not check_ffmpeg():
            write_status("stitching_video:failed:ffmpeg_not_found")
            return None
        
        write_status("stitching_video:validating_files")
        
        # Filter out invalid audio files before processing
        valid_pairs = []
        for slide_path, audio_path in zip(slide_image_paths, audio_paths):
            if not os.path.exists(slide_path):
                print(f"⚠️  Warning: Slide image not found: {slide_path}", file=sys.stderr)
                continue
            if not validate_audio_file(audio_path):
                print(f"⚠️  Warning: Invalid audio file, skipping slide: {audio_path}", file=sys.stderr)
                continue
            valid_pairs.append((slide_path, audio_path))
        
        if not valid_pairs:
            print("❌ No valid slide-audio pairs found", file=sys.stderr)
            write_status("stitching_video:failed:no_valid_pairs")
            return None
        
        # Update lists to only include valid pairs
        slide_image_paths = [pair[0] for pair in valid_pairs]
        audio_paths = [pair[1] for pair in valid_pairs]
        
        write_status(f"stitching_video:calculating_durations:{len(valid_pairs)}_pairs")
        
        # CRITICAL: Validate we have exactly 6 segments
        EXPECTED_SEGMENT_COUNT = 6
        if len(valid_pairs) != EXPECTED_SEGMENT_COUNT:
            error_msg = f"Expected exactly {EXPECTED_SEGMENT_COUNT} slide-audio pairs, but found {len(valid_pairs)}"
            print(f"❌ ERROR: {error_msg}", file=sys.stderr)
            print(f"   Found pairs: {[f'slide_{i+1}' for i in range(len(valid_pairs))]}", file=sys.stderr)
            write_status(f"stitching_video:failed:wrong_segment_count:{len(valid_pairs)}")
            return None
        
        # Calculate total audio duration and segment durations
        audio_durations = []
        for i, audio_path in enumerate(audio_paths, 1):
            write_status(f"stitching_video:getting_duration:{i}_of_{len(audio_paths)}")
            duration = get_audio_duration(audio_path)
            if duration <= 0:
                print(f"❌ ERROR: Invalid audio duration ({duration:.2f}s) for audio {i}", file=sys.stderr)
                write_status(f"stitching_video:failed:invalid_audio_duration:{i}")
                return None
            audio_durations.append(duration)
        
        total_audio_duration = sum(audio_durations)
        
        # Calculate proportional durations to fit TARGET_VIDEO_DURATION exactly
        if total_audio_duration > 0:
            ratio = Config.TARGET_VIDEO_DURATION / total_audio_duration
            segment_durations = [(d * ratio) for d in audio_durations]
            
            # CRITICAL: Adjust to ensure exact 90-second total
            # Round to 2 decimal places and adjust last segment to hit exact target
            segment_durations = [round(d, 2) for d in segment_durations]
            current_total = sum(segment_durations)
            difference = Config.TARGET_VIDEO_DURATION - current_total
            
            # Adjust the last segment to compensate for rounding errors
            if abs(difference) > 0.01:  # If difference is significant (>10ms)
                segment_durations[-1] = round(segment_durations[-1] + difference, 2)
            
            final_total = sum(segment_durations)
            
            print(f"📊 Original audio duration: {total_audio_duration:.2f}s → Compressed to: {Config.TARGET_VIDEO_DURATION}s")
            print(f"   Compression ratio: {ratio:.2f}x")
            print(f"   Segment durations: {[f'{d:.2f}s' for d in segment_durations]}")
            print(f"   Total duration: {final_total:.2f}s (target: {Config.TARGET_VIDEO_DURATION}s)")
            
            # Validate total is exactly 90 seconds (±0.5s tolerance)
            if abs(final_total - Config.TARGET_VIDEO_DURATION) > 0.5:
                error_msg = f"Calculated total duration ({final_total:.2f}s) is too far from target ({Config.TARGET_VIDEO_DURATION}s)"
                print(f"❌ ERROR: {error_msg}", file=sys.stderr)
                write_status(f"stitching_video:failed:duration_mismatch:{final_total:.2f}")
                return None
            
            print()
        else:
            # Fallback: equal distribution (should not happen with valid audio)
            segment_durations = [Config.TARGET_VIDEO_DURATION / len(audio_paths)] * len(audio_paths)
            segment_durations = [round(d, 2) for d in segment_durations]
            # Adjust last segment to ensure exact total
            current_total = sum(segment_durations)
            difference = Config.TARGET_VIDEO_DURATION - current_total
            segment_durations[-1] = round(segment_durations[-1] + difference, 2)
            
            print(f"⚠️  Could not detect audio durations, using equal distribution")
            print(f"   Each segment: {segment_durations[0]:.2f}s")
            print(f"   Total duration: {sum(segment_durations):.2f}s\n")
        
        # Create video segments
        write_status(f"stitching_video:creating_segments:{len(slide_image_paths)}_segments")
        segment_paths = []
        
        # CRITICAL: Validate we have exactly 6 slides before creating segments
        EXPECTED_SEGMENT_COUNT = 6
        if len(slide_image_paths) != EXPECTED_SEGMENT_COUNT:
            error_msg = f"Expected exactly {EXPECTED_SEGMENT_COUNT} slides, but found {len(slide_image_paths)}"
            print(f"❌ ERROR: {error_msg}", file=sys.stderr)
            write_status(f"stitching_video:failed:wrong_slide_count:{len(slide_image_paths)}")
            return None
        
        # Validate all required files exist before creating segments
        for i in range(1, EXPECTED_SEGMENT_COUNT + 1):
            slide_path = slide_image_paths[i - 1]
            audio_path = audio_paths[i - 1]
            
            if not os.path.exists(slide_path):
                print(f"❌ ERROR: Slide image not found for segment {i:02d}: {slide_path}", file=sys.stderr)
                write_status(f"stitching_video:failed:missing_slide_{i:02d}")
                return None
            
            if not validate_audio_file(audio_path):
                print(f"❌ ERROR: Invalid audio file for segment {i:02d}: {audio_path}", file=sys.stderr)
                write_status(f"stitching_video:failed:invalid_audio_{i:02d}")
                return None
        
        # Create all segments (1-indexed: segment_01 through segment_06)
        for i, (slide_path, audio_path, duration) in enumerate(zip(slide_image_paths, audio_paths, segment_durations), start=1):
            segment_path = create_video_segment(slide_path, audio_path, i, duration=duration)
            
            if segment_path:
                segment_paths.append(segment_path)
                print(f"   ✅ Segment {i:02d}/{EXPECTED_SEGMENT_COUNT} created successfully ({duration:.2f}s)")
            else:
                print(f"❌ ERROR: Failed to create segment {i:02d}, cannot continue", file=sys.stderr)
                write_status(f"stitching_video:failed:segment_creation_{i:02d}")
                return None
        
        # CRITICAL: Validate all 6 segments were created
        if len(segment_paths) != EXPECTED_SEGMENT_COUNT:
            error_msg = f"Expected {EXPECTED_SEGMENT_COUNT} segments but only created {len(segment_paths)}"
            print(f"❌ ERROR: {error_msg}", file=sys.stderr)
            print(f"   Created segments: {[os.path.basename(p) for p in segment_paths]}", file=sys.stderr)
            write_status(f"stitching_video:failed:segment_count_mismatch:{len(segment_paths)}")
            return None
        
        # Verify segment files exist and are numbered correctly (01-06)
        missing_segments = []
        for i in range(1, EXPECTED_SEGMENT_COUNT + 1):
            expected_segment = os.path.join(Config.VIDEO_SEGMENTS_DIR, f"segment_{i:02d}.mp4")
            if not os.path.exists(expected_segment):
                missing_segments.append(f"segment_{i:02d}.mp4")
        
        if missing_segments:
            error_msg = f"Missing segment files: {', '.join(missing_segments)}"
            print(f"❌ ERROR: {error_msg}", file=sys.stderr)
            write_status(f"stitching_video:failed:missing_segment_files:{','.join(missing_segments)}")
            return None
        
        print(f"\n✅ All {EXPECTED_SEGMENT_COUNT} segments created successfully (segment_01 through segment_{EXPECTED_SEGMENT_COUNT:02d})")
        
        # Concatenate segments
        write_status("stitching_video:merging_segments")
        final_video_path = concatenate_video_segments(segment_paths, output_filename)
        
        if final_video_path:
            # CRITICAL: Validate final video duration is exactly 90 seconds (±0.5s tolerance)
            final_duration = get_audio_duration(final_video_path)
            target_duration = Config.TARGET_VIDEO_DURATION
            tolerance = 0.5  # Stricter tolerance: ±0.5 seconds
            
            if abs(final_duration - target_duration) > tolerance:
                error_msg = f"Final video duration ({final_duration:.2f}s) is outside tolerance (±{tolerance}s) of target ({target_duration}s)"
                print(f"\n❌ ERROR: {error_msg}", file=sys.stderr)
                print(f"   This indicates an issue with segment duration calculation or concatenation", file=sys.stderr)
                write_status(f"stitching_video:failed:final_duration_mismatch:{final_duration:.2f}")
                return None
            else:
                print(f"\n✅ Final video duration: {final_duration:.2f}s (target: {target_duration}s, difference: {abs(final_duration - target_duration):.2f}s)")
            
            print(f"\n✨ SUCCESS! Final video ready: {final_video_path}")
            write_status("stitching_video:complete")
            return final_video_path
        else:
            print("\n❌ Failed to create final video", file=sys.stderr)
            write_status("stitching_video:failed:concatenation")
            return None
    
    except Exception as e:
        print(f"❌ Unexpected error in video stitching: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        write_status(f"stitching_video:failed:error:{str(e)}")
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
        # Extract slide number from filename (e.g., slide_01.png -> 1)
        def extract_slide_number(filename):
            match = re.search(r'slide_(\d+)\.png', filename)
            return int(match.group(1)) if match else None
        
        # Extract audio number from filename (e.g., audio_01.mp3 -> 1)
        def extract_audio_number(filename):
            match = re.search(r'audio_(\d+)\.mp3', filename)
            return int(match.group(1)) if match else None
        
        # Get all slide files with their numbers
        slide_files = {}
        for f in os.listdir(slide_dir):
            if f.endswith('.png') and not f.startswith('.'):
                slide_num = extract_slide_number(f)
                if slide_num:
                    slide_files[slide_num] = os.path.join(slide_dir, f)
        
        # Get all audio files with their numbers, validate them
        audio_files = {}
        for f in os.listdir(audio_dir):
            if f.endswith('.mp3') and not f.startswith('.'):
                audio_num = extract_audio_number(f)
                if audio_num:
                    audio_path = os.path.join(audio_dir, f)
                    if validate_audio_file(audio_path):
                        audio_files[audio_num] = audio_path
                    else:
                        print(f"⚠️  Skipping invalid audio file: {audio_path}", file=sys.stderr)
        
        # Match slides to audio by number
        slide_paths = []
        audio_paths = []
        
        # Get all slide numbers that have both slide and audio
        matched_numbers = sorted(set(slide_files.keys()) & set(audio_files.keys()))
        
        # CRITICAL: Validate we have exactly 6 pairs (01-06)
        EXPECTED_PAIRS = 6
        expected_numbers = set(range(1, EXPECTED_PAIRS + 1))
        found_numbers = set(matched_numbers)
        
        missing_numbers = expected_numbers - found_numbers
        extra_numbers = found_numbers - expected_numbers
        
        if missing_numbers:
            print(f"❌ ERROR: Missing slide-audio pairs for segments: {sorted(missing_numbers)}", file=sys.stderr)
            print(f"   Expected segments 01-{EXPECTED_PAIRS:02d}, but found: {sorted(found_numbers)}", file=sys.stderr)
            return [], []
        
        if extra_numbers:
            print(f"⚠️  Warning: Extra slide-audio pairs found: {sorted(extra_numbers)} (will use first 6)", file=sys.stderr)
        
        # Only use the first 6 pairs (01-06) in order
        for num in sorted(matched_numbers):
            if num <= EXPECTED_PAIRS:
                slide_paths.append(slide_files[num])
                audio_paths.append(audio_files[num])
        
        # Warn about unmatched slides or audio
        unmatched_slides = set(slide_files.keys()) - set(audio_files.keys())
        unmatched_audio = set(audio_files.keys()) - set(slide_files.keys())
        
        if unmatched_slides:
            print(f"⚠️  Warning: {len(unmatched_slides)} slides have no matching audio: {sorted(unmatched_slides)}", file=sys.stderr)
        if unmatched_audio:
            print(f"⚠️  Warning: {len(unmatched_audio)} audio files have no matching slide: {sorted(unmatched_audio)}", file=sys.stderr)
        
        # Final validation: ensure we have exactly 6 pairs
        if len(slide_paths) != EXPECTED_PAIRS or len(audio_paths) != EXPECTED_PAIRS:
            print(f"❌ ERROR: Expected {EXPECTED_PAIRS} pairs but got {len(slide_paths)} slides and {len(audio_paths)} audio files", file=sys.stderr)
            return [], []
        
        return slide_paths, audio_paths
    
    except Exception as e:
        print(f"❌ Error reading directories: {e}", file=sys.stderr)
        return [], []


def main():
    """Main function to stitch slides and audio into final video"""
    # When run directly, automatically find and process files
    try:
        write_status("stitching_video:discovering_files")
        slide_paths, audio_paths = get_file_paths_from_directories()
        
        if not slide_paths:
            print(f"❌ No slide images found in '{Config.RENDERED_SLIDES_DIR}' directory", file=sys.stderr)
            write_status("stitching_video:failed:no_slides_found")
            sys.exit(1)
        
        if not audio_paths:
            print(f"❌ No audio files found in '{Config.GENERATED_AUDIO_DIR}' directory", file=sys.stderr)
            write_status("stitching_video:failed:no_audio_found")
            sys.exit(1)
        
        final_video = stitch_slides_to_video(
            slide_paths, 
            audio_paths, 
            output_filename=Config.FINAL_VIDEO_NAME
        )
        
        if final_video:
            print(f"\n🎉 Video generation complete!")
            print(f"📁 Location: {os.path.abspath(final_video)}")
            # Note: run_pipeline.py will update status to "complete" after this returns
            return final_video
        else:
            print("\n❌ Video generation failed!")
            write_status("stitching_video:failed:main")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        write_status(f"stitching_video:failed:fatal:{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()