#!/usr/bin/env python3

"""
Base data models for Jarvis smart CV pipeline.

This module defines the core data structures used throughout the system
for unified detection, analysis requests, and results.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class ClassifierType(Enum):
    """Available classifier types"""
    PERSON = "person"
    OBJECT = "object"
    FACE = "face"
    GESTURE = "gesture"
    POSE = "pose"
    EMOTION = "emotion"


@dataclass
class UnifiedDetection:
    """Unified detection format for all classifiers"""
    # Core detection data
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str
    classifier_type: str  # "person", "object", "face", etc.
    
    # 3D information
    depth_mm: Optional[float] = None
    position_3d: Optional[Dict[str, float]] = None
    
    # Extended attributes
    attributes: Optional[Dict[str, Any]] = None  # Pose, emotion, etc.
    
    # Metadata
    processing_time_ms: Optional[float] = None
    model_version: Optional[str] = None
    
    def __post_init__(self):
        """Validate detection data after initialization"""
        if len(self.bbox) != 4:
            raise ValueError("bbox must contain exactly 4 coordinates [x1, y1, x2, y2]")
        
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        
        if self.position_3d and len(self.position_3d) != 3:
            raise ValueError("position_3d must contain exactly 3 coordinates [x, y, z]")


@dataclass
class AnalysisRequest:
    """Request for analysis"""
    classifiers: List[str]
    options: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    frame_id: Optional[int] = None
    client_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Validate request data"""
        if not self.classifiers:
            raise ValueError("classifiers list cannot be empty")
        
        # Validate classifier names
        valid_classifiers = [ct.value for ct in ClassifierType]
        for classifier in self.classifiers:
            if classifier not in valid_classifiers:
                raise ValueError(f"Invalid classifier: {classifier}. Valid options: {valid_classifiers}")


@dataclass
class AnalysisResult:
    """Comprehensive analysis result"""
    frame_id: int
    timestamp: float
    processing_time_ms: float
    
    # Organized by classifier type
    detections: Dict[str, List[UnifiedDetection]]
    
    # Frame data
    frame_resolution: Tuple[int, int]
    annotated_frame: Optional[np.ndarray] = None
    
    # Metadata
    pipeline_info: Dict[str, Any] = field(default_factory=dict)
    cache_hit: bool = False
    
    def get_total_detections(self) -> int:
        """Get total number of detections across all classifiers"""
        return sum(len(detections) for detections in self.detections.values())
    
    def get_detections_by_classifier(self, classifier_type: str) -> List[UnifiedDetection]:
        """Get detections for a specific classifier type"""
        return self.detections.get(classifier_type, [])
    
    def has_detections(self) -> bool:
        """Check if any detections were found"""
        return self.get_total_detections() > 0


@dataclass
class PipelineConfig:
    """Pipeline configuration management"""
    # Processing settings
    fps: int = 10
    confidence_threshold: float = 0.5
    max_detections: int = 10
    
    # Frame settings
    width: int = 640
    height: int = 480
    
    # Cache settings
    cache_ttl_seconds: float = 1.0
    cache_max_size: int = 100
    
    # Classifier settings
    enabled_classifiers: List[str] = field(default_factory=lambda: ["person"])
    
    # Depth settings
    include_depth: bool = True
    include_3d_position: bool = True
    
    # Output settings
    include_annotated_frame: bool = False
    include_raw_frame: bool = False
    
    def __post_init__(self):
        """Validate configuration"""
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        
        if self.max_detections <= 0:
            raise ValueError("max_detections must be positive")
        
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")


@dataclass
class FrameMetadata:
    """Metadata about a processed frame"""
    frame_id: int
    timestamp: float
    resolution: Tuple[int, int]
    camera_intrinsics: Optional[Dict[str, float]] = None
    processing_pipeline: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "resolution": list(self.resolution),
            "camera_intrinsics": self.camera_intrinsics,
            "processing_pipeline": self.processing_pipeline
        }


@dataclass
class ClassifierStats:
    """Statistics for a classifier"""
    name: str
    is_enabled: bool
    total_detections: int = 0
    last_detection_time: float = 0.0
    average_processing_time_ms: float = 0.0
    model_version: Optional[str] = None
    
    def update_stats(self, detections_count: int, processing_time_ms: float):
        """Update statistics with new detection data"""
        self.total_detections += detections_count
        self.last_detection_time = time.time()
        
        # Update average processing time
        if self.average_processing_time_ms == 0:
            self.average_processing_time_ms = processing_time_ms
        else:
            # Simple moving average
            self.average_processing_time_ms = (
                self.average_processing_time_ms * 0.9 + processing_time_ms * 0.1
            )


def create_detection_from_legacy(detection, classifier_type: str, depth_mm: float = None, position_3d: Dict = None) -> UnifiedDetection:
    """Convert legacy Detection to UnifiedDetection"""
    return UnifiedDetection(
        bbox=detection.bbox,
        confidence=detection.confidence,
        class_id=detection.class_id,
        class_name=detection.class_name,
        classifier_type=classifier_type,
        depth_mm=depth_mm,
        position_3d=position_3d,
        attributes=None,
        processing_time_ms=None,
        model_version=None
    )


def create_analysis_result_from_legacy(cv_result, detections_by_classifier: Dict[str, List[UnifiedDetection]], processing_time_ms: float) -> AnalysisResult:
    """Convert legacy CVPipelineResult to AnalysisResult"""
    return AnalysisResult(
        frame_id=cv_result.frame_id,
        timestamp=cv_result.timestamp,
        processing_time_ms=processing_time_ms,
        detections=detections_by_classifier,
        frame_resolution=(640, 480),  # Default resolution
        annotated_frame=cv_result.annotated_frame,
        pipeline_info={"legacy_conversion": True},
        cache_hit=False
    )
