#!/usr/bin/env python3

import logging
import time
import threading
import numpy as np
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

try:
    import pyrealsense2 as rs
    REALSENSE_AVAILABLE = True
except ImportError:
    REALSENSE_AVAILABLE = False
    print("Warning: RealSense SDK not available")

logger = logging.getLogger(__name__)

@dataclass
class DepthFrame:
    """Container for depth camera frame data"""
    color_frame: np.ndarray
    depth_frame: np.ndarray
    timestamp: float
    frame_id: int
    intrinsics: Optional[Dict[str, float]] = None

class DepthCamera:
    """Simple interface for RealSense depth camera data"""
    
    def __init__(self, 
                 width: int = 640, 
                 height: int = 480, 
                 fps: int = 30):
        
        self.width = width
        self.height = height
        self.fps = fps
        
        # RealSense pipeline
        self.pipeline = None
        self.config = None
        self.align = None
        
        # Processing state
        self.is_running = False
        self.thread = None
        self.frame_count = 0
        
        # Latest frame data
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # Callbacks
        self.on_new_frame = None
        
        self._initialize_realsense()
    
    def _initialize_realsense(self):
        """Initialize RealSense pipeline"""
        if not REALSENSE_AVAILABLE:
            logger.error("[DEPTH] RealSense SDK not available")
            return False
        
        try:
            # Create pipeline and config
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            
            # Configure streams
            self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, self.fps)
            self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
            
            # Create align object
            self.align = rs.align(rs.stream.color)
            
            # Start pipeline
            profile = self.pipeline.start(self.config)
            logger.info(f"[DEPTH] RealSense pipeline started: {self.width}x{self.height} @ {self.fps}fps")
            
            return True
            
        except Exception as e:
            logger.error(f"[DEPTH] Error initializing RealSense: {e}")
            return False
    
    def _get_intrinsics(self, depth_frame: rs.depth_frame) -> Dict[str, float]:
        """Extract camera intrinsics"""
        try:
            intrinsics = depth_frame.get_intrinsics()
            return {
                'fx': intrinsics.fx,
                'fy': intrinsics.fy,
                'ppx': intrinsics.ppx,
                'ppy': intrinsics.ppy,
                'width': intrinsics.width,
                'height': intrinsics.height
            }
        except Exception as e:
            logger.error(f"[DEPTH] Error getting intrinsics: {e}")
            return {}
    
    def _capture_frame(self):
        """Capture a single frame from the camera"""
        if not self.pipeline:
            return None
        
        try:
            # Wait for frames
            frames = self.pipeline.wait_for_frames()
            
            # Align depth to color
            aligned_frames = self.align.process(frames)
            
            # Get aligned frames
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            
            if not depth_frame or not color_frame:
                return None
            
            # Convert frames to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            # Create depth frame container
            depth_frame_data = DepthFrame(
                color_frame=color_image,
                depth_frame=depth_image,
                timestamp=time.time(),
                frame_id=self.frame_count,
                intrinsics=self._get_intrinsics(depth_frame)
            )
            
            return depth_frame_data
            
        except Exception as e:
            logger.error(f"[DEPTH] Error capturing frame: {e}")
            return None
    
    def _capture_loop(self):
        """Main frame capture loop"""
        logger.info("[DEPTH] Starting frame capture loop...")
        
        while self.is_running:
            try:
                frame = self._capture_frame()
                if frame is not None:
                    # Update latest frame
                    with self.frame_lock:
                        self.latest_frame = frame
                    
                    # Trigger callback
                    if self.on_new_frame:
                        self.on_new_frame(frame)
                    
                    self.frame_count += 1
                
                time.sleep(1.0 / self.fps)  # Control capture rate
                
            except Exception as e:
                logger.error(f"[DEPTH] Error in capture loop: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start frame capture"""
        if self.is_running:
            logger.warning("[DEPTH] Depth camera already running")
            return
        
        if not self.pipeline:
            logger.error("[DEPTH] Cannot start - RealSense pipeline not initialized")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("[DEPTH] Depth camera started")
    
    def stop(self):
        """Stop frame capture"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        if self.pipeline:
            self.pipeline.stop()
        
        logger.info("[DEPTH] Depth camera stopped")
    
    def get_latest_frame(self) -> Optional[DepthFrame]:
        """Get the latest captured frame"""
        with self.frame_lock:
            return self.latest_frame
    
    def capture_single_frame(self) -> Optional[DepthFrame]:
        """Capture a single frame (blocking)"""
        return self._capture_frame()
    
    def set_frame_callback(self, callback):
        """Set callback for new frame events"""
        self.on_new_frame = callback
    
    def get_camera_info(self) -> Dict[str, any]:
        """Get camera information"""
        return {
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'frame_count': self.frame_count,
            'is_running': self.is_running,
            'realsense_available': REALSENSE_AVAILABLE
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        logger.info("[DEPTH] Depth camera cleaned up")


def main():
    """Test the depth camera interface"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("[DEPTH] Testing DepthCamera interface...")
    
    # Initialize depth camera
    depth_cam = DepthCamera(width=640, height=480, fps=30)
    
    try:
        # Start capturing frames
        depth_cam.start()
        logger.info("[DEPTH] Depth camera started, capturing frames...")
        
        # Test for 10 seconds
        for i in range(10):
            time.sleep(1)
            
            # Get latest frame
            frame = depth_cam.get_latest_frame()
            if frame:
                logger.info(f"[DEPTH] Frame {frame.frame_id}: "
                           f"Color {frame.color_frame.shape}, "
                           f"Depth {frame.depth_frame.shape}, "
                           f"Timestamp {frame.timestamp:.3f}")
            else:
                logger.warning("[DEPTH] No frame available")
        
        # Test single frame capture
        logger.info("[DEPTH] Testing single frame capture...")
        single_frame = depth_cam.capture_single_frame()
        if single_frame:
            logger.info(f"[DEPTH] Single frame captured: {single_frame.frame_id}")
        
        # Get camera info
        info = depth_cam.get_camera_info()
        logger.info(f"[DEPTH] Camera info: {info}")
        
    except KeyboardInterrupt:
        logger.info("[DEPTH] Stopping depth camera...")
    finally:
        depth_cam.cleanup()
        logger.info("[DEPTH] Depth camera test completed")


if __name__ == "__main__":
    main()
