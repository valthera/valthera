"""Robotics domain datasets for Valthera."""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import numpy as np
from PIL import Image

from ...core.base import BaseDataset
from ...core.registry import register_component

logger = logging.getLogger(__name__)


@register_component("dataset", "droid", is_default=True)
class DROIDDataset(BaseDataset):
    """DROID dataset loader for robot manipulation tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.data_path = None
        self.episode_data = []
        self.observation_keys = config.get("observation_keys", ["rgb", "depth", "joint_pos"])
        self.action_keys = config.get("action_keys", ["delta_pose"])
        
    def load(self, path: str) -> "DROIDDataset":
        """Load DROID dataset from path.
        
        Args:
            path: Path to the DROID dataset directory
            
        Returns:
            Self for method chaining
        """
        self.data_path = path
        logger.info(f"Loading DROID dataset from: {path}")
        
        # Load episode metadata
        metadata_path = os.path.join(path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            # Try to infer structure from directory
            metadata = self._infer_metadata(path)
        
        # Load episode data
        self.episode_data = []
        for episode_info in metadata.get("episodes", []):
            episode_path = os.path.join(path, episode_info["path"])
            if os.path.exists(episode_path):
                episode_data = self._load_episode(episode_path, episode_info)
                self.episode_data.append(episode_data)
        
        # Flatten episode data into observations and actions
        self._flatten_data()
        
        logger.info(f"Loaded {len(self.episode_data)} episodes, {len(self.observations)} total samples")
        return self
    
    def _infer_metadata(self, path: str) -> Dict[str, Any]:
        """Infer dataset structure from directory."""
        episodes = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # Check if it's an episode directory
                if any(os.path.exists(os.path.join(item_path, f)) for f in ["rgb", "depth", "actions.json"]):
                    episodes.append({
                        "path": item,
                        "length": len([f for f in os.listdir(item_path) if f.startswith("rgb")])
                    })
        
        return {"episodes": episodes}
    
    def _load_episode(self, episode_path: str, episode_info: Dict[str, Any]) -> Dict[str, Any]:
        """Load a single episode."""
        episode_data = {
            "observations": [],
            "actions": [],
            "metadata": episode_info
        }
        
        # Load actions
        actions_path = os.path.join(episode_path, "actions.json")
        if os.path.exists(actions_path):
            with open(actions_path, 'r') as f:
                actions = json.load(f)
            episode_data["actions"] = actions
        
        # Load observations
        for i in range(episode_info.get("length", 100)):  # Default episode length
            obs = {}
            
            # Load RGB image
            rgb_path = os.path.join(episode_path, f"rgb_{i:06d}.png")
            if os.path.exists(rgb_path):
                obs["rgb"] = rgb_path
            
            # Load depth image
            depth_path = os.path.join(episode_path, f"depth_{i:06d}.npy")
            if os.path.exists(depth_path):
                obs["depth"] = depth_path
            
            # Load joint positions
            joint_path = os.path.join(episode_path, f"joint_pos_{i:06d}.npy")
            if os.path.exists(joint_path):
                obs["joint_pos"] = joint_path
            
            if obs:  # Only add if we have some observations
                episode_data["observations"].append(obs)
        
        return episode_data
    
    def _flatten_data(self):
        """Flatten episode data into linear sequences."""
        self.observations = []
        self.actions = []
        
        for episode in self.episode_data:
            # Align observations and actions
            min_length = min(len(episode["observations"]), len(episode["actions"]))
            
            for i in range(min_length):
                self.observations.append(episode["observations"][i])
                self.actions.append(episode["actions"][i])
    
    def get_batch(self, batch_size: int, indices: Optional[List[int]] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get a batch of observations and actions.
        
        Args:
            batch_size: Size of the batch
            indices: Specific indices to use (if None, random selection)
            
        Returns:
            Tuple of (observations, actions) tensors
        """
        if indices is None:
            indices = np.random.choice(len(self), size=batch_size, replace=False)
        
        batch_obs = []
        batch_actions = []
        
        for idx in indices:
            obs = self.observations[idx]
            action = self.actions[idx]
            
            # Process observations (simplified - in practice this would use proper processors)
            processed_obs = self._process_observation(obs)
            batch_obs.append(processed_obs)
            
            # Process actions
            processed_action = torch.tensor(action, dtype=torch.float32)
            batch_actions.append(processed_action)
        
        return torch.stack(batch_obs), torch.stack(batch_actions)
    
    def _process_observation(self, obs: Dict[str, str]) -> torch.Tensor:
        """Process a single observation (simplified)."""
        # This is a simplified version - in practice this would use proper processors
        features = []
        
        if "rgb" in obs:
            # Load and resize image
            img = Image.open(obs["rgb"]).convert('RGB')
            img = img.resize((64, 64))  # Simplified resize
            img_array = np.array(img) / 255.0
            features.append(img_array.flatten())
        
        if "depth" in obs:
            # Load depth data
            depth = np.load(obs["depth"])
            depth = depth.flatten()[:1024]  # Simplified flattening
            features.append(depth)
        
        if "joint_pos" in obs:
            # Load joint positions
            joint_pos = np.load(obs["joint_pos"])
            features.append(joint_pos.flatten())
        
        # Combine features
        if features:
            combined = np.concatenate(features)
            return torch.tensor(combined, dtype=torch.float32)
        else:
            return torch.zeros(1024, dtype=torch.float32)  # Fallback
    
    def split(self, train_ratio: float = 0.8) -> Tuple["DROIDDataset", "DROIDDataset"]:
        """Split the dataset into train and validation sets."""
        train_size = int(len(self) * train_ratio)
        train_indices = list(range(train_size))
        val_indices = list(range(train_size, len(self)))
        
        train_dataset = DROIDDataset(self.config)
        val_dataset = DROIDDataset(self.config)
        
        # Copy data
        train_dataset.data_path = self.data_path
        train_dataset.episode_data = self.episode_data
        train_dataset.observations = [self.observations[i] for i in train_indices]
        train_dataset.actions = [self.actions[i] for i in train_indices]
        
        val_dataset.data_path = self.data_path
        val_dataset.episode_data = self.episode_data
        val_dataset.observations = [self.observations[i] for i in val_indices]
        val_dataset.actions = [self.actions[i] for i in val_indices]
        
        return train_dataset, val_dataset


@register_component("dataset", "robomimic")
class RoboMimicDataset(BaseDataset):
    """RoboMimic dataset loader for robot manipulation tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.data_path = None
        self.hdf5_file = None
        self.demo_keys = []
        
    def load(self, path: str) -> "RoboMimicDataset":
        """Load RoboMimic dataset from HDF5 file.
        
        Args:
            path: Path to the HDF5 dataset file
            
        Returns:
            Self for method chaining
        """
        try:
            import h5py
        except ImportError:
            raise ImportError("h5py is required to load RoboMimic datasets. Install with: pip install h5py")
        
        self.data_path = path
        logger.info(f"Loading RoboMimic dataset from: {path}")
        
        with h5py.File(path, 'r') as f:
            self.demo_keys = list(f.keys())
            
            # Load first demo to get structure
            first_demo = f[self.demo_keys[0]]
            obs_keys = list(first_demo['obs'].keys())
            action_keys = list(first_demo['actions'].keys())
            
            logger.info(f"Found {len(self.demo_keys)} demonstrations")
            logger.info(f"Observation keys: {obs_keys}")
            logger.info(f"Action keys: {action_keys}")
            
            # Load all data
            self._load_all_data(f)
        
        return self
    
    def _load_all_data(self, hdf5_file):
        """Load all demonstration data."""
        all_obs = []
        all_actions = []
        
        for demo_key in self.demo_keys:
            demo = hdf5_file[demo_key]
            
            # Get demo length
            demo_length = demo['actions'].shape[0]
            
            # Load observations and actions
            for i in range(demo_length):
                obs = {}
                for obs_key in demo['obs'].keys():
                    obs[obs_key] = demo['obs'][obs_key][i]
                
                action = demo['actions'][i]
                
                all_obs.append(obs)
                all_actions.append(action)
        
        self.observations = all_obs
        self.actions = all_actions
        
        logger.info(f"Loaded {len(self.observations)} total samples")
    
    def get_batch(self, batch_size: int, indices: Optional[List[int]] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get a batch of observations and actions."""
        if indices is None:
            indices = np.random.choice(len(self), size=batch_size, replace=False)
        
        batch_obs = []
        batch_actions = []
        
        for idx in indices:
            obs = self.observations[idx]
            action = self.actions[idx]
            
            # Process observation (simplified)
            processed_obs = self._process_observation(obs)
            batch_obs.append(processed_obs)
            
            # Process action
            processed_action = torch.tensor(action, dtype=torch.float32)
            batch_actions.append(processed_action)
        
        return torch.stack(batch_obs), torch.stack(batch_actions)
    
    def _process_observation(self, obs: Dict[str, np.ndarray]) -> torch.Tensor:
        """Process a single observation (simplified)."""
        features = []
        
        for key, value in obs.items():
            if key in ['robot0_eef_pos', 'robot0_eef_quat']:
                # Robot end-effector pose
                features.append(value.flatten())
            elif key.startswith('robot0_joint'):
                # Joint positions
                features.append(value.flatten())
            elif key.startswith('object'):
                # Object states
                features.append(value.flatten())
            else:
                # Other observations
                features.append(value.flatten())
        
        if features:
            combined = np.concatenate(features)
            return torch.tensor(combined, dtype=torch.float32)
        else:
            return torch.zeros(100, dtype=torch.float32)  # Fallback
    
    def split(self, train_ratio: float = 0.8) -> Tuple["RoboMimicDataset", "RoboMimicDataset"]:
        """Split the dataset into train and validation sets."""
        train_size = int(len(self) * train_ratio)
        train_indices = list(range(train_size))
        val_indices = list(range(train_size, len(self)))
        
        train_dataset = RoboMimicDataset(self.config)
        val_dataset = RoboMimicDataset(self.config)
        
        # Copy data
        train_dataset.data_path = self.data_path
        train_dataset.observations = [self.observations[i] for i in train_indices]
        train_dataset.actions = [self.actions[i] for i in train_indices]
        
        val_dataset.data_path = self.data_path
        val_dataset.observations = [self.observations[i] for i in val_indices]
        val_dataset.actions = [self.actions[i] for i in val_indices]
        
        return train_dataset, val_dataset
