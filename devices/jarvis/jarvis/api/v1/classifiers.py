#!/usr/bin/env python3

"""
Classifier management endpoints for Jarvis smart CV pipeline.

This module provides endpoints for managing and configuring classifiers.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...classifiers.registry import get_registry, ClassifierRegistry
from ...core.smart_pipeline import SmartCVPipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["classifiers"])

# Global pipeline instance (will be set by main server)
smart_pipeline: Optional[SmartCVPipeline] = None


class ClassifierConfigModel(BaseModel):
    """Pydantic model for classifier configuration"""
    confidence_threshold: float = 0.5
    enabled: bool = True
    model_version: Optional[str] = None


def set_pipeline(pipeline: SmartCVPipeline):
    """Set the global pipeline instance"""
    global smart_pipeline
    smart_pipeline = pipeline


@router.get("/classifiers")
async def list_classifiers():
    """List all available classifiers"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        registry = smart_pipeline.registry
        classifiers = registry.list_classifiers()
        
        return {
            "classifiers": classifiers,
            "total_count": len(classifiers),
            "enabled_count": len([c for c in classifiers if c["enabled"]]),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"[API] Error listing classifiers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list classifiers: {str(e)}")


@router.get("/classifiers/{name}")
async def get_classifier(name: str):
    """Get information about a specific classifier"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        registry = smart_pipeline.registry
        classifier = registry.get_classifier(name)
        
        if not classifier:
            raise HTTPException(status_code=404, detail=f"Classifier '{name}' not found")
        
        return {
            "name": name,
            "stats": classifier.get_stats(),
            "timestamp": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error getting classifier {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get classifier: {str(e)}")


@router.post("/classifiers/{name}/config")
async def configure_classifier(name: str, config: ClassifierConfigModel):
    """Configure a specific classifier"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        registry = smart_pipeline.registry
        classifier = registry.get_classifier(name)
        
        if not classifier:
            raise HTTPException(status_code=404, detail=f"Classifier '{name}' not found")
        
        # Update configuration
        if hasattr(classifier, 'set_confidence_threshold'):
            classifier.set_confidence_threshold(config.confidence_threshold)
        
        classifier.set_enabled(config.enabled)
        
        logger.info(f"[API] Classifier {name} configured: {config.dict()}")
        
        return {
            "status": "success",
            "message": f"Classifier '{name}' configured",
            "config": config.dict(),
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error configuring classifier {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure classifier: {str(e)}")


@router.post("/classifiers/{name}/enable")
async def enable_classifier(name: str):
    """Enable a specific classifier"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        registry = smart_pipeline.registry
        classifier = registry.get_classifier(name)
        
        if not classifier:
            raise HTTPException(status_code=404, detail=f"Classifier '{name}' not found")
        
        classifier.set_enabled(True)
        
        logger.info(f"[API] Classifier {name} enabled")
        
        return {
            "status": "success",
            "message": f"Classifier '{name}' enabled",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error enabling classifier {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable classifier: {str(e)}")


@router.post("/classifiers/{name}/disable")
async def disable_classifier(name: str):
    """Disable a specific classifier"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        registry = smart_pipeline.registry
        classifier = registry.get_classifier(name)
        
        if not classifier:
            raise HTTPException(status_code=404, detail=f"Classifier '{name}' not found")
        
        classifier.set_enabled(False)
        
        logger.info(f"[API] Classifier {name} disabled")
        
        return {
            "status": "success",
            "message": f"Classifier '{name}' disabled",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error disabling classifier {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable classifier: {str(e)}")


@router.post("/classifiers/{name}/initialize")
async def initialize_classifier(name: str):
    """Initialize a specific classifier"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        registry = smart_pipeline.registry
        success = registry.initialize_classifier(name)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to initialize classifier '{name}'")
        
        logger.info(f"[API] Classifier {name} initialized")
        
        return {
            "status": "success",
            "message": f"Classifier '{name}' initialized",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error initializing classifier {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize classifier: {str(e)}")


@router.get("/classifiers/stats")
async def get_classifier_stats():
    """Get statistics for all classifiers"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        registry = smart_pipeline.registry
        stats = registry.get_registry_stats()
        
        return {
            "registry_stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"[API] Error getting classifier stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get classifier stats: {str(e)}")


@router.get("/classifiers/types")
async def get_classifier_types():
    """Get available classifier types"""
    if not smart_pipeline:
        raise HTTPException(status_code=503, detail="Smart CV pipeline not available")
    
    try:
        registry = smart_pipeline.registry
        stats = registry.get_registry_stats()
        
        return {
            "available_types": stats.get("available_types", []),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"[API] Error getting classifier types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get classifier types: {str(e)}")
