"""Example: Trading bot using Valthera.

This example demonstrates how to use Valthera for behavioral cloning
in finance tasks like portfolio management and trading.
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
    logger.info("Starting trading bot example...")
    
    # Initialize BC system for finance domain
    bc = BC(
        domain="finance",
        dataset="market_data",
        model="transformer",
        observations=["tabular", "text"],
        actions=["portfolio_weights"]
    )
    
    logger.info(f"Initialized BC system:")
    logger.info(f"  Domain: {bc.domain}")
    logger.info(f"  Dataset: {bc.dataset_name}")
    logger.info(f"  Model: {bc.model_name}")
    logger.info(f"  Observations: {bc.observation_types}")
    logger.info(f"  Actions: {bc.action_types}")
    
    # Load training data
    data_path = input("Enter path to market data (or press Enter to use dummy data): ").strip()
    
    if data_path and os.path.exists(data_path):
        logger.info(f"Loading data from: {data_path}")
        bc.load_data(data_path)
    else:
        logger.info("Using dummy data for demonstration")
        create_dummy_market_data(bc)
    
    # Train the model
    logger.info("Starting training...")
    try:
        results = bc.train(
            epochs=20,  # Small number for demo
            batch_size=32,
            learning_rate=1e-3
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
        save_path = "models/trading_bot"
        os.makedirs(save_path, exist_ok=True)
        bc.save(save_path)
        logger.info(f"Model saved to: {save_path}")
        
        # Deploy the model
        logger.info("Deploying trading bot...")
        deployment = bc.deploy()
        logger.info("Trading bot deployed successfully!")
        
        # Demonstrate prediction
        logger.info("Demonstrating trading predictions...")
        demonstrate_trading_predictions(bc)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        logger.exception("Full error traceback")


def create_dummy_market_data(bc):
    """Create dummy market data for demonstration purposes."""
    logger.info("Creating dummy market data...")
    
    import numpy as np
    import pandas as pd
    
    # Create dummy market data
    num_samples = 2000
    num_assets = 10
    sequence_length = 50
    
    # Create time series data
    dates = pd.date_range('2023-01-01', periods=num_samples, freq='D')
    
    # Dummy price data (normalized)
    price_data = np.random.randn(num_samples, num_assets) * 0.02 + 1.0
    price_data = np.cumprod(price_data, axis=0)  # Cumulative returns
    
    # Dummy technical indicators
    rsi = np.random.uniform(0, 100, (num_samples, num_assets))
    macd = np.random.randn(num_samples, num_assets) * 0.1
    volume = np.random.uniform(1000, 10000, (num_samples, num_assets))
    
    # Dummy news sentiment (text features)
    sentiment_scores = np.random.uniform(-1, 1, (num_samples, 5))  # 5 sentiment features
    
    # Dummy portfolio weights (actions)
    portfolio_weights = np.random.dirichlet(np.ones(num_assets), num_samples)
    
    # Store in dataset
    bc.dataset.observations = []
    bc.dataset.actions = []
    
    for i in range(num_samples):
        # Create observation dictionary
        obs = {
            "prices": price_data[i],
            "rsi": rsi[i],
            "macd": macd[i],
            "volume": volume[i],
            "sentiment": sentiment_scores[i],
            "date": dates[i]
        }
        bc.dataset.observations.append(obs)
        
        # Create action (portfolio weights)
        bc.dataset.actions.append(portfolio_weights[i])
    
    logger.info(f"Created {num_samples} dummy market data samples")
    logger.info(f"Number of assets: {num_assets}")
    logger.info(f"Features: prices, RSI, MACD, volume, sentiment")


def demonstrate_trading_predictions(bc):
    """Demonstrate making trading predictions with the trained model."""
    logger.info("Making trading predictions on dummy market data...")
    
    import numpy as np
    import pandas as pd
    
    # Create dummy market observations
    num_assets = 10
    dummy_obs = []
    
    for i in range(5):
        obs = {
            "prices": np.random.randn(num_assets) * 0.02 + 1.0,
            "rsi": np.random.uniform(0, 100, num_assets),
            "macd": np.random.randn(num_assets) * 0.1,
            "volume": np.random.uniform(1000, 10000, num_assets),
            "sentiment": np.random.uniform(-1, 1, 5),
            "date": pd.Timestamp.now()
        }
        dummy_obs.append(obs)
    
    # Make predictions
    try:
        predictions = bc.predict(dummy_obs)
        logger.info("Trading predictions made successfully!")
        logger.info(f"Prediction shape: {predictions.shape}")
        
        # Convert to portfolio weights
        portfolio_weights = predictions.numpy()
        
        logger.info("Portfolio weight predictions:")
        for i, weights in enumerate(portfolio_weights[:3]):  # Show first 3
            total_weight = np.sum(weights)
            logger.info(f"  Sample {i+1}: Total weight = {total_weight:.4f}")
            logger.info(f"    Asset weights: {weights[:5]}...")  # Show first 5 assets
        
        # Simulate portfolio performance
        simulate_portfolio_performance(portfolio_weights)
        
    except Exception as e:
        logger.error(f"Trading prediction failed: {e}")


def simulate_portfolio_performance(portfolio_weights):
    """Simulate portfolio performance based on predicted weights."""
    logger.info("Simulating portfolio performance...")
    
    import numpy as np
    
    # Simulate asset returns
    num_samples, num_assets = portfolio_weights.shape
    asset_returns = np.random.randn(num_samples, num_assets) * 0.02  # 2% daily volatility
    
    # Calculate portfolio returns
    portfolio_returns = np.sum(portfolio_weights * asset_returns, axis=1)
    
    # Calculate performance metrics
    total_return = np.prod(1 + portfolio_returns) - 1
    annualized_return = (1 + total_return) ** (252 / num_samples) - 1
    volatility = np.std(portfolio_returns) * np.sqrt(252)
    sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
    
    logger.info("Portfolio Performance Simulation:")
    logger.info(f"  Total Return: {total_return:.4%}")
    logger.info(f"  Annualized Return: {annualized_return:.4%}")
    logger.info(f"  Annualized Volatility: {volatility:.4%}")
    logger.info(f"  Sharpe Ratio: {sharpe_ratio:.4f}")


if __name__ == "__main__":
    main()
