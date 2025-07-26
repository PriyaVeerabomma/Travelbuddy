import json
import requests
from crewai.tools import tool
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

SERPER_API = st.secrets.get("SERPER_API_KEY") or os.getenv("SERPER_API_KEY")

class SearchTools:

    @tool("Search the internet")
    @staticmethod
    def search_internet(input=None):
        """Useful to search the internet about a given topic and return relevant results"""
        
        # Convert input to string if it's not already a string or dict
        if input is not None and not isinstance(input, (str, dict)):
            input = str(input)
        
        # Handle string input
        if isinstance(input, str):
            # Check if it's an empty string
            if not input.strip():
                return "❌ Error: Please provide a search query. Example: {\"query\": \"your search topic\"}"
                
            try:
                # Try to parse as JSON
                input = json.loads(input)
            except json.JSONDecodeError:
                # If not valid JSON, use as direct query
                input = {"query": input}
        
        # Handle empty or None input
        if input is None or input == {}:
            return "❌ Error: Please provide a search query. Example: {\"query\": \"your search topic\"}"
            
        if not isinstance(input, dict):
            return "❌ Error: Input must be a dictionary, e.g., {'query': 'your search topic'}"

        # Extract query from various possible keys
        query = None
        
        # List of potential query keys in priority order
        query_keys = ["query", "topic", "description", "search", "question", "text"]
        
        # Try direct keys first
        for key in query_keys:
            if key in input and input[key] and isinstance(input[key], str):
                query = input[key]
                break
        
        # Try nested keys if no direct key found
        if not query:
            if "input" in input and isinstance(input["input"], dict):
                for key in query_keys:
                    if key in input["input"] and input["input"][key]:
                        query = input["input"][key]
                        break
        
        # Try parameters if present
        if not query and "parameters" in input and isinstance(input["parameters"], dict):
            for key in query_keys:
                if key in input["parameters"] and input["parameters"][key]:
                    query = input["parameters"][key]
                    break
            
            # If no query in parameters but destination is, use that
            if not query and "destination" in input["parameters"]:
                query = f"travel information about {input['parameters']['destination']}"
        
        # If still no query, check if there are any string values we can use
        if not query:
            # Look for any string value in the dictionary that might be a query
            for key, value in input.items():
                if isinstance(value, str) and len(value) > 5:  # Arbitrary min length for a reasonable query
                    query = value
                    break
                    
            # Deep search in nested dictionaries
            if not query:
                for key, value in input.items():
                    if isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            if isinstance(nested_value, str) and len(nested_value) > 5:
                                query = nested_value
                                break

        # If still no query, return error
        if not query:
            return "❌ Error: Could not find a valid search query in your input. Please provide a query using the format: {\"query\": \"your search topic\"}"

        top_result_to_return = 4
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': SERPER_API,
            'content-type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            data = response.json()

            if 'organic' not in data:
                return "❌ No results found. Check your query or Serper API key."

            results = data['organic']
            string = []
            for result in results[:top_result_to_return]:
                try:
                    string.append('\n'.join([
                        f"Title: {result.get('title')}",
                        f"Link: {result.get('link')}",
                        f"Snippet: {result.get('snippet')}",
                        "\n-----------------"
                    ]))
                except Exception:
                    continue

            return '\n'.join(string)

        except Exception as e:
            return f"❌ An error occurred during the search: {str(e)}"