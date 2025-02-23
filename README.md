# Valthera

A CLI tool for processing prompts.

## High-Level Overview

1. **Valthera (Core)**
   - **Purpose**: Provide a generic framework for building agent services.
   - **Key Responsibilities**:
     - Define core abstractions and interfaces for Agents, Tool usage, multi-agent orchestration, and human-in-the-loop flows.
     - Provide a “workflow orchestration” engine that decides how prompts are routed to either a single agent, multiple cooperating agents, or a human reviewer.
     - Expose base classes and contracts (e.g. Agent Base, Tool interface, etc.) that can be extended by domain-specific implementations (LangChain-based or CrewAI-based, etc.).
     - Maintain core design patterns so that modules like `valthera-langchain` or `valthera-crewai` can reuse the same set of abstractions.

2. **Valthera-LangChain**
   - **Purpose**: An implementation of the core abstractions defined in Valthera using LangChain.
   - **Key Responsibilities**:
     - Implement Valthera’s agent interface using LangChain’s agent primitives (Chains, LLM wrappers, memory, etc.).
     - Provide ready-made building blocks (Chains, Tools, Memory) that integrate seamlessly with Valthera’s base designs.
     - Serve as a reference implementation (or “plugin”) to show how to build an agent using a 3rd-party library (LangChain).

3. **Valthera-Tools**
   - **Purpose**: A library of reusable “Tools” (e.g. data retrieval, web search, external API calls, calculators, etc.) that can be leveraged by any agent built on Valthera.
   - **Key Responsibilities**:
     - Each tool is a self-contained module that implements a `Tool` interface from Valthera’s core abstractions.
     - Provide a standardized mechanism for registering and configuring new tools.
     - Support both general-purpose and specialized tools, so any agent in Valthera or Valthera-LangChain can dynamically use them.

## Installation

To install the Valthera packages, run the following commands:

```sh
# Clone the repository
git clone https://github.com/yourusername/valthera.git
cd valthera

# Install dependencies for all packages
make install
```

## Usage

Here is a sample usage of the Valthera framework:

```python
# filepath: /Users/vijayselvaraj/Development/valthera/sample_usage.py
from valthera.core.prompt import Prompt
from valthera.core.agent import AgentResponse
from valthera.managers.workflow import WorkflowManager
from valthera.utils.logging import setup_logger
from valthera.utils.config import load_config

# Setup logger
logger = setup_logger('valthera_logger', 'valthera.log')

# Load configuration
config = load_config('config.ini')

# Define a simple agent
class SimpleAgent(Agent):
    def handle_prompt(self, prompt: Prompt) -> AgentResponse:
        response_text = f"Received prompt: {prompt.text}"
        return AgentResponse(response_text=response_text)

    def register_tool(self, tool: Tool) -> None:
        pass

# Initialize workflow manager and register the agent
workflow_manager = WorkflowManager()
simple_agent = SimpleAgent()
workflow_manager.add_workflow('simple_workflow', [simple_agent.handle_prompt])

# Create a prompt and execute the workflow
prompt = Prompt(text="Hello, Valthera!")
response = workflow_manager.execute_workflow('simple_workflow', prompt)
print(response.response_text)
```

## Project Structure

```plaintext
valthera/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── index.md
│   └── ... (additional documentation files)
├── tests/
│   ├── __init__.py
│   └── test_*.py (unit tests for valthera core)
└── valthera/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── agent.py         # Generic Agent interface/abstract class
    │   ├── multi_agent.py   # MultiAgentManager (abstract or base)
    │   ├── human_loop.py    # HumanInTheLoopManager (abstract or base)
    │   ├── tool.py          # Base Tool interface
    │   └── prompt.py        # Base Prompt/PromptProcessor abstractions
    ├── managers/
    │   ├── __init__.py
    │   ├── workflow.py      # WorkflowEngine / Orchestration logic
    │   └── tool_manager.py  # ToolManager (register and manage tools)
    └── utils/
        ├── __init__.py
        ├── logging.py       # Logging helpers
        └── config.py        # Central config management (env vars, etc.)
```

---

## 1. High-Level Overview

1. **Valthera (Core)**  
   - **Purpose**: Provide a generic framework for building agent services.  
   - **Key Responsibilities**:
     - Define core abstractions and interfaces for Agents, Tool usage, multi-agent orchestration, and human-in-the-loop flows.
     - Provide a “workflow orchestration” engine that decides how prompts are routed to either a single agent, multiple cooperating agents, or a human reviewer.
     - Expose base classes and contracts (e.g. Agent Base, Tool interface, etc.) that can be extended by domain-specific implementations (LangChain-based or CrewAI-based, etc.).
     - Maintain core design patterns so that modules like `valthera-langchain` or `valthera-crewai` can reuse the same set of abstractions.

2. **Valthera-LangChain**  
   - **Purpose**: An implementation of the core abstractions defined in Valthera using LangChain.  
   - **Key Responsibilities**:
     - Implement Valthera’s agent interface using LangChain’s agent primitives (Chains, LLM wrappers, memory, etc.).
     - Provide ready-made building blocks (Chains, Tools, Memory) that integrate seamlessly with Valthera’s base designs.
     - Serve as a reference implementation (or “plugin”) to show how to build an agent using a 3rd-party library (LangChain).

3. **Valthera-Tools**  
   - **Purpose**: A library of reusable “Tools” (e.g. data retrieval, web search, external API calls, calculators, etc.) that can be leveraged by any agent built on Valthera.  
   - **Key Responsibilities**:
     - Each tool is a self-contained module that implements a `Tool` interface from Valthera’s core abstractions.
     - Provide a standardized mechanism for registering and configuring new tools.
     - Support both general-purpose and specialized tools, so any agent in Valthera or Valthera-LangChain can dynamically use them.

---

## 2. Architecture & Module Responsibilities

```plaintext
+--------------------------+
|      valthera (Core)     |
| - Core Abstractions &    |    <- Abstract base classes:
|   Interfaces             |       * Agent
| - Agent Workflow Engine  |       * MultiAgentManager
| - Orchestration Logic    |       * Tool / ToolManager
| - Generic Tools Registry |       * Prompt / PromptProcessor
+-----------^--------------+
            | implements
+-----------+--------------+       +----------------------+
|  valthera-langchain     |       | valthera-tools       |
| - LangChain Integration |       | - Concrete Tools     |
| - LLM / Memory Mgmt     |       | - Tools Registry     |
| - Chain / Prompt Mgmt   |       |   (e.g. WebSearch,   |
+-------------------------+       |    Calc, Database)   |
                                  +----------------------+
```

### 2.1 Valthera (Core)

- **Agent** (Abstract Class or Interface)  
  - `Agent` defines the interface for processing prompts, generating responses, handling sub-requests, and orchestrating the flow of conversation.  
  - Methods might include:
    ```python
    class Agent(ABC):
        @abstractmethod
        def handle_prompt(self, prompt: Prompt) -> AgentResponse:
            pass

        @abstractmethod
        def register_tool(self, tool: Tool) -> None:
            pass
    ```

- **MultiAgentManager**  
  - Facilitates multi-agent scenarios:
    - Splits tasks among multiple agents.
    - Gathers outputs, merges or orchestrates them.
    - Possibly has a pluggable strategy for concurrency or sequential calls.

- **HumanInTheLoopManager**  
  - Provides an interface for deciding when to escalate requests to a human.
  - Could define triggers, thresholds, or rules that indicate the agent’s confidence is too low.

- **Tool** (Interface)  
  - Represents any “action” an agent can perform outside of its own local context.  
  - Example interface:
    ```python
    class Tool(ABC):
        @abstractmethod
        def run(self, input_data: Any) -> Any:
            pass
        
        @property
        @abstractmethod
        def name(self) -> str:
            pass
        
        @property
        @abstractmethod
        def description(self) -> str:
            pass
    ```

- **ToolManager**  
  - Loads, registers, and routes calls to available tools.
  - Enforces authentication, usage policies, or concurrency strategies if needed.

- **Prompt / PromptProcessor**  
  - A minimal prompt container or message structure that can be extended by domain-specific implementations (e.g. a LangChain wrapper).
  - Handles base-level validations, structure, or formatting rules for prompts.

- **Orchestration Logic**  
  - Core logic that decides if a prompt should be handled by a single agent, multi-agent, or escalated to a human.  
  - In practice, might be a “router” service or a “WorkflowEngine” that implements:
    ```python
    class WorkflowEngine:
        def route_prompt(self, prompt: Prompt) -> AgentResponse:
            # Evaluate prompt, choose agent(s), handle multi-agent, etc.
            ...
    ```

> **Goal**: Keep Valthera package “agnostic” to any specific LLM or library. Provide only the building blocks and interfaces.

### 2.2 Valthera-LangChain

- **LangChainAgent** (Concrete Implementation of `Agent`)  
  - Uses LangChain’s `LLMChain` or `Agent` classes under the hood.
  - Adapts the `handle_prompt(...)` method to:
    - Convert `Prompt` into a LangChain-compatible format.
    - Execute the chain (or chain-of-thought).
    - Parse the output back into a `AgentResponse`.

  ```python
  class LangChainAgent(Agent):
      def __init__(self, llm_chain: LLMChain):
          self.llm_chain = llm_chain
          self.tools = []

      def handle_prompt(self, prompt: Prompt) -> AgentResponse:
          # Convert to LangChain format
          # Use llm_chain to get a response
          # Return as an AgentResponse
          ...

      def register_tool(self, tool: Tool) -> None:
          # Possibly wrap a valthera Tool into a LangChain Tool
          ...
  ```

- **LangChainMultiAgentManager** (Implements `MultiAgentManager`)  
  - If multiple LangChain-based agents are needed, or each agent has a separate memory or chain, this manager orchestrates them using concurrency or a conversation-based approach.

- **Memory Integration**  
  - Define how memory is handled (e.g. short-term memory, conversation memory, vector stores).  
  - This logic can be quite specialized to LangChain (like `ConversationBufferMemory`, `VectorStoreRetrieverMemory`, etc.).

- **PromptManager**  
  - Extends the base `PromptProcessor` from Valthera to leverage LangChain’s prompt templates, allowing advanced prompt formatting, variable injection, etc.

Overall, **Valthera-LangChain** is the “bridge” between the generic abstractions from **Valthera** and the concrete implementations that use **LangChain**.

### 2.3 Valthera-Tools

- **Implementations of `Tool`**  
  - Each tool is a Python module or class that implements the `Tool` interface from Valthera.  
  - Examples:
    - **WebSearchTool**: Takes a query string, uses an external API (e.g. Bing, Google) to fetch results.
    - **CalculatorTool**: Evaluates math expressions.
    - **DBQueryTool**: Connects to a database, runs queries, returns results.

  ```python
  class WebSearchTool(Tool):
      def __init__(self, api_key: str):
          self._api_key = api_key

      @property
      def name(self) -> str:
          return "web_search"

      @property
      def description(self) -> str:
          return "Performs web searches using an external API"

      def run(self, input_data: str) -> Any:
          # Implementation logic to call external search API
          ...
  ```

- **Tool Registry**  
  - A library-level registry or set of factories that allow easy discovery of tools.  
  - Could be used by `ToolManager` in Valthera to automatically register new tool classes.

- **Extensibility**  
  - Tools can be mixed and matched with any agent in Valthera.
  - A developer can create new specialized tools (e.g. “GraphPlotTool”, “FinancialDataRetriever”, etc.) and share them as a plugin or library.

---

## 3. Technical Workflow Examples

### 3.1 Single Agent Workflow

1. A user sends a `Prompt` to Valthera’s `WorkflowEngine`.
2. `WorkflowEngine` decides a single agent is sufficient, and forwards the prompt to a `LangChainAgent` (implemented in valthera-langchain).
3. The `LangChainAgent` processes the prompt:
   - Possibly calls `ToolManager` to see which tools are available if it needs external data.
   - Uses `LLMChain` to craft a response.
4. The response is returned to `WorkflowEngine`, which then returns it to the user.

### 3.2 Multi-Agent Workflow

1. A user sends a complex `Prompt` to the `WorkflowEngine`.
2. The `WorkflowEngine` uses a `MultiAgentManager` to break down the prompt into sub-tasks or sub-prompts.
3. Each sub-prompt is routed to different agents (LangChain-based or even future CrewAI-based).
4. Each agent might use tools from `Valthera-Tools` for specialized tasks.
5. The manager merges or aggregates responses from the sub-agents.
6. The final answer is returned to the user.

### 3.3 Human-in-the-Loop Escalation

1. A user sends a prompt that triggers an alert (e.g. the system detects a high risk or low confidence scenario).
2. The `WorkflowEngine` delegates to `HumanInTheLoopManager` for a decision.
3. The manager notifies a human operator or sends an email with the partial agent output for approval.
4. The human operator can provide feedback or override decisions.
5. The final, human-reviewed response is returned to the user.

---

## 4. Technical Considerations & Best Practices

1. **Maintain Strict Separation of Concerns**  
   - Keep **Valthera** purely interface-driven and free from external library references.  
   - Ensure **Valthera-LangChain** is the only place that references LangChain, so we can easily add new implementations (like **Valthera-CrewAI**).

2. **Dependency Injection**  
   - For maximum testability, design each component to accept dependencies (e.g. Tools, Agents, LLM configurations) via constructor injection or a factory pattern.

3. **Plugin Architecture for Tools**  
   - Provide a mechanism for third parties or users to implement custom tools and simply register them with the core.  
   - Could be as simple as placing the tool class in a directory recognized by `ToolManager`, or using an entry-point mechanism in `pyproject.toml`.

4. **Interface Versioning**  
   - As interfaces evolve, use semantic versioning or interface version checks to maintain backward compatibility.

5. **Configuration Management**  
   - Provide a centralized way to manage configuration (API keys, database credentials, timeouts).  
   - Could integrate with environment variables, `.env` files, or a separate config service.

6. **Security & Rate-Limiting**  
   - Tools that access external APIs or manipulate local data should enforce permission checks.  
   - Where appropriate, implement rate-limiting to avoid overloading external services.

7. **Observability & Logging**  
   - Provide hooks for logging each step of prompt processing, tool calls, and agent decisions.  
   - This helps with debugging the chain-of-thought and auditing multi-agent interactions.

8. **Testing & Validation**  
   - Valthera (core) can have unit tests that verify the correctness of the interfaces and orchestration flows with mock agents or mock tools.  
   - Valthera-LangChain can have integration tests verifying the synergy between Valthera’s abstractions and LangChain’s features.

---

## 5. Example Code Sketch

Below is a simplified snippet to illustrate the synergy among packages.

**valthera/core/agent.py**:

```python
from abc import ABC, abstractmethod

class Agent(ABC):
    @abstractmethod
    def handle_prompt(self, prompt: "Prompt") -> "AgentResponse":
        pass

    @abstractmethod
    def register_tool(self, tool: "Tool") -> None:
        pass
```

**valthera/core/tool.py**:

```python
from abc import ABC, abstractmethod

class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def run(self, input_data: dict) -> dict:
        pass
```

**valthera-langchain/agent.py**:

```python
from valthera.core.agent import Agent
from langchain import LLMChain

class LangChainAgent(Agent):
    def __init__(self, llm_chain: LLMChain):
        self.llm_chain = llm_chain
        self.tools = {}

    def handle_prompt(self, prompt: "Prompt") -> "AgentResponse":
        # Convert Prompt to text
        text_input = prompt.to_string()
        # Possibly do some tool lookups if needed
        response_text = self.llm_chain.run(text_input)
        return AgentResponse(response_text)

    def register_tool(self, tool: "Tool") -> None:
        self.tools[tool.name] = tool
```

**valthera-tools/web_search.py**:

```python
from valthera.core.tool import Tool
import requests

class WebSearchTool(Tool):
    def __init__(self, api_key: str):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Perform a web search with a given query string"

    def run(self, input_data: dict) -> dict:
        query = input_data.get("query", "")
        # Call external service
        results = requests.get("https://api.example.com/search", params={"q": query, "key": self._api_key})
        return results.json()
```

---

## 6. Roadmap & Future Steps

- **Short Term**  
  1. Finalize Valthera’s core interfaces (Agent, MultiAgentManager, Tool, Prompt, etc.).  
  2. Implement a baseline `WorkflowEngine` that can route prompts to a single agent.  
  3. Create initial library of tools (WebSearch, Calculator, etc.).

- **Mid Term**  
  1. Expand multi-agent capabilities in **Valthera**: concurrency, conversation orchestration, error handling.  
  2. Develop advanced memory and state management solutions in **Valthera-LangChain**.  
  3. Provide a robust plugin mechanism for `valthera-tools`.

- **Long Term**  
  1. Add **Valthera-CrewAI** integration using the same interfaces.  
  2. Introduce real-time collaboration among multiple agents or user groups.  
  3. Strengthen orchestration logic with advanced routing heuristics (confidence thresholds, usage analytics, etc.).

---

## Conclusion

By keeping **Valthera** focused on generic interfaces and orchestration while leveraging **Valthera-langchain** for LangChain-specific implementations and **Valthera-tools** for a wide range of add-on functionalities, this architecture remains flexible, extensible, and maintainable. It allows for the easy addition of new agent frameworks, specialized tools, and advanced workflows (like human-in-the-loop or multi-agent systems) without forcing changes at the core level.