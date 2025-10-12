#!/usr/bin/env python3

"""
Models module for Jarvis smart CV pipeline.

This module provides data models and structures used throughout the system.
"""

from .base import (
    UnifiedDetection,
    AnalysisRequest,
    AnalysisResult,
    PipelineConfig,
    FrameMetadata,
    ClassifierStats,
    ClassifierType,
    create_detection_from_legacy,
    create_analysis_result_from_legacy
)

__all__ = [
    'UnifiedDetection',
    'AnalysisRequest',
    'AnalysisResult', 
    'PipelineConfig',
    'FrameMetadata',
    'ClassifierStats',
    'ClassifierType',
    'create_detection_from_legacy',
    'create_analysis_result_from_legacy'
]
