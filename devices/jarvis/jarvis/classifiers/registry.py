#!/usr/bin/env python3

"""
Classifier registry system for Jarvis smart CV pipeline.

This module provides dynamic classifier management, shared model loading,
and a registry system for managing multiple AI models efficiently.
"""

import logging
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..models.base import UnifiedDetection, ClassifierType, ClassifierStats

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a model"""
    name: str
    path: str
    model_type: str  # "yolo", "face", "pose", etc.
    classes: Optional[List[int]] = None  # Specific classes to detect
    confidence_threshold: float = 0.5
    version: Optional[str] = None


class BaseClassifier(ABC):
    """Abstract base class for all classifiers"""
    
    def __init__(self, name: str, config: ModelConfig):
        self.name = name
        self.config = config
        self.is_initialized = False
        self.model = None
        self.stats = ClassifierStats(name=name, is_enabled=True)
        self._lock = threading.Lock()
        
    @abstractmethod
    def _load_model(self) -> Any:
        """Load the model. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[UnifiedDetection]:
        """Detect objects in frame. Must be implemented by subclasses."""
        pass
    
    def initialize(self) -> bool:
        """Initialize the classifier"""
        with self._lock:
            if self.is_initialized:
                return True
            
            try:
                self.model = self._load_model()
                self.is_initialized = True
                logger.info(f"[CLASSIFIER] {self.name} initialized successfully")
                return True
            except Exception as e:
                logger.error(f"[CLASSIFIER] Failed to initialize {self.name}: {e}")
                self.is_initialized = False
                return False
    
    def cleanup(self):
        """Cleanup classifier resources"""
        with self._lock:
            if self.model:
                try:
                    # Most models don't need explicit cleanup
                    self.model = None
                    self.is_initialized = False
                    logger.info(f"[CLASSIFIER] {self.name} cleaned up")
                except Exception as e:
                    logger.error(f"[CLASSIFIER] Error cleaning up {self.name}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get classifier statistics"""
        return {
            "name": self.stats.name,
            "is_enabled": self.stats.is_enabled,
            "is_initialized": self.is_initialized,
            "total_detections": self.stats.total_detections,
            "last_detection_time": self.stats.last_detection_time,
            "average_processing_time_ms": self.stats.average_processing_time_ms,
            "model_version": self.stats.model_version,
            "config": {
                "model_type": self.config.model_type,
                "confidence_threshold": self.config.confidence_threshold,
                "classes": self.config.classes
            }
        }
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the classifier"""
        self.stats.is_enabled = enabled
        logger.info(f"[CLASSIFIER] {self.name} {'enabled' if enabled else 'disabled'}")


class SharedModelManager:
    """Manage shared models to reduce memory usage"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self._lock = threading.Lock()
        
        # Default model configurations
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default model configurations"""
        self.model_configs = {
            "yolo_base": ModelConfig(
                name="yolo_base",
                path="yolov8n.pt",
                model_type="yolo",
                classes=None,  # All 80 COCO classes
                confidence_threshold=0.5,
                version="8.0"
            ),
            "yolo_person": ModelConfig(
                name="yolo_person",
                path="yolov8n.pt",
                model_type="yolo",
                classes=[0],  # Person only
                confidence_threshold=0.5,
                version="8.0"
            ),
            "face_detector": ModelConfig(
                name="face_detector",
                path="yolov8n.pt",  # Using YOLO for now, can be replaced
                model_type="yolo",
                classes=None,  # Will filter for faces
                confidence_threshold=0.5,
                version="8.0"
            )
        }
    
    def get_model(self, model_key: str) -> Optional[Any]:
        """Get shared model instance"""
        with self._lock:
            if model_key not in self.models:
                config = self.model_configs.get(model_key)
                if not config:
                    logger.error(f"[MODEL_MANAGER] Unknown model key: {model_key}")
                    return None
                
                try:
                    self.models[model_key] = self._load_model(config)
                    logger.info(f"[MODEL_MANAGER] Loaded shared model: {model_key}")
                except Exception as e:
                    logger.error(f"[MODEL_MANAGER] Failed to load model {model_key}: {e}")
                    return None
            
            return self.models[model_key]
    
    def _load_model(self, config: ModelConfig) -> Any:
        """Load a model based on configuration"""
        if config.model_type == "yolo":
            return self._load_yolo_model(config)
        else:
            raise ValueError(f"Unknown model type: {config.model_type}")
    
    def _load_yolo_model(self, config: ModelConfig) -> Any:
        """Load YOLO model"""
        try:
            from ultralytics import YOLO
            model = YOLO(config.path)
            logger.info(f"[MODEL_MANAGER] YOLO model loaded: {config.path}")
            return model
        except ImportError:
            logger.error("[MODEL_MANAGER] YOLO not available")
            raise
        except Exception as e:
            logger.error(f"[MODEL_MANAGER] Error loading YOLO model: {e}")
            raise
    
    def cleanup(self):
        """Cleanup all shared models"""
        with self._lock:
            for model_key, model in self.models.items():
                try:
                    # Most models don't need explicit cleanup
                    logger.info(f"[MODEL_MANAGER] Cleaned up model: {model_key}")
                except Exception as e:
                    logger.error(f"[MODEL_MANAGER] Error cleaning up {model_key}: {e}")
            
            self.models.clear()


class ClassifierRegistry:
    """Dynamic classifier management system"""
    
    def __init__(self):
        self.classifiers: Dict[str, BaseClassifier] = {}
        self.model_manager = SharedModelManager()
        self._lock = threading.Lock()
        
        # Register available classifier types
        self._classifier_types: Dict[str, Type[BaseClassifier]] = {}
    
    def register_classifier_type(self, classifier_type: str, classifier_class: Type[BaseClassifier]):
        """Register a new classifier type"""
        self._classifier_types[classifier_type] = classifier_class
        logger.info(f"[REGISTRY] Registered classifier type: {classifier_type}")
    
    def create_classifier(self, name: str, classifier_type: str, config: Optional[ModelConfig] = None) -> Optional[BaseClassifier]:
        """Create a new classifier instance"""
        if classifier_type not in self._classifier_types:
            logger.error(f"[REGISTRY] Unknown classifier type: {classifier_type}")
            return None
        
        if config is None:
            # Use default config based on classifier type
            config = self._get_default_config(classifier_type)
        
        try:
            classifier_class = self._classifier_types[classifier_type]
            classifier = classifier_class(name, config)
            
            with self._lock:
                self.classifiers[name] = classifier
            
            logger.info(f"[REGISTRY] Created classifier: {name} ({classifier_type})")
            return classifier
            
        except Exception as e:
            logger.error(f"[REGISTRY] Failed to create classifier {name}: {e}")
            return None
    
    def _get_default_config(self, classifier_type: str) -> ModelConfig:
        """Get default configuration for classifier type"""
        if classifier_type == "person":
            return self.model_manager.model_configs["yolo_person"]
        elif classifier_type == "object":
            return self.model_manager.model_configs["yolo_base"]
        elif classifier_type == "face":
            return self.model_manager.model_configs["face_detector"]
        else:
            # Default to base YOLO
            return self.model_manager.model_configs["yolo_base"]
    
    def get_classifier(self, name: str) -> Optional[BaseClassifier]:
        """Get classifier by name"""
        with self._lock:
            return self.classifiers.get(name)
    
    def get_enabled_classifiers(self) -> List[BaseClassifier]:
        """Get all enabled classifiers"""
        with self._lock:
            return [c for c in self.classifiers.values() if c.stats.is_enabled]
    
    def initialize_classifier(self, name: str) -> bool:
        """Initialize a specific classifier"""
        classifier = self.get_classifier(name)
        if not classifier:
            logger.error(f"[REGISTRY] Classifier not found: {name}")
            return False
        
        return classifier.initialize()
    
    def initialize_all(self) -> Dict[str, bool]:
        """Initialize all classifiers"""
        results = {}
        with self._lock:
            for name, classifier in self.classifiers.items():
                results[name] = classifier.initialize()
        
        return results
    
    def cleanup_classifier(self, name: str):
        """Cleanup a specific classifier"""
        classifier = self.get_classifier(name)
        if classifier:
            classifier.cleanup()
    
    def cleanup_all(self):
        """Cleanup all classifiers and models"""
        with self._lock:
            for classifier in self.classifiers.values():
                classifier.cleanup()
            
            self.classifiers.clear()
        
        self.model_manager.cleanup()
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        with self._lock:
            return {
                "total_classifiers": len(self.classifiers),
                "enabled_classifiers": len(self.get_enabled_classifiers()),
                "available_types": list(self._classifier_types.keys()),
                "classifiers": {
                    name: classifier.get_stats() 
                    for name, classifier in self.classifiers.items()
                },
                "shared_models": {
                    key: {"loaded": key in self.model_manager.models}
                    for key in self.model_manager.model_configs.keys()
                }
            }
    
    def list_classifiers(self) -> List[Dict[str, Any]]:
        """List all classifiers with their status"""
        with self._lock:
            return [
                {
                    "name": name,
                    "type": classifier.__class__.__name__,
                    "enabled": classifier.stats.is_enabled,
                    "initialized": classifier.is_initialized,
                    "stats": classifier.get_stats()
                }
                for name, classifier in self.classifiers.items()
            ]


# Global registry instance
_registry_instance: Optional[ClassifierRegistry] = None


def get_registry() -> ClassifierRegistry:
    """Get the global classifier registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ClassifierRegistry()
    return _registry_instance


def cleanup_registry():
    """Cleanup the global registry"""
    global _registry_instance
    if _registry_instance:
        _registry_instance.cleanup_all()
        _registry_instance = None
