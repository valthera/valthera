import asyncio
import logging
from ..graph.graph import LangChainGraph
from ..nodes.processing import ProcessingNode, FinalNode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_example_workflow():
    logger.info("Creating new LangChain graph")
    graph = LangChainGraph()
    
    # Create nodes
    processor = ProcessingNode(chain_type="processor", model_name="example")
    finalizer = FinalNode(chain_type="finalizer", model_name="example")
    
    # Add nodes to graph
    logger.info("Adding nodes to graph")
    graph.add_node("processor", processor)
    graph.add_node("finalizer", finalizer)
    
    # Set the entrypoint
    logger.info("Setting entrypoint")
    graph.set_entrypoint("processor")
    
    # Connect nodes
    logger.info("Connecting nodes")
    graph.add_edge("processor", "finalizer")
    
    # Execute graph
    initial_state = {"input": "test data"}
    logger.info(f"Executing graph with initial state: {initial_state}")
    
    try:
        result = await graph.execute(initial_state)
        logger.info(f"Graph execution completed. Final state: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during graph execution: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_example_workflow())
