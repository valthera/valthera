#!/usr/bin/env python3

"""
Classifiers module for Jarvis smart CV pipeline.

This module provides various AI classifiers for object detection,
face detection, and other computer vision tasks.
"""

from .registry import BaseClassifier, ClassifierRegistry, SharedModelManager, ModelConfig, get_registry, cleanup_registry
from .person_classifier import PersonClassifier, Detection
from .object_classifier import ObjectClassifier, COCO_CLASSES
from .face_classifier import FaceClassifier

__all__ = [
    'BaseClassifier',
    'ClassifierRegistry', 
    'SharedModelManager',
    'ModelConfig',
    'PersonClassifier',
    'Detection',  # Legacy compatibility
    'ObjectClassifier',
    'COCO_CLASSES',
    'FaceClassifier',
    'get_registry',
    'cleanup_registry'
]
