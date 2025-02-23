from abc import ABC, abstractmethod

class LangChainGraph(ABC):
    # ...existing code...

    def _execute_node(self, node, inputs=None):
        """Execute a single node in the graph.

        Args:
            node: The node to execute
            inputs: Optional inputs for the node

        Returns:
            The output of the node execution
        """
        if inputs is None:
            inputs = {}
        
        # Get the node's runnable
        runnable = self.nodes[node]
        
        # Execute the runnable with the provided inputs
        return runnable.invoke(inputs)

    def _validate_node(self, node):
        """Validate that a node exists and is properly configured.

        Args:
            node: The node to validate

        Returns:
            bool: True if the node is valid
        """
        # Check if node exists in the graph
        if node not in self.nodes:
            return False
            
        # Check if node has a valid runnable
        if not hasattr(self.nodes[node], 'invoke'):
            return False
            
        return True
