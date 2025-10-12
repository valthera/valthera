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

from .center_depth_processor import CenterDepthProcessor
from .core.smart_pipeline import SmartCVPipeline
from .api import api_v1_router
from .api.v1.stream import start_websocket_manager, stop_websocket_manager, broadcast_analysis_result
from .processor_manager import ensure_processors_initialized, get_processors, cleanup_processors

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

app = FastAPI(title="Jarvis Smart CV Pipeline", version="2.0.0")

# CORS for easy local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global processors (managed by processor_manager)
center_depth_processor: Optional[CenterDepthProcessor] = None
smart_pipeline: Optional[SmartCVPipeline] = None


@app.on_event("startup")
async def startup_event():
    """Initialize basic services on startup (without camera processing)"""
    global center_depth_processor, smart_pipeline
    
    logger.info("Starting Jarvis Smart CV Pipeline API...")
    
    try:
        # Start WebSocket manager
        await start_websocket_manager()
        logger.info("WebSocket manager started")
        
        # Initialize processors as None - will be created on-demand
        center_depth_processor = None
        smart_pipeline = None
        
        logger.info("API server ready. Camera processing will start on first request.")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")



@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup processors on shutdown"""
    global center_depth_processor, smart_pipeline
    
    logger.info("Shutting down Jarvis Smart CV Pipeline...")
    
    try:
        # Stop WebSocket manager
        await stop_websocket_manager()
        logger.info("WebSocket manager stopped")
        
        if smart_pipeline:
            smart_pipeline.cleanup()
            logger.info("Smart CV pipeline stopped")
            
        if center_depth_processor:
            center_depth_processor.cleanup()
            logger.info("Center depth processor stopped")
            
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Mount API v1 router
app.include_router(api_v1_router)


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Get current processor status from processor manager
    center_depth_processor, smart_pipeline = get_processors()
    
    status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0",
        "center_depth_processor": {
            "running": center_depth_processor.is_running if center_depth_processor else False,
            "available": center_depth_processor is not None
        },
        "smart_cv_pipeline": {
            "running": smart_pipeline.is_running if smart_pipeline else False,
            "available": smart_pipeline is not None
        }
    }
    
    logger.info(f"Health check: {status}")
    return JSONResponse(status)


@app.post("/api/v1/pipeline/initialize")
async def initialize_pipeline():
    """Manually initialize camera processors"""
    try:
        ensure_processors_initialized()
        return {
            "status": "success",
            "message": "Camera processors initialized successfully",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to initialize processors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize processors: {str(e)}")


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


@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "name": "Jarvis Smart CV Pipeline",
        "version": "2.0.0",
        "description": "Intelligent computer vision pipeline with multi-classifier support",
        "endpoints": {
            "health": "/health",
            "logs": "/logs",
            "api_v1": "/api/v1",
            "analyze": "/api/v1/analyze",
            "stream": "/api/v1/stream",
            "pipeline": "/api/v1/pipeline",
            "classifiers": "/api/v1/classifiers",
            "frames": "/api/v1/frames"
        }
    }


def main():
    """Main function for local testing"""
    import uvicorn
    logger.info(f"Starting Jarvis Smart CV Pipeline on port {HTTP_PORT}")
    uvicorn.run("jarvis.server:app", host="0.0.0.0", port=HTTP_PORT, reload=False)


if __name__ == "__main__":
    main()