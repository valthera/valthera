from valthera.core.prompt import Prompt
from valthera.core.agent import AgentResponse, Agent
from valthera.core.tool import Tool
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
        logger.info(f"Handling prompt: {prompt.text}")
        return AgentResponse(response_text=response_text)

    def register_tool(self, tool: Tool) -> None:
        pass


# Initialize workflow manager and register the agent
workflow_manager = WorkflowManager()
simple_agent = SimpleAgent()
workflow_manager.add_workflow('simple_workflow', [simple_agent.handle_prompt])

# Create a prompt and execute the workflow
prompt = Prompt(text="Hello, Valthera!")
logger.info(f"Executing workflow with prompt: {prompt.text}")
response = workflow_manager.execute_workflow('simple_workflow', prompt)

# Debugging information
if response is None:
    logger.error("Workflow execution returned None")
else:
    logger.info(f"Workflow execution response: {response.response_text}")
    print(response.response_text)
