#!/usr/bin/env python3
"""
DROID GIF Extractor - Complete Fixed Version

This script extracts real robot videos from the DROID dataset generated with old TFDS versions
and creates GIFs with three-camera concatenated views, with comprehensive debugging and parsing.
"""

import os
import sys
import argparse
import logging
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from PIL import Image

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def as_gif(images, path="temp.gif"):
    """Create GIF from images (exact copy of working function)."""
    # Render the images as the gif (15Hz control frequency):
    images[0].save(path, save_all=True, append_images=images[1:], duration=int(1000/15), loop=0)
    gif_bytes = open(path, "rb").read()
    return gif_bytes


class DROIDGIFExtractor:
    """Extract DROID robot videos from old TFDS format with comprehensive parsing."""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.samples_dir = self.output_dir / "samples"
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.samples_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_gifs(self, max_episodes: int = 5) -> bool:
        """Extract DROID episodes as GIFs from old TFDS format."""
        logger.info(f"Extracting {max_episodes} different DROID episodes from old TFDS format...")
        
        try:
            import tensorflow as tf
            import tensorflow_datasets as tfds
            
            logger.info(f"✅ TensorFlow {tf.__version__} imported")
            logger.info(f"✅ TFDS {tfds.__version__} imported")
            
            # Find the dataset directory
            dataset_dir = self._find_dataset_directory()
            if not dataset_dir:
                logger.error("Could not find dataset directory")
                return False
            
            logger.info(f"📁 Using dataset directory: {dataset_dir}")
            
            # Check for dataset_info.json
            self._check_dataset_info(dataset_dir)
            
            # Load TFRecord files directly
            logger.info("🔄 Loading TFRecord files directly...")
            dataset = self._load_tfrecords_directly(dataset_dir)
            
            if not dataset:
                logger.error("❌ Could not load dataset from TFRecord files")
                return False
            
            logger.info("✅ Dataset loaded from TFRecord files!")
            
            episodes_processed = 0
            
            # Process the TFRecord dataset
            for record_idx, serialized_example in enumerate(dataset):
                if episodes_processed >= max_episodes:
                    break
                
                try:
                    episode_id = f"droid_episode_{episodes_processed:06d}"
                    logger.info(f"\n🎬 Processing episode {episodes_processed + 1}/{max_episodes}: {episode_id}")
                    logger.info(f"   From record {record_idx}")
                    
                    # Debug first few records to understand structure
                    if record_idx < 2:
                        logger.info(f"🔍 Debugging record {record_idx} structure...")
                        self._debug_tfrecord_structure(serialized_example)
                    
                    # Parse the TFRecord example with all methods
                    episode_data = self._parse_tfrecord_comprehensive(serialized_example)
                    
                    if not episode_data or not episode_data.get('steps'):
                        logger.warning(f"❌ No valid episode data extracted for record {record_idx}")
                        continue
                    
                    # Extract images from parsed data
                    images = self._extract_images_from_parsed_data(episode_data)
                    
                    if not images:
                        logger.warning(f"❌ No images extracted for episode {episode_id}")
                        continue
                    
                    if len(images) < 3:
                        logger.warning(f"❌ Too few frames ({len(images)}) for episode {episode_id}")
                        continue
                    
                    logger.info(f"   ✅ Extracted {len(images)} frames")
                    
                    # Create sample directory
                    sample_dir = self.samples_dir / episode_id
                    sample_dir.mkdir(exist_ok=True)
                    
                    # Create GIF using exact working function
                    gif_path = sample_dir / "robot_video.gif"
                    as_gif(images, str(gif_path))
                    
                    # Also save in main samples directory
                    main_gif_path = self.samples_dir / f"{episode_id}.gif"
                    as_gif(images, str(main_gif_path))
                    
                    # Save individual frames
                    frames_dir = sample_dir / "frames"
                    frames_dir.mkdir(exist_ok=True)
                    
                    for i, img in enumerate(images):
                        frame_path = frames_dir / f"frame_{i:04d}.png"
                        img.save(frame_path)
                    
                    # Create metadata
                    metadata = {
                        'episode_id': episode_id,
                        'source_record': record_idx,
                        'num_frames': len(images),
                        'frame_rate': '15Hz',
                        'camera_views': self._get_detected_camera_names(episode_data),
                        'concatenation': 'horizontal_three_camera',
                        'extraction_info': {
                            'timestamp': datetime.now().isoformat(),
                            'extractor_version': '15.0.0_comprehensive_debug',
                            'extraction_method': 'Comprehensive TFRecord parsing with debugging',
                            'note': 'Real DROID robot manipulation video - old TFDS format',
                            'status': 'Full video extraction with GIF creation',
                            'tfds_compatibility': 'Old format (<=3.2.1) parsed with comprehensive methods'
                        },
                        'episode_structure': self._get_episode_structure_info(episode_data)
                    }
                    
                    with open(sample_dir / "metadata.json", "w") as f:
                        json.dump(metadata, f, indent=2)
                    
                    # Save summary
                    summary = {
                        'episode_id': episode_id,
                        'source_record': record_idx,
                        'num_frames': len(images),
                        'gif_path': str(gif_path),
                        'main_gif_path': str(main_gif_path),
                        'frames_dir': str(frames_dir),
                        'extraction_method': 'Comprehensive TFRecord parsing',
                        'note': f'Real DROID robot video from record {record_idx}'
                    }
                    
                    with open(sample_dir / "summary.json", "w") as f:
                        json.dump(summary, f, indent=2)
                    
                    episodes_processed += 1
                    logger.info(f"   ✅ Episode {episode_id} completed successfully!")
                    logger.info(f"   📁 GIF saved: {gif_path}")
                    logger.info(f"   📁 Main GIF: {main_gif_path}")
                    logger.info(f"   🖼️  {len(images)} frames saved in: {frames_dir}")
                
                except Exception as e:
                    logger.error(f"Record {record_idx} processing failed: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if episodes_processed > 0:
                logger.info(f"\n✅ Successfully processed {episodes_processed} episodes from old TFDS format!")
                logger.info(f"📁 Output directory: {self.output_dir}")
                logger.info(f"📁 Samples directory: {self.samples_dir}")
                return True
            else:
                logger.error("❌ No episodes were successfully processed")
                return False
            
        except Exception as e:
            logger.error(f"DROID GIF extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _find_dataset_directory(self) -> Optional[Path]:
        """Find the dataset directory."""
        version_dir = self.input_dir / "1.0.0"
        if version_dir.exists():
            return version_dir
        return self.input_dir
    
    def _check_dataset_info(self, dataset_dir: Path):
        """Check dataset_info.json for clues about data structure."""
        try:
            info_file = dataset_dir / "dataset_info.json"
            if info_file.exists():
                logger.info("📋 Found dataset_info.json")
                with open(info_file, 'r') as f:
                    info = json.load(f)
                
                # Log relevant info
                if 'features' in info:
                    logger.info("📝 Dataset features structure:")
                    self._log_features_structure(info['features'], "  ")
                
                if 'name' in info:
                    logger.info(f"📊 Dataset name: {info['name']}")
                if 'version' in info:
                    logger.info(f"📊 Dataset version: {info['version']}")
            else:
                logger.info("📋 No dataset_info.json found")
        except Exception as e:
            logger.debug(f"Error reading dataset_info.json: {e}")
    
    def _log_features_structure(self, features, prefix=""):
        """Recursively log features structure."""
        try:
            if isinstance(features, dict):
                for key, value in features.items():
                    if isinstance(value, dict):
                        logger.info(f"{prefix}{key}:")
                        self._log_features_structure(value, prefix + "  ")
                    else:
                        logger.info(f"{prefix}{key}: {value}")
        except Exception as e:
            logger.debug(f"Error logging features: {e}")
    
    def _load_tfrecords_directly(self, dataset_dir: Path):
        """Load TFRecord files directly from the dataset directory."""
        try:
            import tensorflow as tf
            
            # Find all TFRecord files
            tfrecord_files = []
            
            # Simple patterns
            simple_patterns = ["*.tfrecord", "*.tfrecord-*"]
            
            for pattern in simple_patterns:
                tfrecord_files.extend(list(dataset_dir.glob(pattern)))
            
            # Check subdirectories
            for subdir in dataset_dir.iterdir():
                if subdir.is_dir():
                    for pattern in simple_patterns:
                        tfrecord_files.extend(list(subdir.glob(pattern)))
            
            # Manual search
            if not tfrecord_files:
                logger.info("No TFRecord files found with standard patterns, searching all files...")
                for root, dirs, files in os.walk(dataset_dir):
                    for file in files:
                        if 'tfrecord' in file.lower() or file.endswith('.tfrecord'):
                            tfrecord_files.append(Path(root) / file)
            
            if not tfrecord_files:
                logger.error(f"No TFRecord files found in {dataset_dir}")
                self._examine_directory_structure(dataset_dir)
                return None
            
            logger.info(f"Found {len(tfrecord_files)} TFRecord files:")
            for f in tfrecord_files[:5]:
                logger.info(f"  - {f.name}")
            if len(tfrecord_files) > 5:
                logger.info(f"  ... and {len(tfrecord_files) - 5} more")
            
            # Create dataset from TFRecord files
            file_paths = [str(f) for f in tfrecord_files]
            dataset = tf.data.TFRecordDataset(file_paths)
            
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to load TFRecord files: {e}")
            return None
    
    def _examine_directory_structure(self, dataset_dir: Path):
        """Examine and log the directory structure."""
        try:
            logger.info(f"📂 Examining directory structure of: {dataset_dir}")
            
            def log_directory_contents(path: Path, prefix="", max_depth=3, current_depth=0):
                if current_depth > max_depth:
                    return
                
                try:
                    items = list(path.iterdir())
                    items.sort(key=lambda x: (x.is_file(), x.name))
                    
                    for item in items[:20]:
                        if item.is_dir():
                            logger.info(f"{prefix}📁 {item.name}/")
                            if current_depth < max_depth:
                                log_directory_contents(item, prefix + "  ", max_depth, current_depth + 1)
                        else:
                            size = item.stat().st_size
                            size_str = self._format_file_size(size)
                            logger.info(f"{prefix}📄 {item.name} ({size_str})")
                    
                    if len(items) > 20:
                        logger.info(f"{prefix}... and {len(items) - 20} more items")
                        
                except Exception as e:
                    logger.info(f"{prefix}❌ Error reading directory: {e}")
            
            log_directory_contents(dataset_dir)
            
        except Exception as e:
            logger.error(f"Failed to examine directory structure: {e}")
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    
    def _debug_tfrecord_structure(self, serialized_example):
        """Debug the structure of a TFRecord to understand the format."""
        try:
            import tensorflow as tf
            
            logger.info("🔍 Debugging TFRecord structure...")
            
            # Try SequenceExample first
            try:
                seq_example = tf.train.SequenceExample()
                seq_example.ParseFromString(serialized_example.numpy())
                
                logger.info("✅ Successfully parsed as SequenceExample")
                
                # Debug context features
                context = seq_example.context.feature
                logger.info(f"📝 Context features ({len(context)}):")
                for key, feature in list(context.items())[:10]:
                    feature_type = self._get_feature_type_description(feature)
                    logger.info(f"  - {key}: {feature_type}")
                
                # Debug feature lists
                feature_lists = seq_example.feature_lists.feature_list
                logger.info(f"📝 Feature lists ({len(feature_lists)}):")
                for key, feature_list in list(feature_lists.items())[:15]:
                    logger.info(f"  - {key}: {len(feature_list.feature)} timesteps")
                    
                    if len(feature_list.feature) > 0:
                        first_feature = feature_list.feature[0]
                        feature_type = self._get_feature_type_description(first_feature)
                        logger.info(f"    First timestep: {feature_type}")
                
                return "SequenceExample"
                
            except Exception as e:
                logger.info(f"❌ SequenceExample parsing failed: {e}")
            
            # Try standard Example
            try:
                example = tf.train.Example()
                example.ParseFromString(serialized_example.numpy())
                
                logger.info("✅ Successfully parsed as Example")
                
                features = example.features.feature
                logger.info(f"📝 Features ({len(features)}):")
                for key, feature in list(features.items())[:20]:
                    feature_type = self._get_feature_type_description(feature)
                    logger.info(f"  - {key}: {feature_type}")
                
                return "Example"
                
            except Exception as e:
                logger.info(f"❌ Example parsing failed: {e}")
            
            logger.info("❌ Could not parse TFRecord with any known format")
            return None
            
        except Exception as e:
            logger.error(f"TFRecord debugging failed: {e}")
            return None
    
    def _get_feature_type_description(self, feature):
        """Get human-readable description of a feature type."""
        if feature.HasField('bytes_list'):
            count = len(feature.bytes_list.value)
            if count > 0:
                first_bytes_len = len(feature.bytes_list.value[0])
                return f"bytes_list ({count} items, first: {first_bytes_len} bytes)"
            else:
                return f"bytes_list ({count} items)"
        elif feature.HasField('float_list'):
            count = len(feature.float_list.value)
            return f"float_list ({count} values)"
        elif feature.HasField('int64_list'):
            count = len(feature.int64_list.value)
            return f"int64_list ({count} values)"
        else:
            return "unknown"
    
    def _parse_tfrecord_comprehensive(self, serialized_example):
        """Comprehensive parsing of TFRecord with multiple methods."""
        try:
            import tensorflow as tf
            
            # Method 1: SequenceExample (most likely for DROID)
            try:
                seq_example = tf.train.SequenceExample()
                seq_example.ParseFromString(serialized_example.numpy())
                
                result = self._extract_from_sequence_example(seq_example)
                if result and result.get('steps'):
                    logger.debug(f"✅ SequenceExample method extracted {len(result['steps'])} steps")
                    return result
                    
            except Exception as e:
                logger.debug(f"SequenceExample method failed: {e}")
            
            # Method 2: Standard Example
            try:
                example = tf.train.Example()
                example.ParseFromString(serialized_example.numpy())
                
                result = self._extract_from_standard_example(example)
                if result and result.get('steps'):
                    logger.debug(f"✅ Standard Example method extracted {len(result['steps'])} steps")
                    return result
                    
            except Exception as e:
                logger.debug(f"Standard Example method failed: {e}")
            
            # Method 3: TensorFlow feature parsing
            try:
                result = self._parse_with_tensorflow_features(serialized_example)
                if result and result.get('steps'):
                    logger.debug(f"✅ TensorFlow features method extracted {len(result['steps'])} steps")
                    return result
                    
            except Exception as e:
                logger.debug(f"TensorFlow features method failed: {e}")
            
            return None
            
        except Exception as e:
            logger.debug(f"All parsing methods failed: {e}")
            return None
    
    def _extract_from_sequence_example(self, seq_example):
        """Extract data from SequenceExample format."""
        try:
            episode_data = {'steps': []}
            
            # Get feature lists
            feature_lists = seq_example.feature_lists.feature_list
            
            # Find sequence length
            seq_length = 0
            for key, feature_list in feature_lists.items():
                seq_length = max(seq_length, len(feature_list.feature))
            
            if seq_length == 0:
                return None
            
            # Extract steps
            steps_data = []
            for step_idx in range(seq_length):
                step_data = {'observation': {}}
                
                for key, feature_list in feature_lists.items():
                    if step_idx < len(feature_list.feature):
                        feature = feature_list.feature[step_idx]
                        
                        # Handle images
                        if 'image' in key.lower() and feature.HasField('bytes_list') and feature.bytes_list.value:
                            try:
                                image_bytes = feature.bytes_list.value[0]
                                decoded_image = self._decode_image_bytes(image_bytes)
                                if decoded_image is not None:
                                    step_data['observation'][key] = decoded_image
                            except Exception as e:
                                logger.debug(f"Failed to decode image {key}: {e}")
                        
                        # Handle numerical data
                        elif feature.HasField('float_list'):
                            step_data['observation'][key] = list(feature.float_list.value)
                        elif feature.HasField('int64_list'):
                            step_data['observation'][key] = list(feature.int64_list.value)
                
                if step_data['observation']:
                    steps_data.append(step_data)
            
            episode_data['steps'] = steps_data
            return episode_data if steps_data else None
            
        except Exception as e:
            logger.debug(f"SequenceExample extraction failed: {e}")
            return None
    
    def _extract_from_standard_example(self, example):
        """Extract data from standard Example format."""
        try:
            features = example.features.feature
            episode_data = {'steps': [], 'raw_features': {}}
            
            # Store feature info
            for key, feature in features.items():
                episode_data['raw_features'][key] = self._get_feature_type_description(feature)
            
            # Look for nested episode data
            steps_data = []
            
            # Check for serialized steps
            if 'steps' in features:
                try:
                    steps_bytes = features['steps'].bytes_list.value
                    for step_bytes in steps_bytes:
                        step_data = self._parse_step_data(step_bytes)
                        if step_data:
                            steps_data.append(step_data)
                except Exception as e:
                    logger.debug(f"Steps extraction failed: {e}")
            
            # Try to reconstruct from individual features
            if not steps_data:
                steps_data = self._reconstruct_steps_from_flat_features(features)
            
            episode_data['steps'] = steps_data
            return episode_data if steps_data else None
            
        except Exception as e:
            logger.debug(f"Standard example extraction failed: {e}")
            return None
    
    def _parse_step_data(self, step_bytes):
        """Parse individual step data from bytes."""
        try:
            import tensorflow as tf
            
            step_example = tf.train.Example()
            step_example.ParseFromString(step_bytes)
            
            step_data = {'observation': {}}
            features = step_example.features.feature
            
            for key, feature in features.items():
                if 'image' in key and feature.HasField('bytes_list') and feature.bytes_list.value:
                    try:
                        image_bytes = feature.bytes_list.value[0]
                        image = self._decode_image_bytes(image_bytes)
                        if image is not None:
                            step_data['observation'][key] = image
                    except Exception as e:
                        logger.debug(f"Failed to decode image {key}: {e}")
                elif feature.HasField('float_list'):
                    step_data['observation'][key] = list(feature.float_list.value)
                elif feature.HasField('int64_list'):
                    step_data['observation'][key] = list(feature.int64_list.value)
            
            return step_data if step_data['observation'] else None
            
        except Exception as e:
            logger.debug(f"Step parsing failed: {e}")
            return None
    
    def _reconstruct_steps_from_flat_features(self, features):
        """Try to reconstruct steps from flattened features."""
        try:
            # Look for time-series data patterns
            steps_data = []
            
            # Find features that might contain image sequences
            image_features = {}
            for key, feature in features.items():
                if 'image' in key.lower() and feature.HasField('bytes_list'):
                    image_features[key] = feature.bytes_list.value
            
            if not image_features:
                return []
            
            # Determine sequence length
            seq_length = max(len(values) for values in image_features.values()) if image_features else 0
            
            # Create steps
            for step_idx in range(seq_length):
                step_data = {'observation': {}}
                
                for key, values in image_features.items():
                    if step_idx < len(values):
                        try:
                            image_bytes = values[step_idx]
                            decoded_image = self._decode_image_bytes(image_bytes)
                            if decoded_image is not None:
                                step_data['observation'][key] = decoded_image
                        except Exception as e:
                            logger.debug(f"Failed to decode {key}[{step_idx}]: {e}")
                
                if step_data['observation']:
                    steps_data.append(step_data)
            
            return steps_data
            
        except Exception as e:
            logger.debug(f"Step reconstruction failed: {e}")
            return []
    
    def _parse_with_tensorflow_features(self, serialized_example):
        """Parse using TensorFlow's feature parsing with flexible schema."""
        try:
            import tensorflow as tf
            
            # Try multiple feature descriptions
            feature_descriptions = [
                # Standard DROID format
                {
                    'observation/exterior_image_1_left': tf.io.VarLenFeature(tf.string),
                    'observation/exterior_image_2_left': tf.io.VarLenFeature(tf.string),
                    'observation/wrist_image_left': tf.io.VarLenFeature(tf.string),
                },
                # Alternative format
                {
                    'exterior_image_1_left': tf.io.VarLenFeature(tf.string),
                    'exterior_image_2_left': tf.io.VarLenFeature(tf.string),
                    'wrist_image_left': tf.io.VarLenFeature(tf.string),
                },
                # R2D2 format
                {
                    'image': tf.io.VarLenFeature(tf.string),
                    'image_1': tf.io.VarLenFeature(tf.string),
                    'image_2': tf.io.VarLenFeature(tf.string),
                    'image_3': tf.io.VarLenFeature(tf.string),
                }
            ]
            
            for feature_description in feature_descriptions:
                try:
                    parsed = tf.io.parse_single_example(serialized_example, feature_description)
                    
                    episode_data = {'steps': []}
                    steps_data = []
                    
                    # Find sequence length
                    seq_length = 0
                    for key, tensor in parsed.items():
                        if hasattr(tensor, 'values') and len(tensor.values.shape) > 0:
                            seq_length = max(seq_length, tensor.values.shape[0])
                    
                    # Extract steps
                    for step_idx in range(seq_length):
                        step_data = {'observation': {}}
                        
                        for key, tensor in parsed.items():
                            try:
                                if hasattr(tensor, 'values') and step_idx < len(tensor.values):
                                    if 'image' in key:
                                        image_bytes = tensor.values[step_idx].numpy()
                                        decoded_image = self._decode_image_bytes(image_bytes)
                                        if decoded_image is not None:
                                            clean_key = key.replace('observation/', '')
                                            step_data['observation'][clean_key] = decoded_image
                            except Exception as e:
                                logger.debug(f"Failed to extract {key}[{step_idx}]: {e}")
                        
                        if step_data['observation']:
                            steps_data.append(step_data)
                    
                    if steps_data:
                        episode_data['steps'] = steps_data
                        return episode_data
                        
                except Exception as e:
                    logger.debug(f"Feature description failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"TensorFlow features parsing failed: {e}")
            return None
    
    def _decode_image_bytes(self, image_bytes):
        """Decode image from bytes with multiple fallback methods."""
        try:
            import tensorflow as tf
            
            # Method 1: TensorFlow decode_image
            try:
                image_tensor = tf.io.decode_image(image_bytes, channels=3)
                image_array = image_tensor.numpy()
                if image_array.size > 0 and len(image_array.shape) == 3:
                    return image_array
            except Exception as e:
                logger.debug(f"TF decode_image failed: {e}")
            
            # Method 2: JPEG decode
            try:
                image_tensor = tf.io.decode_jpeg(image_bytes, channels=3)
                image_array = image_tensor.numpy()
                if image_array.size > 0 and len(image_array.shape) == 3:
                    return image_array
            except Exception as e:
                logger.debug(f"JPEG decode failed: {e}")
            
            # Method 3: PNG decode
            try:
                image_tensor = tf.io.decode_png(image_bytes, channels=3)
                image_array = image_tensor.numpy()
                if image_array.size > 0 and len(image_array.shape) == 3:
                    return image_array
            except Exception as e:
                logger.debug(f"PNG decode failed: {e}")
            
            # Method 4: PIL decode
            try:
                from PIL import Image as PILImage
                import io
                
                pil_image = PILImage.open(io.BytesIO(image_bytes))
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                image_array = np.array(pil_image)
                if image_array.size > 0 and len(image_array.shape) == 3:
                    return image_array
            except Exception as e:
                logger.debug(f"PIL decode failed: {e}")
            
            return None
            
        except Exception as e:
            logger.debug(f"Image decoding error: {e}")
            return None
    
    def _extract_images_from_parsed_data(self, episode_data):
        """Extract and concatenate images from parsed episode data."""
        try:
            images = []
            steps = episode_data.get('steps', [])
            
            if not steps:
                return []
            
            # Find available camera names
            available_cameras = set()
            for step in steps:
                observation = step.get('observation', {})
                for key in observation.keys():
                    if 'image' in key.lower():
                        available_cameras.add(key)
            
            logger.info(f"   📷 Available cameras: {list(available_cameras)}")
            
            # Define preferred camera mappings
            camera_mappings = [
                # Standard DROID format
                ['exterior_image_1_left', 'exterior_image_2_left', 'wrist_image_left'],
                # Alternative names
                ['observation/exterior_image_1_left', 'observation/exterior_image_2_left', 'observation/wrist_image_left'],
                # Simplified names
                ['image_1', 'image_2', 'image_3'],
                ['camera_1', 'camera_2', 'camera_3'],
                # R2D2 style
                ['exterior_1', 'exterior_2', 'wrist'],
                # Generic
                ['image', 'image1', 'image2'],
            ]
            
            # Find best camera mapping
            selected_cameras = None
            for mapping in camera_mappings:
                if all(cam in available_cameras for cam in mapping):
                    selected_cameras = mapping
                    logger.info(f"   ✅ Using camera mapping: {mapping}")
                    break
            
            # Fallback: use any three available cameras
            if not selected_cameras and len(available_cameras) >= 3:
                selected_cameras = list(available_cameras)[:3]
                logger.info(f"   🔄 Using fallback cameras: {selected_cameras}")
            
            # Single camera fallback
            if not selected_cameras and len(available_cameras) >= 1:
                selected_cameras = [list(available_cameras)[0]]
                logger.info(f"   🔄 Using single camera: {selected_cameras}")
            
            if not selected_cameras:
                logger.warning("   ❌ No image cameras found")
                return []
            
            # Extract frames
            for i, step in enumerate(steps):
                try:
                    observation = step.get('observation', {})
                    
                    # Get camera images
                    camera_images = []
                    for cam_name in selected_cameras:
                        if cam_name in observation:
                            img_array = observation[cam_name]
                            if img_array is not None and hasattr(img_array, 'shape') and img_array.size > 0:
                                # Ensure proper format
                                if img_array.dtype != np.uint8:
                                    if img_array.max() <= 1.0:
                                        img_array = (img_array * 255).astype(np.uint8)
                                    else:
                                        img_array = img_array.astype(np.uint8)
                                camera_images.append(img_array)
                    
                    # Create concatenated frame
                    if len(camera_images) >= 3:
                        # Three camera concatenation
                        try:
                            # Ensure same height
                            min_height = min(img.shape[0] for img in camera_images[:3])
                            resized_images = []
                            for img in camera_images[:3]:
                                if img.shape[0] != min_height:
                                    aspect_ratio = img.shape[1] / img.shape[0]
                                    new_width = int(min_height * aspect_ratio)
                                    img = np.resize(img, (min_height, new_width, 3))
                                resized_images.append(img)
                            
                            concatenated = np.concatenate(resized_images, axis=1)
                            pil_image = Image.fromarray(concatenated)
                            images.append(pil_image)
                        except Exception as e:
                            logger.debug(f"Three-camera concatenation failed for step {i}: {e}")
                            # Fallback to single camera
                            if camera_images:
                                pil_image = Image.fromarray(camera_images[0])
                                images.append(pil_image)
                    
                    elif len(camera_images) == 2:
                        # Two camera concatenation
                        try:
                            min_height = min(img.shape[0] for img in camera_images)
                            resized_images = []
                            for img in camera_images:
                                if img.shape[0] != min_height:
                                    aspect_ratio = img.shape[1] / img.shape[0]
                                    new_width = int(min_height * aspect_ratio)
                                    img = np.resize(img, (min_height, new_width, 3))
                                resized_images.append(img)
                            
                            concatenated = np.concatenate(resized_images, axis=1)
                            pil_image = Image.fromarray(concatenated)
                            images.append(pil_image)
                        except Exception as e:
                            logger.debug(f"Two-camera concatenation failed for step {i}: {e}")
                            if camera_images:
                                pil_image = Image.fromarray(camera_images[0])
                                images.append(pil_image)
                    
                    elif len(camera_images) == 1:
                        # Single camera
                        pil_image = Image.fromarray(camera_images[0])
                        images.append(pil_image)
                
                except Exception as e:
                    logger.debug(f"Step {i} processing failed: {e}")
                    continue
            
            logger.info(f"   📸 Extracted {len(images)} concatenated images")
            return images
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return []
    
    def _get_detected_camera_names(self, episode_data):
        """Get the names of cameras detected in the episode data."""
        try:
            cameras = set()
            for step in episode_data.get('steps', []):
                observation = step.get('observation', {})
                for key in observation.keys():
                    if 'image' in key.lower():
                        cameras.add(key)
            return list(cameras)
        except:
            return []
    
    def _get_episode_structure_info(self, episode_data):
        """Get information about the episode structure."""
        try:
            steps = episode_data.get('steps', [])
            if not steps:
                return {'num_steps': 0, 'observations': []}
            
            # Get observation keys from first step
            first_step = steps[0]
            observation_keys = list(first_step.get('observation', {}).keys())
            
            return {
                'num_steps': len(steps),
                'observation_keys': observation_keys,
                'image_keys': [k for k in observation_keys if 'image' in k.lower()]
            }
        except:
            return {'error': 'Could not extract structure info'}


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="DROID GIF Extractor - Complete Fixed Version")
    parser.add_argument("--input_dir", type=str, required=True,
                       help="Input directory with DROID dataset (old TFDS format)")
    parser.add_argument("--output_dir", type=str, default="droid_gifs_output",
                       help="Output directory for extracted GIFs")
    parser.add_argument("--max_episodes", type=int, default=5,
                       help="Maximum number of episodes to extract as GIFs")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if input directory exists
    input_path = Path(args.input_dir)
    if not input_path.exists():
        logger.error(f"Input directory not found: {args.input_dir}")
        return 1
    
    logger.info(f"Input directory: {input_path}")
    
    # List contents
    contents = list(input_path.iterdir())
    logger.info(f"Directory contents: {[c.name for c in contents]}")
    
    # Extract DROID GIFs from old TFDS format
    extractor = DROIDGIFExtractor(args.input_dir, args.output_dir)
    success = extractor.extract_gifs(args.max_episodes)
    
    if success:
        logger.info("✅ DROID GIF extraction completed successfully!")
        logger.info(f"📁 GIFs and samples saved to: {args.output_dir}")
        logger.info("🎬 Extracted videos from old TFDS format!")
        logger.info("🤖 Three-camera concatenated views showing robot actions!")
        return 0
    else:
        logger.error("❌ DROID GIF extraction failed!")
        logger.info("💡 Try running with --debug for more detailed logging")
        return 1


if __name__ == "__main__":
    exit(main())