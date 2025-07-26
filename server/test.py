import os
import json
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_amadeus_access_token() -> str:
    """Get Amadeus API access token"""
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return "dummy_token_for_testing"
    
    token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    # Skip actual API call in test mode
    return "dummy_token_for_testing"

def flight_search_agent(input_str: str) -> dict:
    """Function to test the flight_search_agent from the original code"""
    try:
        print(f"🔍 Received input_str: {input_str}")
        # Parse input string into parameters
        params = {}
        for param in input_str.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
        
        # Get required parameters
        origin_city = params.get("from", "")
        destination_city = params.get("to", "")
        departure_date = params.get("departureDate", "")
        adults = int(params.get("adults", "1"))
        
        print(f"Parsed parameters:")
        print(f"  From: {origin_city}")
        print(f"  To: {destination_city}")
        print(f"  Date: {departure_date}")
        print(f"  Adults: {adults}")
        
        # Generate mock flight data instead of calling the API
        mock_flight_response = {
            "flight": {
                "meta": {
                    "count": 2,
                    "links": {
                        "self": f"https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode={origin_city}&destinationLocationCode={destination_city}"
                    }
                },
                "data": [
                    {
                        "type": "flight-offer",
                        "id": "1",
                        "source": "GDS",
                        "lastTicketingDate": departure_date.split("T")[0],
                        "numberOfBookableSeats": 9,
                        "itineraries": [
                            {
                                "duration": "PT6H10M",
                                "segments": [
                                    {
                                        "departure": {
                                            "iataCode": origin_city[:3].upper(),
                                            "terminal": "4",
                                            "at": f"{departure_date}T08:00:00"
                                        },
                                        "arrival": {
                                            "iataCode": destination_city[:3].upper(),
                                            "terminal": "6",
                                            "at": f"{departure_date}T14:10:00"
                                        },
                                        "carrierCode": "DL",
                                        "number": "1234",
                                        "duration": "PT6H10M"
                                    }
                                ]
                            }
                        ],
                        "price": {
                            "currency": "USD",
                            "total": "325.67",
                            "base": "280.00",
                            "grandTotal": "325.67"
                        }
                    },
                    {
                        "type": "flight-offer",
                        "id": "2",
                        "source": "GDS",
                        "lastTicketingDate": departure_date.split("T")[0],
                        "numberOfBookableSeats": 5,
                        "itineraries": [
                            {
                                "duration": "PT8H25M",
                                "segments": [
                                    {
                                        "departure": {
                                            "iataCode": origin_city[:3].upper(),
                                            "terminal": "8",
                                            "at": f"{departure_date}T10:30:00"
                                        },
                                        "arrival": {
                                            "iataCode": "DFW",
                                            "terminal": "0",
                                            "at": f"{departure_date}T13:30:00"
                                        },
                                        "carrierCode": "AA",
                                        "number": "5678",
                                        "duration": "PT3H"
                                    },
                                    {
                                        "departure": {
                                            "iataCode": "DFW",
                                            "terminal": "0",
                                            "at": f"{departure_date}T15:00:00"
                                        },
                                        "arrival": {
                                            "iataCode": destination_city[:3].upper(),
                                            "terminal": "4",
                                            "at": f"{departure_date}T16:55:00"
                                        },
                                        "carrierCode": "AA",
                                        "number": "9012",
                                        "duration": "PT1H55M"
                                    }
                                ]
                            }
                        ],
                        "price": {
                            "currency": "USD",
                            "total": str(278.35 * adults),
                            "base": str(245.00 * adults),
                            "grandTotal": str(278.35 * adults)
                        }
                    }
                ]
            }
        }
        
        return mock_flight_response
        
    except Exception as e:
        print(f"❌ Flight Search Error: {e}")
        return {"error": str(e)}

def test_function_call():
    """Test the flight_search_agent function directly"""
    print("\n🧪 TESTING FLIGHT_SEARCH_AGENT FUNCTION 🧪")
    
    # Test case 1
    input_str_1 = "from=NYC&to=LAX&departureDate=2025-05-15&adults=1"
    print(f"\nTest Case 1: {input_str_1}")
    result_1 = flight_search_agent(input_str_1)
    print_flight_summary(result_1)
    
    # Test case 2
    input_str_2 = "from=SFO&to=JFK&departureDate=2025-06-20&adults=2"
    print(f"\nTest Case 2: {input_str_2}")
    result_2 = flight_search_agent(input_str_2)
    print_flight_summary(result_2)
    
    # Test case 3 - with error
    input_str_3 = "from=London&to=Tokyo&adults=1"  # Missing departure date
    print(f"\nTest Case 3: {input_str_3}")
    result_3 = flight_search_agent(input_str_3)
    print_flight_summary(result_3)

def print_flight_summary(result):
    """Print a summary of flight search results"""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
        
    flight_data = result.get("flight", {})
    if "data" not in flight_data or not flight_data["data"]:
        print("⚠️ No flights found or unexpected response format")
        return
    
    flight_count = len(flight_data["data"])
    print(f"✅ Found {flight_count} flight options")
    
    for i, flight in enumerate(flight_data["data"][:2]):  # Show max 2 options
        print(f"\nFlight Option {i+1}:")
        price = flight.get("price", {}).get("total", "Unknown")
        print(f"💰 Price: ${price} USD")
        
        for j, itinerary in enumerate(flight.get("itineraries", [])):
            segments = itinerary.get("segments", [])
            print(f"✈️ Segments: {len(segments)}")
            
            for k, segment in enumerate(segments):
                dep = segment.get("departure", {})
                arr = segment.get("arrival", {})
                carrier = segment.get("carrierCode", "Unknown")
                flight_number = segment.get("number", "Unknown")
                
                print(f"  {dep.get('iataCode', '?')} ({dep.get('at', '?')}) → {arr.get('iataCode', '?')} ({arr.get('at', '?')})")
                print(f"  Flight: {carrier} {flight_number}")

if __name__ == "__main__":
    print("🛫 Testing Flight Search Function...")
    test_function_call()