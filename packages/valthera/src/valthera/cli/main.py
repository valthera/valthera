"""Command-line interface for Valthera."""

import click
import logging
import os
import sys
from pathlib import Path

# Make torch optional
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    from valthera import BC
    from valthera.core.registry import registry
except ImportError as e:
    click.echo(f"Error importing Valthera: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool, quiet: bool):
    """Setup logging based on verbosity flags."""
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


@click.group()
@click.option('--version', is_flag=True, help='Show version and exit')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
@click.option('-q', '--quiet', is_flag=True, help='Suppress logging output')
@click.pass_context
def cli(ctx, version, verbose, quiet):
    """Valthera: Universal Behavioral Cloning Library.
    
    A domain-agnostic library for learning from expert demonstrations across
    multiple domains including robotics, finance, gaming, and autonomous driving.
    """
    if version:
        click.echo("Valthera 0.1.0")
        return
    
    setup_logging(verbose, quiet)
    
    # Ensure context object exists
    if ctx.obj is None:
        ctx.obj = {}


@cli.command()
@click.option('--domain', '-d', required=True, help='Domain (robotics, finance, gaming)')
@click.option('--dataset', help='Dataset name')
@click.option('--model', help='Model architecture')
@click.option('--observations', '-o', multiple=True, help='Observation processor types')
@click.option('--actions', '-a', multiple=True, help='Action processor types')
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--data-path', required=True, help='Path to training data')
@click.option('--output-dir', default='./output', help='Output directory for model')
@click.option('--epochs', default=100, help='Number of training epochs')
@click.option('--batch-size', default=32, help='Training batch size')
@click.option('--learning-rate', default=0.001, help='Learning rate')
@click.option('--train-ratio', default=0.8, help='Training/validation split ratio')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def train(domain, dataset, model, observations, actions, config, data_path, 
          output_dir, epochs, batch_size, learning_rate, train_ratio, verbose):
    """Train a behavioral cloning model."""
    try:
        # Convert observations and actions to lists if provided
        obs_list = list(observations) if observations else None
        act_list = list(actions) if actions else None
        
        # Initialize BC
        bc = BC(
            domain=domain,
            dataset=dataset,
            observations=obs_list,
            actions=act_list,
            model=model,
            config_path=config
        )
        
        # Load data
        click.echo(f"Loading data from {data_path}...")
        bc.load_data(data_path)
        
        # Train model
        click.echo("Starting training...")
        training_config = {
            'epochs': epochs,
            'batch_size': batch_size,
            'learning_rate': learning_rate
        }
        
        results = bc.train(train_ratio=train_ratio, **training_config)
        
        # Save model
        os.makedirs(output_dir, exist_ok=True)
        model_path = os.path.join(output_dir, 'model.pt')
        bc.save(model_path)
        
        click.echo(f"Training completed! Model saved to {model_path}")
        click.echo(f"Training results: {results}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        if verbose:
            raise
        sys.exit(1)


@cli.command()
@click.option('--model-path', required=True, help='Path to trained model')
@click.option('--test-data', help='Path to test data')
@click.option('--output-file', help='Output file for evaluation results')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def evaluate(model_path, test_data, output_file, verbose):
    """Evaluate a trained behavioral cloning model."""
    try:
        # Load model
        click.echo(f"Loading model from {model_path}...")
        bc = BC(domain="unknown")  # Domain will be loaded from saved model
        bc.load(model_path)
        
        # Evaluate model
        click.echo("Evaluating model...")
        if test_data:
            metrics = bc.evaluate(test_data_path=test_data)
        else:
            metrics = bc.evaluate()
        
        # Display results
        click.echo("Evaluation Results:")
        for metric, value in metrics.items():
            click.echo(f"  {metric}: {value:.4f}")
        
        # Save results if output file specified
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            click.echo(f"Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        if verbose:
            raise
        sys.exit(1)


@cli.command()
@click.option('--model-path', required=True, help='Path to trained model')
@click.option('--deployment-config', help='Path to deployment configuration')
@click.option('--output-dir', default='./deployment', help='Output directory for deployment')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def deploy(model_path, deployment_config, output_dir, verbose):
    """Deploy a trained behavioral cloning model."""
    try:
        # Load model
        click.echo(f"Loading model from {model_path}...")
        bc = BC(domain="unknown")  # Domain will be loaded from saved model
        bc.load(model_path)
        
        # Load deployment config if provided
        config = None
        if deployment_config:
            import yaml
            with open(deployment_config, 'r') as f:
                config = yaml.safe_load(f)
        
        # Deploy model
        click.echo("Deploying model...")
        deployment = bc.deploy(config=config)
        
        # Save deployment info
        os.makedirs(output_dir, exist_ok=True)
        deployment_info = {
            'model_path': model_path,
            'deployment_type': type(deployment).__name__,
            'status': 'deployed'
        }
        
        import json
        with open(os.path.join(output_dir, 'deployment_info.json'), 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        click.echo(f"Model deployed successfully! Deployment info saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        if verbose:
            raise
        sys.exit(1)


@cli.command()
@click.option('--component-type', help='Filter by component type')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def list_components(component_type, verbose):
    """List available components."""
    try:
        if component_type:
            components = registry.list_components(component_type)
            click.echo(f"Available {component_type} components:")
            for comp in components:
                config = registry.get_config(component_type, comp)
                click.echo(f"  {comp}: {config}")
        else:
            component_types = registry.list_components()
            click.echo("Available component types:")
            for comp_type in component_types:
                components = registry.list_components(comp_type)
                click.echo(f"  {comp_type}: {components}")
                
    except Exception as e:
        logger.error(f"Failed to list components: {e}")
        if verbose:
            raise
        sys.exit(1)


@cli.command()
@click.option('--domain', required=True, help='Domain name for the template')
@click.option('--output-dir', default='./domain_template', help='Output directory for template')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def create_template(domain, output_dir, verbose):
    """Create a template for a new domain."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Create domain directory structure
        domain_dir = os.path.join(output_dir, domain)
        os.makedirs(domain_dir, exist_ok=True)
        
        # Create __init__.py
        init_content = f'''"""Template domain components for Valthera."""

# TODO: Implement {domain} domain components
# - datasets.py: Dataset loaders for your domain
# - observations.py: Observation processors for your domain
# - actions.py: Action processors for your domain
# - configs/default.yaml: Default configuration for your domain

__all__ = []
'''
        
        with open(os.path.join(domain_dir, '__init__.py'), 'w') as f:
            f.write(init_content)
        
        # Create configs directory and default config
        configs_dir = os.path.join(domain_dir, 'configs')
        os.makedirs(configs_dir, exist_ok=True)
        
        config_content = f'''# Default configuration for {domain} domain
domain: {domain}

# Dataset configuration
dataset: default
dataset_config:
  observation_keys: ["default"]
  action_keys: ["default"]

# Model configuration
model: mlp
model_config:
  hidden_size: 256
  num_layers: 2
  dropout: 0.1

# Observation processors
observations: ["tabular"]
observation_configs:
  tabular:
    feature_dim: 64
    normalize: true

# Action processor
actions: ["continuous"]
action_configs:
  continuous:
    action_dim: 1
    normalize: true
    clip_actions: true

# Training configuration
training:
  batch_size: 32
  learning_rate: 0.001
  epochs: 100
  optimizer: "adam"
  scheduler: "cosine"
  weight_decay: 0.0001
  gradient_clip: 1.0

  # Loss configuration
  loss:
    type: "mse"
    reduction: "mean"

  # Validation
  val_split: 0.2
  early_stopping: true
  patience: 10

  # Logging
  log_interval: 100
  save_interval: 1000
  tensorboard: false
  wandb: false

# Deployment configuration
deployment:
  model_format: "torchscript"
  quantization: false
  batch_inference: true
  max_batch_size: 64
'''
        
        with open(os.path.join(configs_dir, 'default.yaml'), 'w') as f:
            f.write(config_content)
        
        click.echo(f"Domain template created in {domain_dir}")
        click.echo("Edit the files to implement your domain-specific components.")
        
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        if verbose:
            raise
        sys.exit(1)


@cli.command()
def info():
    """Show information about the Valthera installation."""
    try:
        click.echo("Valthera: Universal Behavioral Cloning Library")
        click.echo(f"Version: {BC.__module__.__version__ if hasattr(BC.__module__, '__version__') else '0.1.0'}")
        click.echo(f"Python: {sys.version}")
        
        if TORCH_AVAILABLE:
            click.echo(f"PyTorch: {torch.__version__}")
        else:
            click.echo("PyTorch: Not available")
        
        click.echo(f"Registry components: {len(registry.list_components())}")
        
        # Show available domains
        domains = ["robotics", "finance", "gaming"]
        click.echo(f"Supported domains: {', '.join(domains)}")
        
    except Exception as e:
        logger.error(f"Failed to get info: {e}")
        raise


if __name__ == '__main__':
    cli()
