# restaurant_search_tool.py

from langchain_core.tools import tool
from typing import Dict, Any
from tools.google_restaurant_api import perform_google_restaurant_search
import os

@tool
def search_restaurants(input_str: str) -> Dict[str, Any]:
    """
    LangChain tool for searching top restaurants in a city using Google Places API.

    Input format:
    "location=Paris"

    Requires:
    - GOOGLE_API_KEY set in environment or .env
    """
    try:
        if "location=" not in input_str:
            return {"error": "Missing required 'location=' parameter."}

        location = input_str.split("location=", 1)[-1].strip()
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            return {"error": "Missing GOOGLE_API_KEY in environment."}

        return perform_google_restaurant_search(location, api_key)

    except Exception as e:
        return {"error": f"Restaurant search failed: {str(e)}"}