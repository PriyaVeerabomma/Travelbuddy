#!/usr/bin/env python3
"""
Simple test script for the Weather MCP Server
"""

import os
import sys
import json
from weather_mcp_server import get_weather_forecast

def main():
    """Test the weather forecast function directly"""
    # Check if API key is set
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        print("Error: OPENWEATHER_API_KEY environment variable not set")
        print("Please set the environment variable and try again:")
        print("  export OPENWEATHER_API_KEY=your_key_here")
        sys.exit(1)

    print(f"Using API key: {api_key[:5]}...{api_key[-5:]}")

    location = "New York"
    timezone_offset = -4

    print(f"\nTesting get_weather_forecast for {location}...")
    try:
        result = get_weather_forecast(location, timezone_offset, api_key)

        print("\nFull API Response Structure:")
        print(json.dumps(result, indent=2))  # 👈 moved inside here

        print("\nAPI Response:")
        if isinstance(result, dict):
            if 'error' in result:
                print(f"Error in response: {result['error']}")
            else:
                print("Keys in result:", list(result.keys()))
                if 'current' in result:
                    print("\nCurrent weather data:")
                    print(result['current'])
                else:
                    print("WARNING: 'current' key not found in result")

                if 'daily_forecasts' in result:
                    print(f"\nNumber of daily forecasts: {len(result['daily_forecasts'])}")
                else:
                    print("WARNING: 'daily_forecasts' key not found in result")
        else:
            print(f"Unexpected result type: {type(result)}")
            print(result)

    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\nTest complete")

if __name__ == "__main__":
    main()
