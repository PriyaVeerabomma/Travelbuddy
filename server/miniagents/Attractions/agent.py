import re
import logging
import traceback
from typing import Dict, Any

# Import the explore_places_tool
from tools.explore_places_tool import explore_places

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('attractions_agent')

# ------------------ Cache ------------------ #
# Simple in-memory cache to reduce API calls
ATTRACTIONS_CACHE = {}

# ------------------ Attractions Search ------------------ #
def search_attractions(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Core attractions search function that takes parsed parameters
    and returns attractions search results or error
    """
    try:
        # Required field guard
        if "location" not in params or not params["location"]:
            return {"error": "Missing required parameter: location"}

        # Create a cache key - just use location since that's all explore_places needs
        cache_key = params["location"]
        if cache_key in ATTRACTIONS_CACHE:
            logger.info(f"🔍 Attraction results for {cache_key} found in cache")
            return ATTRACTIONS_CACHE[cache_key]

        # Construct the query string for explore_places
        query = f"location={params['location']}"
        
        try:
            # Use the explore_places tool to find attractions
            result = explore_places(query)
            
            if "error" in result:
                logger.error(f"❌ Attraction search error: {result['error']}")
                return {"error": result["error"]}
            
            logger.info(f"✅ Attraction search success")
            
            # Create a response with query metadata
            attractions_data = {
                "attractions_list": result,
                "query": {
                    "location": params["location"]
                }
            }
            
            # Cache the result
            ATTRACTIONS_CACHE[cache_key] = {"attractions": attractions_data}
            
            return {"attractions": attractions_data}
            
        except Exception as e:
            logger.error(f"❌ Attraction search request error: {e}")
            return {"error": f"Error searching for attractions: {str(e)}"}

    except Exception as e:
        logger.error(f"❌ Attraction Search Exception: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Internal error: {str(e)}"}

# ------------------ Attractions Agent Main Function ------------------ #
def attractions_search_agent(*, input_str: str) -> Dict[str, Any]:
    """
    Main attractions search agent function that takes either natural language
    or structured input and returns attractions search results and API data
    """
    try:
        logger.info(f"🔍 Received input_str: {input_str}")

        # Parse the input string (either directly or preprocess with LLM in the other file)
        if "location=" in input_str:
            # Already in structured format (may or may not include attraction_type)
            params = dict(param.split("=", 1) for param in input_str.split("&") if "=" in param)
            logger.info(f"🔧 Params parsed: {params}")
            result = search_attractions(params)
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
        formatted_text = format_attractions_results(result)
        
        # Create a structured response with both formatted text and raw data
        complete_result = {
            "formatted_text": formatted_text,
            "attractions": result.get("attractions", {}),
            "api_data": result,
            "status": "error" if "error" in result else "success"
        }
        
        return complete_result

    except Exception as e:
        logger.error(f"❌ Attraction Search Agent Exception: {e}")
        logger.error(traceback.format_exc())
        
        error_result = {
            "error": f"Internal error: {str(e)}",
            "formatted_text": f"❌ Attraction search error: Internal error occurred.",
            "status": "error",
            "api_data": {
                "error": f"Internal error: {str(e)}",
                "status": "error"
            }
        }
        return error_result
# ------------------ Formatting ------------------ #
def format_attractions_results(attractions_data: Dict[str, Any]) -> str:
    """Format attractions search results into a readable string"""
    # Handle error case first
    if isinstance(attractions_data, dict) and "error" in attractions_data:
        return f"❌ Attraction search error: {attractions_data['error']}"
    
    # Handle missing data
    if not isinstance(attractions_data, dict) or "attractions" not in attractions_data:
        return "⚠️ No attraction data received."
    
    attractions_list = attractions_data["attractions"]["attractions_list"]
    location = attractions_data["attractions"]["query"]["location"]
    
    if "error" in attractions_list:
        return f"❌ Error finding attractions: {attractions_list['error']}"
    
    if not attractions_list.get("attractions", []):
        return f"No attractions found for {location}."
    
    msg = f"Top attractions in {location}:\n\n"
    
    # Build the attractions list
    for i, attraction in enumerate(attractions_list.get("attractions", [])[:5], 1):
        name = attraction.get("name", "Unknown Attraction")
        address = attraction.get("address", "Unknown Location")
        rating = attraction.get("rating", "N/A")
        total_ratings = attraction.get("total_ratings", "N/A")
        
        msg += f"**{i}. {name}**\n"
        msg += f"📍 Address: {address}\n"
        msg += f"⭐ Rating: {rating}/5"
        if total_ratings != "N/A":
            msg += f" ({total_ratings} reviews)"
        msg += "\n"
        
        # Add photo if available
        if photo_url := attraction.get("photo_url"):
            msg += f"📸 [View Photo]({photo_url})\n"
        
        # Add types/categories if available
        if "types" in attraction and attraction["types"]:
            msg += f"🏷️ Types: {', '.join(attraction['types'][:3])}\n"
        
        msg += "\n"
    
    return msg