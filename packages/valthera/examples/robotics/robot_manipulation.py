"""Example: Robot manipulation using Valthera.

This example demonstrates how to use Valthera for behavioral cloning
in robotics tasks using the DROID dataset.
"""

import os
import logging
from pathlib import Path

from valthera import BC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    logger.info("Starting robot manipulation example...")
    
    # Initialize BC system for robotics domain
    bc = BC(
        domain="robotics",
        dataset="droid",
        model="gru",
        observations=["vision", "proprioception"],
        actions=["delta_pose"]
    )
    
    logger.info(f"Initialized BC system:")
    logger.info(f"  Domain: {bc.domain}")
    logger.info(f"  Dataset: {bc.dataset_name}")
    logger.info(f"  Model: {bc.model_name}")
    logger.info(f"  Observations: {bc.observation_types}")
    logger.info(f"  Actions: {bc.action_types}")
    
    # Load training data
    # Note: In practice, you would have actual DROID dataset
    data_path = input("Enter path to DROID dataset (or press Enter to use dummy data): ").strip()
    
    if data_path and os.path.exists(data_path):
        logger.info(f"Loading data from: {data_path}")
        bc.load_data(data_path)
    else:
        logger.info("Using dummy data for demonstration")
        # Create dummy data for demonstration
        create_dummy_data(bc)
    
    # Train the model
    logger.info("Starting training...")
    try:
        results = bc.train(
            epochs=10,  # Small number for demo
            batch_size=16,
            learning_rate=1e-4
        )
        logger.info("Training completed successfully!")
        logger.info(f"Training results: {results}")
        
        # Evaluate the model
        logger.info("Evaluating model...")
        metrics = bc.evaluate()
        logger.info("Evaluation completed!")
        logger.info("Metrics:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")
        
        # Save the model
        save_path = "models/robot_manipulation"
        os.makedirs(save_path, exist_ok=True)
        bc.save(save_path)
        logger.info(f"Model saved to: {save_path}")
        
        # Deploy the model
        logger.info("Deploying model...")
        deployment = bc.deploy()
        logger.info("Model deployed successfully!")
        
        # Demonstrate prediction
        logger.info("Demonstrating prediction...")
        demonstrate_prediction(bc)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        logger.exception("Full error traceback")


def create_dummy_data(bc):
    """Create dummy data for demonstration purposes."""
    logger.info("Creating dummy training data...")
    
    # Create dummy observations and actions
    import numpy as np
    
    # Dummy observations (simulating vision + proprioception)
    num_samples = 1000
    vision_features = np.random.randn(num_samples, 512)  # Vision features
    proprio_features = np.random.randn(num_samples, 64)  # Proprioception features
    
    # Dummy actions (delta pose: 3 pos + 4 quat)
    actions = np.random.randn(num_samples, 7)
    
    # Store in dataset
    bc.dataset.observations = []
    bc.dataset.actions = []
    
    for i in range(num_samples):
        # Create observation dictionary
        obs = {
            "rgb": f"dummy_rgb_{i}.png",
            "depth": f"dummy_depth_{i}.npy",
            "joint_pos": f"dummy_joint_{i}.npy"
        }
        bc.dataset.observations.append(obs)
        
        # Create action
        bc.dataset.actions.append(actions[i])
    
    logger.info(f"Created {num_samples} dummy samples")


def demonstrate_prediction(bc):
    """Demonstrate making predictions with the trained model."""
    logger.info("Making predictions on dummy observations...")
    
    # Create dummy observations
    import numpy as np
    
    dummy_obs = []
    for i in range(5):
        obs = {
            "rgb": f"test_rgb_{i}.png",
            "depth": f"test_depth_{i}.npy",
            "joint_pos": f"test_joint_{i}.npy"
        }
        dummy_obs.append(obs)
    
    # Make predictions
    try:
        predictions = bc.predict(dummy_obs)
        logger.info("Predictions made successfully!")
        logger.info(f"Prediction shape: {predictions.shape}")
        logger.info(f"Sample predictions:\n{predictions[:3]}")
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")


if __name__ == "__main__":
    main()
