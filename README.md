# 🎓 Confucius Lecture Summarizer

An AI-powered video generation pipeline that transforms lecture transcripts into professional educational videos with slides and narration.

## 🌟 Features

- **AI-Powered Slide Generation**: Uses Google Gemini AI to convert transcripts into structured slides
- **Professional Voice Narration**: ElevenLabs TTS with Confucius-inspired voice (deep, authoritative)
- **Automated Video Production**: FFmpeg-based video stitching with synchronized audio
- **90-Second Target**: Automatic compression to create concise, engaging videos
- **Production-Ready Code**: Comprehensive error handling, logging, and validation

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- FFmpeg (for video processing)
- API Keys:
  - [ElevenLabs API Key](https://elevenlabs.io/)
  - [Google Gemini API Key](https://makersuite.google.com/app/apikey)

### Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg
brew install ffmpeg  # macOS
# sudo apt-get install ffmpeg  # Linux
```

### Configuration

1. Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:

```env
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
```

### Generate Video

```bash
cd backend/slides
python3 pipeline.py
```

The final video will be saved to `backend/slides/final_output/confucius_lecture_summary.mp4`

## 📁 Project Structure

```
backend/
├── requirements.txt          # Python dependencies
├── .env                      # API keys (create this)
└── slides/
    ├── config.py            # Centralized configuration
    ├── env_loader.py        # Environment variable management
    ├── pipeline.py          # Main orchestrator (RUN THIS)
    ├── slides_generator.py  # AI slide generation (Gemini)
    ├── slides_renderer.py   # PNG image rendering
    ├── audio_generator.py   # TTS audio generation (ElevenLabs)
    ├── video_stitcher.py    # Video compilation (FFmpeg)
    ├── generated_slides.json
    ├── rendered_slides/     # Output: PNG slides
    ├── generated_audio/     # Output: MP3 audio files
    ├── video_segments/      # Output: MP4 segments
    └── final_output/        # Output: Final video
```

## 🎬 Pipeline Flow

```
Transcript JSON
      ↓
[1] slides_generator.py → generated_slides.json
      ↓
[2] slides_renderer.py → rendered_slides/*.png
      ↓
[3] audio_generator.py → generated_audio/*.mp3  (ElevenLabs TTS)
      ↓
[4] video_stitcher.py → video_segments/*.mp4
      ↓
[5] Concatenate → final_output/confucius_lecture_summary.mp4
      ↓
✨ Final Video (90 seconds)
```

## 🔧 Configuration

### Video Settings

Edit `config.py` to customize:

```python
TARGET_VIDEO_DURATION = 90  # seconds
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
```

### Voice Settings

The voice is pre-configured for philosophical content:

- **Voice**: Adam (deep, authoritative)
- **Model**: eleven_multilingual_v2
- **Stability**: 0.7 (calm, steady)
- **Similarity**: 0.8 (consistent)
- **Style**: 0.4 (moderate emphasis)

To change, edit `config.py` voice constants.

### Slide Design

Customize in `config.py`:

```python
SLIDE_BACKGROUND_COLOR = "#111111"
SLIDE_TITLE_COLOR = "white"
SLIDE_TEXT_COLOR = "#DDDDDD"
```

## 🐛 Troubleshooting

### FFmpeg Not Found
```bash
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux
```

### API Key Errors
- Ensure `.env` file exists in `backend/` directory
- Check API keys are valid and have correct permissions
- ElevenLabs: Needs text-to-speech permission
- Gemini: Needs content generation permission

### Audio Not Playing in Video
- Ensure all audio files were generated successfully
- Check `generated_audio/` directory for MP3 files
- Verify FFmpeg is installed correctly

### Python Version Issues
- Pillow 10.3.0 is incompatible with Python 3.13
- Use `Pillow>=11.0.0` (already in requirements.txt)
- Or use Python 3.11 or earlier

## 📊 Output Specifications

### Video
- **Resolution**: 1920x1080 (Full HD)
- **Format**: MP4 (H.264 video, AAC audio)
- **Duration**: 90 seconds (configurable)
- **Audio Bitrate**: 192 kbps
- **Codec**: libx264 with yuv420p pixel format

### Audio
- **Format**: MP3
- **Sample Rate**: 44.1 kHz
- **Bitrate**: 128 kbps
- **Voice**: Adam (ElevenLabs)

### Slides
- **Format**: PNG
- **Resolution**: 1920x1080
- **Background**: Dark (#111111)
- **Title**: White, 80pt
- **Body**: Light gray (#DDDDDD), 48pt

## 🧪 Testing

Run individual components for testing:

```bash
# Test slide rendering
python3 slides_renderer.py

# Test audio generation
python3 audio_generator.py

# Test video stitching
python3 video_stitcher.py

# Validate environment setup
python3 validate_setup.py
```

## 🤝 Contributing

This project was built for HackNYU. Contributions are welcome!

## 📄 License

MIT License - See LICENSE file for details

## 👥 Authors

Confucius Lecture Summarizer Team

## 🙏 Acknowledgments

- **ElevenLabs** for world-class TTS API
- **Google Gemini** for AI content generation
- **FFmpeg** for video processing capabilities
- **HackNYU** for inspiration and support

---

**Made with ❤️ for HackNYU**
