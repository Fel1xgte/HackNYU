import uvicorn
import shutil
import os
import subprocess
import tempfile
import math
import torch
import whisper
import zipfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from config import Config # Import your config for paths

# Load environment variables from .env file
from env_loader import load_env_file
load_env_file()

# We will create 'run_pipeline.py' to orchestrate your scripts.
from run_pipeline import run_pipeline_task

# Import Q&A and TTS services
from qa_service import answer_question
from tts_service import text_to_speech

# --- Configuration ---
app = FastAPI(title="Video Processing API")

# Validation constants
MAX_FILE_SIZE_MB = 100  # 100 MB limit
MAX_VIDEO_DURATION_SEC = 800  # 10 minutes limit
ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi']

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A central directory for all working files
# We'll make all scripts read/write from here
WORKSPACE_DIR = Path("workspace")
INPUT_VIDEO_PATH = WORKSPACE_DIR / "input_video.mp4"
STATUS_FILE = WORKSPACE_DIR / "status.txt"

# Ensure the base directory exists
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using FFprobe"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
             video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        return float(result.stdout.strip())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid video file: {str(e)}")


# --- API Endpoints ---

@app.post("/process-video/")
async def process_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    """
    Upload and process video with comprehensive validation
    """
    try:
        # VALIDATION 1: Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # VALIDATION 2: Check content type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=400,
                detail="File must be a video"
            )
        
        # VALIDATION 3: Check file size (read in chunks)
        content = bytearray()
        chunk_size = 1024 * 1024  # 1 MB chunks
        total_size = 0
        max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        
        while chunk := await file.read(chunk_size):
            total_size += len(chunk)
            if total_size > max_size_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB"
                )
            content.extend(chunk)
        
        print(f"📊 Uploaded file size: {total_size / (1024*1024):.2f} MB")
        
        # VALIDATION 4: Save to temp file and check duration
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            duration = get_video_duration(temp_path)
            print(f"⏱️  Video duration: {duration:.2f} seconds")
            
            if duration > MAX_VIDEO_DURATION_SEC:
                os.remove(temp_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"Video too long. Maximum duration: {MAX_VIDEO_DURATION_SEC/60:.1f} minutes"
                )
            
            # VALIDATION PASSED: Move to workspace
            if STATUS_FILE.exists():
                os.remove(STATUS_FILE)
            
            os.makedirs(WORKSPACE_DIR, exist_ok=True)
            shutil.move(temp_path, INPUT_VIDEO_PATH)
            
        except HTTPException:
            raise
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=400, detail=f"Video validation failed: {str(e)}")
        
        # Start processing
        print("✅ Validation passed - Starting pipeline...")
        background_tasks.add_task(run_pipeline_task, STATUS_FILE)
        
        # Respond immediately to the UI
        return JSONResponse(
            status_code=202, # 202 "Accepted"
            content={
                "status": "processing_started",
                "file_size_mb": round(total_size / (1024*1024), 2),
                "duration_sec": round(duration, 2)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"status": "error", "detail": str(e)}
        )

@app.get("/get-video-status/")
async def get_video_status():
    """
    Endpoint for the UI to ask: "Are you done yet?"
    """
    if not STATUS_FILE.exists():
        return {"status": "not_started"}
        
    status = STATUS_FILE.read_text().strip()
    
    # Check if video exists even if status says stitching_video (recovery from crash)
    if status == "stitching_video" or "stitching_video" in status:
        final_video_path = Config.FINAL_OUTPUT_DIR / Config.FINAL_VIDEO_NAME
        if final_video_path.exists():
            # Video exists but status wasn't updated - fix it
            STATUS_FILE.write_text("complete")
            return {"status": "complete", "download_url": "/get-video/"}
    
    if status == "complete":
        return {"status": "complete", "download_url": "/get-video/"}
    elif "failed" in status:
        return {"status": "failed", "detail": status}
    else:
        # Return the current step (e.g., "decoding_video")
        return {"status": "processing", "step": status}


@app.get("/get-video/")
async def get_video():
    """
    Endpoint to DOWNLOAD the final video.
    The UI will call this once /get-video-status/ returns "complete".
    Supports HTTP range requests for video streaming.
    """
    # Get the final path from your config file
    final_video_path = Config.FINAL_OUTPUT_DIR / Config.FINAL_VIDEO_NAME
    
    if final_video_path.exists():
        print(f"Sending final video: {final_video_path}")
        return FileResponse(
            final_video_path,
            media_type="video/mp4",
            filename="final_summary.mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Type": "video/mp4",
            }
        )
    else:
        return JSONResponse(
            status_code=404, 
            content={"status": "not_found", "detail": "File not ready or does not exist."}
        )


@app.get("/download-slides/")
async def download_slides(background_tasks: BackgroundTasks):
    """
    Endpoint to DOWNLOAD all slide images as a ZIP archive.
    Reads PNG files from RENDERED_SLIDES_DIR and creates a ZIP file.
    """
    slides_dir = Config.RENDERED_SLIDES_DIR
    
    if not slides_dir.exists():
        return JSONResponse(
            status_code=404,
            content={"status": "not_found", "detail": "Slides directory does not exist."}
        )
    
    # Find all PNG files in the slides directory
    slide_files = sorted(slides_dir.glob("*.png"))
    
    if not slide_files:
        return JSONResponse(
            status_code=404,
            content={"status": "not_found", "detail": "No slide images found."}
        )
    
    # Create a temporary ZIP file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
        zip_path = Path(tmp_zip.name)
        
        try:
            # Create ZIP archive
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for slide_file in slide_files:
                    # Add file to ZIP with just the filename (not full path)
                    zipf.write(slide_file, slide_file.name)
            
            print(f"Created slides ZIP: {zip_path} with {len(slide_files)} slides")
            
            # Cleanup function
            def cleanup():
                if zip_path.exists():
                    os.unlink(zip_path)
            
            # Add cleanup task
            background_tasks.add_task(cleanup)
            
            # Return ZIP file
            return FileResponse(
                zip_path,
                media_type="application/zip",
                filename="confucius-lecture-slides.zip"
            )
        except Exception as e:
            # Clean up on error
            if zip_path.exists():
                os.unlink(zip_path)
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": f"Failed to create ZIP archive: {str(e)}"}
            )


# --- Voice Q&A Endpoints ---

# Global Whisper model instance (lazy loaded)
_whisper_model = None

def get_whisper_model():
    """Get or initialize Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[STT] Loading Whisper model 'base' on {device}...")
        _whisper_model = whisper.load_model("base", device=device)
    return _whisper_model


@app.post("/api/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Speech-to-Text endpoint using Whisper.
    Accepts audio blob (WebM/MP3) and returns transcript.
    
    Args:
        audio: Audio file upload (WebM, MP3, or other supported formats)
    
    Returns:
        JSON with transcript and confidence score
    
    Raises:
        HTTPException: If audio processing fails
    """
    MAX_AUDIO_SIZE_MB = 10  # 10 MB limit for audio files
    temp_path = None
    
    try:
        # Validate file size
        content = await audio.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"Audio file too large. Maximum size: {MAX_AUDIO_SIZE_MB}MB"
            )
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Transcribe using Whisper with timeout protection
            model = get_whisper_model()
            
            # Transcribe with error handling
            try:
                result = model.transcribe(
                    temp_path,
                    language="en",
                    verbose=False,
                    fp16=False  # Use fp32 for better compatibility
                )
            except Exception as transcribe_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Transcription failed: {str(transcribe_error)}"
                )
            
            # Get transcript and confidence
            transcript = result.get("text", "").strip()
            segments = result.get("segments", [])
            
            # Calculate average confidence
            if segments:
                avg_logprob = sum(seg.get("avg_logprob", -1.0) for seg in segments) / len(segments)
                confidence = min(1.0, max(0.0, math.exp(avg_logprob)))
            else:
                confidence = 0.5
            
            # Validate transcript
            if not transcript:
                return {
                    "transcript": "",
                    "confidence": 0.0
                }
            
            return {
                "transcript": transcript,
                "confidence": round(confidence, 3)
            }
        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as cleanup_error:
                    print(f"⚠️  Failed to cleanup temp file: {cleanup_error}")
                
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️  STT error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"STT processing failed: {error_msg}"
        )


class QARequest(BaseModel):
    question: str
    currentTime: float
    projectId: Optional[str] = None


@app.post("/api/qa")
async def question_answer(request: QARequest):
    """
    Question-Answering endpoint.
    Takes question and currentTime, returns answer with action.
    Includes comprehensive validation and error handling.
    
    Args:
        request: QARequest with question, currentTime, and optional projectId
    
    Returns:
        JSON with answerText, action, targetTime (optional), and evidence
    
    Raises:
        HTTPException: If validation fails or QA processing fails
    """
    # Validate inputs with comprehensive checks
    if not request.question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    if not isinstance(request.question, str):
        raise HTTPException(
            status_code=400,
            detail="Question must be a string"
        )
    
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    # Validate question length
    MAX_QUESTION_LENGTH = 1000
    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Question too long. Maximum {MAX_QUESTION_LENGTH} characters."
        )
    
    # Validate currentTime
    if not isinstance(request.currentTime, (int, float)):
        raise HTTPException(
            status_code=400,
            detail="currentTime must be a number"
        )
    
    if request.currentTime < 0:
        request.currentTime = 0.0
    
    # Validate projectId if provided
    if request.projectId is not None and not isinstance(request.projectId, str):
        raise HTTPException(
            status_code=400,
            detail="projectId must be a string"
        )
    
    try:
        result = answer_question(
            question=question,
            current_time=float(request.currentTime),
            project_id=request.projectId
        )
        
        # Validate result structure comprehensively
        if not isinstance(result, dict):
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from QA service"
            )
        
        required_fields = ["answerText", "action", "evidence"]
        for field in required_fields:
            if field not in result:
                raise HTTPException(
                    status_code=500,
                    detail=f"Missing required field in response: {field}"
                )
        
        # Validate field types
        if not isinstance(result["answerText"], str):
            raise HTTPException(
                status_code=500,
                detail="Invalid answerText type in response"
            )
        
        if not isinstance(result["action"], str):
            raise HTTPException(
                status_code=500,
                detail="Invalid action type in response"
            )
        
        if not isinstance(result["evidence"], list):
            raise HTTPException(
                status_code=500,
                detail="Invalid evidence type in response"
            )
        
        # Ensure answerText is not empty
        if not result["answerText"].strip():
            result["answerText"] = "I apologize, but I couldn't generate a proper answer. Please try again."
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log full error for debugging but don't expose to client
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"⚠️  QA error [{error_type}]: {error_msg}")
        
        # Return generic error message to client (security: don't expose internals)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again."
        )


class TTSRequest(BaseModel):
    text: str
    voiceId: Optional[str] = None


@app.post("/api/tts")
async def text_to_speech_endpoint(request: TTSRequest):
    """
    Text-to-Speech endpoint using ElevenLabs.
    Returns audio file path or base64 data URL.
    
    Args:
        request: TTSRequest with text and optional voiceId
    
    Returns:
        JSON with audioUrl
    
    Raises:
        HTTPException: If TTS generation fails
    """
    # Validate inputs
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty"
        )
    
    # Limit text length to prevent abuse
    MAX_TEXT_LENGTH = 5000
    if len(request.text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long. Maximum {MAX_TEXT_LENGTH} characters."
        )
    
    try:
        audio_path = text_to_speech(request.text.strip(), request.voiceId)
        if audio_path and os.path.exists(audio_path):
            # Validate file exists and is readable
            if os.path.getsize(audio_path) == 0:
                raise HTTPException(
                    status_code=500,
                    detail="Generated audio file is empty"
                )
            # Return file path (frontend can fetch it)
            return {"audioUrl": f"/api/tts/audio/{Path(audio_path).name}"}
        else:
            raise HTTPException(
                status_code=500,
                detail="TTS generation failed. Please check API configuration."
            )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️  TTS error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"TTS processing failed: {error_msg}"
        )


@app.get("/api/tts/audio/{filename}")
async def get_tts_audio(filename: str):
    """
    Serve TTS audio files from cache.
    
    Args:
        filename: Name of the audio file to serve
    
    Returns:
        FileResponse with audio file
    
    Raises:
        HTTPException: If file not found or invalid
    """
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    audio_path = Path("workspace/tts_cache") / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    if not audio_path.is_file():
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    try:
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename=filename,
            headers={"Cache-Control": "public, max-age=31536000"}  # Cache for 1 year
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve audio file: {str(e)}"
        )


@app.get("/api/transcript")
async def get_transcript():
    """
    Get transcript endpoint.
    Returns workspace/decoded_video.json or sample_transcript.json structure.
    """
    from qa_service import load_transcript
    
    transcript = load_transcript()
    if transcript:
        return transcript
    else:
        raise HTTPException(status_code=404, detail="No transcript available")


@app.get("/api/qa/status")
async def get_qa_status():
    """
    Get QA service status including API key configuration.
    Useful for debugging and setup verification.
    """
    from qa_service import get_api_key_status
    
    status = get_api_key_status()
    
    # Add helpful setup instructions
    setup_info = {
        "status": status,
        "setup_instructions": {
            "gemini": {
                "required": True,
                "configured": status["gemini_configured"],
                "instructions": "Set GEMINI_API_KEY in your .env file. Get your free key at: https://makersuite.google.com/app/apikey"
            }
        },
        "note": "Even without Gemini API key, the service will use fallback keyword-based answers."
    }
    
    return setup_info

# --- Run Server ---
if __name__ == "__main__":
    print("Starting FastAPI server at http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)