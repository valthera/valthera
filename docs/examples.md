# Valthera Examples

## 1. Multi-Agent Workflow

```python
from valthera.core.agent import Agent, AgentResponse
from valthera.core.prompt import Prompt
from valthera.managers.workflow import WorkflowManager

# Define specialized agents
class ResearchAgent(Agent):
    def handle_prompt(self, prompt: Prompt) -> AgentResponse:
        # Perform research tasks
        return AgentResponse(response_text="Research findings...")

class WritingAgent(Agent):
    def handle_prompt(self, prompt: Prompt) -> AgentResponse:
        # Generate written content
        return AgentResponse(response_text="Generated content...")

# Set up workflow
workflow_manager = WorkflowManager()
research_agent = ResearchAgent()
writing_agent = WritingAgent()

# Create multi-step workflow
workflow_manager.add_workflow('content_creation', [
    research_agent.handle_prompt,
    writing_agent.handle_prompt
])

# Execute
prompt = Prompt(text="Write an article about AI")
result = workflow_manager.execute_workflow('content_creation', prompt)
```

## 2. Tool Integration

```python
from valthera.core.tool import Tool
from typing import Dict, Any

class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for information"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query")
        # Implement web search logic
        return {"results": ["result1", "result2"]}

class CalculatorTool(Tool):
    name = "calculator"
    description = "Perform mathematical calculations"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        expression = input_data.get("expression")
        # Implement calculation logic
        return {"result": eval(expression)}

# Register tools with an agent
agent = SimpleAgent()
agent.register_tool(WebSearchTool())
agent.register_tool(CalculatorTool())
```

## 3. LangChain Integration

```python
from valthera_langchain.graph import LangChainGraph
from valthera_langchain.nodes import ProcessingNode, FinalNode
import asyncio

async def run_complex_workflow():
    graph = LangChainGraph()
    
    # Define nodes
    researcher = ProcessingNode(
        chain_type="researcher",
        model_name="gpt-4"
    )
    writer = ProcessingNode(
        chain_type="writer",
        model_name="gpt-4"
    )
    editor = FinalNode(
        chain_type="editor",
        model_name="gpt-4"
    )
    
    # Build graph
    graph.add_node("researcher", researcher)
    graph.add_node("writer", writer)
    graph.add_node("editor", editor)
    
    graph.set_entrypoint("researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "editor")
    
    # Execute
    initial_state = {
        "topic": "AI Ethics",
        "style": "academic",
        "length": "2000 words"
    }
    
    result = await graph.execute(initial_state)
    return result

# Run the workflow
result = asyncio.run(run_complex_workflow())
```

## 4. Error Handling

```python
from valthera.core.agent import Agent, AgentResponse
from valthera.utils.logging import setup_logger

logger = setup_logger('error_handling', 'errors.log')

class RobustAgent(Agent):
    def handle_prompt(self, prompt: Prompt) -> AgentResponse:
        try:
            # Attempt to process prompt
            result = self._process_prompt(prompt)
            return AgentResponse(response_text=result)
        except Exception as e:
            logger.error(f"Error processing prompt: {str(e)}")
            return AgentResponse(
                response_text="An error occurred",
                metadata={"error": str(e)}
            )
```

## 5. Configuration Management

```python
from valthera.utils.config import load_config

# Load configuration
config = load_config('config.ini')

# Access configuration values
api_key = config['api']['key']
model_name = config['model']['name']
max_tokens = int(config['model']['max_tokens'])

# Initialize components with configuration
agent = SimpleAgent(
    model_name=model_name,
    max_tokens=max_tokens
)
```

For more examples and detailed explanations, see:
- [Advanced Workflows](./advanced-workflows.md)
- [Custom Tool Development](./custom-tools.md)
- [Agent Patterns](./agent-patterns.md)
