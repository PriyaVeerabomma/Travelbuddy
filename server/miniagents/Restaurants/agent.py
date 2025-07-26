import os
import json
import re
import logging
import traceback
from typing import Dict, Any, List, Optional

# Import the restaurant search tool
from tools.restaurant_search_tool import search_restaurants

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('restaurant_agent')

# ------------------ Cache ------------------ #
# Simple in-memory cache to reduce API calls
RESTAURANT_CACHE = {}

# ------------------ Restaurant Agent Main Function ------------------ #
def restaurant_search_agent(*, input_str: str) -> Dict[str, Any]:
    """
    Main restaurant search agent function that takes either natural language
    or structured input and returns restaurant search results and API data
    """
    try:
        logger.info(f"🔍 Received input_str: {input_str}")

        # Check if it's already in cache
        if input_str in RESTAURANT_CACHE:
            logger.info(f"🔍 Results for {input_str} found in cache")
            cache_result = RESTAURANT_CACHE[input_str]
            
            # Ensure cached result includes formatted_text
            if "formatted_text" not in cache_result:
                cache_result["formatted_text"] = format_restaurant_results(cache_result)
                
            return cache_result

        # Parse the input string to extract location
        if "location=" in input_str:
            # Already in structured format - use directly
            logger.info(f"🔧 Using structured input: {input_str}")
            result = search_restaurants(input_str)
        else:
            # For natural language input, try to extract the location
            location_match = re.search(r"(?:in|at|near|around)\s+([A-Za-z\s,]+)", input_str)
            if location_match:
                location = location_match.group(1).strip()
                logger.info(f"🔧 Extracted location: {location}")
                structured_input = f"location={location}"
                result = search_restaurants(structured_input)
            else:
                error_result = {
                    "error": "Could not determine location from input. Please specify a location.",
                    "formatted_text": "❌ Could not determine location from input. Please specify a location.",
                    "status": "error",
                    "api_data": {
                        "error": "Could not determine location from input. Please specify a location.",
                        "status": "error"
                    }
                }
                return error_result
        
        # Format the results for human-readable output
        formatted_text = format_restaurant_results(result)
        
        # Create a structured response with both formatted text and raw data
        complete_result = {
            "formatted_text": formatted_text,
            "restaurants": result.get("restaurants", {}),
            "api_data": result,
            "status": "error" if "error" in result else "success"
        }
        
        # Cache the result
        RESTAURANT_CACHE[input_str] = complete_result
        logger.info(f"🔍 from Reestarauatent agent before {complete_result}")
        return complete_result

    except Exception as e:
        logger.error(f"❌ Restaurant Search Agent Exception: {e}")
        logger.error(traceback.format_exc())
        
        error_result = {
            "error": f"Internal error: {str(e)}",
            "formatted_text": f"❌ Restaurant search error: Internal error occurred.",
            "status": "error",
            "api_data": {
                "error": f"Internal error: {str(e)}",
                "status": "error"
            }
        }
        return error_result
# ------------------ Formatting ------------------ #
def format_restaurant_results(restaurant_data: Dict[str, Any]) -> str:
    """Format restaurant search results into a readable string"""
    try:
        # Check for error case
        if "error" in restaurant_data:
            return f"❌ Restaurant search error: {restaurant_data['error']}"
        
        # Check for restaurants data
        if "restaurants" not in restaurant_data:
            return "⚠️ No restaurant data received."
        
        restaurants = restaurant_data["restaurants"]
        
        # Handle case where restaurants is a list rather than dictionary
        if isinstance(restaurants, list):
            if not restaurants:
                return "No restaurants found matching your criteria."
            
            location = restaurant_data.get("location", "Unknown Location")
            msg = f"Here are some recommended restaurants in {location}:\n\n"
            
            for i, restaurant in enumerate(restaurants[:5], 1):
                name = restaurant.get("name", "Unnamed Restaurant")
                rating = restaurant.get("rating", "N/A")
                price_level = restaurant.get("price_level", "")
                price_display = "$" * price_level if isinstance(price_level, int) else price_level
                address = restaurant.get("formatted_address", "Address unavailable")
                
                msg += f"### Restaurant {i}: {name}\n"
                msg += f"Rating: {rating}/5\n"
                msg += f"Price: {price_display}\n"
                msg += f"Address: {address}\n"
                
                # Add cuisine types if available
                if "types" in restaurant:
                    cuisine_types = [t for t in restaurant["types"] if t not in ["restaurant", "food", "establishment", "point_of_interest"]]
                    if cuisine_types:
                        msg += f"Cuisine: {', '.join(cuisine_types)}\n"
                
                # Add open status if available
                if "open_now" in restaurant:
                    open_status = "Open now" if restaurant["open_now"] else "Closed"
                    msg += f"Status: {open_status}\n"
                
                msg += "\n"
            
            return msg
        
        # Original implementation expecting a dictionary
        else:
            location = restaurants.get("location", "Unknown Location")
            results = restaurants.get("results", [])
            
            if not results:
                return "No restaurants found matching your criteria."
            
            msg = f"Here are some recommended restaurants in {location}:\n\n"
            
            for i, restaurant in enumerate(results[:5], 1):
                name = restaurant.get("name", "Unnamed Restaurant")
                rating = restaurant.get("rating", "N/A")
                price_level = restaurant.get("price_level", "")
                price_display = "$" * price_level if isinstance(price_level, int) else price_level
                address = restaurant.get("formatted_address", "Address unavailable")
                
                msg += f"### Restaurant {i}: {name}\n"
                msg += f"Rating: {rating}/5\n"
                msg += f"Price: {price_display}\n"
                msg += f"Address: {address}\n"
                
                # Add cuisine types if available
                if "types" in restaurant:
                    cuisine_types = [t for t in restaurant["types"] if t not in ["restaurant", "food", "establishment", "point_of_interest"]]
                    if cuisine_types:
                        msg += f"Cuisine: {', '.join(cuisine_types)}\n"
                
                # Add open status if available
                if "opening_hours" in restaurant and "open_now" in restaurant["opening_hours"]:
                    open_status = "Open now" if restaurant["opening_hours"]["open_now"] else "Closed"
                    msg += f"Status: {open_status}\n"
                
                msg += "\n"
            
            return msg
        
    except Exception as e:
        logger.error(f"Error formatting restaurant results: {str(e)}")
        return f"❌ Restaurant search error: Internal error occurred."