from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Optional
from uuid import uuid4
import shutil
import os
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://a.k-lab.su",  # Указываем полное доменное имя
        "http://localhost",    # Доступ с localhost
        "http://127.0.0.1"     # Доступ с IP адреса
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processes: Dict[str, Dict] = {}
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class VideoURL(BaseModel):
    url: HttpUrl

class VideoResponse(BaseModel):
    id: str

class StatusResponse(BaseModel):
    status: str
    tags: Optional[list] = None

def generate_id() -> str:
    return str(uuid4())

async def process_video(process_id: str):
    processes[process_id]['status'] = 'processing'
    await asyncio.sleep(10)
    processes[process_id]['status'] = 'done'
    processes[process_id]['tags'] = ['tag1', 'tag2', 'tag3']

@app.post("/video/formData", response_model=VideoResponse)
async def upload_video_formData(video: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    process_id = generate_id()
    file_path = os.path.join(UPLOAD_FOLDER, f"{process_id}_{video.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    processes[process_id] = {
        'status': 'queued',
        'tags': None,
        'file_path': file_path
    }
    background_tasks.add_task(process_video, process_id)
    return VideoResponse(id=process_id)

@app.post("/video/url", response_model=VideoResponse)
async def submit_video_url(video_url: VideoURL, background_tasks: BackgroundTasks):
    process_id = generate_id()
    processes[process_id] = {
        'status': 'queued',
        'tags': None,
        'url': video_url.url
    }
    background_tasks.add_task(process_video, process_id)
    return VideoResponse(id=process_id)

@app.get("/video/{process_id}", response_model=StatusResponse)
async def get_video_status(process_id: str):
    process = processes.get(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process ID not found")
    if process['status'] == 'done':
        return StatusResponse(status=process['status'], tags=process['tags'])
    else:
        return StatusResponse(status=process['status'])
