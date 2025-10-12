#!/usr/bin/env python3

"""
Object classifier for Jarvis smart CV pipeline.

This module provides general object detection using YOLO for all 80 COCO classes.
"""

import logging
import time
from typing import List, Optional, Any

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..classifiers.registry import BaseClassifier, ModelConfig
from ..models.base import UnifiedDetection

logger = logging.getLogger(__name__)

# COCO class names
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
    'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]


class ObjectClassifier(BaseClassifier):
    """YOLO-based object detector for all COCO classes"""
    
    def __init__(self, 
                 name: str = "object",
                 config: Optional[ModelConfig] = None):
        """
        Initialize the object classifier.
        
        Args:
            name: Classifier name
            config: Model configuration
        """
        if config is None:
            config = ModelConfig(
                name="object",
                path="yolov8n.pt",
                model_type="yolo",
                classes=None,  # All 80 COCO classes
                confidence_threshold=0.5
            )
        
        super().__init__(name, config)
        self.stats.model_version = config.version or "8.0"
    
    def _load_model(self) -> Any:
        """Load the YOLO model"""
        try:
            from ultralytics import YOLO
            model = YOLO(self.config.path)
            logger.info(f"[OBJECT_CLASSIFIER] YOLO model loaded: {self.config.path}")
            return model
        except ImportError:
            logger.error("[OBJECT_CLASSIFIER] YOLO not available")
            return None
        except Exception as e:
            logger.error(f"[OBJECT_CLASSIFIER] Error loading YOLO model: {e}")
            return None
    
    def detect(self, frame: np.ndarray) -> List[UnifiedDetection]:
        """
        Detect objects in the given frame.
        
        Args:
            frame: Input image as numpy array (BGR format)
            
        Returns:
            List of UnifiedDetection objects with bounding boxes
        """
        if not self.is_initialized or not self.model:
            return []
        
        if not NUMPY_AVAILABLE or frame is None:
            return []
        
        start_time = time.time()
        
        try:
            # Run YOLO inference
            results = self.model(frame, verbose=False)
            
            detections = []
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Check confidence threshold
                        if confidence >= self.config.confidence_threshold:
                            # Extract bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            
                            # Get class name
                            class_name = COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else f"class_{class_id}"
                            
                            detection = UnifiedDetection(
                                bbox=[int(x1), int(y1), int(x2), int(y2)],
                                confidence=confidence,
                                class_id=class_id,
                                class_name=class_name,
                                classifier_type=self.name,
                                depth_mm=None,  # Will be filled by pipeline
                                position_3d=None,  # Will be filled by pipeline
                                attributes=None,
                                processing_time_ms=None,  # Will be calculated
                                model_version=self.stats.model_version
                            )
                            detections.append(detection)
            
            # Update performance tracking
            processing_time = (time.time() - start_time) * 1000
            self.stats.update_stats(len(detections), processing_time)
            
            # Update processing time in detections
            for detection in detections:
                detection.processing_time_ms = processing_time / len(detections) if detections else processing_time
            
            return detections
            
        except Exception as e:
            logger.error(f"[OBJECT_CLASSIFIER] Error detecting objects: {e}")
            return []
    
    def detect_by_class(self, frame: np.ndarray, target_classes: List[str]) -> List[UnifiedDetection]:
        """
        Detect specific object classes in the given frame.
        
        Args:
            frame: Input image as numpy array (BGR format)
            target_classes: List of class names to detect
            
        Returns:
            List of UnifiedDetection objects for specified classes only
        """
        all_detections = self.detect(frame)
        
        # Filter by target classes
        filtered_detections = []
        for detection in all_detections:
            if detection.class_name in target_classes:
                filtered_detections.append(detection)
        
        return filtered_detections
    
    def get_detection_summary(self, detections: List[UnifiedDetection]) -> dict:
        """
        Get a summary of detections by class.
        
        Args:
            detections: List of UnifiedDetection objects
            
        Returns:
            Dictionary with class counts and confidence stats
        """
        class_counts = {}
        class_confidences = {}
        
        for detection in detections:
            class_name = detection.class_name
            
            if class_name not in class_counts:
                class_counts[class_name] = 0
                class_confidences[class_name] = []
            
            class_counts[class_name] += 1
            class_confidences[class_name].append(detection.confidence)
        
        # Calculate average confidence per class
        avg_confidences = {}
        for class_name, confidences in class_confidences.items():
            avg_confidences[class_name] = sum(confidences) / len(confidences)
        
        return {
            "class_counts": class_counts,
            "average_confidences": avg_confidences,
            "total_detections": len(detections)
        }


def main():
    """Test the object classifier"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("[OBJECT_CLASSIFIER] Testing ObjectClassifier...")
    
    # Initialize classifier
    classifier = ObjectClassifier()
    
    if not classifier.initialize():
        logger.error("[OBJECT_CLASSIFIER] Failed to initialize classifier")
        return
    
    logger.info(f"[OBJECT_CLASSIFIER] Available classes: {len(COCO_CLASSES)}")
    logger.info(f"[OBJECT_CLASSIFIER] Class names: {COCO_CLASSES[:10]}...")
    
    # Test with a sample frame (you would normally get this from camera)
    if NUMPY_AVAILABLE:
        # Create a dummy frame for testing
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = classifier.detect(dummy_frame)
        logger.info(f"[OBJECT_CLASSIFIER] Detected {len(detections)} objects")
        
        # Test class filtering
        person_detections = classifier.detect_by_class(dummy_frame, ["person", "car", "dog"])
        logger.info(f"[OBJECT_CLASSIFIER] Person/car/dog detections: {len(person_detections)}")
    
    classifier.cleanup()
    logger.info("[OBJECT_CLASSIFIER] Test completed")


if __name__ == "__main__":
    main()
