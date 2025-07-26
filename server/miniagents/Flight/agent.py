import os
import json
import re
import logging
import traceback
from typing import Dict, Any

# Import the flight_search tool
from tools.flight_search import flight_search
from datetime import datetime 
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('flight_agent')

# ------------------ Flight Agent Main Function ------------------ #
def flight_search_agent(*, input_str: str) -> Dict[str, Any]:
    """
    Main flight search agent function that takes either natural language
    or structured input and returns flight search results by using the flight_search tool
    """
    try:
        print("🔧 flight_search_agent CALLED with:", input_str)
        logger.info(f"🔍 Received input_str: {input_str}")

        # Parse the input string (either directly or preprocess with LLM in the other file)
        if re.search(r"from=.*&to=.*&departureDate=", input_str):
            # Already in structured format - use the flight_search tool directly
            logger.info(f"🔧 Using flight_search tool with input: {input_str}")
            api_data = flight_search(input_str)
            
            # Check if there was an error
            if "error" in api_data:
                return api_data
                
            # Return both human-readable formatted text and the complete API data
            return {
                "formatted_text": format_flight_results(api_data),
                "flight": api_data.get("flight", {}),
                "api_data": api_data  # Include the complete API response
            }
        else:
            # For natural language input, we need to call the LLM parser
            # This will be handled in the parent file that imports this module
            return {"error": "Natural language parsing should be handled by the parent module"}

    except Exception as e:
        logger.error(f"❌ Flight Search Agent Exception: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Internal error: {str(e)}"}
# ------------------ Formatting ------------------ #
# def format_flight_results(flight_data: Dict[str, Any]) -> str:
    
    
#     """Format flight search results into a readable string"""
#     if "error" in flight_data:
#         return f"❌ Flight search error: {flight_data['error']}"
#     if "flight" not in flight_data:
#         return "⚠️ No flight data received."
#     offers = flight_data["flight"].get("data", [])
#     if not offers:
#         return "No flights found matching your criteria."
#     logger.info("Formatting flight search results", flight_data)
#     msg = "Here are your flight options:\n\n"
#     for i, offer in enumerate(offers[:5], 1):
#         price = offer.get("price", {}).get("total", "N/A")
#         currency = offer.get("price", {}).get("currency", "USD")
#         msg += f"Option {i}: {price} {currency}\n"
#         for j, itinerary in enumerate(offer.get("itineraries", [])):
#             trip_type = "Outbound" if j == 0 else "Return"
#             msg += f"  {trip_type} Journey:\n"
#             for segment in itinerary.get("segments", []):
#                 dep = segment["departure"]["iataCode"]
#                 arr = segment["arrival"]["iataCode"]
#                 dep_time = segment["departure"]["at"].replace("T", " ").split("+")[0]
#                 arr_time = segment["arrival"]["at"].replace("T", " ").split("+")[0]
#                 flight_code = f"{segment.get('carrierCode', '')} {segment.get('number', '')}"
#                 msg += f"    {dep} → {arr} ({flight_code})\n    {dep_time} → {arr_time}\n"
#         msg += "\n"
#     return msg

def format_flight_results(flight_data: Dict[str, Any]) -> str:
    """Format flight search results into a readable string"""
    try:
        # Handle error cases
        if "error" in flight_data:
            return f"❌ Flight search error: {flight_data['error']}"
        
        # Check for flight data
        if "flight" not in flight_data:
            return "⚠️ No flight data received."
        
        # Extract offers
        offers = flight_data["flight"].get("data", [])
        if not offers:
            return "No flights found matching your criteria."
        
        # Log for debugging
        logger.info(f"Formatting {len(offers)} flight offers")
        
        # Build the message
        msg = f"Here are some flight options from {offers[0]['itineraries'][0]['segments'][0]['departure']['iataCode']} to "
        destination = offers[0]['itineraries'][0]['segments'][-1]['arrival']['iataCode']
        
        # Get departure and return dates
        dep_date = offers[0]['itineraries'][0]['segments'][0]['departure']['at'].split('T')[0]
        ret_date = offers[0]['itineraries'][1]['segments'][0]['departure']['at'].split('T')[0] if len(offers[0]['itineraries']) > 1 else "N/A"
        
        msg += f"{destination}, departing on {dep_date} and returning on {ret_date}, {datetime.now().year}:\n\n"
        
        for i, offer in enumerate(offers[:5], 1):
            price = offer.get("price", {}).get("total", "N/A")
            currency = offer.get("price", {}).get("currency", "USD")
            
            # Format option heading with ### for better visibility
            msg += f"### Option {i}: ${price} {currency} - "
            
            # Format itineraries
            for j, itinerary in enumerate(offer.get("itineraries", [])):
                trip_type = "Outbound Journey" if j == 0 else "Return Journey"
                msg += f"{trip_type}: - "
                
                for k, segment in enumerate(itinerary.get("segments", [])):
                    # Origin to destination format
                    dep = segment["departure"]["iataCode"]
                    arr = segment["arrival"]["iataCode"]
                    
                    # Add connector if not the first segment
                    if k > 0:
                        msg += " - "
                    
                    msg += f"{dep} to {arr}"
                    
                    # Full details of this segment
                    flight_code = f"{segment.get('carrierCode', '')} {segment.get('number', '')}"
                    dep_time = segment["departure"]["at"].replace("T", " at ").split("+")[0]
                    arr_time = segment["arrival"]["at"].replace("T", " at ").split("+")[0]
                    
                    msg += f": Flight {flight_code} - Departure: {dep_time} - Arrival: {arr_time}"
                    
                    # Add separator between segments if needed
                    if k < len(itinerary.get("segments", [])) - 1:
                        msg += " - "
                
                # Add separator between outbound and return
                if j == 0 and len(offer.get("itineraries", [])) > 1:
                    msg += " - "
            
            # Add newline between options
            msg += "\n"
        
        # Add summary message
        all_same_price = all(offer.get("price", {}).get("total") == offers[0].get("price", {}).get("total") for offer in offers)
        if all_same_price:
            msg += f"\nAll options are priced at ${offers[0].get('price', {}).get('total')} {offers[0].get('price', {}).get('currency', 'USD')}. Let me know if you need more details or assistance with booking!"
        
        return msg
        
    except Exception as e:
        logger.error(f"Error formatting flight results: {str(e)}")
        return f"Error formatting flight results: {str(e)}"