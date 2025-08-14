# DROID Behavioral Cloning Example

This example demonstrates a complete pipeline for behavioral cloning on the DROID dataset using Valthera's robotics components.

## Overview

The example implements:

1. **Dataset Processing**: Downloads and processes the DROID robot manipulation dataset
2. **Mock V-JEPA2 Embeddings**: Simulates vision encoder outputs (replace with actual V-JEPA2 model)
3. **Behavioral Cloning Training**: Trains a policy network on vision features and robot actions
4. **Model Evaluation**: Evaluates the trained model's performance
5. **Inference Demo**: Shows how to use the trained model for robot control

## Features

- **Modular Architecture**: Clean separation between vision encoder, policy network, and training
- **Mock Data Generation**: Creates synthetic data for demonstration (replace with real DROID data)
- **Configurable Training**: Adjustable hyperparameters for different scenarios
- **Comprehensive Evaluation**: Multiple metrics for pose, gripper, and stop signal prediction
- **Production Ready**: Includes checkpointing, logging, and deployment utilities

## Quick Start

### 1. Install Dependencies

```bash
cd packages/valthera/examples
pip install -r requirements.txt
```

### 2. Run the Example

```bash
# Basic run with default settings
python droid_behavioral_cloning.py

# Custom configuration
python droid_behavioral_cloning.py \
    --num_videos 100 \
    --epochs 30 \
    --batch_size 32 \
    --learning_rate 5e-5
```

### 3. Command Line Options

- `--num_videos`: Number of videos to process (default: 50)
- `--epochs`: Training epochs (default: 20)
- `--batch_size`: Batch size (default: 16)
- `--learning_rate`: Learning rate (default: 1e-4)
- `--sequence_length`: Sequence length for training (default: 32)
- `--data_root`: Path to DROID dataset (default: "droid_100")

## Architecture

### Components

1. **VisionEncoder**: Mock V-JEPA2 encoder (replace with actual model)
   - CNN backbone for feature extraction
   - Configurable output dimensions
   - Freezable for transfer learning

2. **PolicyNetwork**: Recurrent policy for action prediction
   - GRU/LSTM-based architecture
   - Outputs: pose deltas, gripper state, stop signal
   - Configurable hidden dimensions and layers

3. **BehavioralCloningModel**: End-to-end model combining vision and policy
   - Manages component interactions
   - Handles checkpointing and deployment
   - Configurable freezing strategies

4. **BehavioralCloningTrainer**: Training orchestration
   - Data loading and preprocessing
   - Loss computation and optimization
   - Validation and evaluation

### Data Flow

```
DROID Videos → Vision Encoder → Features → Policy Network → Robot Actions
     ↓              ↓           ↓           ↓              ↓
  RGB Frames   Mock V-JEPA2  Embeddings  GRU/LSTM    [dx,dy,dz,dyaw,grip,stop]
```

## Customization

### Using Real V-JEPA2 Model

Replace the mock encoder in `VisionEncoder`:

```python
# In vision_encoder.py
def _create_encoder(self):
    # Load your actual V-JEPA2 model
    from your_vjepa2_module import load_vjepa2_model
    encoder = load_vjepa2_model()
    return encoder
```

### Custom Robot Actions

Modify the action space in `PolicyNetwork`:

```python
# Change output dimensions for your robot
self.output_dim = config.get("output_dim", 8)  # e.g., 7-DoF arm + gripper
```

### Different Training Strategies

Extend the trainer for your needs:

```python
class CustomTrainer(BehavioralCloningTrainer):
    def compute_loss(self, predictions, targets):
        # Add your custom loss functions
        custom_loss = self.compute_custom_loss(predictions, targets)
        return super().compute_loss(predictions, targets) + custom_loss
```

## Real DROID Dataset

To use the actual DROID dataset:

1. **Download**: Use Google Cloud Storage
   ```bash
   gsutil -m cp -r gs://gresearch/robotics/droid_100 .
   ```

2. **Process**: Update `DROIDDataProcessor._create_mock_dataset()` to load real data

3. **Vision Features**: Replace mock embeddings with actual V-JEPA2 outputs

## Performance Tips

- **GPU Training**: Set `device="cuda"` for faster training
- **Batch Size**: Increase batch size if memory allows
- **Sequence Length**: Adjust based on your robot's temporal dependencies
- **Data Augmentation**: Add image augmentation for better generalization

## Evaluation Metrics

The model is evaluated on:

- **Pose MAE**: Mean absolute error in pose delta predictions
- **Grip Accuracy**: Binary accuracy for gripper state prediction
- **Stop Accuracy**: Binary accuracy for stop signal prediction

## Deployment

### Load Trained Model

```python
from valthera.models.components.behavioral_cloning import BehavioralCloningModel

# Load model
model = BehavioralCloningModel()
model.load_checkpoint("checkpoints/droid_bc_model.pt")

# Run inference
features = vision_encoder.encode(camera_frame)
action = model.predict_action(features)
```

### Robot Integration

```python
# Convert predictions to robot commands
pose_delta = action['dpose']  # [dx, dy, dz, dyaw]
gripper_cmd = action['grip'] > 0.5
stop_cmd = action['stop'] > 0.7

# Send to robot
robot.move_relative(pose_delta)
robot.set_gripper(gripper_cmd)
if stop_cmd:
    robot.stop()
```

## Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce batch size or sequence length
2. **Import Errors**: Ensure you're in the correct directory and dependencies are installed
3. **CUDA Issues**: Set `device="cpu"` for CPU-only training

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To extend this example:

1. **Add New Models**: Implement new vision encoders or policy networks
2. **Support More Datasets**: Add loaders for other robot datasets
3. **Advanced Training**: Implement curriculum learning, multi-task training, etc.
4. **Real-time Control**: Add real-time inference and robot control loops

## References

- [DROID Dataset Paper](https://arxiv.org/abs/2303.04731)
- [V-JEPA2 Paper](https://arxiv.org/abs/2401.10104)
- [Behavioral Cloning Survey](https://arxiv.org/abs/2006.09359)

## License

This example is part of the Valthera project and follows the same license terms.
