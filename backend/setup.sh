#!/bin/bash

# Video Generation Setup Script
# This script sets up the environment for the Confucius Lecture Summarizer

echo "=========================================="
echo "🎓 Confucius Lecture Summarizer Setup"
echo "=========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  Warning: This script is optimized for macOS"
    echo "   You may need to adjust commands for your OS"
    echo ""
fi

# Step 1: Check Python
echo "📦 Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ Python found: $PYTHON_VERSION"
else
    echo "   ❌ Python 3 not found!"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi
echo ""

# Step 2: Check/Install FFmpeg
echo "🎬 Step 2: Checking FFmpeg installation..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
    echo "   ✅ FFmpeg found: $FFMPEG_VERSION"
else
    echo "   ❌ FFmpeg not found!"
    echo "   Installing FFmpeg with Homebrew..."
    
    if command -v brew &> /dev/null; then
        brew install ffmpeg
        echo "   ✅ FFmpeg installed successfully"
    else
        echo "   ❌ Homebrew not found!"
        echo "   Please install FFmpeg manually:"
        echo "   macOS: brew install ffmpeg"
        echo "   Ubuntu: sudo apt-get install ffmpeg"
        exit 1
    fi
fi
echo ""

# Step 3: Install Python packages
echo "📚 Step 3: Installing Python dependencies..."
cd "$(dirname "$0")" || exit 1

if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
    echo "   ✅ Python packages installed"
else
    echo "   ❌ requirements.txt not found!"
    exit 1
fi
echo ""

# Step 4: Check environment variables
echo "🔑 Step 4: Checking environment variables..."

MISSING_VARS=()

if [ -z "$ELEVENLABS_API_KEY" ]; then
    MISSING_VARS+=("ELEVENLABS_API_KEY")
fi

if [ -z "$GEMINI_API_KEY" ]; then
    MISSING_VARS+=("GEMINI_API_KEY")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "   ⚠️  Missing environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "      • $var"
    done
    echo ""
    echo "   Please set them in your shell profile:"
    echo "   export ELEVENLABS_API_KEY='your-api-key-here'"
    echo "   export GEMINI_API_KEY='your-api-key-here'"
    echo ""
    echo "   Or set them temporarily:"
    echo "   export ELEVENLABS_API_KEY='your-api-key-here'"
    echo "   export GEMINI_API_KEY='your-api-key-here'"
    echo ""
else
    echo "   ✅ All environment variables set"
fi
echo ""

# Step 5: Create necessary directories
echo "📁 Step 5: Creating output directories..."
cd slides || exit 1
mkdir -p rendered_slides generated_audio video_segments final_output
echo "   ✅ Directories created"
echo ""

echo "=========================================="
echo "✨ Setup Complete!"
echo "=========================================="
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Generate slides (if not already done):"
echo "   cd slides"
echo "   python3 slides_generator.py"
echo ""
echo "2. Run the full video generation pipeline:"
echo "   python3 pipeline.py"
echo ""
echo "3. Or run individual steps:"
echo "   python3 slides_renderer.py     # Render PNG slides"
echo "   python3 audio_generator.py     # Generate audio with ElevenLabs"
echo "   python3 video_stitcher.py      # Stitch video with FFmpeg"
echo ""
echo "📹 Final video will be saved to: slides/final_output/confucius_lecture_summary.mp4"
echo ""
