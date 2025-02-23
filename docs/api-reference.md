# Valthera API Reference

## Core Components

### Agent

```python
class Agent(ABC):
    @abstractmethod
    def handle_prompt(self, prompt: Prompt) -> AgentResponse:
        """Process a prompt and return a response."""
        pass

    @abstractmethod
    def register_tool(self, tool: Tool) -> None:
        """Register a tool for the agent to use."""
        pass
```

### Prompt

```python
class Prompt(BaseModel):
    user_id: Optional[str] = None
    text: str
    metadata: Optional[Dict[str, Any]] = None
```

### Tool

```python
class Tool(ABC, BaseModel):
    name: str
    description: str

    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
```

## Workflow Management

### WorkflowManager

```python
class WorkflowManager:
    def add_workflow(self, name: str, workflow: List[Callable]) -> None:
        """Add a new workflow sequence."""
        pass

    def execute_workflow(self, name: str, *args, **kwargs) -> Any:
        """Execute a named workflow."""
        pass
```

## LangChain Integration

### LangChainGraph

```python
class LangChainGraph:
    def add_node(self, node_id: str, node: LangChainNode) -> None:
        """Add a node to the graph."""
        pass

    def set_entrypoint(self, node_id: str) -> None:
        """Set the graph's entry point."""
        pass

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add a directed edge between nodes."""
        pass

    async def execute(self, initial_state: Dict[str, Any]) -> Any:
        """Execute the graph workflow."""
        pass
```

### LangChainNode

```python
class LangChainNode:
    def __init__(self, chain_type: Optional[str] = None, 
                 model_name: Optional[str] = None):
        pass

    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Override this method to implement node logic."""
        pass
```

## Utility Functions

### Logging Setup

```python
def setup_logger(name: str, 
                log_file: str, 
                level: int = logging.INFO) -> logging.Logger:
    """Configure a logger with file output."""
    pass
```

### Configuration Management

```python
def load_config(file_path: str) -> Config:
    """Load configuration from a file."""
    pass
```

For more detailed information about each component, see:
- [Workflow Engine Documentation](./workflow-engine.md)
- [Tool Development Guide](./tool-development.md)
- [Agent Implementation Guide](./agent-implementation.md)
