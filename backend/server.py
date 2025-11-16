import uvicorn
import shutil
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from config import Config # Import your config for paths

# We will create 'run_pipeline.py' to orchestrate your scripts.
from run_pipeline import run_pipeline_task

# --- Configuration ---
app = FastAPI(title="Video Processing API")

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


# --- API Endpoints ---

@app.post("/process-video/")
async def process_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    """
    Endpoint to UPLOAD the video.
    It receives a video, saves it, and starts the pipeline
    in the background.
    """
    try:
        # Clean up any previous run's status
        if STATUS_FILE.exists():
            os.remove(STATUS_FILE)
        
        # Save the uploaded video to the path the pipeline expects
        print(f"Saving video to: {INPUT_VIDEO_PATH}")
        with open(INPUT_VIDEO_PATH, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Start the pipeline in the background.
        # The UI will not have to wait for it to finish.
        print("Starting pipeline in the background...")
        background_tasks.add_task(run_pipeline_task, STATUS_FILE)
        
        # Respond immediately to the UI
        return JSONResponse(
            status_code=202, # 202 "Accepted"
            content={"status": "processing_started"}
        )

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