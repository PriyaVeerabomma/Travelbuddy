from langchain_core.tools import BaseTool
from typing import Dict, Any
import re
import logging
import traceback
from tools.hotel_search import hotel_search

logger = logging.getLogger('hotel_agent')

# ------------------ Hotel Agent Main Function with Tool ------------------ #
def hotel_search_agent(*, input_str: str) -> Dict[str, Any]:
    """
    Main hotel search agent function that takes either natural language
    or structured input and returns hotel search results using the hotel_search tool
    """
    try:
        logger.info(f"🔍 Received input_str: {input_str}")

        # Parse the input string (either directly or preprocess with LLM in the other file)
        if re.search(r"city=.*&checkInDate=.*&checkOutDate=.*&adults=", input_str):
            # Already in structured format, use the hotel_search tool directly
            logger.info(f"🔧 Using structured input with hotel_search tool: {input_str}")
            result = hotel_search(input_str)
        else:
            # For natural language input, we need to call the LLM parser
            # This will be handled in the parent file that imports this module
            error_result = {
                "error": "Natural language parsing should be handled by the parent module",
                "formatted_text": "❌ Error: Natural language input requires preprocessing.",
                "status": "error",
                "api_data": {
                    "error": "Natural language parsing should be handled by the parent module",
                    "status": "error"
                }
            }
            return error_result
        
        # Format the results for human-readable output
        formatted_text = format_hotel_results(result)
        
        # Create a structured response with both formatted text and raw data
        complete_result = {
            "formatted_text": formatted_text,
            "hotels": result.get("hotels", {}),
            "api_data": result,
            "status": "error" if "error" in result else "success"
        }
        
        return complete_result

    except Exception as e:
        logger.error(f"❌ Hotel Search Agent Exception: {e}")
        logger.error(traceback.format_exc())
        
        error_result = {
            "error": f"Internal error: {str(e)}",
            "formatted_text": f"❌ Hotel search error: Internal error occurred.",
            "status": "error",
            "api_data": {
                "error": f"Internal error: {str(e)}",
                "status": "error"
            }
        }
        return error_result
def format_hotel_results(hotels_data: Dict[str, Any]) -> str:
    """Format hotel search results into a readable string"""
    # Handle error case first
    if isinstance(hotels_data, dict) and "error" in hotels_data:
        return f"❌ Hotel search error: {hotels_data['error']}"
    
    # Handle missing data
    if not isinstance(hotels_data, dict) or "hotels" not in hotels_data:
        return "⚠️ No hotel data received."
    
    hotels = hotels_data["hotels"]
    
    # Safety check for data structure
    if not isinstance(hotels, dict) or "data" not in hotels:
        return "⚠️ Unexpected hotel data format."
    
    hotel_list = hotels.get("data", [])
    city_code = hotels.get("request", {}).get("cityCode", "Unknown")
    check_in = hotels.get("request", {}).get("checkInDate", "Unknown")
    check_out = hotels.get("request", {}).get("checkOutDate", "Unknown")
    
    if not hotel_list:
        return f"⚠️ No hotels found in {city_code} for your dates."
    
    msg = f"Hotels in {city_code} from {check_in} to {check_out}:\n\n"
    
    for i, hotel in enumerate(hotel_list[:5], 1):
        name = hotel.get("name", "Unknown Hotel")
        hotel_id = hotel.get("hotelId", "Unknown ID")
        chain_code = hotel.get("chainCode", "Independent")
        
        msg += f"### {i}. {name}\n"
        msg += f"- Chain: {chain_code}\n"
        
        # Add location if available
        if location := hotel.get("geoCode"):
            latitude = location.get("latitude", "Unknown")
            longitude = location.get("longitude", "Unknown")
            msg += f"- Location: {latitude}, {longitude}\n"
        
        # Add amenities if available
        if amenities := hotel.get("amenities", []):
            msg += f"- Amenities: {', '.join(amenities[:5])}\n"
        
        msg += "\n"
    
    return msg