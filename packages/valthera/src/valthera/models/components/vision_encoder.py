"""Vision encoder component for Valthera."""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, Union
import cv2

from ...core.base import BaseComponent


class VisionEncoder(BaseComponent, nn.Module):
    """Vision encoder that can serve as a mock V-JEPA2 encoder."""
    
    def __init__(self, config: Optional[dict] = None):
        BaseComponent.__init__(self, config)
        nn.Module.__init__(self)
        
        # Configuration
        self.output_dim = config.get("output_dim", 768)
        self.image_size = config.get("image_size", (224, 224))
        self.use_pretrained = config.get("use_pretrained", False)
        self.freeze_encoder = config.get("freeze_encoder", True)
        
        # Initialize encoder
        self.encoder = self._create_encoder()
        
        # Freeze if requested
        if self.freeze_encoder:
            for param in self.encoder.parameters():
                param.requires_grad = False
        
        self._is_initialized = True
    
    def _create_encoder(self) -> nn.Module:
        """Create the vision encoder network."""
        # Simple CNN backbone as V-JEPA2 substitute
        encoder = nn.Sequential(
            # Conv block 1
            nn.Conv2d(3, 32, 7, stride=2, padding=3),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, stride=2),

            # Conv block 2
            nn.Conv2d(32, 64, 5, stride=2, padding=2),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, stride=2),

            # Conv block 3
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, stride=2),

            # Conv block 4
            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4))
        )

        classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 4 * 4, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(1024, self.output_dim)  # Use dynamic output_dim
        )
        
        return nn.ModuleDict({
            'features': encoder,
            'classifier': classifier
        })
    
    def preprocess_image(self, image: Union[np.ndarray, torch.Tensor]) -> torch.Tensor:
        """Preprocess image for the encoder."""
        if isinstance(image, np.ndarray):
            # Resize and convert to RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                # BGR to RGB conversion
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # OpenCV resize expects (width, height), but image_size is (height, width)
            # So we need to swap the dimensions
            resize_dims = (self.image_size[1], self.image_size[0])  # (width, height)
            image = cv2.resize(image, resize_dims)
            image = image.astype(np.float32) / 255.0
            
            # Normalize with ImageNet stats
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            image = (image - mean) / std
            
            # Convert to tensor and add batch dim
            image = torch.from_numpy(image.transpose(2, 0, 1)).float()
        else:
            # Already a tensor
            image = image.float()
        
        return image
    
    def encode(self, images: Union[np.ndarray, torch.Tensor, list], 
               batch_size: int = 8) -> torch.Tensor:
        """Encode images to features."""
        if not self._is_initialized:
            raise RuntimeError("Encoder not initialized")
        
        if isinstance(images, list):
            # Process list of images
            all_embeddings = []
            
            for i in range(0, len(images), batch_size):
                batch_images = images[i:i+batch_size]
                
                # Preprocess batch
                batch_tensors = []
                for img in batch_images:
                    preprocessed = self.preprocess_image(img)
                    batch_tensors.append(preprocessed)
                
                batch_input = torch.stack(batch_tensors)
                
                with torch.no_grad():
                    batch_embeddings = self.forward(batch_input)
                    all_embeddings.append(batch_embeddings)
            
            # Concatenate all embeddings
            embeddings = torch.cat(all_embeddings, dim=0)
        else:
            # Single image or batch
            if isinstance(images, np.ndarray) and images.ndim == 3:
                # Single image - preprocess first, then add batch dim
                preprocessed = self.preprocess_image(images)
                preprocessed = preprocessed.unsqueeze(0)  # Add batch dimension
            else:
                # Already a batch or tensor
                preprocessed = self.preprocess_image(images)
            
            embeddings = self.forward(preprocessed)
        
        return embeddings
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the encoder."""
        features = self.encoder['features'](x)
        embeddings = self.encoder['classifier'](features)
        return embeddings
    
    def get_feature_dim(self) -> int:
        """Get the output feature dimension."""
        return self.output_dim
    
    def unfreeze(self):
        """Unfreeze the encoder for fine-tuning."""
        for param in self.encoder.parameters():
            param.requires_grad = True
        self.freeze_encoder = False
    
    def freeze(self):
        """Freeze the encoder."""
        for param in self.encoder.parameters():
            param.requires_grad = False
        self.freeze_encoder = True
    
    def parameters(self, recurse: bool = True):
        """Get parameters for the encoder (required for PyTorch compatibility)."""
        return self.encoder.parameters(recurse=recurse)
    
    def state_dict(self):
        """Get state dict for the encoder (required for PyTorch compatibility)."""
        return self.encoder.state_dict()
    
    def load_state_dict(self, state_dict):
        """Load state dict for the encoder (required for PyTorch compatibility)."""
        self.encoder.load_state_dict(state_dict)
