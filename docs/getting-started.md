# Getting Started with Valthera

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/valthera.git
cd valthera
```

2. Install dependencies using Make:
```bash
make install
```

This will install all required dependencies for:
- valthera (core)
- valthera-langchain
- valthera-tools

## Basic Usage

### 1. Create a Simple Agent

```python
from valthera.core.prompt import Prompt
from valthera.core.agent import Agent, AgentResponse
from valthera.core.tool import Tool

class SimpleAgent(Agent):
    def handle_prompt(self, prompt: Prompt) -> AgentResponse:
        response_text = f"Processed: {prompt.text}"
        return AgentResponse(response_text=response_text)

    def register_tool(self, tool: Tool) -> None:
        pass
```

### 2. Set Up a Workflow

```python
from valthera.managers.workflow import WorkflowManager

# Initialize workflow manager
workflow_manager = WorkflowManager()

# Create and register your agent
agent = SimpleAgent()
workflow_manager.add_workflow('simple_workflow', [agent.handle_prompt])

# Create and execute a prompt
prompt = Prompt(text="Hello, Valthera!")
response = workflow_manager.execute_workflow('simple_workflow', prompt)
print(response.response_text)
```

### 3. Using LangChain Integration

```python
from valthera_langchain.graph import LangChainGraph
from valthera_langchain.nodes import ProcessingNode, FinalNode

# Create a graph
graph = LangChainGraph()

# Add nodes
processor = ProcessingNode(chain_type="processor", model_name="gpt-4")
finalizer = FinalNode(chain_type="finalizer", model_name="gpt-4")

# Set up the graph
graph.add_node("processor", processor)
graph.add_node("finalizer", finalizer)
graph.set_entrypoint("processor")
graph.add_edge("processor", "finalizer")

# Execute
initial_state = {"input": "What's the weather like?"}
result = await graph.execute(initial_state)
```

## Development Setup

For development work:

```bash
# Install in development mode
make develop

# Run tests
make test

# Clean build artifacts
make clean
```

## Next Steps

- Check out the [API Reference](./api-reference.md) for detailed documentation
- See [Examples](./examples.md) for more usage patterns
- Read about [Advanced Features](./advanced-features.md)
