
class WorkflowManager:
    def __init__(self):
        self.workflows = {}

    def add_workflow(self, name, workflow):
        """Add a new workflow to the manager."""
        self.workflows[name] = workflow

    def get_workflow(self, name):
        """Retrieve a workflow by name."""
        return self.workflows.get(name)

    def execute_workflow(self, name, *args, **kwargs):
        """Execute a workflow by name with the given arguments."""
        workflow = self.get_workflow(name)
        if workflow:
            for task in workflow:
                task(*args, **kwargs)
        else:
            raise ValueError(f"Workflow '{name}' not found.")
