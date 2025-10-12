#!/usr/bin/env python3

"""
Smart CV pipeline for Jarvis.

This module provides intelligent computer vision processing with multi-classifier
support, parallel processing, and efficient result caching.
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..models.base import (
    UnifiedDetection, AnalysisRequest, AnalysisResult, 
    PipelineConfig, FrameMetadata, create_analysis_result_from_legacy
)
from ..classifiers.registry import get_registry, ClassifierRegistry
from .cache import get_cache, ResultCache
from ..depth_camera import DepthCamera, DepthFrame

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for processing pipeline"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_processing_time_ms: float = 0.0
    last_processing_time_ms: float = 0.0
    total_detections: int = 0


class ProcessingPipeline:
    """Intelligent processing with result sharing"""
    
    def __init__(self, registry: ClassifierRegistry, cache: ResultCache):
        self.registry = registry
        self.cache = cache
        self.stats = ProcessingStats()
        self._lock = threading.Lock()
    
    async def execute(self, frame: np.ndarray, request: AnalysisRequest) -> AnalysisResult:
        """Execute processing pipeline efficiently"""
        start_time = time.time()
        
        # 1. Check cache first
        cached_result = self.cache.get_cached_result(frame, request)
        if cached_result:
            with self._lock:
                self.stats.cache_hits += 1
                self.stats.total_requests += 1
            logger.debug("[PIPELINE] Cache hit - returning cached result")
            return cached_result
        
        with self._lock:
            self.stats.cache_misses += 1
            self.stats.total_requests += 1
        
        # 2. Preprocessing (shared across all classifiers)
        preprocessed_frame = await self._preprocess(frame)
        
        # 3. Run classifiers in parallel where possible
        classifier_results = await self._run_classifiers_parallel(preprocessed_frame, request)
        
        # 4. Post-processing and fusion
        final_result = await self._fuse_results(classifier_results, request, frame)
        
        # 5. Cache result
        self.cache.cache_result(frame, request, final_result)
        
        # Update statistics
        processing_time = (time.time() - start_time) * 1000
        with self._lock:
            self.stats.last_processing_time_ms = processing_time
            if self.stats.average_processing_time_ms == 0:
                self.stats.average_processing_time_ms = processing_time
            else:
                # Simple moving average
                self.stats.average_processing_time_ms = (
                    self.stats.average_processing_time_ms * 0.9 + processing_time * 0.1
                )
            self.stats.total_detections += final_result.get_total_detections()
        
        return final_result
    
    async def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame (shared across all classifiers)"""
        if not NUMPY_AVAILABLE or frame is None:
            return frame
        
        try:
            # Basic preprocessing - resize if needed, normalize, etc.
            # For now, just return the frame as-is
            return frame
        except Exception as e:
            logger.error(f"[PIPELINE] Error in preprocessing: {e}")
            return frame
    
    async def _run_classifiers_parallel(self, frame: np.ndarray, request: AnalysisRequest) -> Dict[str, List[UnifiedDetection]]:
        """Run multiple classifiers in parallel"""
        # Get enabled classifiers that match the request
        enabled_classifiers = self.registry.get_enabled_classifiers()
        requested_classifiers = [c for c in enabled_classifiers if c.name in request.classifiers]
        
        if not requested_classifiers:
            logger.warning("[PIPELINE] No enabled classifiers match request")
            return {}
        
        # Create tasks for parallel execution
        tasks = []
        for classifier in requested_classifiers:
            if classifier.is_initialized:
                task = asyncio.create_task(
                    self._run_classifier(classifier, frame, request)
                )
                tasks.append((classifier.name, task))
        
        # Wait for all classifiers to complete
        classifier_results = {}
        for classifier_name, task in tasks:
            try:
                result = await task
                classifier_results[classifier_name] = result
            except Exception as e:
                logger.error(f"[PIPELINE] Classifier {classifier_name} failed: {e}")
                classifier_results[classifier_name] = []
        
        return classifier_results
    
    async def _run_classifier(self, classifier, frame: np.ndarray, request: AnalysisRequest) -> List[UnifiedDetection]:
        """Run a single classifier"""
        try:
            # Run detection in thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            detections = await loop.run_in_executor(None, classifier.detect, frame)
            
            # Apply filters if specified
            if request.filters:
                detections = self._apply_filters(detections, request.filters)
            
            return detections
        except Exception as e:
            logger.error(f"[PIPELINE] Error running classifier {classifier.name}: {e}")
            return []
    
    def _apply_filters(self, detections: List[UnifiedDetection], filters: Dict[str, Any]) -> List[UnifiedDetection]:
        """Apply filters to detections"""
        filtered_detections = detections
        
        # Filter by minimum confidence
        min_confidence = filters.get("min_confidence")
        if min_confidence is not None:
            filtered_detections = [d for d in filtered_detections if d.confidence >= min_confidence]
        
        # Filter by maximum distance
        max_distance = filters.get("max_distance_mm")
        if max_distance is not None:
            filtered_detections = [d for d in filtered_detections 
                                 if d.depth_mm is None or d.depth_mm <= max_distance]
        
        # Filter by classes
        allowed_classes = filters.get("classes")
        if allowed_classes:
            filtered_detections = [d for d in filtered_detections if d.class_name in allowed_classes]
        
        return filtered_detections
    
    async def _fuse_results(self, classifier_results: Dict[str, List[UnifiedDetection]], 
                          request: AnalysisRequest, frame: np.ndarray) -> AnalysisResult:
        """Fuse results from multiple classifiers"""
        # Create frame metadata
        frame_metadata = FrameMetadata(
            frame_id=request.frame_id or int(time.time() * 1000),
            timestamp=time.time(),
            resolution=(frame.shape[1], frame.shape[0]) if NUMPY_AVAILABLE and frame is not None else (640, 480),
            processing_pipeline=list(classifier_results.keys())
        )
        
        # Create analysis result
        result = AnalysisResult(
            frame_id=frame_metadata.frame_id,
            timestamp=frame_metadata.timestamp,
            processing_time_ms=0.0,  # Will be set by caller
            detections=classifier_results,
            frame_resolution=frame_metadata.resolution,
            annotated_frame=None,  # Will be set if requested
            pipeline_info={
                "classifiers_used": list(classifier_results.keys()),
                "total_detections": sum(len(detections) for detections in classifier_results.values()),
                "frame_metadata": frame_metadata.to_dict()
            },
            cache_hit=False
        )
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        with self._lock:
            cache_hit_rate = (self.stats.cache_hits / self.stats.total_requests * 100) if self.stats.total_requests > 0 else 0
            
            return {
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "average_processing_time_ms": round(self.stats.average_processing_time_ms, 2),
                "last_processing_time_ms": round(self.stats.last_processing_time_ms, 2),
                "total_detections": self.stats.total_detections
            }


class SmartCVPipeline:
    """Intelligent CV pipeline with multi-classifier support"""
    
    def __init__(self, 
                 depth_camera: Optional[DepthCamera] = None,
                 config: Optional[PipelineConfig] = None):
        """
        Initialize the smart CV pipeline.
        
        Args:
            depth_camera: Existing depth camera instance (optional)
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        self.depth_camera = depth_camera
        
        # Core components
        self.registry = get_registry()
        self.cache = get_cache()
        self.processing_pipeline = ProcessingPipeline(self.registry, self.cache)
        
        # Pipeline state
        self.is_running = False
        self.thread = None
        self.frame_count = 0
        self.last_process_time = 0
        self.process_interval = 1.0 / self.config.fps
        
        # Latest result
        self.latest_result: Optional[AnalysisResult] = None
        self.result_lock = threading.Lock()
        
        # Callbacks
        self.on_new_detection: Optional[Callable[[AnalysisResult], None]] = None
        
        # Initialize classifiers
        self._initialize_classifiers()
    
    def _initialize_classifiers(self):
        """Initialize available classifiers"""
        try:
            # Register classifier types
            from .classifiers.person_classifier import PersonClassifier
            from .classifiers.object_classifier import ObjectClassifier
            from .classifiers.face_classifier import FaceClassifier
            
            self.registry.register_classifier_type("person", PersonClassifier)
            self.registry.register_classifier_type("object", ObjectClassifier)
            self.registry.register_classifier_type("face", FaceClassifier)
            
            # Create default classifiers
            for classifier_type in self.config.enabled_classifiers:
                classifier = self.registry.create_classifier(classifier_type, classifier_type)
                if classifier:
                    classifier.initialize()
                    logger.info(f"[SMART_PIPELINE] Initialized classifier: {classifier_type}")
            
            logger.info(f"[SMART_PIPELINE] Initialized {len(self.config.enabled_classifiers)} classifiers")
            
        except Exception as e:
            logger.error(f"[SMART_PIPELINE] Error initializing classifiers: {e}")
    
    async def process_request(self, request: AnalysisRequest) -> AnalysisResult:
        """Main processing entry point"""
        if not self.depth_camera:
            raise RuntimeError("Depth camera not available")
        
        # Get latest frame
        depth_frame = self.depth_camera.get_latest_frame()
        if not depth_frame:
            raise RuntimeError("No frame available")
        
        # Process the request
        result = await self.processing_pipeline.execute(depth_frame.color_frame, request)
        
        # Add depth information if requested
        if request.options.get("include_depth", True):
            result = await self._add_depth_information(result, depth_frame)
        
        # Update latest result
        with self.result_lock:
            self.latest_result = result
        
        return result
    
    async def _add_depth_information(self, result: AnalysisResult, depth_frame: DepthFrame) -> AnalysisResult:
        """Add depth information to detections"""
        if not depth_frame.depth_frame is not None:
            return result
        
        # Add depth to each detection
        for classifier_type, detections in result.detections.items():
            for detection in detections:
                if detection.depth_mm is None:
                    # Calculate center point of bounding box
                    x1, y1, x2, y2 = detection.bbox
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    # Get depth at center point
                    if (0 <= center_y < depth_frame.depth_frame.shape[0] and 
                        0 <= center_x < depth_frame.depth_frame.shape[1]):
                        depth_mm = float(depth_frame.depth_frame[center_y, center_x])
                        detection.depth_mm = depth_mm
                        
                        # Convert to 3D position if requested
                        if result.pipeline_info.get("include_3d_position", True):
                            detection.position_3d = self._depth_to_3d(
                                center_x, center_y, depth_mm, depth_frame.intrinsics
                            )
        
        return result
    
    def _depth_to_3d(self, x: int, y: int, depth_mm: float, intrinsics: Dict[str, float]) -> Dict[str, float]:
        """Convert pixel coordinates and depth to 3D position"""
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
            logger.error(f"[SMART_PIPELINE] Error converting depth to 3D: {e}")
            return {"x": 0.0, "y": 0.0, "z": 0.0}
    
    def start(self):
        """Start the smart CV pipeline"""
        if self.is_running:
            logger.warning("[SMART_PIPELINE] Pipeline already running")
            return
        
        if not self.depth_camera:
            logger.error("[SMART_PIPELINE] Cannot start - depth camera not available")
            return
        
        # Start depth camera
        self.depth_camera.start()
        
        # Start pipeline loop
        self.is_running = True
        self.thread = threading.Thread(target=self._pipeline_loop, daemon=True)
        self.thread.start()
        
        logger.info("[SMART_PIPELINE] Smart CV pipeline started")
    
    def stop(self):
        """Stop the smart CV pipeline"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop depth camera
        if self.depth_camera:
            self.depth_camera.stop()
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        logger.info("[SMART_PIPELINE] Smart CV pipeline stopped")
    
    def _pipeline_loop(self):
        """Main CV pipeline processing loop"""
        logger.info("[SMART_PIPELINE] Starting smart CV pipeline loop...")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Process at specified interval
                if current_time - self.last_process_time >= self.process_interval:
                    # Get latest depth frame
                    depth_frame = self.depth_camera.get_latest_frame()
                    
                    if depth_frame:
                        # Create default analysis request
                        request = AnalysisRequest(
                            classifiers=self.config.enabled_classifiers,
                            options={
                                "confidence_threshold": self.config.confidence_threshold,
                                "include_depth": self.config.include_depth,
                                "include_3d_position": self.config.include_3d_position,
                                "max_detections": self.config.max_detections
                            },
                            frame_id=depth_frame.frame_id
                        )
                        
                        # Process request (run in async context)
                        try:
                            # Create a new event loop for this thread
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            try:
                                result = loop.run_until_complete(self.process_request(request))
                                
                                # Update latest result
                                with self.result_lock:
                                    self.latest_result = result
                                
                                # Trigger callback
                                if self.on_new_detection:
                                    self.on_new_detection(result)
                                
                                # Log detections
                                if result.has_detections():
                                    logger.info(f"[SMART_PIPELINE] Detected {result.get_total_detections()} objects in frame {result.frame_id}")
                            
                            finally:
                                loop.close()
                                # Clear the event loop to avoid conflicts
                                asyncio.set_event_loop(None)
                        
                        except Exception as e:
                            logger.error(f"[SMART_PIPELINE] Error processing request: {e}")
                    
                    self.last_process_time = current_time
                else:
                    # Sleep to avoid busy waiting
                    time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"[SMART_PIPELINE] Error in pipeline loop: {e}")
                time.sleep(0.1)
    
    def get_latest_result(self) -> Optional[AnalysisResult]:
        """Get the latest analysis result"""
        with self.result_lock:
            return self.latest_result
    
    def set_detection_callback(self, callback: Callable[[AnalysisResult], None]):
        """Set callback for new detection events"""
        self.on_new_detection = callback
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get pipeline information and status"""
        return {
            "is_running": self.is_running,
            "config": {
                "fps": self.config.fps,
                "confidence_threshold": self.config.confidence_threshold,
                "max_detections": self.config.max_detections,
                "enabled_classifiers": self.config.enabled_classifiers,
                "include_depth": self.config.include_depth,
                "include_3d_position": self.config.include_3d_position
            },
            "frame_count": self.frame_count,
            "depth_camera_available": self.depth_camera is not None,
            "registry_stats": self.registry.get_registry_stats(),
            "processing_stats": self.processing_pipeline.get_stats(),
            "cache_stats": self.cache.get_stats()
        }
    
    def cleanup(self):
        """Cleanup pipeline resources"""
        self.stop()
        
        if self.depth_camera:
            self.depth_camera.cleanup()
        
        # Cleanup registry and cache
        try:
            from ..classifiers.registry import cleanup_registry
            cleanup_registry()
        except ImportError:
            logger.warning("[SMART_PIPELINE] Could not import registry cleanup")
        
        try:
            from .cache import cleanup_cache
            cleanup_cache()
        except ImportError:
            logger.warning("[SMART_PIPELINE] Could not import cache cleanup")
        
        logger.info("[SMART_PIPELINE] Smart CV pipeline cleaned up")


def main():
    """Test the smart CV pipeline"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("[SMART_PIPELINE] Testing SmartCVPipeline...")
    
    # Initialize pipeline
    pipeline = SmartCVPipeline()
    
    try:
        # Start pipeline
        pipeline.start()
        logger.info("[SMART_PIPELINE] Pipeline started, processing frames...")
        
        # Test for 30 seconds
        for i in range(30):
            time.sleep(1)
            
            # Get latest result
            result = pipeline.get_latest_result()
            if result and result.has_detections():
                logger.info(f"[SMART_PIPELINE] Frame {result.frame_id}: "
                           f"Detected {result.get_total_detections()} objects")
        
        # Get pipeline info
        info = pipeline.get_pipeline_info()
        logger.info(f"[SMART_PIPELINE] Pipeline info: {info}")
        
    except KeyboardInterrupt:
        logger.info("[SMART_PIPELINE] Stopping pipeline...")
    finally:
        pipeline.cleanup()
        logger.info("[SMART_PIPELINE] Pipeline test completed")


if __name__ == "__main__":
    main()
