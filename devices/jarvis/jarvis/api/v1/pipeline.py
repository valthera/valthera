#!/usr/bin/env python3

"""
Pipeline control endpoints for Jarvis smart CV pipeline.

This module provides endpoints for controlling the pipeline state and configuration.
"""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models.base import PipelineConfig
from ...core.smart_pipeline import SmartCVPipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pipeline"])

# Global pipeline instance (will be set by main server)
smart_pipeline: Optional[SmartCVPipeline] = None


class PipelineConfigModel(BaseModel):
    """Pydantic model for pipeline configuration"""
    fps: int = 10
    confidence_threshold: float = 0.5
    max_detections: int = 10
    enabled_classifiers: list[str] = ["person"]
    include_depth: bool = True
    include_3d_position: bool = True
    include_annotated_frame: bool = False
    include_raw_frame: bool = False


def set_pipeline(pipeline: SmartCVPipeline):
    """Set the global pipeline instance"""
    global smart_pipeline
    smart_pipeline = pipeline


@router.get("/status")
async def get_status():
    """Get detailed system status"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        info = smart_pipeline.get_pipeline_info()
        
        return {
            "status": "running" if info["is_running"] else "stopped",
            "timestamp": time.time(),
            "pipeline_info": info,
            "websocket_stats": {
                "connections": 0,  # Will be updated by stream module
                "subscriptions": 0
            }
        }
    except Exception as e:
        logger.error(f"[API] Error getting status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/start")
async def start_pipeline():
    """Start the CV pipeline"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        if smart_pipeline.is_running:
            return {"status": "already_running", "message": "Pipeline already running"}
        
        smart_pipeline.start()
        logger.info("[API] Pipeline started via API")
        
        return {"status": "success", "message": "Pipeline started"}
        
    except Exception as e:
        logger.error(f"[API] Error starting pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


@router.post("/stop")
async def stop_pipeline():
    """Stop the CV pipeline"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        if not smart_pipeline.is_running:
            return {"status": "already_stopped", "message": "Pipeline already stopped"}
        
        smart_pipeline.stop()
        logger.info("[API] Pipeline stopped via API")
        
        return {"status": "success", "message": "Pipeline stopped"}
        
    except Exception as e:
        logger.error(f"[API] Error stopping pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop pipeline: {str(e)}")


@router.post("/reset")
async def reset_pipeline():
    """Reset the CV pipeline"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        # Stop and restart pipeline
        smart_pipeline.stop()
        time.sleep(0.1)  # Brief pause
        smart_pipeline.start()
        
        logger.info("[API] Pipeline reset via API")
        
        return {"status": "success", "message": "Pipeline reset"}
        
    except Exception as e:
        logger.error(f"[API] Error resetting pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset pipeline: {str(e)}")


@router.get("/config")
async def get_pipeline_config():
    """Get current pipeline configuration"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        info = smart_pipeline.get_pipeline_info()
        config = info.get("config", {})
        
        return {
            "config": config,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"[API] Error getting pipeline config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/config")
async def update_pipeline_config(config: PipelineConfigModel):
    """Update pipeline configuration"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        # Update configuration
        smart_pipeline.config.fps = config.fps
        smart_pipeline.config.confidence_threshold = config.confidence_threshold
        smart_pipeline.config.max_detections = config.max_detections
        smart_pipeline.config.enabled_classifiers = config.enabled_classifiers
        smart_pipeline.config.include_depth = config.include_depth
        smart_pipeline.config.include_3d_position = config.include_3d_position
        smart_pipeline.config.include_annotated_frame = config.include_annotated_frame
        smart_pipeline.config.include_raw_frame = config.include_raw_frame
        
        # Update process interval
        smart_pipeline.process_interval = 1.0 / config.fps
        
        logger.info(f"[API] Pipeline config updated: {config.dict()}")
        
        return {
            "status": "success", 
            "message": "Configuration updated",
            "config": config.dict()
        }
        
    except Exception as e:
        logger.error(f"[API] Error updating pipeline config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    if not smart_pipeline:
        return {
            "status": "unhealthy",
            "message": "Smart CV pipeline not available",
            "timestamp": time.time()
        }
    
    try:
        info = smart_pipeline.get_pipeline_info()
        
        return {
            "status": "healthy" if info["is_running"] else "degraded",
            "pipeline_running": info["is_running"],
            "depth_camera_available": info["depth_camera_available"],
            "enabled_classifiers": len(info["config"]["enabled_classifiers"]),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"[API] Error in health check: {e}")
        return {
            "status": "unhealthy",
            "message": str(e),
            "timestamp": time.time()
        }
