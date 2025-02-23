from valthera.managers.workflow import Workflow, WorkflowStep, WorkflowManager
from valthera.core.prompt import Prompt
from valthera.core.agent import AgentResponse

# Sample action functions
def agent_action(prompt: Prompt) -> AgentResponse:
    return AgentResponse(response_text=f"Agent processed: {prompt.text}")

def human_action(prompt: Prompt) -> AgentResponse:
    return AgentResponse(response_text=f"Human processed: {prompt.text}")

# Sample workflows
def create_single_agent_workflow():
    steps = [
        WorkflowStep(name="Agent Step 1", action=agent_action),
        WorkflowStep(name="Agent Step 2", action=agent_action)
    ]
    return Workflow(name="Single Agent Workflow", steps=steps)

def create_multi_agent_workflow():
    steps = [
        WorkflowStep(name="Agent Step 1", action=agent_action),
        WorkflowStep(name="Agent Step 2", action=agent_action),
        WorkflowStep(name="Agent Step 3", action=agent_action)
    ]
    return Workflow(name="Multi Agent Workflow", steps=steps)

def create_human_in_the_loop_workflow():
    steps = [
        WorkflowStep(name="Agent Step 1", action=agent_action),
        WorkflowStep(name="Human Step 1", action=human_action),
        WorkflowStep(name="Agent Step 2", action=agent_action)
    ]
    return Workflow(name="Human in the Loop Workflow", steps=steps)

# Example usage
if __name__ == "__main__":
    manager = WorkflowManager()

    single_agent_workflow = create_single_agent_workflow()
    multi_agent_workflow = create_multi_agent_workflow()
    human_in_the_loop_workflow = create_human_in_the_loop_workflow()

    manager.add_workflow(single_agent_workflow)
    manager.add_workflow(multi_agent_workflow)
    manager.add_workflow(human_in_the_loop_workflow)

    prompt = Prompt(text="Sample prompt text")

    print(manager.execute_workflow("Single Agent Workflow", prompt))
    print(manager.execute_workflow("Multi Agent Workflow", prompt))
    print(manager.execute_workflow("Human in the Loop Workflow", prompt))
