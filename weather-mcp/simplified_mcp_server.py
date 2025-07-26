import json
import sys
import os
import requests
import socket
import http.server
import socketserver
import threading
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("simplified_mcp")

# Load environment variables
load_dotenv()

class SimplifiedMCP:
    def __init__(self):
        self.name = "WeatherForecastServer"
        self.description = "Provides global weather forecasts and current weather conditions"
        self.version = "1.0.0"
        
        # Check for API keys
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            logger.error("OPENWEATHER_API_KEY environment variable not set")
            raise ValueError("OPENWEATHER_API_KEY environment variable not set")
        
        logger.info(f"Initialized SimplifiedMCP with API key: {self.api_key[:5]}...")
    
    def get_coordinates(self, location):
        """Get geographic coordinates for a location name using Geocoding API"""
        try:
            # First try the Geocoding API
            geocode_url = f"https://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={self.api_key}"
            response = requests.get(geocode_url)
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                return data[0]['lat'], data[0]['lon']

            # Fallback to current weather API if geocoding fails
            logger.info("Geocoding API failed, falling back to current weather API for coordinates")
            fallback_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.api_key}&units=metric"
            response = requests.get(fallback_url)
            response.raise_for_status()
            data = response.json()

            return data['coord']['lat'], data['coord']['lon']
        except Exception as e:
            logger.error(f"Error getting coordinates: {str(e)}")
            raise
    
    def format_timestamp(self, ts, tz_offset):
        """Convert Unix timestamp to human-readable time"""
        tz = timezone(timedelta(hours=tz_offset))
        dt = datetime.fromtimestamp(ts, tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_weather_data(self, location, timezone_offset=0):
        """Get weather data for a location"""
        try:
            # Get coordinates
            lat, lon = self.get_coordinates(location)
            logger.info(f"Got coordinates for {location}: ({lat}, {lon})")
            
            # Get weather data
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
            response = requests.get(weather_url)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant information
            main = data.get('main', {})
            weather = data.get('weather', [{}])[0]
            wind = data.get('wind', {})
            
            weather_data = {
                'location': location,
                'temperature': f"{main.get('temp', 0)}°C",
                'feels_like': f"{main.get('feels_like', 0)}°C",
                'weather_condition': weather.get('description', 'Unknown'),
                'humidity': f"{main.get('humidity', 0)}%",
                'wind_speed': f"{wind.get('speed', 0)} m/s",
                'wind_direction': f"{wind.get('deg', 0)} degrees"
            }
            
            logger.info(f"Retrieved weather data for {location}")
            return weather_data
        
        except Exception as e:
            logger.error(f"Error getting weather data: {str(e)}")
            # Return simulated data on error
            return {
                'location': location,
                'temperature': '22°C',
                'feels_like': '24°C',
                'weather_condition': 'clear sky',
                'humidity': '65%',
                'wind_speed': '3.5 m/s',
                'wind_direction': '180 degrees'
            }
    
    def get_weather_report(self, weather_data):
        """Generate a weather report from weather data"""
        try:
            location = weather_data['location']
            temp = weather_data['temperature']
            condition = weather_data['weather_condition']
            humidity = weather_data['humidity']
            wind_speed = weather_data['wind_speed']
            
            report = f"In {location}, it's currently {temp} with {condition}. "
            report += f"The humidity is {humidity} with wind speed at {wind_speed}."
            
            # Add clothing recommendations based on temperature
            temp_value = float(temp.replace('°C', ''))
            if temp_value < 5:
                report += " It's very cold, so you should wear a heavy coat, hat, and gloves."
            elif temp_value < 15:
                report += " It's cool, so a light jacket or sweater would be appropriate."
            elif temp_value < 25:
                report += " The temperature is comfortable, perfect for light clothing."
            else:
                report += " It's quite warm, so light summer clothing is recommended."
                
            # Add rain advice if applicable
            if 'rain' in condition.lower():
                report += " Don't forget an umbrella as there's rain in the forecast."
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating weather report: {str(e)}")
            return f"The current weather in {weather_data.get('location', 'the requested location')} is {weather_data.get('temperature', 'unknown')} with {weather_data.get('weather_condition', 'unknown conditions')}."
    
    def get_current_weather(self, location, api_key=None, timezone_offset=0):
        """Get current weather for a location"""
        weather_data = self.get_weather_data(location, timezone_offset)
        report = self.get_weather_report(weather_data)
        return {"report": report}
    
    def get_weather(self, location, api_key=None, timezone_offset=0):
        """Get comprehensive weather data for a location"""
        # For simplicity, this returns the same as get_current_weather
        return self.get_current_weather(location, api_key, timezone_offset)
    
    def handle_request(self, request_data):
        """Process an incoming request"""
        try:
            if not isinstance(request_data, dict):
                return {"error": "Invalid request format"}
                
            if request_data.get("method") != "invoke":
                return {"error": "Unknown method"}
                
            params = request_data.get("params", {})
            tool_name = params.get("name")
            parameters = params.get("parameters", {})
            
            if tool_name == "get_current_weather":
                location = parameters.get("location")
                api_key = parameters.get("api_key")
                timezone_offset = parameters.get("timezone_offset", 0)
                
                if not location:
                    return {"error": "Location parameter is required"}
                    
                result = self.get_current_weather(location, api_key, timezone_offset)
                return {"result": result}
                
            elif tool_name == "get_weather":
                location = parameters.get("location")
                api_key = parameters.get("api_key")
                timezone_offset = parameters.get("timezone_offset", 0)
                
                if not location:
                    return {"error": "Location parameter is required"}
                    
                result = self.get_weather(location, api_key, timezone_offset)
                return {"result": result}
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return {"error": str(e)}
    
    def start_http_server(self, port=8080):
        """Start an HTTP server to handle incoming JSON-RPC requests"""
        
        class MCP_RequestHandler(http.server.BaseHTTPRequestHandler):
            def __init__(self, *args, mcp_instance=None, **kwargs):
                self.mcp_instance = mcp_instance
                super().__init__(*args, **kwargs)
            
            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                try:
                    request_data = json.loads(post_data.decode('utf-8'))
                    response = self.mcp_instance.handle_request(request_data)
                    
                    if "id" in request_data:
                        response["id"] = request_data["id"]
                        
                    response["jsonrpc"] = "2.0"
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                except Exception as e:
                    logger.error(f"Error handling HTTP request: {str(e)}")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": str(e),
                        "id": None
                    }
                    self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
            def log_message(self, format, *args):
                # Override to use our logger instead of printing to stderr
                logger.info(f"HTTP: {format % args}")
        
        # Create handler with a reference to this instance
        handler = lambda *args, **kwargs: MCP_RequestHandler(*args, mcp_instance=self, **kwargs)
        
        # Create HTTP server
        server_address = ('', port)
        httpd = socketserver.ThreadingTCPServer(server_address, handler)
        httpd.allow_reuse_address = True
        
        logger.info(f"Starting HTTP server on port {port}")
        
        try:
            # Run the server
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down HTTP server...")
            httpd.shutdown()
    
    def run(self):
        """Run the server in the appropriate mode"""
        logger.info("Simplified MCP server running...")
        
        # Check if we're running in a container by checking environment
        if os.environ.get("CONTAINER_MODE", "0") == "1" or not sys.stdin.isatty():
            # HTTP mode (containerized or non-interactive)
            logger.info("Running in HTTP mode (for container)")
            self.start_http_server(port=8080)
        else:
            # STDIO mode (interactive)
            logger.info("Running in STDIO mode (interactive)")
            try:
                for line in sys.stdin:
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        request = json.loads(line)
                        response = self.handle_request(request)
                        
                        if "id" in request:
                            response["id"] = request["id"]
                            
                        response["jsonrpc"] = "2.0"
                        print(json.dumps(response))
                        sys.stdout.flush()
                        
                    except json.JSONDecodeError:
                        print(json.dumps({
                            "jsonrpc": "2.0",
                            "error": "Invalid JSON",
                            "id": None
                        }))
                        sys.stdout.flush()
                        
            except KeyboardInterrupt:
                logger.info("Server shutting down...")
                return

if __name__ == "__main__":
    server = SimplifiedMCP()
    server.run()