import os
import sys
import logging
from dotenv import load_dotenv
from tools.weather_tool import weather_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_weather")

# Load environment variables
load_dotenv()

# Print environment variables for debugging
print("Environment variables:")
print(f"OPENWEATHER_API_KEY: {'Set' if os.getenv('OPENWEATHER_API_KEY') else 'Not set'}")
print(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
print(f"WEATHER_API_KEY: {'Set' if os.getenv('WEATHER_API_KEY') else 'Not set'}")

# Copy API key if needed
if not os.getenv('OPENAI_API_KEY') and os.getenv('OPENAI_API_KEY') != os.getenv('OPENWEATHER_API_KEY'):
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENWEATHER_API_KEY', '')
    print("Copied OPENWEATHER_API_KEY to OPENAI_API_KEY")

try:
    print("\nStarting test...")
    print("Getting weather data for London...")
    
    # Test location extraction
    test_queries = [
        "What's the weather in London?",
        "How is the weather in Paris today?",
        "I want to plan a trip to New York",
        "Should I pack an umbrella for Tokyo?",
        "Will it rain in Berlin tomorrow?"
    ]
    
    print("\nTesting location extraction:")
    for query in test_queries:
        location = weather_tool.extract_location(query)
        print(f"Query: '{query}' → Location: '{location}'")
    
    # Test weather data retrieval
    print("\nTesting weather data retrieval:")
    cities = ["London", "Paris", "New York", "Tokyo", "Berlin"]
    
    for city in cities:
        print(f"\nGetting weather for {city}...")
        result = weather_tool.get_current_weather(city)
        print(f"Result for {city}: {result}")
        
    print("\nTest completed successfully!")
    
except Exception as e:
    print(f"\nError during test: {str(e)}")
    import traceback
    traceback.print_exc()
    
finally:
    print("\nCleaning up...")
    weather_tool.stop_server()
    print("Server stopped")
