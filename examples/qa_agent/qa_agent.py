import sys
import asyncio
import logging
import json

from valthera_langchain.graph.graph import LangChainGraph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_example_workflow():
    # Load JSON data containing both graph config and initial state.
    with open("data.json", "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in data.json: {e}")
            raise
    
    # Instantiate LangChainGraph from JSON data directly.
    graph = LangChainGraph.from_json(data)        
    
    try:
        result = await graph.execute(data.get("initial_state"))
        logger.info(f"Graph execution completed. Final state: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during graph execution: {e}")
        raise

    
    
if __name__ == "__main__":
    asyncio.run(run_example_workflow())
