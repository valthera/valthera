#!/usr/bin/env python3

"""
Classifier module for Jarvis CV pipeline.

This module provides YOLO-based object detection capabilities,
specifically optimized for person detection with bounding boxes.
"""

from .person_classifier import PersonClassifier

__all__ = ['PersonClassifier']
