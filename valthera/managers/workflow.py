import logging
from typing import List, Callable
from pydantic import BaseModel
from valthera.core.prompt import Prompt
from valthera.core.agent import AgentResponse
import json


class WorkflowStep(BaseModel):
    name: str
    action: Callable[[Prompt], AgentResponse]
    agent: str  # Add agent attribute to WorkflowStep


class Workflow(BaseModel):
    name: str
    steps: List<WorkflowStep]


class WorkflowManager:
    def __init__(self):
        self.workflows = {}
        self.logger = logging.getLogger('valthera_logger')

    def add_workflow(self, workflow: Workflow):
        self.workflows[workflow.name] = workflow.steps
        self.logger.info(f"Added workflow: {workflow.name} with steps: {[step.name for step in workflow.steps]}")

    def execute_workflow(self, name: str, prompt: Prompt) -> AgentResponse:
        if name not in self.workflows:
            self.logger.error(f"Workflow {name} not found")
            return None
        
        self.logger.info(f"Executing workflow: {name} with prompt: {prompt.text}")
        steps = self.workflows[name]
        response = None

        for step in steps:
            self.logger.info(f"Executing step: {step.name} with agent: {step.agent}")
            response = step.action(prompt)
            self.logger.info(f"Step response: {response.response_text}")

        return response

    def load_workflow_from_json(self, json_file_path: str):
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            steps = [WorkflowStep(**step) for step in data['steps']]
            workflow = Workflow(name=data['name'], steps=steps)
            self.add_workflow(workflow)
            self.logger.info(f"Loaded workflow from {json_file_path}")

# Example usage
if __name__ == "__main__":
    from valthera.core.prompt import Prompt
    from valthera.core.agent import AgentResponse

    def agent1_action1(prompt: Prompt) -> AgentResponse:
        return AgentResponse(response_text=f"Agent1 processed: {prompt.text}")

    def agent2_action1(prompt: Prompt) -> AgentResponse:
        return AgentResponse(response_text=f"Agent2 processed: {prompt.text}")

    def agent1_action2(prompt: Prompt) -> AgentResponse:
        return AgentResponse(response_text=f"Agent1 processed again: {prompt.text}")

    def agent2_action2(prompt: Prompt) -> AgentResponse:
        return AgentResponse(response_text=f"Agent2 processed again: {prompt.text}")

    step1 = WorkflowStep(name="Agent1Step1", action=agent1_action1, agent="Agent1")
    step2 = WorkflowStep(name="Agent2Step1", action=agent2_action1, agent="Agent2")
    step3 = WorkflowStep(name="Agent1Step2", action=agent1_action2, agent="Agent1")
    step4 = WorkflowStep(name="Agent2Step2", action=agent2_action2, agent="Agent2")

    multi_agent_workflow = Workflow(name="MultiAgentWorkflow", steps=[step1, step2, step3, step4])

    manager = WorkflowManager()
    manager.add_workflow(multi_agent_workflow)

    prompt = Prompt(text="Example prompt for multi-agent workflow")
    response = manager.execute_workflow("MultiAgentWorkflow", prompt)
    print(f"Final response: {response.response_text}")

    # Load workflow from JSON
    manager.load_workflow_from_json('/path/to/langgraph_multi_agent_workflow.json')
    response = manager.execute_workflow("LangGraphMultiAgentWorkflow", prompt)
    print(f"Final response: {response.response_text}")
