# Valthera: Universal Behavioral Cloning Library

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-1.12+-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Valthera is a domain-agnostic behavioral cloning library that enables learning from expert demonstrations across multiple domains including robotics, finance, gaming, and autonomous driving.

## 🚀 Features

- **Domain-Agnostic Design**: Single API for multiple domains
- **Modular Architecture**: Mix and match components
- **Production Ready**: Built-in deployment and monitoring
- **Easy Extension**: Clear patterns for adding new domains
- **Simple API**: Works out of the box with sensible defaults

## 📚 What is Behavioral Cloning?

Behavioral cloning is a technique for learning to imitate expert behavior from observation-action pairs. The agent learns to map observations (like camera images, sensor data, or game states) to actions (like robot movements, trading decisions, or game controls) by mimicking expert demonstrations.

## 🏗️ Architecture

```
valthera/
├── core/                     # Core abstractions and BC class
├── domains/                  # Domain-specific implementations
│   ├── robotics/            # Robot manipulation
│   ├── finance/             # Trading/portfolio management
│   ├── gaming/              # Game AI
│   └── template/            # Template for new domains
├── observations/            # Generic observation processors
├── actions/                 # Generic action processors
├── models/                  # Neural network architectures
├── training/                # Training infrastructure
├── deployment/              # Production deployment
└── analysis/                # Evaluation and visualization
```

## 🚀 Quick Start

### Installation

```bash
# Install with Poetry
poetry install

# Install with development dependencies
poetry install --with dev

# Install with domain-specific dependencies
poetry install --with robotics    # Robotics domain
poetry install --with finance     # Finance domain
poetry install --with gaming      # Gaming domain

# Install with all domain dependencies
poetry install --with robotics,finance,gaming
```

### Basic Usage

```python
from valthera import BC

# Simple usage with defaults
bc = BC(domain="robotics", dataset="droid", model="gru")
bc.load_data("/path/to/data")
bc.train()
policy = bc.deploy()

# Advanced usage with custom components
bc = BC(
    domain="finance",
    observations=["tabular", "text"],
    actions=["portfolio_weights"], 
    model="transformer"
)
```

### Command Line Interface

```bash
# Train a model
valthera train --domain robotics --dataset droid --model gru

# Evaluate a model
valthera evaluate --model-path /path/to/model

# Deploy a model
valthera deploy --model-path /path/to/model

# List available components
valthera list-components

# Create a new domain template
valthera create-template --domain autonomous-driving
```

## 🎯 Supported Domains

### 🤖 Robotics
- **Datasets**: DROID, RoboMimic
- **Observations**: RGB images, depth maps, joint positions
- **Actions**: Delta poses, joint control
- **Models**: GRU, LSTM, Transformer

### 💰 Finance
- **Datasets**: Market data, trading logs
- **Observations**: Price data, indicators, news sentiment
- **Actions**: Portfolio weights, trade decisions
- **Models**: Transformer, Decision Transformer

### 🎮 Gaming
- **Datasets**: Game replays, demonstrations
- **Observations**: Screen capture, game state
- **Actions**: Controller inputs, game commands
- **Models**: CNN, Vision Transformer

## 🔧 Core Components

### Observation Processors
- **Vision**: Image/video processing with CNN, ViT, CLIP
- **Tabular**: Structured data and time series
- **Text**: Language processing
- **Multimodal**: Multi-modal fusion

### Action Processors
- **Continuous**: Continuous action spaces
- **Discrete**: Discrete action spaces
- **Structured**: Complex/hierarchical actions
- **Postprocessing**: Safety, constraints, smoothing

### Models
- **Feedforward**: MLP policies
- **Recurrent**: GRU/LSTM policies
- **Transformer**: Transformer/Decision Transformer
- **Components**: Reusable model components

## 📖 Examples

### Robotics Example

```python
from valthera import BC

# Initialize robotics BC system
bc = BC(domain="robotics")

# Load DROID dataset
bc.load_data("/path/to/droid_dataset")

# Train the model
results = bc.train(epochs=100, batch_size=32)

# Evaluate performance
metrics = bc.evaluate()

# Deploy for real-time inference
deployment = bc.deploy()
```

### Finance Example

```python
from valthera import BC

# Initialize finance BC system
bc = BC(
    domain="finance",
    observations=["tabular", "text"],
    actions=["portfolio_weights"],
    model="transformer"
)

# Load market data
bc.load_data("/path/to/market_data")

# Train trading model
results = bc.train(epochs=200, learning_rate=1e-3)

# Deploy trading bot
trading_bot = bc.deploy()
```

## 🛠️ Development

### Setting up development environment

```bash
git clone https://github.com/valthera/valthera.git
cd valthera
poetry install --with dev
```

### Running tests

```bash
pytest tests/
```

### Code formatting

```bash
black src/
isort src/
```

### Type checking

```bash
mypy src/
```

## 📚 Documentation

- [API Reference](https://valthera.readthedocs.io/api/)
- [Tutorials](https://valthera.readthedocs.io/tutorials/)
- [Examples](https://github.com/valthera/valthera/tree/main/examples)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Adding a New Domain

1. Create a new directory in `src/valthera/domains/`
2. Implement domain-specific components:
   - `datasets.py`: Data loaders
   - `observations.py`: Observation processors
   - `actions.py`: Action processors
   - `configs/default.yaml`: Default configuration
3. Register components using the `@register_component` decorator
4. Add tests and documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by research in behavioral cloning and imitation learning
- Built on PyTorch ecosystem
- Community contributions and feedback

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/valthera/valthera/issues)
- **Discussions**: [GitHub Discussions](https://github.com/valthera/valthera/discussions)
- **Documentation**: [Read the Docs](https://valthera.readthedocs.io/)

## 🔮 Roadmap

- [ ] Multi-agent behavioral cloning
- [ ] Hierarchical imitation learning
- [ ] Meta-learning for few-shot imitation
- [ ] Real-time adaptation
- [ ] Safety and robustness features
- [ ] Web-based training interface
- [ ] Cloud deployment support

---

**Valthera**: Empowering AI agents to learn from human expertise across all domains.
