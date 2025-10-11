#!/usr/bin/env python3

import asyncio
import logging
import os
import sys
import time
import threading
import json
import queue
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .audio_processor import AudioProcessor
from .video_processor import VideoProcessor
from .center_depth_processor import CenterDepthProcessor

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
center_depth_processor: Optional[CenterDepthProcessor] = None

# WebSocket connection management
active_connections: set[WebSocket] = set()
main_event_loop: Optional[asyncio.AbstractEventLoop] = None
depth_data_queue: asyncio.Queue = asyncio.Queue()


@app.on_event("startup")
async def startup_event():
    """Initialize processors on startup"""
    global audio_processor, video_processor, center_depth_processor, main_event_loop
    
    # Store reference to main event loop
    main_event_loop = asyncio.get_running_loop()
    
    logger.info("Starting Jarvis multi-modal agent...")
    
    # Automatically initialize depth processor in background
    try:
        # Start background task to process depth data queue
        asyncio.create_task(process_depth_queue())
        logger.info("Depth queue processor started")
        
        # Initialize center depth processor in background to avoid blocking
        def init_in_background():
            global center_depth_processor
            try:
                logger.info("Initializing center depth processor...")
                center_depth_processor = CenterDepthProcessor()
                center_depth_processor.start()
                logger.info("Center depth processor started")
                
                # Set up global depth update callback
                def on_depth_update(depth_data):
                    schedule_depth_broadcast(depth_data)
                
                center_depth_processor.set_depth_update_callback(on_depth_update)
                logger.info("Depth update callback configured")
            except Exception as e:
                logger.error(f"Failed to initialize depth processor: {e}")
        
        # Start in a separate thread to avoid blocking the event loop
        import threading
        threading.Thread(target=init_in_background, daemon=True).start()
        
    except Exception as e:
        logger.error(f"Failed to initialize depth processor during startup: {e}")
        logger.warning("Depth processor will not be available. Use /init-depth to retry.")
    
    logger.info("Jarvis multi-modal agent is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup processors on shutdown"""
    global audio_processor, video_processor, center_depth_processor
    
    logger.info("Shutting down Jarvis multi-modal agent...")
    
    try:
        if audio_processor:
            audio_processor.cleanup()
            logger.info("Audio processor stopped")
        
        if video_processor:
            video_processor.cleanup()
            logger.info("Video processor stopped")
        
        if center_depth_processor:
            center_depth_processor.cleanup()
            logger.info("Center depth processor stopped")
            
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
        },
        "center_depth_processor": {
            "running": center_depth_processor.is_running if center_depth_processor else False,
            "available": center_depth_processor is not None
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
        },
        "center_depth": {
            "running": center_depth_processor.is_running if center_depth_processor else False,
            "available": center_depth_processor is not None,
            "processor_info": center_depth_processor.get_processor_info() if center_depth_processor else {}
        }
    }
    
    return JSONResponse(status)


@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "name": "Jarvis Multi-Modal Agent",
        "version": "0.1.0",
        "description": "Wake word detection + speech-to-text + person detection + center depth streaming",
        "endpoints": {
            "health": "/health",
            "logs": "/logs",
            "status": "/status",
            "websocket": "/ws/center-depth"
        }
    }


async def broadcast_depth_data(depth_data):
    """Broadcast depth data to all connected WebSocket clients"""
    global active_connections
    
    if not active_connections:
        logger.info("No active WebSocket connections, skipping broadcast")
        return
    
    # Send JSON message with depth data
    message = {
        "type": "center_depth",
        "avg_depth": depth_data.avg_depth,
        "frame_id": depth_data.frame_id,
        "valid_pixels": depth_data.valid_pixels,
        "total_pixels": depth_data.total_pixels,
        "timestamp": depth_data.timestamp
    }
    
    logger.info(f"Broadcasting depth data to {len(active_connections)} clients: {depth_data.avg_depth:.1f}mm")
    
    # Send to all connected clients
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except WebSocketDisconnect:
            disconnected.add(connection)
        except Exception as e:
            logger.error(f"Error sending depth data to WebSocket client: {e}")
            disconnected.add(connection)
    
    # Remove disconnected clients
    active_connections -= disconnected


def schedule_depth_broadcast(depth_data):
    """Schedule depth data broadcast using queue"""
    try:
        logger.info(f"Queuing depth broadcast: {depth_data.avg_depth:.1f}mm")
        depth_data_queue.put_nowait(depth_data)
    except Exception as e:
        logger.error(f"Error queuing depth broadcast: {e}")


async def process_depth_queue():
    """Background task to process depth data queue"""
    logger.info("Starting depth queue processor...")
    
    while True:
        try:
            # Wait for depth data with timeout
            try:
                depth_data = await asyncio.wait_for(depth_data_queue.get(), timeout=1.0)
                await broadcast_depth_data(depth_data)
                depth_data_queue.task_done()
            except asyncio.TimeoutError:
                # No data available, continue
                await asyncio.sleep(0.1)
                continue
                
        except Exception as e:
            logger.error(f"Error processing depth queue: {e}")
            await asyncio.sleep(0.1)


@app.post("/init-depth")
async def init_depth():
    """Manually initialize depth processor"""
    global center_depth_processor
    
    try:
        if center_depth_processor and center_depth_processor.is_running:
            return {"status": "already_running", "message": "Depth processor already running"}
        
        # Start background task to process depth data queue
        asyncio.create_task(process_depth_queue())
        logger.info("Depth queue processor started")
        
        # Initialize center depth processor
        logger.info("Initializing center depth processor...")
        center_depth_processor = CenterDepthProcessor()
        center_depth_processor.start()
        logger.info("Center depth processor started")
        
        # Set up global depth update callback
        def on_depth_update(depth_data):
            schedule_depth_broadcast(depth_data)
        
        center_depth_processor.set_depth_update_callback(on_depth_update)
        logger.info("Depth update callback configured")
        
        return {"status": "success", "message": "Depth processor initialized"}
        
    except Exception as e:
        logger.error(f"Failed to initialize depth processor: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/test-websocket")
async def test_websocket():
    """Test WebSocket by sending dummy data"""
    global active_connections
    
    if not active_connections:
        return {"status": "no_connections", "message": "No WebSocket connections active"}
    
    # Send test data to all connected clients
    test_data = {
        "timestamp": time.time(),
        "avg_depth": 1234.5,
        "valid_pixels": 1000,
        "total_pixels": 1000,
        "frame_id": 999
    }
    
    await broadcast_depth_data(test_data)
    return {"status": "success", "message": f"Sent test data to {len(active_connections)} clients"}


@app.websocket("/ws/center-depth")
async def websocket_center_depth(websocket: WebSocket):
    """WebSocket endpoint for streaming center depth data"""
    global active_connections
    
    await websocket.accept()
    active_connections.add(websocket)
    
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    
    try:
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong or other commands)
                data = await websocket.receive_text()
                
                # Handle ping messages
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "get_latest":
                    # Send latest depth data immediately
                    if center_depth_processor:
                        latest_depth = center_depth_processor.get_latest_depth()
                        if latest_depth:
                            await broadcast_depth_data(latest_depth)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")


def main():
    """Main function for local testing"""
    import uvicorn
    logger.info(f"Starting Jarvis server on port {HTTP_PORT}")
    uvicorn.run("jarvis.server:app", host="0.0.0.0", port=HTTP_PORT, reload=False)


if __name__ == "__main__":
    main()
