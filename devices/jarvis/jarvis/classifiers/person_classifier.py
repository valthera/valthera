#!/usr/bin/env python3

import logging
import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: YOLO not available")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: NumPy not available")

from ..classifiers.registry import BaseClassifier, ModelConfig
from ..models.base import UnifiedDetection

logger = logging.getLogger(__name__)

@dataclass
class Detection:
    """Container for a single detection result (legacy compatibility)"""
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str

class PersonClassifier(BaseClassifier):
    """YOLO-based person detector with bounding box support"""
    
    def __init__(self, 
                 name: str = "person",
                 config: Optional[ModelConfig] = None,
                 person_class_id: int = 0):
        """
        Initialize the person classifier.
        
        Args:
            name: Classifier name
            config: Model configuration
            person_class_id: COCO class ID for person (default: 0)
        """
        if config is None:
            config = ModelConfig(
                name="person",
                path="yolov8n.pt",
                model_type="yolo",
                classes=[person_class_id],
                confidence_threshold=0.5
            )
        
        super().__init__(name, config)
        self.person_class_id = person_class_id
        self.stats.model_version = config.version or "8.0"
    
    def _load_model(self) -> Any:
        """Load the YOLO model"""
        try:
            if YOLO_AVAILABLE:
                # Load YOLOv8n model (nano - fastest for Jetson)
                model = YOLO(self.config.path)
                logger.info(f"[CLASSIFIER] YOLOv8n model loaded: {self.config.path}")
                return model
            else:
                logger.error("[CLASSIFIER] YOLO not available - person detection disabled")
                return None
        except Exception as e:
            logger.error(f"[CLASSIFIER] Error loading YOLO model: {e}")
            return None
    
    def detect(self, frame: np.ndarray) -> List[UnifiedDetection]:
        """
        Detect people in the given frame.
        
        Args:
            frame: Input image as numpy array (BGR format)
            
        Returns:
            List of UnifiedDetection objects with bounding boxes
        """
        if not self.is_initialized or not YOLO_AVAILABLE or not self.model:
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
                        # Check if detected object is a person
                        class_id = int(box.cls[0])
                        if class_id == self.person_class_id:
                            confidence = float(box.conf[0])
                            
                            # Check confidence threshold
                            if confidence >= self.config.confidence_threshold:
                                # Extract bounding box coordinates
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                                
                                detection = UnifiedDetection(
                                    bbox=[int(x1), int(y1), int(x2), int(y2)],
                                    confidence=confidence,
                                    class_id=class_id,
                                    class_name="person",
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
            logger.error(f"[CLASSIFIER] Error detecting people: {e}")
            return []
    
    def annotate_frame(self, frame: np.ndarray, detections: List[UnifiedDetection]) -> np.ndarray:
        """
        Draw bounding boxes and labels on the frame.
        
        Args:
            frame: Input image as numpy array
            detections: List of UnifiedDetection objects
            
        Returns:
            Annotated frame with bounding boxes drawn
        """
        if not CV2_AVAILABLE or frame is None:
            return frame
        
        annotated_frame = frame.copy()
        
        try:
            for detection in detections:
                x1, y1, x2, y2 = detection.bbox
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw label with confidence
                label = f"{detection.class_name}: {detection.confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                
                # Draw label background
                cv2.rectangle(annotated_frame, 
                             (x1, y1 - label_size[1] - 10), 
                             (x1 + label_size[0], y1), 
                             (0, 255, 0), -1)
                
                # Draw label text
                cv2.putText(annotated_frame, label, 
                           (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            return annotated_frame
            
        except Exception as e:
            logger.error(f"[CLASSIFIER] Error annotating frame: {e}")
            return frame
    
    def annotate_frame_legacy(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Draw bounding boxes and labels on the frame (legacy compatibility).
        
        Args:
            frame: Input image as numpy array
            detections: List of legacy Detection objects
            
        Returns:
            Annotated frame with bounding boxes drawn
        """
        if not CV2_AVAILABLE or frame is None:
            return frame
        
        annotated_frame = frame.copy()
        
        try:
            for detection in detections:
                x1, y1, x2, y2 = detection.bbox
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw label with confidence
                label = f"{detection.class_name}: {detection.confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                
                # Draw label background
                cv2.rectangle(annotated_frame, 
                             (x1, y1 - label_size[1] - 10), 
                             (x1 + label_size[0], y1), 
                             (0, 255, 0), -1)
                
                # Draw label text
                cv2.putText(annotated_frame, label, 
                           (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            return annotated_frame
            
        except Exception as e:
            logger.error(f"[CLASSIFIER] Error annotating frame: {e}")
            return frame
    
    def set_confidence_threshold(self, threshold: float):
        """Update confidence threshold"""
        self.config.confidence_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"[CLASSIFIER] Confidence threshold set to {self.config.confidence_threshold}")
    
    def detect_legacy(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect people in the given frame (legacy compatibility).
        
        Args:
            frame: Input image as numpy array (BGR format)
            
        Returns:
            List of legacy Detection objects with bounding boxes
        """
        unified_detections = self.detect(frame)
        
        # Convert to legacy format
        legacy_detections = []
        for detection in unified_detections:
            legacy_detection = Detection(
                bbox=detection.bbox,
                confidence=detection.confidence,
                class_id=detection.class_id,
                class_name=detection.class_name
            )
            legacy_detections.append(legacy_detection)
        
        return legacy_detections


def main():
    """Test the person classifier"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("[CLASSIFIER] Testing PersonClassifier...")
    
    # Initialize classifier
    classifier = PersonClassifier()
    
    if not classifier.initialize():
        logger.error("[CLASSIFIER] Failed to initialize classifier")
        return
    
    # Test with webcam if available
    if not CV2_AVAILABLE:
        logger.error("[CLASSIFIER] OpenCV not available for camera test")
        return
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("[CLASSIFIER] No camera available for testing")
        return
    
    logger.info("[CLASSIFIER] Starting detection test... Press 'q' to quit")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("[CLASSIFIER] Failed to read frame")
                continue
            
            # Detect people
            detections = classifier.detect(frame)
            
            # Annotate frame
            annotated_frame = classifier.annotate_frame(frame, detections)
            
            # Display frame
            cv2.imshow('Person Detection Test', annotated_frame)
            
            # Log detections
            if detections:
                logger.info(f"[CLASSIFIER] Detected {len(detections)} person(s)")
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        logger.info("[CLASSIFIER] Stopping test...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        classifier.cleanup()
        logger.info("[CLASSIFIER] Test completed")


if __name__ == "__main__":
    main()
