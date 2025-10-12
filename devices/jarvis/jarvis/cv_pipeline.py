#!/usr/bin/env python3

import logging
import time
import threading
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: NumPy not available")

from .depth_camera import DepthCamera, DepthFrame
from .classifier.person_classifier import PersonClassifier, Detection

logger = logging.getLogger(__name__)

@dataclass
class Detection3D:
    """Container for 3D detection result"""
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str
    depth_mm: float
    position_3d: Dict[str, float]  # {"x": float, "y": float, "z": float}

@dataclass
class CVPipelineResult:
    """Container for CV pipeline output"""
    frame_id: int
    timestamp: float
    detections: List[Detection3D]
    annotated_frame: Optional[np.ndarray] = None

class CVPipeline:
    """CV pipeline that combines person detection with depth data for 3D positioning"""
    
    def __init__(self,
                 depth_camera=None,
                 width: int = 640,
                 height: int = 480,
                 fps: int = 10,
                 confidence_threshold: float = 0.5):
        """
        Initialize the CV pipeline.
        
        Args:
            depth_camera: Existing depth camera instance (optional)
            width: Camera width
            height: Camera height  
            fps: Processing FPS
            confidence_threshold: Detection confidence threshold
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.confidence_threshold = confidence_threshold
        
        # Components
        self.depth_camera = depth_camera
        self.person_classifier = None
        
        # Pipeline state
        self.is_running = False
        self.thread = None
        self.frame_count = 0
        self.last_process_time = 0
        self.process_interval = 1.0 / self.fps
        
        # Latest result
        self.latest_result = None
        self.result_lock = threading.Lock()
        
        # Callbacks
        self.on_new_detection = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize depth camera and person classifier"""
        try:
            # Initialize depth camera only if not provided
            if not self.depth_camera:
                self.depth_camera = DepthCamera(
                    width=self.width,
                    height=self.height,
                    fps=30  # Capture at higher FPS than processing
                )
                logger.info("[CV_PIPELINE] Depth camera initialized")
            else:
                logger.info("[CV_PIPELINE] Using provided depth camera")
            
            # Initialize person classifier
            self.person_classifier = PersonClassifier(
                confidence_threshold=self.confidence_threshold
            )
            logger.info("[CV_PIPELINE] Person classifier initialized")
            
        except Exception as e:
            logger.error(f"[CV_PIPELINE] Error initializing components: {e}")
    
    def _depth_to_3d(self, x: int, y: int, depth_mm: float, intrinsics: Dict[str, float]) -> Dict[str, float]:
        """
        Convert pixel coordinates and depth to 3D position.
        
        Args:
            x, y: Pixel coordinates
            depth_mm: Depth in millimeters
            intrinsics: Camera intrinsics
            
        Returns:
            3D position in camera frame
        """
        if not intrinsics or depth_mm <= 0:
            return {"x": 0.0, "y": 0.0, "z": 0.0}
        
        try:
            fx = intrinsics.get('fx', 0)
            fy = intrinsics.get('fy', 0)
            ppx = intrinsics.get('ppx', 0)
            ppy = intrinsics.get('ppy', 0)
            
            if fx == 0 or fy == 0:
                return {"x": 0.0, "y": 0.0, "z": 0.0}
            
            # Convert depth from mm to meters
            z = depth_mm / 1000.0
            
            # Calculate 3D coordinates
            x_3d = (x - ppx) * z / fx
            y_3d = (y - ppy) * z / fy
            
            return {
                "x": float(x_3d),
                "y": float(y_3d), 
                "z": float(z)
            }
            
        except Exception as e:
            logger.error(f"[CV_PIPELINE] Error converting depth to 3D: {e}")
            return {"x": 0.0, "y": 0.0, "z": 0.0}
    
    def _process_frame(self, depth_frame: DepthFrame) -> Optional[CVPipelineResult]:
        """
        Process a single frame for 3D person detection.
        
        Args:
            depth_frame: Synchronized color and depth frame
            
        Returns:
            CVPipelineResult with 3D detections
        """
        if not self.person_classifier or not depth_frame:
            return None
        
        try:
            # Run person detection on color frame
            detections_2d = self.person_classifier.detect(depth_frame.color_frame)
            
            # Convert to 3D detections
            detections_3d = []
            for detection in detections_2d:
                x1, y1, x2, y2 = detection.bbox
                
                # Calculate center point of bounding box
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Get depth at center point
                depth_mm = 0.0
                if (0 <= center_y < depth_frame.depth_frame.shape[0] and 
                    0 <= center_x < depth_frame.depth_frame.shape[1]):
                    depth_mm = float(depth_frame.depth_frame[center_y, center_x])
                
                # Convert to 3D position
                position_3d = self._depth_to_3d(
                    center_x, center_y, depth_mm, depth_frame.intrinsics
                )
                
                detection_3d = Detection3D(
                    bbox=detection.bbox,
                    confidence=detection.confidence,
                    class_id=detection.class_id,
                    class_name=detection.class_name,
                    depth_mm=depth_mm,
                    position_3d=position_3d
                )
                detections_3d.append(detection_3d)
            
            # Create result
            result = CVPipelineResult(
                frame_id=depth_frame.frame_id,
                timestamp=depth_frame.timestamp,
                detections=detections_3d,
                annotated_frame=None  # Will be set if needed
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[CV_PIPELINE] Error processing frame: {e}")
            return None
    
    def _pipeline_loop(self):
        """Main CV pipeline processing loop"""
        logger.info("[CV_PIPELINE] Starting CV pipeline loop...")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Process at specified interval
                if current_time - self.last_process_time >= self.process_interval:
                    # Get latest depth frame
                    depth_frame = self.depth_camera.get_latest_frame()
                    
                    if depth_frame:
                        # Process frame
                        result = self._process_frame(depth_frame)
                        
                        if result:
                            # Update latest result
                            with self.result_lock:
                                self.latest_result = result
                            
                            # Trigger callback
                            if self.on_new_detection:
                                self.on_new_detection(result)
                            
                            # Log detections
                            if result.detections:
                                logger.info(f"[CV_PIPELINE] Detected {len(result.detections)} person(s) in frame {result.frame_id}")
                    
                    self.last_process_time = current_time
                else:
                    # Sleep to avoid busy waiting
                    time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"[CV_PIPELINE] Error in pipeline loop: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start the CV pipeline"""
        if self.is_running:
            logger.warning("[CV_PIPELINE] CV pipeline already running")
            return
        
        if not self.depth_camera or not self.person_classifier:
            logger.error("[CV_PIPELINE] Cannot start - components not initialized")
            return
        
        # Start depth camera
        self.depth_camera.start()
        
        # Start pipeline loop
        self.is_running = True
        self.thread = threading.Thread(target=self._pipeline_loop, daemon=True)
        self.thread.start()
        
        logger.info("[CV_PIPELINE] CV pipeline started")
    
    def stop(self):
        """Stop the CV pipeline"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop depth camera
        if self.depth_camera:
            self.depth_camera.stop()
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.info("[CV_PIPELINE] CV pipeline stopped")
    
    def get_latest_result(self) -> Optional[CVPipelineResult]:
        """Get the latest detection result"""
        with self.result_lock:
            return self.latest_result
    
    def get_annotated_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame with bounding boxes drawn"""
        result = self.get_latest_result()
        if not result or not self.person_classifier:
            return None
        
        try:
            # Convert 3D detections back to 2D for annotation
            detections_2d = []
            for detection_3d in result.detections:
                detection_2d = Detection(
                    bbox=detection_3d.bbox,
                    confidence=detection_3d.confidence,
                    class_id=detection_3d.class_id,
                    class_name=detection_3d.class_name
                )
                detections_2d.append(detection_2d)
            
            # Get latest color frame
            depth_frame = self.depth_camera.get_latest_frame()
            if depth_frame:
                return self.person_classifier.annotate_frame(
                    depth_frame.color_frame, detections_2d
                )
            
        except Exception as e:
            logger.error(f"[CV_PIPELINE] Error getting annotated frame: {e}")
        
        return None
    
    def set_detection_callback(self, callback: Callable[[CVPipelineResult], None]):
        """Set callback for new detection events"""
        self.on_new_detection = callback
    
    def get_pipeline_info(self) -> Dict[str, any]:
        """Get pipeline information and status"""
        return {
            "is_running": self.is_running,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "confidence_threshold": self.confidence_threshold,
            "frame_count": self.frame_count,
            "depth_camera_available": self.depth_camera is not None,
            "classifier_available": self.person_classifier is not None,
            "classifier_stats": self.person_classifier.get_stats() if self.person_classifier else {}
        }
    
    def cleanup(self):
        """Cleanup pipeline resources"""
        self.stop()
        
        if self.depth_camera:
            self.depth_camera.cleanup()
        
        if self.person_classifier:
            self.person_classifier.cleanup()
        
        logger.info("[CV_PIPELINE] CV pipeline cleaned up")


def main():
    """Test the CV pipeline"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("[CV_PIPELINE] Testing CVPipeline...")
    
    # Initialize pipeline
    pipeline = CVPipeline()
    
    try:
        # Start pipeline
        pipeline.start()
        logger.info("[CV_PIPELINE] Pipeline started, processing frames...")
        
        # Test for 30 seconds
        for i in range(30):
            time.sleep(1)
            
            # Get latest result
            result = pipeline.get_latest_result()
            if result and result.detections:
                logger.info(f"[CV_PIPELINE] Frame {result.frame_id}: "
                           f"Detected {len(result.detections)} person(s)")
                
                for j, detection in enumerate(result.detections):
                    logger.info(f"[CV_PIPELINE]   Person {j+1}: "
                               f"bbox={detection.bbox}, "
                               f"depth={detection.depth_mm:.1f}mm, "
                               f"3D=({detection.position_3d['x']:.2f}, "
                               f"{detection.position_3d['y']:.2f}, "
                               f"{detection.position_3d['z']:.2f})")
        
        # Get pipeline info
        info = pipeline.get_pipeline_info()
        logger.info(f"[CV_PIPELINE] Pipeline info: {info}")
        
    except KeyboardInterrupt:
        logger.info("[CV_PIPELINE] Stopping pipeline...")
    finally:
        pipeline.cleanup()
        logger.info("[CV_PIPELINE] Pipeline test completed")


if __name__ == "__main__":
    main()
