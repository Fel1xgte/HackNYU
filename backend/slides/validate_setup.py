#!/usr/bin/env python3
"""
Pre-Flight Validation Script for Confucius Lecture Summarizer

This script validates the entire setup before running the pipeline:
- Python version and required modules
- FFmpeg installation
- Environment variables (.env file)
- Directory structure
- Input files
- Code syntax

Usage:
    python3 validate_setup.py
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_result(check_name, passed, message=""):
    """Print check result"""
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")
    if message:
        print(f"   → {message}")
    return passed


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 8
    msg = f"Python {version.major}.{version.minor}.{version.micro}"
    return print_result(
        "Python Version", 
        is_valid, 
        msg + (" (OK)" if is_valid else " (need 3.8+)")
    )


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return print_result("FFmpeg Installation", True, "Found")
    except (FileNotFoundError, subprocess.CalledProcessError):
        return print_result(
            "FFmpeg Installation", 
            False, 
            "Not found. Install: brew install ffmpeg"
        )


def check_python_modules():
    """Check if required Python modules are installed"""
    required = {
        "PIL": "Pillow",
        "elevenlabs": "elevenlabs",
        "google.generativeai": "google-generativeai"
    }
    
    all_installed = True
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
            print_result(f"Module: {package_name}", True, "Installed")
        except ImportError:
            print_result(
                f"Module: {package_name}", 
                False, 
                "Not installed. Run: pip install -r ../requirements.txt"
            )
            all_installed = False
    
    return all_installed


def check_env_file():
    """Check if .env file exists and has required keys"""
    env_path = Path("../env")
    env_example_path = Path("../.env.example")
    
    if not env_path.exists():
        if env_example_path.exists():
            return print_result(
                ".env File", 
                False, 
                "Not found. Copy: cp ../.env.example ../.env"
            )
        else:
            return print_result(
                ".env File", 
                False, 
                ".env.example not found either!"
            )
    
    # Check if it has the required keys
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        has_elevenlabs = "ELEVENLABS_API_KEY" in content
        has_gemini = "GEMINI_API_KEY" in content
        
        if has_elevenlabs and has_gemini:
            return print_result(".env File", True, "Found with required keys")
        else:
            missing = []
            if not has_elevenlabs:
                missing.append("ELEVENLABS_API_KEY")
            if not has_gemini:
                missing.append("GEMINI_API_KEY")
            return print_result(
                ".env File", 
                False, 
                f"Missing keys: {', '.join(missing)}"
            )
    except Exception as e:
        return print_result(".env File", False, f"Error reading file: {e}")


def check_api_keys():
    """Check if API keys are actually set (not placeholders)"""
    # Load .env file
    from env_loader import load_env_file
    load_env_file()
    
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    
    elevenlabs_valid = elevenlabs_key and "your-" not in elevenlabs_key.lower()
    gemini_valid = gemini_key and "your-" not in gemini_key.lower()
    
    print_result(
        "ELEVENLABS_API_KEY", 
        elevenlabs_valid, 
        "Set" if elevenlabs_valid else "Not set or still placeholder"
    )
    print_result(
        "GEMINI_API_KEY", 
        gemini_valid, 
        "Set" if gemini_valid else "Not set or still placeholder"
    )
    
    return elevenlabs_valid and gemini_valid


def check_directories():
    """Check if required directories exist"""
    required_dirs = [
        "rendered_slides",
        "generated_audio",
        "video_segments",
        "final_output"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        exists = os.path.exists(dir_name)
        if not exists:
            all_exist = False
        print_result(
            f"Directory: {dir_name}", 
            exists, 
            "Exists" if exists else "Will be created automatically"
        )
    
    return True  # Not critical, they'll be created


def check_input_files():
    """Check if sample input files exist"""
    files = {
        "generated_slides.json": "Slide content (required for pipeline)",
        "sample_transcript.json": "Sample input (for slides_generator.py)"
    }
    
    any_found = False
    for filename, description in files.items():
        exists = os.path.exists(filename)
        if exists:
            any_found = True
        print_result(
            f"Input: {filename}", 
            exists, 
            description if exists else "Not found (generate first)"
        )
    
    return any_found


def check_code_syntax():
    """Check if all Python files have valid syntax"""
    python_files = [
        "env_loader.py",
        "audio_generator.py",
        "video_stitcher.py",
        "slides_renderer.py",
        "slides_generator.py",
        "pipeline.py"
    ]
    
    all_valid = True
    for filename in python_files:
        if not os.path.exists(filename):
            print_result(f"Syntax: {filename}", False, "File not found")
            all_valid = False
            continue
        
        try:
            with open(filename, "r", encoding="utf-8") as f:
                compile(f.read(), filename, "exec")
            print_result(f"Syntax: {filename}", True, "Valid")
        except SyntaxError as e:
            print_result(f"Syntax: {filename}", False, f"Error at line {e.lineno}")
            all_valid = False
    
    return all_valid


def main():
    """Run all validation checks"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "     CONFUCIUS LECTURE SUMMARIZER - SETUP VALIDATION".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    results = {}
    
    print_header("SYSTEM REQUIREMENTS")
    results["python"] = check_python_version()
    results["ffmpeg"] = check_ffmpeg()
    
    print_header("PYTHON MODULES")
    results["modules"] = check_python_modules()
    
    print_header("ENVIRONMENT CONFIGURATION")
    results["env_file"] = check_env_file()
    results["api_keys"] = check_api_keys()
    
    print_header("DIRECTORY STRUCTURE")
    results["directories"] = check_directories()
    
    print_header("INPUT FILES")
    results["input_files"] = check_input_files()
    
    print_header("CODE VALIDATION")
    results["syntax"] = check_code_syntax()
    
    # Final summary
    print_header("VALIDATION SUMMARY")
    
    critical_checks = ["python", "ffmpeg", "modules", "api_keys", "syntax"]
    critical_passed = all(results.get(check, False) for check in critical_checks)
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    print(f"✓ Passed: {passed_checks}/{total_checks} checks")
    print()
    
    if critical_passed:
        print("🎉 All critical checks passed! You're ready to run the pipeline.")
        print()
        print("Next steps:")
        print("  1. If generated_slides.json doesn't exist:")
        print("     python3 slides_generator.py")
        print("  2. Run the full pipeline:")
        print("     python3 pipeline.py")
        print()
        return 0
    else:
        print("⚠️  Some critical checks failed. Please fix the issues above.")
        print()
        print("Setup help:")
        print("  • Install dependencies: pip install -r ../requirements.txt")
        print("  • Install FFmpeg: brew install ffmpeg")
        print("  • Create .env file: cp ../.env.example ../.env")
        print("  • Edit .env and add your actual API keys")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
