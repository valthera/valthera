#!/usr/bin/env python3

"""
Frame access endpoints for Jarvis smart CV pipeline.

This module provides endpoints for accessing frames, depth maps, and other visual data.
"""

import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from ...core.smart_pipeline import SmartCVPipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["frames"])

# Global pipeline instance (will be set by main server)
smart_pipeline: Optional[SmartCVPipeline] = None


def set_pipeline(pipeline: SmartCVPipeline):
    """Set the global pipeline instance"""
    global smart_pipeline
    smart_pipeline = pipeline


@router.get("/latest")
async def get_latest_result():
    """Get the latest analysis result"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        result = smart_pipeline.get_latest_result()
        if not result:
            return {"message": "No analysis result available", "timestamp": time.time()}
        
        # Convert detections to JSON-serializable format
        detections_data = {}
        for classifier_type, detections in result.detections.items():
            detections_data[classifier_type] = []
            for detection in detections:
                detection_data = {
                    "bbox": detection.bbox,
                    "confidence": detection.confidence,
                    "class_id": detection.class_id,
                    "class_name": detection.class_name,
                    "classifier_type": detection.classifier_type,
                    "depth_mm": detection.depth_mm,
                    "position_3d": detection.position_3d,
                    "attributes": detection.attributes,
                    "processing_time_ms": detection.processing_time_ms,
                    "model_version": detection.model_version
                }
                detections_data[classifier_type].append(detection_data)
        
        return {
            "frame_id": result.frame_id,
            "timestamp": result.timestamp,
            "processing_time_ms": result.processing_time_ms,
            "detections": detections_data,
            "frame_resolution": list(result.frame_resolution),
            "pipeline_info": result.pipeline_info,
            "cache_hit": result.cache_hit,
            "detection_count": result.get_total_detections()
        }
        
    except Exception as e:
        logger.error(f"[API] Error getting latest result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest result: {str(e)}")


@router.get("/frame/annotated")
async def get_annotated_frame():
    """Get the latest annotated frame as JPEG"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        result = smart_pipeline.get_latest_result()
        if not result or not result.annotated_frame:
            raise HTTPException(status_code=404, detail="No annotated frame available")
        
        if not CV2_AVAILABLE:
            raise HTTPException(status_code=503, detail="OpenCV not available for image encoding")
        
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', result.annotated_frame)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error encoding annotated frame: {e}")
        raise HTTPException(status_code=500, detail=f"Error encoding frame: {str(e)}")


@router.get("/frame/raw")
async def get_raw_frame():
    """Get the latest raw frame as JPEG"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        if not smart_pipeline.depth_camera:
            raise HTTPException(status_code=503, detail="Depth camera not available")
        
        depth_frame = smart_pipeline.depth_camera.get_latest_frame()
        if not depth_frame or depth_frame.color_frame is None:
            raise HTTPException(status_code=404, detail="No raw frame available")
        
        if not CV2_AVAILABLE:
            raise HTTPException(status_code=503, detail="OpenCV not available for image encoding")
        
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', depth_frame.color_frame)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error encoding raw frame: {e}")
        raise HTTPException(status_code=500, detail=f"Error encoding frame: {str(e)}")


@router.get("/depth/map")
async def get_depth_map():
    """Get the latest depth map as JPEG"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        if not smart_pipeline.depth_camera:
            raise HTTPException(status_code=503, detail="Depth camera not available")
        
        depth_frame = smart_pipeline.depth_camera.get_latest_frame()
        if not depth_frame or depth_frame.depth_frame is None:
            raise HTTPException(status_code=404, detail="No depth map available")
        
        if not CV2_AVAILABLE:
            raise HTTPException(status_code=503, detail="OpenCV not available for image encoding")
        
        # Normalize depth map for visualization
        depth_normalized = cv2.normalize(depth_frame.depth_frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
        # Apply colormap for better visualization
        depth_colored = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_JET)
        
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', depth_colored)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error encoding depth map: {e}")
        raise HTTPException(status_code=500, detail=f"Error encoding depth map: {str(e)}")


@router.get("/depth/data")
async def get_depth_data():
    """Get the latest depth data as JSON"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        if not smart_pipeline.depth_camera:
            raise HTTPException(status_code=503, detail="Depth camera not available")
        
        depth_frame = smart_pipeline.depth_camera.get_latest_frame()
        if not depth_frame:
            raise HTTPException(status_code=404, detail="No depth data available")
        
        return {
            "frame_id": depth_frame.frame_id,
            "timestamp": depth_frame.timestamp,
            "resolution": list(depth_frame.depth_frame.shape) if depth_frame.depth_frame is not None else None,
            "intrinsics": depth_frame.intrinsics,
            "has_color_frame": depth_frame.color_frame is not None,
            "has_depth_frame": depth_frame.depth_frame is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error getting depth data: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting depth data: {str(e)}")


@router.get("/frame/info")
async def get_frame_info():
    """Get information about the latest frame"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        result = smart_pipeline.get_latest_result()
        if not result:
            return {"message": "No frame information available", "timestamp": time.time()}
        
        return {
            "frame_id": result.frame_id,
            "timestamp": result.timestamp,
            "resolution": list(result.frame_resolution),
            "processing_time_ms": result.processing_time_ms,
            "pipeline_info": result.pipeline_info,
            "detection_count": result.get_total_detections(),
            "cache_hit": result.cache_hit
        }
        
    except Exception as e:
        logger.error(f"[API] Error getting frame info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting frame info: {str(e)}")
