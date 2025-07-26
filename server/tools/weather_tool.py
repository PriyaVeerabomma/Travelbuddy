import json
import os
import re
import requests
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("weather_tool")

# Load environment variables from .env file
load_dotenv()

class WeatherTool:
    def __init__(self, mcp_server_url=None):
        # URL for the containerized MCP server
        self.mcp_server_url = mcp_server_url or "http://weather-mcp:8080"
        
        # Fallback to localhost if container name doesn't resolve
        self.fallback_url = "http://localhost:8080"
        
        # Check for OpenWeather API key
        if "OPENWEATHER_API_KEY" not in os.environ:
            logger.error("OPENWEATHER_API_KEY environment variable not set")
            raise ValueError("OPENWEATHER_API_KEY environment variable not set")
        
        logger.info(f"Initialized WeatherTool with MCP server URL: {self.mcp_server_url}")
        logger.info(f"Using OpenWeather API key: {os.environ.get('OPENWEATHER_API_KEY', '')[:5]}...")
    
    def call_mcp(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call the containerized MCP server with parameters"""
        try:
            # Create JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "method": "invoke",
                "params": {
                    "name": tool_name,
                    "parameters": parameters
                },
                "id": "1"
            }
            
            logger.info(f"Sending request to MCP server: {json.dumps(request)[:100]}...")
            
            # Try the primary URL first
            try:
                response = self._send_request(self.mcp_server_url, request)
                return response
            except requests.RequestException as e:
                logger.warning(f"Failed to connect to primary MCP server URL: {str(e)}")
                
                # Try the fallback URL
                logger.info(f"Trying fallback URL: {self.fallback_url}")
                try:
                    response = self._send_request(self.fallback_url, request)
                    # If fallback works, update the primary URL for future calls
                    self.mcp_server_url = self.fallback_url
                    return response
                except requests.RequestException as fallback_error:
                    logger.error(f"Failed to connect to fallback MCP server URL: {str(fallback_error)}")
                    # Return simulated data as last resort
                    if tool_name in ["get_weather", "get_current_weather"]:
                        location = parameters.get("location", "Unknown location")
                        return self.get_simulated_weather(location)
                    return {"error": f"Failed to connect to MCP server: {str(fallback_error)}"}
                
        except Exception as e:
            logger.error(f"Error calling MCP: {str(e)}")
            return {"error": f"Error calling MCP: {str(e)}"}
    
    def _send_request(self, url: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to MCP server and process response"""
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(request),
            timeout=30  # 30 second timeout
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse response
        response_data = response.json()
        logger.info(f"Received response from MCP server: {json.dumps(response_data)[:100]}...")
        
        if "error" in response_data:
            logger.error(f"Error in MCP response: {response_data['error']}")
            return {"error": response_data["error"]}
        
        return response_data.get("result", {})
    
    def get_weather(self, location: str, timezone_offset: float = 0) -> Dict[str, Any]:
        """Get comprehensive weather forecast for a location"""
        logger.info(f"Getting weather forecast for {location}")
        return self.call_mcp("get_weather", {
            "location": location,
            "api_key": os.getenv("OPENWEATHER_API_KEY", ""),
            "timezone_offset": timezone_offset
        })
    
    def get_current_weather(self, location: str, timezone_offset: float = 0) -> Dict[str, Any]:
        """Get current weather for a location"""
        logger.info(f"Getting current weather for {location}")
        return self.call_mcp("get_current_weather", {
            "location": location,
            "api_key": os.getenv("OPENWEATHER_API_KEY", ""),
            "timezone_offset": timezone_offset
        })
        
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location from user query"""
        logger.info(f"Extracting location from text: {text}")
        
        # If the input includes chat history, extract only the current query
        if "current query:" in text.lower():
            try:
                text = text.lower().split("current query:")[-1].strip()
                logger.info(f"Extracted current query for location extraction: {text}")
            except Exception as e:
                logger.error(f"Error extracting current query for location: {str(e)}")
        
        # Add more patterns to catch different phrasings
        patterns = [
            r"weather (?:in|at|for) ([A-Za-z\s]+)(?:,|\.|$)",
            r"weather (?:forecast|report|conditions) (?:in|at|for) ([A-Za-z\s]+)(?:,|\.|$)",
            r"(?:in|at) ([A-Za-z\s]+) (?:weather|forecast)",
            r"how is the weather (?:in|at) ([A-Za-z\s]+)(?:,|\.|$)",
            r"what's the weather (?:in|at|like in) ([A-Za-z\s]+)(?:,|\.|$)",
            r"what is the weather (?:in|at|like in) ([A-Za-z\s]+)(?:,|\.|$)",
            r"how's the weather (?:in|at) ([A-Za-z\s]+)(?:,|\.|$)",
            r"tell me (?:about )?(?:the )?weather (?:in|at|for) ([A-Za-z\s]+)(?:,|\.|$)",
            r"is it (?:raining|sunny|cold|hot|warm) in ([A-Za-z\s]+)(?:,|\.|$)",
            r"(?:plan|planning) (?:a )?(?:trip|vacation|visit) to ([A-Za-z\s]+)(?:,|\.|$)",
            r"traveling to ([A-Za-z\s]+)(?:,|\.|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                logger.info(f"Extracted location: {location}")
                return location
        
        # If none of the patterns match, check for city names
        common_cities = ["New York", "London", "Paris", "Tokyo", "Berlin", "Rome", "Madrid", "Beijing", "Sydney", "Cairo", 
                        "Boston", "Chicago", "Los Angeles", "San Francisco", "Seattle", "Miami", "Toronto", "Vancouver",
                        "Mumbai", "Delhi", "Bangkok", "Singapore", "Seoul", "Shanghai", "Mexico City", "Rio de Janeiro",
                        "Cape Town", "Dubai", "Istanbul", "Moscow", "Amsterdam", "Barcelona", "Vienna", "Prague"]
        
        for city in common_cities:
            if city.lower() in text.lower():
                logger.info(f"Found city name in text: {city}")
                return city
        
        logger.info("No location found in text")
        return None
        
    def extract_multiple_locations(self, text: str) -> List[str]:
        """Extract multiple locations from user query"""
        logger.info(f"Extracting multiple locations from text: {text}")
        
        # If the input includes chat history, extract only the current query
        if "current query:" in text.lower():
            try:
                text = text.lower().split("current query:")[-1].strip()
                logger.info(f"Extracted current query: {text}")
            except Exception as e:
                logger.error(f"Error extracting current query: {str(e)}")
        
        locations = []
        
        # Pattern for locations with connecting words ("and", "or", etc.)
        location_pattern = r"(?:in|at|for)\s+([A-Za-z\s]+?)(?:(?:,|\s+and|\s+&|\s+or|\s+as well as)|\s+and\s+([A-Za-z\s]+?)(?:$|,)|\s+or\s+([A-Za-z\s]+?)(?:$|,))"
        
        # Extract locations from patterns
        matches = list(re.finditer(location_pattern, text, re.IGNORECASE))
        for match in matches:
            # Get the first match group
            location = match.group(1).strip() if match.group(1) else None
            if location and location.lower() not in [loc.lower() for loc in locations]:
                locations.append(location)
            
            # Check for additional locations in other groups
            for i in range(2, 4):  # Check groups 2 and 3 if they exist
                if match.group(i):
                    location = match.group(i).strip()
                    if location and location.lower() not in [loc.lower() for loc in locations]:
                        locations.append(location)
        
        # Also try the single location extractor for the first location
        single_location = self.extract_location(text)
        if single_location and single_location.lower() not in [loc.lower() for loc in locations]:
            locations.append(single_location)
        
        # If we found multiple locations, great!
        if len(locations) > 1:
            logger.info(f"Multiple locations extracted: {locations}")
            return locations
        
        # If we only found one or no locations using the complex pattern,
        # try looking for common city names
        if len(locations) <= 1:
            common_cities = ["New York", "London", "Paris", "Tokyo", "Berlin", "Rome", "Madrid", "Beijing", "Sydney", 
                            "Boston", "Chicago", "Los Angeles", "San Francisco", "Seattle", "Miami", "Toronto", 
                            "Mumbai", "Delhi", "Bangkok", "Singapore", "Seoul", "Shanghai", "Mexico City"]
            
            # Simple pattern to match cities separated by connectors
            cities_pattern = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s*(?:,|and|&|or)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            
            city_matches = re.finditer(cities_pattern, text)
            for match in city_matches:
                for i in range(1, 3):  # Check groups 1 and 2
                    if match.group(i):
                        potential_city = match.group(i).strip()
                        if potential_city in common_cities and potential_city.lower() not in [loc.lower() for loc in locations]:
                            locations.append(potential_city)
            
            # Direct city name extraction
            for city in common_cities:
                if city.lower() in text.lower() and city.lower() not in [loc.lower() for loc in locations]:
                    locations.append(city)
        
        logger.info(f"Final locations extracted: {locations}")
        return locations

    def get_weather_for_multiple_locations(self, locations: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get weather data for multiple locations"""
        weather_results = {}
        
        for location in locations:
            try:
                weather_data = self.get_current_weather(location)
                weather_results[location] = weather_data
            except Exception as e:
                logger.error(f"Error getting weather for {location}: {str(e)}")
                weather_results[location] = {
                    "error": str(e),
                    "location": location
                }
        
        return weather_results

    def format_weather_response(self, weather_results: Dict[str, Dict[str, Any]]) -> str:
        """Format weather data from multiple locations into a readable response"""
        if not weather_results:
            return "I couldn't find weather information for the locations you mentioned."
        
        # Single location case
        if len(weather_results) == 1:
            location = list(weather_results.keys())[0]
            data = weather_results[location]
            
            if "error" in data:
                return f"I tried to get weather information for {location}, but encountered an error: {data['error']}"
            
            return f"Here's the current weather for {location}: {data.get('report', 'No data available.')}"
        
        # Multiple locations
        response_parts = ["Here's the current weather information:"]
        
        for location, data in weather_results.items():
            if "error" in data:
                response_parts.append(f"• {location}: Sorry, I couldn't retrieve weather data for this location.")
            else:
                report = data.get("report", "No data available")
                response_parts.append(f"• {location}: {report}")
        
        return "\n\n".join(response_parts)

    def get_simulated_weather(self, location: str) -> Dict[str, Any]:
        """Provide simulated weather data when MCP server fails"""
        logger.info(f"Generating simulated weather for {location}")
        return {
            "report": f"In {location}, it's currently 22°C with clear skies. The humidity is around 65% with light winds. (This is simulated data as the weather service is unavailable.)"
        }

# Singleton instance
weather_tool = WeatherTool()

# For testing
if __name__ == "__main__":
    try:
        logger.info("Starting weather tool test")
        
        # Test with both the container hostname and localhost fallback
        test_locations = ["London", "New York", "Tokyo"]
        
        for location in test_locations:
            try:
                result = weather_tool.get_current_weather(location)
                logger.info(f"Weather for {location}: {result}")
            except Exception as e:
                logger.error(f"Error getting weather for {location}: {str(e)}")
                
        # Test location extraction
        test_queries = [
            "What's the weather like in Paris?",
            "Tell me about the weather in Tokyo and London",
            "I'm planning a trip to Berlin next week"
        ]
        
        for query in test_queries:
            location = weather_tool.extract_location(query)
            logger.info(f"Query: {query} -> Location: {location}")
            
            locations = weather_tool.extract_multiple_locations(query)
            logger.info(f"Query: {query} -> Multiple locations: {locations}")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
    finally:
        logger.info("Test complete")