# explore_places_tool.py

from langchain_core.tools import tool
from typing import Dict, Any
from tools.google_places_api import perform_google_places_explore
import os

@tool
def explore_places(input_str: str) -> Dict[str, Any]:
    """
    LangChain tool to explore top 10 attractions using Google Places API.

    Input format:
    "location=Boston"

    Note: Expects GOOGLE_API_KEY to be set in environment or .env
    """
    try:
        if "location=" not in input_str:
            return {"error": "Missing required 'location=' parameter"}

        location = input_str.split("location=", 1)[-1]
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            return {"error": "Google Places API key not set in environment variable 'GOOGLE_API_KEY'"}

        return perform_google_places_explore(location, api_key)

    except Exception as e:
        return {"error": f"Explore tool failed: {str(e)}"}
