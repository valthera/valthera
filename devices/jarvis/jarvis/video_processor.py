#!/usr/bin/env python3

import logging
import time
import threading
from typing import Optional, Tuple

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

# Configure logging
logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, camera_index: int = 0, model_name: str = "yolov8n.pt"):
        self.camera_index = camera_index
        self.model_name = model_name
        self.cap = None
        self.model = None
        self.is_running = False
        self.thread = None
        
        # Video configuration
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 10  # Process every 0.1 seconds for Jetson efficiency
        self.last_process_time = 0
        self.process_interval = 1.0 / self.fps
        
        # Person detection
        self.person_class_id = 0  # COCO class 0 is 'person'
        self.last_person_count = 0
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize YOLOv8 model"""
        try:
            if YOLO_AVAILABLE:
                # Load YOLOv8n model (nano - fastest for Jetson)
                self.model = YOLO(self.model_name)
                logger.info(f"[VIDEO] YOLOv8n model loaded: {self.model_name}")
            else:
                logger.error("[VIDEO] YOLO not available - person detection disabled")
        except Exception as e:
            logger.error(f"[VIDEO] Error loading YOLO model: {e}")
            self.model = None
    
    def _find_camera(self):
        """Find available camera device"""
        if not CV2_AVAILABLE:
            return None
        
        try:
            # Try different camera indices
            for i in range(5):  # Try indices 0-4
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        cap.release()
                        logger.info(f"[VIDEO] Found camera at index {i}")
                        return i
                    cap.release()
            return None
        except Exception as e:
            logger.error(f"[VIDEO] Error finding camera: {e}")
            return None
    
    def _start_camera(self):
        """Start camera capture"""
        if not CV2_AVAILABLE:
            logger.error("[VIDEO] OpenCV not available - camera disabled")
            return False
        
        try:
            camera_index = self._find_camera()
            if camera_index is None:
                logger.error("[VIDEO] No camera device found")
                return False
            
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                logger.error(f"[VIDEO] Failed to open camera at index {camera_index}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)  # Camera FPS
            
            # Get actual properties
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"[VIDEO] Camera started: {actual_width}x{actual_height} @ {actual_fps}fps")
            return True
            
        except Exception as e:
            logger.error(f"[VIDEO] Error starting camera: {e}")
            return False
    
    def _stop_camera(self):
        """Stop camera capture"""
        if self.cap:
            try:
                self.cap.release()
                self.cap = None
                logger.info("[VIDEO] Camera stopped")
            except Exception as e:
                logger.error(f"[VIDEO] Error stopping camera: {e}")
    
    def _detect_people(self, frame) -> int:
        """Detect people in frame and return count"""
        if not YOLO_AVAILABLE or not self.model or not NUMPY_AVAILABLE:
            return 0
        
        try:
            # Run YOLO inference
            results = self.model(frame, verbose=False)
            
            person_count = 0
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # Check if detected object is a person (class 0)
                        if int(box.cls[0]) == self.person_class_id:
                            # Check confidence threshold
                            if float(box.conf[0]) > 0.5:  # 50% confidence threshold
                                person_count += 1
            
            return person_count
            
        except Exception as e:
            logger.error(f"[VIDEO] Error detecting people: {e}")
            return 0
    
    def _process_frame(self):
        """Process a single frame for person detection"""
        if not self.cap or not self.cap.isOpened():
            return
        
        try:
            # Read frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.warning("[VIDEO] Failed to read frame from camera")
                return
            
            # Detect people
            person_count = self._detect_people(frame)
            
            # Log if count changed or periodically
            current_time = time.time()
            if person_count != self.last_person_count or (current_time - self.last_process_time) > 5.0:
                logger.info(f"[VIDEO] Detected {person_count} person(s) in frame")
                self.last_person_count = person_count
                self.last_process_time = current_time
            
        except Exception as e:
            logger.error(f"[VIDEO] Error processing frame: {e}")
    
    def _video_loop(self):
        """Main video processing loop"""
        logger.info("[VIDEO] Starting video processing loop...")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Process frame at specified interval
                if current_time - self.last_process_time >= self.process_interval:
                    self._process_frame()
                    self.last_process_time = current_time
                else:
                    # Sleep for a short time to avoid busy waiting
                    time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"[VIDEO] Error in video loop: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start video processing"""
        if self.is_running:
            logger.warning("[VIDEO] Video processor already running")
            return
        
        if not CV2_AVAILABLE:
            logger.error("[VIDEO] Cannot start - OpenCV not available")
            return
        
        if not self._start_camera():
            logger.error("[VIDEO] Cannot start - failed to initialize camera")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._video_loop, daemon=True)
        self.thread.start()
        logger.info("[VIDEO] Video processor started")
    
    def stop(self):
        """Stop video processing"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_camera()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.info("[VIDEO] Video processor stopped")
    
    def get_person_count(self) -> int:
        """Get the last detected person count"""
        return self.last_person_count
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        
        if self.model:
            try:
                # YOLO models don't need explicit cleanup
                self.model = None
            except Exception as e:
                logger.error(f"[VIDEO] Error cleaning up YOLO model: {e}")


def main():
    """Test the video processor"""
    logging.basicConfig(level=logging.INFO)
    
    processor = VideoProcessor()
    
    try:
        processor.start()
        logger.info("[VIDEO] Starting person detection... Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            count = processor.get_person_count()
            if count > 0:
                logger.info(f"[VIDEO] Current person count: {count}")
            
    except KeyboardInterrupt:
        logger.info("[VIDEO] Stopping video processor...")
    finally:
        processor.cleanup()


if __name__ == "__main__":
    main()
