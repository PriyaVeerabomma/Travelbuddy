from langchain_core.tools import tool
from typing import Dict, Any
from tools.amadeus_hotels_api import perform_hotel_search_api

@tool
def hotel_search(input_str: str) -> Dict[str, Any]:
    """
    LangChain-compatible tool for hotel search using Amadeus.

    Expected input_str:
    "city=Paris&checkInDate=2025-05-01&checkOutDate=2025-05-05&adults=2"
    """
    try:
        if not all(k in input_str for k in ["city=", "checkInDate=", "checkOutDate=", "adults="]):
            return {"error": "Missing required keys in query string."}
        params = dict(p.split("=", 1) for p in input_str.split("&") if "=" in p)
        return perform_hotel_search_api(params)
    except Exception as e:
        return {"error": f"Failed to process hotel search: {str(e)}"}
