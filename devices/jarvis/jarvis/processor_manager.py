#!/usr/bin/env python3

"""
Processor initialization utilities for Jarvis.

This module provides functions to initialize camera processors on-demand
to avoid circular imports.
"""

import logging
import threading
import asyncio
from typing import Optional

from .center_depth_processor import CenterDepthProcessor
from .core.smart_pipeline import SmartCVPipeline
from .api.v1.stream import broadcast_analysis_result

logger = logging.getLogger(__name__)

# Global processors
center_depth_processor: Optional[CenterDepthProcessor] = None
smart_pipeline: Optional[SmartCVPipeline] = None

def ensure_processors_initialized():
    """Initialize processors on-demand if not already initialized"""
    global center_depth_processor, smart_pipeline
    
    if center_depth_processor is None or smart_pipeline is None:
        logger.info("Initializing camera processors on-demand...")
        
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
            raise

def get_processors():
    """Get the current processor instances"""
    return center_depth_processor, smart_pipeline

def cleanup_processors():
    """Cleanup processors on shutdown"""
    global center_depth_processor, smart_pipeline
    
    try:
        if smart_pipeline:
            logger.info("Stopping smart CV pipeline...")
            smart_pipeline.stop()
            smart_pipeline = None
            
        if center_depth_processor:
            logger.info("Stopping center depth processor...")
            center_depth_processor.stop()
            center_depth_processor = None
            
        logger.info("Processors cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error during processor cleanup: {e}")
