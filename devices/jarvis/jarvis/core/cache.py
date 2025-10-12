#!/usr/bin/env python3

"""
Result cache system for Jarvis smart CV pipeline.

This module provides efficient caching of analysis results to avoid
duplicate processing and improve system performance.
"""

import hashlib
import logging
import threading
import time
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..models.base import AnalysisResult, AnalysisRequest

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    result: AnalysisResult
    timestamp: float
    access_count: int = 0
    last_access: float = 0.0


class ResultCache:
    """Smart caching system to avoid duplicate processing"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: float = 1.0):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        logger.info(f"[CACHE] Initialized with max_size={max_size}, ttl={ttl_seconds}s")
    
    def _compute_frame_hash(self, frame: np.ndarray) -> str:
        """Compute hash for frame to use as cache key"""
        if not NUMPY_AVAILABLE or frame is None:
            return "no_frame"
        
        try:
            # Use a subset of the frame for hashing to improve performance
            # Sample every 10th pixel to create a representative hash
            sample = frame[::10, ::10]
            frame_bytes = sample.tobytes()
            return hashlib.md5(frame_bytes).hexdigest()
        except Exception as e:
            logger.error(f"[CACHE] Error computing frame hash: {e}")
            return f"error_{int(time.time())}"
    
    def _create_cache_key(self, frame_hash: str, classifiers: List[str], options: Dict[str, Any]) -> str:
        """Create cache key from frame hash, classifiers, and options"""
        # Sort classifiers for consistent keys
        sorted_classifiers = sorted(classifiers)
        
        # Create options hash (only include relevant options)
        relevant_options = {
            "confidence_threshold": options.get("confidence_threshold"),
            "include_depth": options.get("include_depth"),
            "include_3d_position": options.get("include_3d_position"),
            "max_detections": options.get("max_detections")
        }
        
        # Create key components
        key_parts = [
            frame_hash,
            ":".join(sorted_classifiers),
            str(sorted(relevant_options.items()))
        ]
        
        return "|".join(key_parts)
    
    def get_cached_result(self, frame: np.ndarray, request: AnalysisRequest) -> Optional[AnalysisResult]:
        """Get cached result if available and valid"""
        frame_hash = self._compute_frame_hash(frame)
        cache_key = self._create_cache_key(frame_hash, request.classifiers, request.options)
        
        with self._lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                current_time = time.time()
                
                # Check if entry is still valid
                if current_time - entry.timestamp < self.ttl_seconds:
                    # Update access statistics
                    entry.access_count += 1
                    entry.last_access = current_time
                    self.hits += 1
                    
                    logger.debug(f"[CACHE] Hit for key: {cache_key[:20]}...")
                    return entry.result
                else:
                    # Entry expired, remove it
                    del self.cache[cache_key]
                    logger.debug(f"[CACHE] Expired entry removed: {cache_key[:20]}...")
            
            self.misses += 1
            return None
    
    def cache_result(self, frame: np.ndarray, request: AnalysisRequest, result: AnalysisResult):
        """Cache processing result"""
        frame_hash = self._compute_frame_hash(frame)
        cache_key = self._create_cache_key(frame_hash, request.classifiers, request.options)
        
        with self._lock:
            # Check if we need to evict entries
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            # Create cache entry
            entry = CacheEntry(
                result=result,
                timestamp=time.time(),
                access_count=1,
                last_access=time.time()
            )
            
            self.cache[cache_key] = entry
            logger.debug(f"[CACHE] Cached result for key: {cache_key[:20]}...")
    
    def _evict_oldest(self):
        """Evict the oldest cache entry"""
        if not self.cache:
            return
        
        # Find oldest entry (least recently accessed)
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_access)
        del self.cache[oldest_key]
        self.evictions += 1
        
        logger.debug(f"[CACHE] Evicted oldest entry: {oldest_key[:20]}...")
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self.cache.items():
                if current_time - entry.timestamp >= self.ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
        
        if expired_keys:
            logger.debug(f"[CACHE] Cleaned up {len(expired_keys)} expired entries")
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            logger.info("[CACHE] Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_percent": round(hit_rate, 2),
                "evictions": self.evictions,
                "total_requests": total_requests
            }
    
    def get_cache_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about cache entries"""
        with self._lock:
            current_time = time.time()
            return [
                {
                    "key": key[:20] + "..." if len(key) > 20 else key,
                    "age_seconds": round(current_time - entry.timestamp, 2),
                    "access_count": entry.access_count,
                    "last_access_seconds_ago": round(current_time - entry.last_access, 2),
                    "is_expired": current_time - entry.timestamp >= self.ttl_seconds,
                    "detection_count": entry.result.get_total_detections()
                }
                for key, entry in self.cache.items()
            ]


# Global cache instance
_cache_instance: Optional[ResultCache] = None


def get_cache() -> ResultCache:
    """Get the global result cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResultCache()
    return _cache_instance


def cleanup_cache():
    """Cleanup the global cache"""
    global _cache_instance
    if _cache_instance:
        _cache_instance.clear()
        _cache_instance = None
