import asyncio
import logging
from agents.rootAgent import root_agent
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_direct_weather")

async def test_weather_query(query):
    logger.info(f"Testing query: {query}")
    
    # Call the agent
    result = await root_agent.ainvoke({"input": query})
    
    # Print the result
    logger.info(f"Result: {result.get('output', 'No output')}")
    
    return result

async def main():
    # Test different weather queries
    queries = [
        "What's the weather in London?",
        "How is the weather in Tokyo?",
        "What's the temperature in New York?",
        "Should I bring an umbrella to Paris?",
        "Will it rain in Berlin tomorrow?",
        "What's the weather like in Hyderabad?",
        "How hot is it in Dubai right now?",
        "Is it cold in Moscow?",
        "What's the forecast for Sydney this week?"
    ]
    
    print("Starting weather query tests...\n")
    
    for query in queries:
        result = await test_weather_query(query)
        print(f"\nQuery: {query}")
        print(f"Response: {result.get('output', 'No output')}")
        print("-" * 80)
        
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
