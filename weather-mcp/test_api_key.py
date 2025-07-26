#!/usr/bin/env python3
"""
Simple script to test OpenWeatherMap API key validity
Tests both geocoding API and the One Call API
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_api_key(api_key):
    """Test the API key against various OpenWeatherMap endpoints"""
    print(f"Testing API key: {api_key[:5]}...{api_key[-5:]}")
    
    # List of endpoints to test
    endpoints = [
        {
            "name": "Current Weather API (2.5)",
            "url": f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}"
        },
        {
            "name": "Geocoding API",
            "url": f"https://api.openweathermap.org/geo/1.0/direct?q=London&limit=1&appid={api_key}"
        },
        {
            "name": "One Call API (2.5)",
            "url": f"https://api.openweathermap.org/data/2.5/onecall?lat=51.5074&lon=-0.1278&appid={api_key}&units=metric"
        },
        {
            "name": "One Call API (3.0)",
            "url": f"https://api.openweathermap.org/data/3.0/onecall?lat=51.5074&lon=-0.1278&appid={api_key}&units=metric"
        }
    ]
    
    # Test each endpoint
    for endpoint in endpoints:
        print(f"\nTesting {endpoint['name']}...")
        try:
            response = requests.get(endpoint['url'])
            if response.status_code == 200:
                print(f"✅ SUCCESS: Status code {response.status_code}")
                print(f"Response contains keys: {list(response.json().keys())}")
            else:
                print(f"❌ FAILED: Status code {response.status_code}")
                print(f"Error message: {response.text}")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    # Try to get API key from .env file
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    
    if not api_key:
        print("Error: OPENWEATHER_API_KEY environment variable not set")
        exit(1)
    
    test_api_key(api_key)
    
    # Ask if user wants to try a different key
    different_key = input("\nDo you want to test a different API key? (y/n): ")
    if different_key.lower() == 'y':
        new_key = input("Enter the OpenWeatherMap API key to test: ")
        test_api_key(new_key)
