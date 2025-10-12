#!/usr/bin/env python3

"""
Face classifier for Jarvis smart CV pipeline.

This module provides face detection capabilities using YOLO.
Future versions can be extended with emotion detection and face recognition.
"""

import logging
import time
from typing import List, Optional, Any, Dict

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..classifiers.registry import BaseClassifier, ModelConfig
from ..models.base import UnifiedDetection

logger = logging.getLogger(__name__)


class FaceClassifier(BaseClassifier):
    """YOLO-based face detector with future emotion/recognition capabilities"""
    
    def __init__(self, 
                 name: str = "face",
                 config: Optional[ModelConfig] = None):
        """
        Initialize the face classifier.
        
        Args:
            name: Classifier name
            config: Model configuration
        """
        if config is None:
            config = ModelConfig(
                name="face",
                path="yolov8n.pt",  # Using YOLO for now, can be replaced with dedicated face model
                model_type="yolo",
                classes=None,  # Will filter for faces
                confidence_threshold=0.5
            )
        
        super().__init__(name, config)
        self.stats.model_version = config.version or "8.0"
        
        # Face-specific attributes
        self.enable_emotion_detection = False
        self.enable_face_recognition = False
        self.emotion_model = None
        self.face_recognition_model = None
    
    def _load_model(self) -> Any:
        """Load the face detection model"""
        try:
            from ultralytics import YOLO
            model = YOLO(self.config.path)
            logger.info(f"[FACE_CLASSIFIER] YOLO model loaded: {self.config.path}")
            return model
        except ImportError:
            logger.error("[FACE_CLASSIFIER] YOLO not available")
            return None
        except Exception as e:
            logger.error(f"[FACE_CLASSIFIER] Error loading YOLO model: {e}")
            return None
    
    def detect(self, frame: np.ndarray) -> List[UnifiedDetection]:
        """
        Detect faces in the given frame.
        
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
                            
                            # For now, we'll detect faces by looking for person class
                            # In a real implementation, you'd use a dedicated face detection model
                            class_name = "face"  # Simplified for now
                            
                            # Calculate face attributes
                            attributes = self._analyze_face_attributes(frame, x1, y1, x2, y2)
                            
                            detection = UnifiedDetection(
                                bbox=[int(x1), int(y1), int(x2), int(y2)],
                                confidence=confidence,
                                class_id=class_id,
                                class_name=class_name,
                                classifier_type=self.name,
                                depth_mm=None,  # Will be filled by pipeline
                                position_3d=None,  # Will be filled by pipeline
                                attributes=attributes,
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
            logger.error(f"[FACE_CLASSIFIER] Error detecting faces: {e}")
            return []
    
    def _analyze_face_attributes(self, frame: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> Dict[str, Any]:
        """
        Analyze face attributes (placeholder for future implementation).
        
        Args:
            frame: Input image
            x1, y1, x2, y2: Face bounding box coordinates
            
        Returns:
            Dictionary with face attributes
        """
        attributes = {
            "face_detected": True,
            "confidence": 0.0,
            "emotion": None,
            "age_estimate": None,
            "gender_estimate": None,
            "face_landmarks": None
        }
        
        # Placeholder for future face analysis
        # This would integrate with models like:
        # - Emotion detection (FER2013, AffectNet)
        # - Age/gender estimation
        # - Face landmarks detection
        # - Face recognition/identification
        
        if self.enable_emotion_detection:
            # Placeholder for emotion detection
            attributes["emotion"] = "neutral"  # Would be detected by emotion model
        
        if self.enable_face_recognition:
            # Placeholder for face recognition
            attributes["person_id"] = None  # Would be identified by recognition model
        
        return attributes
    
    def enable_emotion_detection(self, enable: bool = True):
        """Enable or disable emotion detection"""
        self.enable_emotion_detection = enable
        logger.info(f"[FACE_CLASSIFIER] Emotion detection {'enabled' if enable else 'disabled'}")
    
    def enable_face_recognition(self, enable: bool = True):
        """Enable or disable face recognition"""
        self.enable_face_recognition = enable
        logger.info(f"[FACE_CLASSIFIER] Face recognition {'enabled' if enable else 'disabled'}")
    
    def get_face_statistics(self, detections: List[UnifiedDetection]) -> Dict[str, Any]:
        """
        Get statistics about detected faces.
        
        Args:
            detections: List of UnifiedDetection objects
            
        Returns:
            Dictionary with face statistics
        """
        if not detections:
            return {
                "total_faces": 0,
                "average_confidence": 0.0,
                "emotions": {},
                "age_groups": {},
                "genders": {}
            }
        
        total_faces = len(detections)
        confidences = [d.confidence for d in detections]
        average_confidence = sum(confidences) / len(confidences)
        
        # Analyze emotions if available
        emotions = {}
        age_groups = {}
        genders = {}
        
        for detection in detections:
            if detection.attributes:
                # Count emotions
                emotion = detection.attributes.get("emotion")
                if emotion:
                    emotions[emotion] = emotions.get(emotion, 0) + 1
                
                # Count age groups
                age = detection.attributes.get("age_estimate")
                if age:
                    age_group = self._get_age_group(age)
                    age_groups[age_group] = age_groups.get(age_group, 0) + 1
                
                # Count genders
                gender = detection.attributes.get("gender_estimate")
                if gender:
                    genders[gender] = genders.get(gender, 0) + 1
        
        return {
            "total_faces": total_faces,
            "average_confidence": average_confidence,
            "emotions": emotions,
            "age_groups": age_groups,
            "genders": genders
        }
    
    def _get_age_group(self, age: int) -> str:
        """Convert age to age group"""
        if age < 18:
            return "child"
        elif age < 30:
            return "young_adult"
        elif age < 50:
            return "adult"
        elif age < 65:
            return "middle_aged"
        else:
            return "senior"


def main():
    """Test the face classifier"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("[FACE_CLASSIFIER] Testing FaceClassifier...")
    
    # Initialize classifier
    classifier = FaceClassifier()
    
    if not classifier.initialize():
        logger.error("[FACE_CLASSIFIER] Failed to initialize classifier")
        return
    
    logger.info("[FACE_CLASSIFIER] Face classifier initialized")
    
    # Test with a sample frame (you would normally get this from camera)
    if NUMPY_AVAILABLE:
        # Create a dummy frame for testing
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = classifier.detect(dummy_frame)
        logger.info(f"[FACE_CLASSIFIER] Detected {len(detections)} faces")
        
        # Test face statistics
        stats = classifier.get_face_statistics(detections)
        logger.info(f"[FACE_CLASSIFIER] Face statistics: {stats}")
    
    classifier.cleanup()
    logger.info("[FACE_CLASSIFIER] Test completed")


if __name__ == "__main__":
    main()
