#!/usr/bin/env python3

"""
API v1 router for Jarvis smart CV pipeline.

This module provides the main analysis endpoint for unified processing.
"""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...models.base import AnalysisRequest, AnalysisResult, UnifiedDetection
from ...core.smart_pipeline import SmartCVPipeline
from ...processor_manager import ensure_processors_initialized

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

# Global pipeline instance (will be set by main server)
smart_pipeline: Optional[SmartCVPipeline] = None


class AnalysisRequestModel(BaseModel):
    """Pydantic model for analysis requests"""
    classifiers: list[str] = Field(..., description="List of classifiers to use")
    options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")
    filters: Optional[Dict[str, Any]] = Field(None, description="Detection filters")
    frame_id: Optional[int] = Field(None, description="Frame ID for tracking")
    client_id: Optional[str] = Field(None, description="Client identifier")


class AnalysisResponseModel(BaseModel):
    """Pydantic model for analysis responses"""
    frame_id: int
    timestamp: float
    processing_time_ms: float
    detections: Dict[str, list[Dict[str, Any]]]
    frame_resolution: list[int]
    pipeline_info: Dict[str, Any]
    cache_hit: bool
    detection_count: int


def set_pipeline(pipeline: SmartCVPipeline):
    """Set the global pipeline instance"""
    global smart_pipeline
    smart_pipeline = pipeline


@router.post("analyze", response_model=AnalysisResponseModel)
async def analyze(request: AnalysisRequestModel):
    """
    Unified analysis endpoint for computer vision processing.
    
    This endpoint intelligently processes requests using multiple classifiers
    and returns comprehensive detection results with 3D positioning.
    """
    # Ensure processors are initialized on-demand
    try:
        ensure_processors_initialized()
    except Exception as e:
        logger.error(f"Failed to initialize processors: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to initialize camera processors: {str(e)}")
    
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        # Convert Pydantic model to internal model
        analysis_request = AnalysisRequest(
            classifiers=request.classifiers,
            options=request.options,
            filters=request.filters,
            frame_id=request.frame_id,
            client_id=request.client_id
        )
        
        # Process the request
        result = await smart_pipeline.process_request(analysis_request)
        
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
        
        # Create response
        response = AnalysisResponseModel(
            frame_id=result.frame_id,
            timestamp=result.timestamp,
            processing_time_ms=result.processing_time_ms,
            detections=detections_data,
            frame_resolution=list(result.frame_resolution),
            pipeline_info=result.pipeline_info,
            cache_hit=result.cache_hit,
            detection_count=result.get_total_detections()
        )
        
        logger.info(f"[API] Analysis completed: {response.detection_count} detections in {response.processing_time_ms:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"[API] Error in analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analyze/status")
async def get_analysis_status():
    """Get current analysis pipeline status"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        info = smart_pipeline.get_pipeline_info()
        return {
            "status": "running" if info["is_running"] else "stopped",
            "pipeline_info": info,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"[API] Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/analyze/test")
async def test_analysis():
    """Test analysis endpoint with default parameters"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        # Create test request
        test_request = AnalysisRequestModel(
            classifiers=["person"],
            options={
                "confidence_threshold": 0.5,
                "include_depth": True,
                "include_3d_position": True,
                "max_detections": 10
            },
            filters={
                "min_confidence": 0.3,
                "max_distance_mm": 5000
            }
        )
        
        # Process test request
        result = await analyze(test_request)
        
        return {
            "message": "Test analysis completed successfully",
            "result": result,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"[API] Error in test analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Test analysis failed: {str(e)}")
