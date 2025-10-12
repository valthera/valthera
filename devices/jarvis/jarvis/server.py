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

# Global processors
center_depth_processor: Optional[CenterDepthProcessor] = None
smart_pipeline: Optional[SmartCVPipeline] = None


@app.on_event("startup")
async def startup_event():
    """Initialize processors on startup"""
    global center_depth_processor, smart_pipeline
    
    logger.info("Starting Jarvis Smart CV Pipeline...")
    
    try:
        # Start WebSocket manager
        await start_websocket_manager()
        logger.info("WebSocket manager started")
        
        # Initialize processors in background to avoid blocking
        def init_in_background():
            global center_depth_processor, smart_pipeline
            try:
                # Initialize center depth processor
                logger.info("Initializing center depth processor...")
                center_depth_processor = CenterDepthProcessor()
                center_depth_processor.start()
                logger.info("Center depth processor started")
                
                # Initialize smart CV pipeline with existing depth camera
                logger.info("Initializing smart CV pipeline...")
                existing_depth_camera = center_depth_processor.get_depth_camera()
                smart_pipeline = SmartCVPipeline(depth_camera=existing_depth_camera)
                smart_pipeline.start()
                logger.info("Smart CV pipeline started")
                
                # Set up detection callback for WebSocket broadcasting
                def on_detection(result):
                    try:
                        # Try to get the current event loop
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Schedule the coroutine to run
                            asyncio.run_coroutine_threadsafe(broadcast_analysis_result(result), loop)
                        else:
                            # If no running loop, just log the result
                            logger.info(f"[CALLBACK] Detection result: {result.get_total_detections()} objects")
                    except RuntimeError:
                        # No event loop available, just log
                        logger.info(f"[CALLBACK] Detection result: {result.get_total_detections()} objects")
                
                smart_pipeline.set_detection_callback(on_detection)
                logger.info("Detection callback configured")
                
                # Set pipeline in API modules
                from .api.v1.analyze import set_pipeline as set_analyze_pipeline
                from .api.v1.stream import set_pipeline as set_stream_pipeline
                from .api.v1.pipeline import set_pipeline as set_pipeline_pipeline
                from .api.v1.classifiers import set_pipeline as set_classifiers_pipeline
                from .api.v1.frames import set_pipeline as set_frames_pipeline
                
                set_analyze_pipeline(smart_pipeline)
                set_stream_pipeline(smart_pipeline)
                set_pipeline_pipeline(smart_pipeline)
                set_classifiers_pipeline(smart_pipeline)
                set_frames_pipeline(smart_pipeline)
                
                logger.info("API modules configured with pipeline")
                
            except Exception as e:
                logger.error(f"Failed to initialize processors: {e}")
        
        # Start in a separate thread to avoid blocking the event loop
        threading.Thread(target=init_in_background, daemon=True).start()
        
    except Exception as e:
        logger.error(f"Failed to initialize processors during startup: {e}")
        logger.warning("Processors will not be available. Use /api/v1/pipeline/start to retry.")
    
    logger.info("Jarvis Smart CV Pipeline is ready!")


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