import uvicorn
import shutil
import os
import subprocess
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from config import Config # Import your config for paths

# Load environment variables from .env file
from env_loader import load_env_file
load_env_file()

# We will create 'run_pipeline.py' to orchestrate your scripts.
from run_pipeline import run_pipeline_task

# --- Configuration ---
app = FastAPI(title="Video Processing API")

# Validation constants
MAX_FILE_SIZE_MB = 100  # 100 MB limit
MAX_VIDEO_DURATION_SEC = 800  # 10 minutes limit
ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi']

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
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
    """
    # Get the final path from your config file
    final_video_path = Config.FINAL_OUTPUT_DIR / Config.FINAL_VIDEO_NAME
    
    if final_video_path.exists():
        print(f"Sending final video: {final_video_path}")
        return FileResponse(
            final_video_path,
            media_type="video/mp4",
            filename="final_summary.mp4"
        )
    else:
        return JSONResponse(
            status_code=404, 
            content={"status": "not_found", "detail": "File not ready or does not exist."}
        )

# --- Run Server ---
if __name__ == "__main__":
    print("Starting FastAPI server at http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)