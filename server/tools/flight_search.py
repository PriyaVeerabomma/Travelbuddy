from langchain_core.tools import tool
from tools.amadeus_api import perform_flight_search_api
from typing import Dict, Any

@tool
def flight_search(input_str: str) -> Dict[str, Any]:
    """
    Finds flights based on user query.
    Input should be a URL-style string, e.g., 'origin=NYC&destination=Paris&departure_date=2025-05-01'.
    """
    params = dict(param.split("=", 1) for param in input_str.split("&") if "=" in param)
    return perform_flight_search_api(params)
