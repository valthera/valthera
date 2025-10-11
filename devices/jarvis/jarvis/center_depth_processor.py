#!/usr/bin/env python3

import logging
import time
import threading
import numpy as np
from typing import Optional, Callable
from dataclasses import dataclass

from .depth_camera import DepthCamera, DepthFrame

logger = logging.getLogger(__name__)

@dataclass
class CenterDepthData:
    """Center depth data container"""
    avg_depth: float
    timestamp: float
    frame_id: int
    valid_pixels: int
    total_pixels: int

class CenterDepthProcessor:
    """Processor for calculating center region average depth"""
    
    def __init__(self, 
                 center_region_size: float = 0.3,  # 30% of frame size
                 fps: int = 10):  # Lower FPS for WebSocket streaming
        
        self.center_region_size = center_region_size
        self.fps = fps
        
        # Depth camera
        self.depth_camera = None
        
        # Processing state
        self.is_running = False
        self.thread = None
        
        # Latest center depth data
        self.latest_depth_data = None
        self.depth_lock = threading.Lock()
        
        # Callbacks
        self.on_depth_update = None
        
        self._initialize_depth_camera()
    
    def _initialize_depth_camera(self):
        """Initialize depth camera"""
        try:
            self.depth_camera = DepthCamera(width=640, height=480, fps=30)
            # Set the callback to process new frames
            self.depth_camera.set_frame_callback(self._on_new_frame)
            logger.info("[CENTER_DEPTH] Depth camera initialized with callback")
        except Exception as e:
            logger.error(f"[CENTER_DEPTH] Error initializing depth camera: {e}")
            self.depth_camera = None
    
    def _calculate_center_depth(self, depth_frame: np.ndarray) -> Optional[CenterDepthData]:
        """Calculate average depth of center region"""
        if depth_frame is None or depth_frame.size == 0:
            return None
        
        try:
            height, width = depth_frame.shape
            
            # Calculate center region bounds (30% of frame size)
            center_width = int(width * self.center_region_size)
            center_height = int(height * self.center_region_size)
            
            # Calculate center region coordinates
            x_start = (width - center_width) // 2
            y_start = (height - center_height) // 2
            x_end = x_start + center_width
            y_end = y_start + center_height
            
            # Extract center region
            center_region = depth_frame[y_start:y_end, x_start:x_end]
            
            # Get valid depth values (non-zero)
            valid_depths = center_region[center_region > 0]
            
            if len(valid_depths) == 0:
                return None
            
            # Calculate average depth
            avg_depth = np.mean(valid_depths)
            
            depth_data = CenterDepthData(
                avg_depth=avg_depth,
                timestamp=time.time(),
                frame_id=getattr(self, 'frame_count', 0),
                valid_pixels=len(valid_depths),
                total_pixels=center_width * center_height
            )
            
            return depth_data
            
        except Exception as e:
            logger.error(f"[CENTER_DEPTH] Error calculating center depth: {e}")
            return None
    
    def _on_new_frame(self, frame: DepthFrame):
        """Callback for new depth frames"""
        if not self.is_running:
            return
        
        try:
            # Calculate center depth
            depth_data = self._calculate_center_depth(frame.depth_frame)
            
            if depth_data is not None:
                # Update latest depth data
                with self.depth_lock:
                    self.latest_depth_data = depth_data
                
                # Trigger callback
                if self.on_depth_update:
                    self.on_depth_update(depth_data)
                
                # Log every 30 frames (about every 3 seconds at 10fps)
                if depth_data.frame_id % 30 == 0:
                    logger.info(f"[CENTER_DEPTH] Center depth: {depth_data.avg_depth:.1f}mm "
                               f"({depth_data.valid_pixels}/{depth_data.total_pixels} pixels)")
            else:
                logger.warning(f"[CENTER_DEPTH] No valid depth data in frame {frame.frame_id}")
            
        except Exception as e:
            logger.error(f"[CENTER_DEPTH] Error processing frame: {e}")
    
    def _processing_loop(self):
        """Main processing loop"""
        logger.info("[CENTER_DEPTH] Starting center depth processing loop...")
        
        while self.is_running:
            try:
                # The actual processing happens in the frame callback
                # This loop just maintains the thread and controls timing
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                logger.error(f"[CENTER_DEPTH] Error in processing loop: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start center depth processing"""
        if self.is_running:
            logger.warning("[CENTER_DEPTH] Center depth processor already running")
            return
        
        if not self.depth_camera:
            logger.error("[CENTER_DEPTH] Cannot start - depth camera not initialized")
            return
        
        try:
            # Set up frame callback
            self.depth_camera.set_frame_callback(self._on_new_frame)
            
            # Start depth camera
            self.depth_camera.start()
            
            # Start processing loop
            self.is_running = True
            self.thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.thread.start()
            
            logger.info("[CENTER_DEPTH] Center depth processor started")
            
        except Exception as e:
            logger.error(f"[CENTER_DEPTH] Error starting processor: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop center depth processing"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop depth camera
        if self.depth_camera:
            self.depth_camera.stop()
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.info("[CENTER_DEPTH] Center depth processor stopped")
    
    def get_latest_depth(self) -> Optional[CenterDepthData]:
        """Get latest center depth data"""
        with self.depth_lock:
            return self.latest_depth_data
    
    def set_depth_update_callback(self, callback: Callable[[CenterDepthData], None]):
        """Set callback for depth updates"""
        self.on_depth_update = callback
    
    def get_processor_info(self) -> dict:
        """Get processor information"""
        return {
            'center_region_size': self.center_region_size,
            'fps': self.fps,
            'is_running': self.is_running,
            'depth_camera_available': self.depth_camera is not None,
            'depth_camera_running': self.depth_camera.is_running if self.depth_camera else False
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        
        if self.depth_camera:
            self.depth_camera.cleanup()
        
        logger.info("[CENTER_DEPTH] Center depth processor cleaned up")


def main():
    """Test the center depth processor"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("[CENTER_DEPTH] Testing CenterDepthProcessor...")
    
    # Initialize processor
    processor = CenterDepthProcessor(center_region_size=0.3, fps=5)
    
    try:
        # Set up callback
        def on_depth_update(depth_data: CenterDepthData):
            logger.info(f"[CENTER_DEPTH] Depth update: {depth_data.avg_depth:.1f}mm "
                       f"({depth_data.valid_pixels}/{depth_data.total_pixels} pixels)")
        
        processor.set_depth_update_callback(on_depth_update)
        
        # Start processing
        processor.start()
        logger.info("[CENTER_DEPTH] Processor started, running for 10 seconds...")
        
        # Test for 10 seconds
        for i in range(10):
            time.sleep(1)
            
            # Get latest depth
            depth_data = processor.get_latest_depth()
            if depth_data:
                logger.info(f"[CENTER_DEPTH] Latest depth: {depth_data.avg_depth:.1f}mm")
            else:
                logger.warning("[CENTER_DEPTH] No depth data available")
        
        # Get processor info
        info = processor.get_processor_info()
        logger.info(f"[CENTER_DEPTH] Processor info: {info}")
        
    except KeyboardInterrupt:
        logger.info("[CENTER_DEPTH] Stopping processor...")
    finally:
        processor.cleanup()
        logger.info("[CENTER_DEPTH] Center depth processor test completed")


if __name__ == "__main__":
    main()
