# itinerary_agent.py

import os
import json
import logging
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import the tools directly
from tools.flight_search import flight_search
from tools.explore_places_tool import explore_places
from tools.hotel_search import hotel_search
from tools.restaurant_search_tool import search_restaurants

# Import LLM
from langchain_openai import ChatOpenAI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('itinerary_agent')

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# ------------------ Itinerary Agent Main Function ------------------ #
def itinerary_agent(*, input_str: str) -> Dict[str, Any]:
    """
    Main itinerary agent function that coordinates various travel tools
    to build a comprehensive travel itinerary.
    
    This function:
    1. Parses structured query parameters from the input string
    2. Validates required parameters (destination, start date, end date)
    3. Coordinates calls to multiple travel APIs:
       - Flight search (if origin provided)
       - Hotel search
       - Attractions search
       - Restaurant recommendations
    4. Uses an LLM to generate a comprehensive itinerary based on API results
    5. Returns both machine-readable data and human-readable formatted text
    
    Parameters:
    -----------
    input_str : str
        URL-style parameter string with the following parameters:
        - destination: Required. City/location to visit
        - startDate: Required. Trip start date (YYYY-MM-DD format)
        - endDate: Required. Trip end date (YYYY-MM-DD format)
        - origin: Optional. Origin location for flights
        - travelers: Optional. Number of travelers (default: 1)
        - interests: Optional. Comma-separated list of traveler interests
        
        Example: "destination=Paris&startDate=2025-06-10&endDate=2025-06-15&origin=New York&travelers=2"
    
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing:
        - formatted_text: Human-readable itinerary (markdown format)
        - itinerary: Structured itinerary data
        - trip_name: Generated name for the trip
        - api_data: Raw data from all API calls
        - status: "success" or "error"
        - error: Error message (only present if status is "error")
    """
    try:
        logger.info(f"🔍 Received input_str: {input_str}")
        
        # Parse the input string into a structured format
        if "destination=" in input_str and "startDate=" in input_str:
            # Already in structured format
            params = dict(param.split("=", 1) for param in input_str.split("&") if "=" in param)
            logger.info(f"🔧 Params parsed: {params}")
        else:
            # For natural language input, we would need LLM parsing
            # This would be handled in the parent module
            return {"error": "Natural language parsing should be handled by the parent module"}
        
        # Create the itinerary 
        result = build_itinerary(params)
        
        # Check for errors
        if "error" in result:
            return {
                "error": result["error"],
                "formatted_text": f"❌ Itinerary creation error: {result['error']}",
                "status": "error",
                "api_data": {"error": result["error"]}
            }
        
        # Format the results for human-readable output
        if "formatted_text" not in result:
            formatted_text = generate_formatted_text(result["itinerary"])
            result["formatted_text"] = formatted_text
        
        # Create a structured response
        origin_val = params.get('origin', 'Home')
        dest_val = params.get('destination', 'Destination')
        trip_name = f"{origin_val} to {dest_val} Trip"
        
        complete_result = {
            "formatted_text": result.get("formatted_text", ""),
            "itinerary": result.get("itinerary", {}),
            "trip_name": result.get("itinerary", {}).get("trip_name", trip_name),
            "api_data": result,
            "status": "success"
        }
        
        return complete_result

    except Exception as e:
        logger.error(f"❌ Itinerary Agent Exception: {e}")
        logger.error(traceback.format_exc())
        
        error_result = {
            "error": f"Internal error: {str(e)}",
            "formatted_text": f"❌ Itinerary creation error: Internal error occurred.",
            "status": "error",
            "api_data": {
                "error": f"Internal error: {str(e)}",
                "status": "error"
            }
        }
        return error_result

# ------------------ Itinerary Building ------------------ #
def build_itinerary(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Core itinerary building function that coordinates multiple tools
    and uses an LLM to create a complete travel plan
    """
    try:
        # Required field guards
        required_fields = ["destination", "startDate", "endDate"]
        missing = [f for f in required_fields if f not in params or not params[f]]
        if missing:
            return {"error": f"Missing required parameter(s): {', '.join(missing)}"}
        
        destination = params["destination"]
        start_date = params["startDate"]
        end_date = params["endDate"]
        origin = params.get("origin", "")  # Optional origin for flights
        num_travelers = int(params.get("travelers", "1"))
        interests = params.get("interests", "").split(",") if "interests" in params else []
        
        # Collect all travel data
        travel_data = collect_travel_data(destination, start_date, end_date, origin, num_travelers, interests)
        
        # If there was an error collecting data
        if "error" in travel_data:
            return {"error": travel_data["error"]}
        
        # Use LLM to generate the itinerary
        generated_itinerary = generate_llm_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            origin=origin,
            num_travelers=num_travelers,
            interests=interests,
            travel_data=travel_data
        )
        
        # Return the result
        return generated_itinerary
        
    except Exception as e:
        logger.error(f"❌ Itinerary Building Exception: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error building itinerary: {str(e)}"}

def collect_travel_data(
    destination: str,
    start_date: str,
    end_date: str,
    origin: str = "",
    num_travelers: int = 1,
    interests: List[str] = []
) -> Dict[str, Any]:
    """
    Collect all necessary travel data from various APIs
    """
    travel_data = {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "origin": origin,
        "num_travelers": num_travelers,
        "interests": interests
    }
    
    # Collect flight data if origin is provided
    if origin:
        logger.info(f"🛫 Searching for flights from {origin} to {destination}")
        flight_query = f"from={origin}&to={destination}&departureDate={start_date}"
        if end_date:
            flight_query += f"&returnDate={end_date}"
        flight_query += f"&adults={num_travelers}"
        
        flight_result = flight_search(flight_query)
        if "error" not in flight_result:
            travel_data["flights"] = flight_result.get("flight", {})
            logger.info(f"✅ Found flight options")
        else:
            logger.warning(f"⚠️ Flight search error: {flight_result.get('error')}")
    
    # Collect hotel data
    logger.info(f"🏨 Searching for hotels in {destination}")
    hotel_query = f"city={destination}&checkInDate={start_date}&checkOutDate={end_date}&adults={num_travelers}"
    hotel_result = hotel_search(hotel_query)
    if "error" not in hotel_result:
        travel_data["hotels"] = hotel_result.get("hotels", {})
        logger.info(f"✅ Found hotel options")
    else:
        logger.warning(f"⚠️ Hotel search error: {hotel_result.get('error')}")
    
    # Collect attractions data
    logger.info(f"🏛️ Searching for attractions in {destination}")
    attractions_query = f"location={destination}"
    attractions_result = explore_places(attractions_query)
    if "error" not in attractions_result:
        travel_data["attractions"] = attractions_result
        logger.info(f"✅ Found attractions")
    else:
        logger.warning(f"⚠️ Attractions search error: {attractions_result.get('error')}")
    
    # Collect restaurant data
    logger.info(f"🍽️ Searching for restaurants in {destination}")
    restaurant_query = f"location={destination}"
    restaurant_result = search_restaurants(restaurant_query)
    if "error" not in restaurant_result:
        travel_data["restaurants"] = restaurant_result
        logger.info(f"✅ Found restaurants")
    else:
        logger.warning(f"⚠️ Restaurant search error: {restaurant_result.get('error')}")
    
    return travel_data

def generate_llm_itinerary(
    destination: str,
    start_date: str,
    end_date: str,
    origin: str,
    num_travelers: int,
    interests: List[str],
    travel_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a comprehensive itinerary using an LLM based on collected travel data
    """
    try:
        # Format the travel data for the LLM
        llm_input = format_travel_data_for_llm(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            origin=origin,
            num_travelers=num_travelers,
            interests=interests,
            travel_data=travel_data
        )
        
        # Create the prompt for the LLM - Store as a normal string, not an f-string
        prompt = """Create a Dream Itinerary! 
You are a professional travel planner tasked with crafting an exciting and well-organized itinerary summary based on the travel details provided below. Please use a clear and readable structure, incorporating professional bullet points where helpful to make the itinerary engaging and easy to follow.

Travel Details:
""" + llm_input + """

Your Task:
Weather Advisory: Begin by highlighting any important weather conditions or advisories for the travel period.
Itinerary Structure: Organize the itinerary into daily segments (e.g., Day 1, Day 2, etc.). Only make heading points bold all other text should be normal.
Inclusions:
Travel Dates: Clearly state the start and end dates of the trip.
Weather Highlights: Mention any notable weather conditions during the trip.
Popular Places: List must-visit attractions and experiences.
Food Suggestions: Recommend local cuisine or must-try dishes.
Events: Include any notable events happening during the trip.
Flight Summary: If applicable, provide a brief overview of flights (e.g., departure and arrival times, airlines).
Travel Tips: If the distance between destinations is significant, suggest whether flying is the best option or if a scenic drive is recommended.

Example Structure:
Weather Advisory:
[Insert weather advisory here]

Itinerary:
**Day 1:** [Describe activities and places to visit]
**Day 2:** [Continue with daily activities]
**Day 3:** [And so on]

Additional Tips:
[Provide any additional travel tips or recommendations]

Let's create an unforgettable journey!

IMPORTANT: Return both the formatted text itinerary for human reading AND a JSON structure for machine processing. 
The JSON structure should include the complete itinerary with days, events, times, and all details in the following format:
{
  "trip_name": "Origin to Destination Trip",
  "destination": "Destination",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "origin": "Origin",
  "num_travelers": Number,
  "days": [
    {
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "events": [
        {
          "event_type": "flight",
          "description": "Flight description",
          "flight_number": "AA123",
          "departure_airport": "AAA",
          "arrival_airport": "BBB",
          "boarding_time": "HH:MM",
          "departure_time": "HH:MM",
          "arrival_time": "HH:MM",
          "seat_number": "TBD",
          "booking_required": true,
          "price": "price",
          "booking_id": ""
        },
        {
          "event_type": "hotel",
          "description": "Hotel name",
          "address": "Hotel address",
          "check_in_time": "15:00",
          "check_out_time": "11:00",
          "room_selection": "Standard Room",
          "booking_required": true,
          "price": "price",
          "booking_id": ""
        },
        {
          "event_type": "visit",
          "description": "Visit attraction",
          "address": "Attraction address",
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "booking_required": false
        }
      ]
    }
  ]
}

Your response should have two sections:
1. FORMATTED_TEXT: The human-readable itinerary
2. JSON_DATA: The machine-readable JSON structure
Each section should be clearly labeled.
"""
        
        # Get the response from the LLM
        response = llm.invoke(prompt)
        logger.info(f"✅ LLM generated itinerary response")
        
        # Process the response
        formatted_text, json_data = extract_formatted_text_and_json(response.content)
        
        # Process any final adjustments to the itinerary
        if json_data:
            # Ensure required structure even if LLM didn't follow instructions exactly
            if "trip_name" not in json_data:
                origin_val = origin if origin else 'Home'
                json_data["trip_name"] = f"{origin_val} to {destination} Trip"
            if "destination" not in json_data:
                json_data["destination"] = destination
            if "start_date" not in json_data:
                json_data["start_date"] = start_date
            if "end_date" not in json_data:
                json_data["end_date"] = end_date
            if "origin" not in json_data:
                json_data["origin"] = origin if origin else "Home"
            if "num_travelers" not in json_data:
                json_data["num_travelers"] = num_travelers
            
            # Return the completed itinerary
            return {
                "itinerary": json_data,
                "formatted_text": formatted_text
            }
        else:
            # Fallback to generating a basic itinerary
            logger.warning("⚠️ Failed to extract JSON data from LLM response, using fallback")
            fallback_itinerary = generate_fallback_itinerary(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                origin=origin,
                num_travelers=num_travelers,
                travel_data=travel_data
            )
            
            return {
                "itinerary": fallback_itinerary,
                "formatted_text": formatted_text if formatted_text else generate_formatted_text(fallback_itinerary)
            }
            
    except Exception as e:
        logger.error(f"❌ LLM Itinerary Generation Error: {e}")
        logger.error(traceback.format_exc())
        
        # Fallback to generating a basic itinerary
        fallback_itinerary = generate_fallback_itinerary(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            origin=origin,
            num_travelers=num_travelers,
            travel_data=travel_data
        )
        
        return {
            "itinerary": fallback_itinerary,
            "formatted_text": generate_formatted_text(fallback_itinerary)
        }

def format_travel_data_for_llm(
    destination: str,
    start_date: str,
    end_date: str,
    origin: str,
    num_travelers: int,
    interests: List[str],
    travel_data: Dict[str, Any]
) -> str:
    """
    Format the travel data in a way that's easy for the LLM to understand
    """
    # Calculate trip duration
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    num_days = (end - start).days + 1
    
    # Format interests
    interests_str = ", ".join(interests) if interests else "general sightseeing"
    
    # Basic travel information
    formatted_data = "Destination: " + destination + "\n"
    formatted_data += "Origin: " + (origin if origin else 'Home') + "\n"
    formatted_data += "Travel Dates: " + start_date + " to " + end_date + " (" + str(num_days) + " days)\n"
    formatted_data += "Number of Travelers: " + str(num_travelers) + "\n"
    formatted_data += "Interests: " + interests_str + "\n\n"
    
    # Flight information
    if "flights" in travel_data and "data" in travel_data["flights"] and travel_data["flights"]["data"]:
        flights = travel_data["flights"]["data"]
        formatted_data += "Flight Information:\n"
        
        for i, flight in enumerate(flights[:3]):
            price = flight.get("price", {}).get("total", "Unknown")
            currency = flight.get("price", {}).get("currency", "USD")
            
            formatted_data += "Option " + str(i+1) + " - Price: " + str(price) + " " + currency + "\n"
            
            for j, itinerary in enumerate(flight.get("itineraries", [])):
                if j == 0:
                    formatted_data += "  Outbound Journey:\n"
                else:
                    formatted_data += "  Return Journey:\n"
                
                for segment in itinerary.get("segments", []):
                    dep = segment["departure"]["iataCode"]
                    arr = segment["arrival"]["iataCode"]
                    # Fix for nested f-string issue - build parts separately
                    dep_time_raw = segment["departure"]["at"]
                    arr_time_raw = segment["arrival"]["at"]
                    dep_time = dep_time_raw.replace("T", " ").split("+")[0]
                    arr_time = arr_time_raw.replace("T", " ").split("+")[0]
                    carrier = segment.get("carrierCode", "")
                    flight_num = segment.get("number", "")
                    
                    formatted_data += "    " + dep + " to " + arr + ": " + carrier + " " + flight_num + "\n"
                    formatted_data += "    Departure: " + dep_time + ", Arrival: " + arr_time + "\n"
            
            formatted_data += "\n"
    
    # Hotel information
    if "hotels" in travel_data and "data" in travel_data["hotels"] and travel_data["hotels"]["data"]:
        formatted_data += "Hotel Options:\n"
        hotels = travel_data["hotels"]["data"]
        
        for i, hotel in enumerate(hotels[:3]):
            name = hotel.get("name", "Unknown Hotel")
            
            # Format address
            address_components = []
            if "address" in hotel:
                if "lines" in hotel["address"] and hotel["address"]["lines"]:
                    address_components.extend(hotel["address"]["lines"])
                if "cityName" in hotel["address"]:
                    address_components.append(hotel["address"]["cityName"])
            
            address = ", ".join(address_components) if address_components else "Address not available"
            
            formatted_data += str(i+1) + ". " + name + "\n"
            formatted_data += "   Address: " + address + "\n"
            formatted_data += "   Check-in: 15:00, Check-out: 11:00\n\n"
    
    # Attraction information
    if "attractions" in travel_data and "attractions" in travel_data["attractions"]:
        formatted_data += "Top Attractions:\n"
        attractions = travel_data["attractions"]["attractions"]
        
        for i, attraction in enumerate(attractions[:10]):
            name = attraction.get("name", "Unknown Attraction")
            address = attraction.get("address", "Address not available")
            rating = attraction.get("rating", "N/A")
            
            formatted_data += str(i+1) + ". " + name + "\n"
            formatted_data += "   Address: " + address + "\n"
            formatted_data += "   Rating: " + str(rating) + "/5\n\n"
    
    # Restaurant information
    if "restaurants" in travel_data and "restaurants" in travel_data["restaurants"]:
        formatted_data += "Restaurant Recommendations:\n"
        restaurants = travel_data["restaurants"]["restaurants"]
        
        for i, restaurant in enumerate(restaurants[:6]):
            name = restaurant.get("name", "Unknown Restaurant")
            address = restaurant.get("address", "Address not available")
            rating = restaurant.get("rating", "N/A")
            
            formatted_data += str(i+1) + ". " + name + "\n"
            formatted_data += "   Address: " + address + "\n"
            formatted_data += "   Rating: " + str(rating) + "/5\n\n"
    
    return formatted_data

def extract_formatted_text_and_json(response_text: str) -> tuple:
    """
    Extract the formatted text and JSON data from the LLM response
    """
    # Initialize variables
    formatted_text = ""
    json_data = None
    
    # Check for section markers
    formatted_text_marker = "FORMATTED_TEXT:"
    json_data_marker = "JSON_DATA:"
    
    if formatted_text_marker in response_text and json_data_marker in response_text:
        # Split by markers
        parts = response_text.split(formatted_text_marker, 1)
        if len(parts) > 1:
            second_part = parts[1]
            text_parts = second_part.split(json_data_marker, 1)
            if len(text_parts) > 1:
                formatted_text = text_parts[0].strip()
                json_str = text_parts[1].strip()
                
                # Try to extract JSON
                try:
                    # Look for JSON-like content
                    json_start = json_str.find('{')
                    json_end = json_str.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_content = json_str[json_start:json_end]
                        json_data = json.loads(json_content)
                except json.JSONDecodeError:
                    logger.warning("⚠️ Failed to parse JSON from LLM response")
    else:
        # If no markers, try to find JSON and use the rest as formatted text
        try:
            # Look for JSON-like content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_text[json_start:json_end]
                json_data = json.loads(json_content)
                
                # Use everything before JSON as formatted text
                formatted_text = response_text[:json_start].strip()
                
                # If no formatted text was found, use everything after JSON
                if not formatted_text:
                    formatted_text = response_text[json_end:].strip()
            else:
                # No JSON found, use entire response as formatted text
                formatted_text = response_text
        except json.JSONDecodeError:
            # No valid JSON found, use entire response as formatted text
            formatted_text = response_text
    
    return formatted_text, json_data

def generate_fallback_itinerary(
    destination: str,
    start_date: str,
    end_date: str,
    origin: str,
    num_travelers: int,
    travel_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a basic itinerary as a fallback when LLM generation fails
    """
    logger.info("⚠️ Using fallback itinerary generation")
    
    # Initialize the itinerary structure
    origin_val = origin if origin else 'Home'
    itinerary = {
        "trip_name": f"{origin_val} to {destination} Trip",
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "origin": origin_val,
        "num_travelers": num_travelers,
        "days": []
    }
    
    # Calculate trip duration
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    num_days = (end - start).days + 1
    
    # Get available data
    flights = travel_data.get("flights", {}).get("data", [])
    hotels = travel_data.get("hotels", {}).get("data", [])
    attractions = travel_data.get("attractions", {}).get("attractions", [])
    restaurants = travel_data.get("restaurants", {}).get("restaurants", [])
    
    # Calculate how many attractions and restaurants per day
    attractions_per_day = min(2, len(attractions) // max(1, num_days)) if attractions else 0
    restaurants_per_day = min(2, len(restaurants) // max(1, num_days)) if restaurants else 0
    
    # Generate days
    for day_num in range(num_days):
        current_date = start + timedelta(days=day_num)
        day_str = current_date.strftime("%Y-%m-%d")
        
        day = {
            "day_number": day_num + 1,
            "date": day_str,
            "events": []
        }
        
        # First day: Add outbound flight and hotel check-in
        if day_num == 0:
            # Add flight if available
            if flights:
                flight = flights[0]
                outbound = flight["itineraries"][0]["segments"][0]
                
                # Fix for nested f-strings - use intermediate variables
                departure_at = outbound["departure"]["at"].replace("Z", "+00:00")
                arrival_at = outbound["arrival"]["at"].replace("Z", "+00:00")
                
                departure_datetime = datetime.fromisoformat(departure_at)
                arrival_datetime = datetime.fromisoformat(arrival_at)
                boarding_datetime = departure_datetime - timedelta(minutes=30)
                
                boarding_time = boarding_datetime.strftime("%H:%M")
                departure_time = departure_datetime.strftime("%H:%M")
                arrival_time = arrival_datetime.strftime("%H:%M")
                
                # Get carrier and flight number
                carrier = outbound.get('carrierCode', '')
                flight_num = outbound.get('number', '')
                flight_id = carrier + " " + flight_num
                
                # Construct flight description
                flight_desc = "Flight from " + origin + " to " + destination
                
                flight_event = {
                    "event_type": "flight",
                    "description": flight_desc,
                    "flight_number": flight_id,
                    "departure_airport": outbound["departure"]["iataCode"],
                    "arrival_airport": outbound["arrival"]["iataCode"],
                    "boarding_time": boarding_time,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "seat_number": "TBD",
                    "booking_required": True,
                    "price": flight["price"]["total"],
                    "booking_id": ""
                }
                day["events"].append(flight_event)
            
            # Add hotel check-in if available
            if hotels:
                hotel = hotels[0]
                address_components = []
                if "address" in hotel:
                    if "lines" in hotel["address"] and hotel["address"]["lines"]:
                        address_components.extend(hotel["address"]["lines"])
                    if "cityName" in hotel["address"]:
                        address_components.append(hotel["address"]["cityName"])
                
                address = ", ".join(address_components) if address_components else destination
                hotel_name = hotel.get("name", "Hotel Accommodation")
                
                hotel_event = {
                    "event_type": "hotel",
                    "description": hotel_name,
                    "address": address,
                    "check_in_time": "15:00",
                    "check_out_time": "11:00",
                    "room_selection": "Standard Room",
                    "booking_required": True,
                    "price": "TBD",
                    "booking_id": ""
                }
                day["events"].append(hotel_event)
        
        # Last day: Add return flight and hotel checkout
        if day_num == num_days - 1:
            # Add hotel checkout if we have hotel data
            if hotels:
                hotel = hotels[0]
                address_components = []
                if "address" in hotel:
                    if "lines" in hotel["address"] and hotel["address"]["lines"]:
                        address_components.extend(hotel["address"]["lines"])
                    if "cityName" in hotel["address"]:
                        address_components.append(hotel["address"]["cityName"])
                
                address = ", ".join(address_components) if address_components else destination
                hotel_name = hotel.get('name', 'Hotel')
                checkout_desc = "Check out from " + hotel_name
                
                checkout_event = {
                    "event_type": "visit",
                    "description": checkout_desc,
                    "address": address,
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "booking_required": False
                }
                day["events"].append(checkout_event)
            
            # Add return flight if available
            if flights and len(flights[0]["itineraries"]) > 1:
                flight = flights[0]
                return_flight = flight["itineraries"][1]["segments"][0]
                
                # Fix for nested f-strings - use intermediate variables
                departure_at = return_flight["departure"]["at"].replace("Z", "+00:00")
                arrival_at = return_flight["arrival"]["at"].replace("Z", "+00:00")
                
                departure_datetime = datetime.fromisoformat(departure_at)
                arrival_datetime = datetime.fromisoformat(arrival_at)
                boarding_datetime = departure_datetime - timedelta(minutes=30)
                
                boarding_time = boarding_datetime.strftime("%H:%M")
                departure_time = departure_datetime.strftime("%H:%M")
                arrival_time = arrival_datetime.strftime("%H:%M")
                
                # Get carrier and flight number
                carrier = return_flight.get('carrierCode', '')
                flight_num = return_flight.get('number', '')
                flight_id = carrier + " " + flight_num
                
                # Construct flight description
                flight_desc = "Return Flight from " + destination + " to " + origin
                
                flight_event = {
                    "event_type": "flight",
                    "description": flight_desc,
                    "flight_number": flight_id,
                    "departure_airport": return_flight["departure"]["iataCode"],
                    "arrival_airport": return_flight["arrival"]["iataCode"],
                    "boarding_time": boarding_time,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "seat_number": "TBD",
                    "booking_required": True,
                    "price": flight["price"]["total"],
                    "booking_id": ""
                }
                day["events"].append(flight_event)
        
        # Add attractions for all days
        start_idx = day_num * attractions_per_day
        end_idx = min((day_num + 1) * attractions_per_day, len(attractions))
        
        for i, idx in enumerate(range(start_idx, end_idx)):
            attraction = attractions[idx]
            
            # Morning or afternoon based on index
            if i == 0:
                start_time = "09:00"
                end_time = "12:00"
            else:
                start_time = "14:00"
                end_time = "17:00"
            
            attraction_name = attraction.get('name', 'Local Attraction')
            attraction_desc = "Visit " + attraction_name
            
            attraction_event = {
                "event_type": "visit",
                "description": attraction_desc,
                "address": attraction.get("address", ""),
                "start_time": start_time,
                "end_time": end_time,
                "booking_required": False
            }
            day["events"].append(attraction_event)
        
        # Add restaurants for all days
        start_idx = day_num * restaurants_per_day
        end_idx = min((day_num + 1) * restaurants_per_day, len(restaurants))
        
        for i, idx in enumerate(range(start_idx, end_idx)):
            if idx < len(restaurants):
                restaurant = restaurants[idx]
                
                # Lunch or dinner based on index
                if i == 0:
                    time = "12:30"
                    meal = "Lunch"
                else:
                    time = "19:00"
                    meal = "Dinner"
                
                restaurant_name = restaurant.get('name', 'Local Restaurant')
                restaurant_desc = meal + " at " + restaurant_name
                
                restaurant_event = {
                    "event_type": "visit",
                    "description": restaurant_desc,
                    "address": restaurant.get("address", ""),
                    "start_time": time,
                    "end_time": "",
                    "booking_required": False
                }
                day["events"].append(restaurant_event)
        
        # Sort events by time
        day["events"].sort(key=lambda x: x.get("boarding_time", "") or x.get("start_time", "00:00"))
        
        # Add day to itinerary
        itinerary["days"].append(day)
    
    return itinerary

def generate_formatted_text(itinerary: Dict[str, Any]) -> str:
    """
    Generate a human-readable formatted text from the itinerary data
    """
    # Basic trip information
    trip_name = itinerary.get("trip_name", "Your Trip")
    destination = itinerary.get("destination", "Destination")
    start_date = itinerary.get("start_date", "")
    end_date = itinerary.get("end_date", "")
    origin = itinerary.get("origin", "")
    num_travelers = itinerary.get("num_travelers", 1)
    
    # Build the formatted text using concatenation rather than f-strings
    formatted_text = "# " + trip_name + "\n\n"
    formatted_text += "Travel Dates: " + start_date + " to " + end_date + "\n"
    formatted_text += "Destination: " + destination + "\n"
    if origin:
        formatted_text += "Origin: " + origin + "\n"
    formatted_text += "Number of Travelers: " + str(num_travelers) + "\n\n"
    
    # Weather advisory (placeholder)
    formatted_text += "Weather Advisory:\n"
    formatted_text += "Please check local weather forecasts closer to your travel dates.\n\n"
    
    # Daily itinerary
    formatted_text += "Itinerary:\n\n"
    
    for day in itinerary.get("days", []):
        day_num = day.get("day_number", 0)
        date = day.get("date", "")
        
        formatted_text += "**Day " + str(day_num) + ": " + date + "**\n\n"
        
        for event in day.get("events", []):
            event_type = event.get("event_type", "")
            description = event.get("description", "")
            
            if event_type == "flight":
                # Flight event
                dep_airport = event.get("departure_airport", "")
                arr_airport = event.get("arrival_airport", "")
                dep_time = event.get("departure_time", "")
                boarding_time = event.get("boarding_time", "")
                
                formatted_text += "- " + description + "\n"
                formatted_text += "  Boarding: " + boarding_time + ", Departure: " + dep_time + "\n"
                formatted_text += "  " + dep_airport + " to " + arr_airport + "\n\n"
                
            elif event_type == "hotel":
                # Hotel event
                address = event.get("address", "")
                check_in_time = event.get("check_in_time", "")
                
                formatted_text += "- " + description + "\n"
                formatted_text += "  Check-in: " + check_in_time + "\n"
                formatted_text += "  " + address + "\n\n"
                
            else:
                # Regular visit/activity
                address = event.get("address", "")
                start_time = event.get("start_time", "")
                end_time = event.get("end_time", "")
                
                formatted_text += "- " + description + "\n"
                if start_time:
                    time_str = start_time
                    if end_time:
                        time_str += " - " + end_time
                    formatted_text += "  Time: " + time_str + "\n"
                if address:
                    formatted_text += "  Location: " + address + "\n"
                formatted_text += "\n"
        
        formatted_text += "\n"
    
    # Additional tips
    formatted_text += "Additional Tips:\n"
    formatted_text += "- It's advisable to reconfirm all bookings before your trip\n"
    formatted_text += "- Consider travel insurance for peace of mind\n"
    formatted_text += "- Keep important documents (passports, IDs) in a safe place\n"
    formatted_text += "- Check local COVID-19 guidelines before travel\n"
    
    return formatted_text