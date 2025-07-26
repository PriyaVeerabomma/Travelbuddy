#!/usr/bin/env python3
"""
Script to update the OpenWeatherMap API key in the .env file
"""
import os
import re
from dotenv import load_dotenv

def update_env_file(new_key):
    """Update the OpenWeatherMap API key in the .env file"""
    # Load current .env file
    load_dotenv()
    
    try:
        # Read the current .env file
        with open('.env', 'r') as file:
            env_content = file.read()
        
        # Update the OpenWeatherMap API keys
        env_content = re.sub(
            r'WEATHER_API_KEY="[^"]*"', 
            f'WEATHER_API_KEY="{new_key}"', 
            env_content
        )
        env_content = re.sub(
            r'OPENWEATHER_API_KEY="[^"]*"', 
            f'OPENWEATHER_API_KEY="{new_key}"', 
            env_content
        )
        
        # Write the updated content back to the .env file
        with open('.env', 'w') as file:
            file.write(env_content)
        
        print("API key updated successfully in .env file!")
        
    except Exception as e:
        print(f"Error updating .env file: {str(e)}")

if __name__ == "__main__":
    print("OpenWeatherMap API Key Updater")
    print("------------------------------")
    
    # Get the current key
    current_key = os.environ.get("OPENWEATHER_API_KEY", "Not set")
    print(f"Current API key: {current_key[:5]}...{current_key[-5:] if len(current_key) > 10 else ''}")
    
    # Ask for the new key
    new_key = input("Enter your new OpenWeatherMap API key: ")
    
    if not new_key:
        print("No key entered. Exiting without making changes.")
        exit(0)
    
    # Update the .env file
    update_env_file(new_key)
    
    # Suggest next steps
    print("\nNext steps:")
    print("1. Run 'poetry run python test_api_key.py' to verify your new key")
    print("2. Run 'poetry run python test_client.py' to test the full application")
