#!/usr/bin/env python3

"""
API v1 module for Jarvis smart CV pipeline.

This module provides the unified API endpoints for the smart CV pipeline.
"""

from fastapi import APIRouter

from .analyze import router as analyze_router
from .stream import router as stream_router
from .pipeline import router as pipeline_router
from .classifiers import router as classifiers_router
from .frames import router as frames_router

# Create main API v1 router
api_v1_router = APIRouter(prefix="/api/v1")

# Include all sub-routers with their respective prefixes
api_v1_router.include_router(analyze_router, prefix="/analyze", tags=["analysis"])
api_v1_router.include_router(stream_router, prefix="/stream", tags=["streaming"])
api_v1_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
api_v1_router.include_router(classifiers_router, prefix="/classifiers", tags=["classifiers"])
api_v1_router.include_router(frames_router, prefix="/frames", tags=["frames"])

__all__ = ['api_v1_router']
