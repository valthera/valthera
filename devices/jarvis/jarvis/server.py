#!/usr/bin/env python3

import asyncio
import logging
import os
import sys
import time
import threading
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .audio_processor import AudioProcessor
from .video_processor import VideoProcessor

# Configuration
HTTP_PORT = int(os.environ.get("JARVIS_HTTP_PORT", "8001"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/jarvis.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Jarvis Multi-Modal Agent", version="0.1.0")

# CORS for easy local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global processors
audio_processor: Optional[AudioProcessor] = None
video_processor: Optional[VideoProcessor] = None


@app.on_event("startup")
async def startup_event():
    """Initialize audio and video processors on startup"""
    global audio_processor, video_processor
    
    logger.info("Starting Jarvis multi-modal agent...")
    
    try:
        # Initialize audio processor
        logger.info("Initializing audio processor...")
        audio_processor = AudioProcessor()
        audio_processor.start()
        logger.info("Audio processor started")
        
        # Initialize video processor
        logger.info("Initializing video processor...")
        video_processor = VideoProcessor()
        video_processor.start()
        logger.info("Video processor started")
        
        logger.info("Jarvis multi-modal agent is ready!")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Continue running even if processors fail to initialize


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup processors on shutdown"""
    global audio_processor, video_processor
    
    logger.info("Shutting down Jarvis multi-modal agent...")
    
    try:
        if audio_processor:
            audio_processor.cleanup()
            logger.info("Audio processor stopped")
        
        if video_processor:
            video_processor.cleanup()
            logger.info("Video processor stopped")
            
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": time.time(),
        "audio_processor": {
            "running": audio_processor.is_running if audio_processor else False,
            "available": audio_processor is not None
        },
        "video_processor": {
            "running": video_processor.is_running if video_processor else False,
            "available": video_processor is not None,
            "person_count": video_processor.get_person_count() if video_processor else 0
        }
    }
    
    logger.info(f"Health check: {status}")
    return JSONResponse(status)


@app.get("/logs")
async def get_logs():
    """Get recent log entries"""
    try:
        with open('/tmp/jarvis.log', 'r') as f:
            lines = f.readlines()
            # Return last 100 lines
            recent_lines = lines[-100:] if len(lines) > 100 else lines
            return JSONResponse({
                "log_entries": recent_lines,
                "total_lines": len(lines),
                "showing_last": len(recent_lines)
            })
    except FileNotFoundError:
        return JSONResponse({"error": "Log file not found", "log_entries": []})
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return JSONResponse({"error": str(e), "log_entries": []})


@app.get("/status")
async def get_status():
    """Get detailed status of all processors"""
    status = {
        "timestamp": time.time(),
        "audio": {
            "running": audio_processor.is_running if audio_processor else False,
            "available": audio_processor is not None,
            "wake_word": "Jarvis",
            "transcription_available": audio_processor is not None
        },
        "video": {
            "running": video_processor.is_running if video_processor else False,
            "available": video_processor is not None,
            "person_count": video_processor.get_person_count() if video_processor else 0,
            "model": "YOLOv8n"
        }
    }
    
    return JSONResponse(status)


@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "name": "Jarvis Multi-Modal Agent",
        "version": "0.1.0",
        "description": "Wake word detection + speech-to-text + person detection",
        "endpoints": {
            "health": "/health",
            "logs": "/logs",
            "status": "/status"
        }
    }


def main():
    """Main function for local testing"""
    import uvicorn
    logger.info(f"Starting Jarvis server on port {HTTP_PORT}")
    uvicorn.run("jarvis.server:app", host="0.0.0.0", port=HTTP_PORT, reload=False)


if __name__ == "__main__":
    main()
