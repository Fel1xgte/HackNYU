#!/usr/bin/env python3
"""
Validation Script for Video Decoder Output

This script validates the decoded_video.json file to ensure all fixes are working correctly.
Run after video_decoder.py to verify data quality.

Usage:
    python validate_decoder_output.py [path_to_decoded_video.json]
"""

import json
import sys
from pathlib import Path


def validate_confidence_scores(data):
    """Validate that all confidence scores are in valid range (0-1)."""
    print("\n🔍 Validating confidence scores...")
    issues = []
    
    for seg in data.get("audio_segments", []):
        confidence = seg.get("confidence", 0)
        seg_id = seg.get("segment_id", "unknown")
        
        if confidence < 0 or confidence > 1:
            issues.append(f"  ❌ {seg_id}: Invalid confidence {confidence} (must be 0-1)")
        
        # Check for suspiciously low confidence
        if confidence < 0.01:
            issues.append(f"  ⚠️  {seg_id}: Very low confidence {confidence:.4f}")
    
    if issues:
        print(f"  Found {len(issues)} confidence issues:")
        for issue in issues[:10]:  # Show first 10
            print(issue)
        return False
    else:
        print(f"  ✅ All {len(data.get('audio_segments', []))} segments have valid confidence scores")
        return True


def validate_alignments(data):
    """Validate that no alignments are empty."""
    print("\n🔍 Validating audio-visual alignments...")
    empty_alignments = []
    
    for align in data.get("alignments", {}).get("audio_to_visual", []):
        seg_id = align.get("segment_id", "unknown")
        frame_ids = align.get("frame_ids", [])
        
        if not frame_ids:
            empty_alignments.append(seg_id)
    
    if empty_alignments:
        print(f"  ❌ Found {len(empty_alignments)} empty alignments:")
        for seg_id in empty_alignments[:10]:
            print(f"    - {seg_id}")
        return False
    else:
        print(f"  ✅ All {len(data.get('alignments', {}).get('audio_to_visual', []))} alignments have frames")
        return True


def validate_alignment_quality(data):
    """Check alignment validation report."""
    print("\n🔍 Checking alignment validation report...")
    
    validation = data.get("metadata", {}).get("alignment_validation", {})
    
    if not validation:
        print("  ⚠️  No validation report found in metadata")
        return False
    
    is_valid = validation.get("valid", False)
    issues_count = validation.get("issues_count", 0)
    issues = validation.get("issues", [])
    
    if is_valid:
        print(f"  ✅ All alignments are temporally consistent")
        return True
    else:
        print(f"  ⚠️  Found {issues_count} suspicious alignments:")
        for issue in issues[:5]:  # Show first 5
            seg_id = issue.get("segment_id")
            frame_id = issue.get("frame_id")
            time_diff = issue.get("time_diff", 0)
            print(f"    - {seg_id} ↔ {frame_id}: time_diff={time_diff:.1f}s")
        return False


def validate_ocr_deduplication(data):
    """Check if OCR deduplication is working."""
    print("\n🔍 Checking OCR deduplication...")
    
    duplicate_count = 0
    total_frames = 0
    
    for frame in data.get("visual_keyframes", []):
        total_frames += 1
        ocr_text = frame.get("ocr_text", "")
        if "[DUPLICATE_OF_PREVIOUS]" in ocr_text:
            duplicate_count += 1
    
    if duplicate_count > 0:
        print(f"  ✅ OCR deduplication active: {duplicate_count}/{total_frames} frames marked as duplicates")
        return True
    else:
        print(f"  ℹ️  No duplicate OCR detected (may be normal for videos with unique slides)")
        return True


def validate_data_structure(data):
    """Validate basic data structure."""
    print("\n🔍 Validating data structure...")
    
    required_keys = ["schema_version", "project_id", "video", "models", 
                     "audio_segments", "visual_keyframes", "alignments", "metadata"]
    
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        print(f"  ❌ Missing required keys: {missing_keys}")
        return False
    
    print(f"  ✅ All required top-level keys present")
    
    # Check counts
    seg_count = len(data.get("audio_segments", []))
    frame_count = len(data.get("visual_keyframes", []))
    align_count = len(data.get("alignments", {}).get("audio_to_visual", []))
    
    print(f"  📊 Data counts:")
    print(f"    - Audio segments: {seg_count}")
    print(f"    - Visual keyframes: {frame_count}")
    print(f"    - Alignments: {align_count}")
    
    if seg_count == 0:
        print(f"  ⚠️  WARNING: No audio segments (video may be silent)")
    
    if frame_count == 0:
        print(f"  ❌ ERROR: No visual keyframes extracted")
        return False
    
    return True


def validate_metadata(data):
    """Validate metadata fields."""
    print("\n🔍 Validating metadata...")
    
    metadata = data.get("metadata", {})
    
    expected_fields = ["frame_sampling_strategy", "frame_sampling_interval_sec", 
                      "alignment_validation", "notes"]
    
    missing = [field for field in expected_fields if field not in metadata]
    
    if missing:
        print(f"  ⚠️  Missing metadata fields: {missing}")
        return False
    
    print(f"  ✅ All expected metadata fields present")
    return True


def main():
    """Main validation function."""
    print("=" * 70)
    print("🧪 Video Decoder Output Validator")
    print("=" * 70)
    
    # Get file path
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = "workspace/decoded_video.json"
    
    # Check file exists
    if not Path(json_path).exists():
        print(f"\n❌ ERROR: File not found: {json_path}")
        sys.exit(1)
    
    print(f"\n📁 Loading: {json_path}")
    
    # Load JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR: Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: Failed to load file: {e}")
        sys.exit(1)
    
    print("✅ JSON loaded successfully")
    
    # Run all validations
    results = []
    
    results.append(("Data Structure", validate_data_structure(data)))
    results.append(("Confidence Scores", validate_confidence_scores(data)))
    results.append(("Alignments", validate_alignments(data)))
    results.append(("Alignment Quality", validate_alignment_quality(data)))
    results.append(("OCR Deduplication", validate_ocr_deduplication(data)))
    results.append(("Metadata", validate_metadata(data)))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} | {test_name}")
    
    print("=" * 70)
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validations passed! Data quality is good.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Review issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
