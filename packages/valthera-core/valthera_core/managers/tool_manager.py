
class ToolManager:
    def __init__(self):
        self.tools = {}

    def register_tool(self, name, tool):
        """Register a new tool with the manager."""
        self.tools[name] = tool

    def get_tool(self, name):
        """Retrieve a tool by name."""
        return self.tools.get(name)

    def execute_tool(self, name, *args, **kwargs):
        """Execute a tool by name with the given arguments."""
        tool = self.get_tool(name)
        if tool:
            return tool(*args, **kwargs)
        else:
            raise ValueError(f"Tool '{name}' not found.")
