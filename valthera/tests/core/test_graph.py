import unittest
from valthera.core.graph import Graph, GraphNode, NodeType
from valthera.core.prompt import Prompt
import tempfile
import os
from rich.console import Console
from io import StringIO

class TestGraph(unittest.TestCase):
    def setUp(self):
        self.sample_graph_data = {
            "nodes": [
                {"id": "start", "type": "router"},
                {"id": "agent1", "type": "agent", "agent_id": "test_agent"},
                {"id": "decision", "type": "decision", "condition": "x > 0"},
                {"id": "end", "type": "router"}
            ],
            "edges": [
                {"from": "start", "to": "agent1"},
                {"from": "agent1", "to": "decision"},
                {"from": "decision", "to": "end"}
            ],
            "entry_points": ["start"],
            "exit_points": ["end"]
        }
        self.valid_graph = Graph.from_dict(self.sample_graph_data)

    def test_graph_creation(self):
        graph = Graph()
        self.assertIsInstance(graph.nodes, dict)
        self.assertIsInstance(graph.edges, dict)
        self.assertIsInstance(graph.entry_points, set)
        self.assertIsInstance(graph.exit_points, set)

    def test_add_node(self):
        graph = Graph()
        node = GraphNode(id="test", type=NodeType.AGENT, agent_id="test_agent")
        graph.add_node(node)
        self.assertIn("test", graph.nodes)
        self.assertEqual(graph.nodes["test"].agent_id, "test_agent")

    def test_add_edge(self):
        graph = Graph()
        node1 = GraphNode(id="node1", type=NodeType.AGENT)
        node2 = GraphNode(id="node2", type=NodeType.AGENT)
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge("node1", "node2")
        self.assertIn("node2", graph.edges["node1"])

    def test_entry_exit_points(self):
        graph = Graph()
        node = GraphNode(id="test", type=NodeType.AGENT)
        graph.add_node(node)
        graph.set_entry_point("test")
        graph.set_exit_point("test")
        self.assertIn("test", graph.entry_points)
        self.assertIn("test", graph.exit_points)

    def test_validate_valid_graph(self):
        self.assertTrue(self.valid_graph.validate())

    def test_validate_unreachable_nodes(self):
        graph = Graph()
        node1 = GraphNode(id="node1", type=NodeType.AGENT)
        node2 = GraphNode(id="node2", type=NodeType.AGENT)
        graph.add_node(node1)
        graph.add_node(node2)
        graph.set_entry_point("node1")
        self.assertFalse(graph.validate())

    def test_cycle_detection(self):
        graph = Graph()
        for i in range(3):
            node = GraphNode(id=f"node{i}", type=NodeType.AGENT)
            graph.add_node(node)
        
        graph.add_edge("node0", "node1")
        graph.add_edge("node1", "node2")
        graph.add_edge("node2", "node0")
        graph.set_entry_point("node0")
        
        self.assertTrue(graph.validate())
        self.assertGreater(len(graph.cycles), 0)

    def test_json_serialization(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            self.valid_graph.to_json(tmp.name)
            self.assertTrue(os.path.exists(tmp.name))
            loaded_graph = Graph.from_json(tmp.name)
            self.assertEqual(len(loaded_graph.nodes), len(self.valid_graph.nodes))
            self.assertEqual(len(loaded_graph.edges), len(self.valid_graph.edges))
            self.assertEqual(loaded_graph.entry_points, self.valid_graph.entry_points)
            self.assertEqual(loaded_graph.exit_points, self.valid_graph.exit_points)
            os.unlink(tmp.name)

    def test_pretty_print(self):
        console = Console(file=StringIO())
        self.valid_graph.pretty_print()
        self.valid_graph.print_as_table()

    def test_from_dict_empty_data(self):
        graph = Graph.from_dict({})
        self.assertEqual(len(graph.nodes), 0)
        self.assertEqual(len(graph.edges), 0)
        self.assertEqual(len(graph.entry_points), 0)
        self.assertEqual(len(graph.exit_points), 0)

    def test_invalid_node_type(self):
        with self.assertRaises(ValueError):
            GraphNode(id="test", type="invalid_type")

if __name__ == '__main__':
    unittest.main()
