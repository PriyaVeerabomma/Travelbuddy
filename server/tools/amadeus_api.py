from typing import Dict, Any
import os
import time
import json
import httpx
import logging

logger = logging.getLogger("amadeus_api")
logging.basicConfig(level=logging.INFO)

# ------------------ IATA Code Cache ------------------ #
IATA_CODE_CACHE = {}

# ------------------ Rate Limiter ------------------ #
class RateLimiter:
    def __init__(self, max_calls=10, time_frame=1):
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.call_timestamps = []
        self.last_429_time = None
        self.backoff_time = 5

    def wait_time(self) -> float:
        now = time.time()
        self.call_timestamps = [t for t in self.call_timestamps if now - t <= self.time_frame]
        if self.last_429_time and now - self.last_429_time < self.backoff_time:
            return self.backoff_time - (now - self.last_429_time)
        if len(self.call_timestamps) >= self.max_calls:
            return max(0, self.time_frame - (now - self.call_timestamps[0]))
        return 0

    def record_call(self):
        self.call_timestamps.append(time.time())

    def record_429(self):
        self.last_429_time = time.time()
        self.backoff_time = min(self.backoff_time * 2, 60)
        logger.warning(f"⚠️ Rate limited. New backoff time: {self.backoff_time}s")

rate_limiter = RateLimiter()

# ------------------ Amadeus Access Token ------------------ #
def get_amadeus_access_token() -> str:
    wait = rate_limiter.wait_time()
    if wait > 0:
        logger.info(f"⏳ Waiting {wait:.2f}s before requesting token")
        time.sleep(wait)

    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("AMADEUS_CLIENT_ID"),
        "client_secret": os.getenv("AMADEUS_CLIENT_SECRET")
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        rate_limiter.record_call()
        response = httpx.post(url, data=payload, headers=headers, timeout=30)
        if response.status_code == 429:
            rate_limiter.record_429()
            if hasattr(get_amadeus_access_token, "last_valid_token"):
                logger.info("🔑 Using cached token")
                return get_amadeus_access_token.last_valid_token
            raise Exception("Rate limited and no cached token available")
        response.raise_for_status()
        token = response.json()["access_token"]
        get_amadeus_access_token.last_valid_token = token
        return token
    except Exception as e:
        logger.error(f"❌ Token fetch failed: {e}")
        if hasattr(get_amadeus_access_token, "last_valid_token"):
            return get_amadeus_access_token.last_valid_token
        raise

# ------------------ IATA Resolver ------------------ #
def get_iata_code(city: str, token: str) -> str:
    city_key = city.lower().strip()
    if city_key in IATA_CODE_CACHE:
        return IATA_CODE_CACHE[city_key]

    common_cities = {
        "new york": "NYC", "los angeles": "LAX", "chicago": "CHI", "london": "LON", "paris": "PAR",
        "tokyo": "TYO", "beijing": "BJS", "sydney": "SYD", "san francisco": "SFO", "washington": "WAS",
        "boston": "BOS", "miami": "MIA", "seattle": "SEA", "dallas": "DFW", "toronto": "YTO",
        "frankfurt": "FRA", "rome": "ROM", "madrid": "MAD", "berlin": "BER", "amsterdam": "AMS"
    }
    if city_key in common_cities:
        IATA_CODE_CACHE[city_key] = common_cities[city_key]
        return common_cities[city_key]

    wait = rate_limiter.wait_time()
    if wait > 0:
        logger.info(f"⏳ Waiting {wait:.2f}s before IATA lookup")
        time.sleep(wait)

    try:
        rate_limiter.record_call()
        url = "https://test.api.amadeus.com/v1/reference-data/locations"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"keyword": city, "subType": "CITY"}
        res = httpx.get(url, headers=headers, params=params, timeout=30)
        if res.status_code == 429:
            rate_limiter.record_429()
            return city[:3].upper()
        res.raise_for_status()
        iata_code = res.json().get("data", [{}])[0].get("iataCode", city[:3].upper())
        IATA_CODE_CACHE[city_key] = iata_code
        return iata_code
    except Exception as e:
        logger.error(f"❌ Failed to get IATA code for {city}: {e}")
        return city[:3].upper()

# ------------------ Flight Search ------------------ #
def perform_flight_search_api(params: Dict[str, str]) -> Dict[str, Any]:
    required_keys = ["from", "to", "departureDate"]
    missing = [k for k in required_keys if not params.get(k)]
    if missing:
        return {"error": f"Missing required parameter(s): {', '.join(missing)}"}

    try:
        token = get_amadeus_access_token()
        origin = get_iata_code(params["from"], token)
        destination = get_iata_code(params["to"], token)
        adults = int(params.get("adults", "1") or 1)
        is_one_way = not params.get("returnDate")
        
        # Fixed max_results to exactly 5, no user input
        max_results = 5

        body = {
            "currencyCode": "USD",
            "originDestinations": [
                {
                    "id": "1",
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDateTimeRange": {
                        "date": params["departureDate"]
                    }
                }
            ],
            "travelers": [{"id": str(i), "travelerType": "ADULT"} for i in range(1, adults + 1)],
            "sources": ["GDS"],
            "searchCriteria": {
                "maxFlightOffers": max_results,
                "flightFilters": {
                    "cabinRestrictions": [
                        {
                            "cabin": "ECONOMY",
                            "coverage": "MOST_SEGMENTS",
                            "originDestinationIds": ["1"]
                        }
                    ]
                }
            }
        }

        if not is_one_way:
            body["originDestinations"].append({
                "id": "2",
                "originLocationCode": destination,
                "destinationLocationCode": origin,
                "departureDateTimeRange": {
                    "date": params["returnDate"]
                }
            })
            body["searchCriteria"]["flightFilters"]["cabinRestrictions"][0]["originDestinationIds"].append("2")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        wait = rate_limiter.wait_time()
        if wait > 0:
            logger.info(f"⏳ Waiting {wait:.2f}s before search")
            time.sleep(wait)

        rate_limiter.record_call()
        response = httpx.post(
            "https://test.api.amadeus.com/v2/shopping/flight-offers",
            headers=headers,
            json=body,
            timeout=60
        )

        if response.status_code == 429:
            rate_limiter.record_429()
            return {"error": "Rate limit exceeded. Please try again shortly."}

        response.raise_for_status()
        return {"flight": response.json()}

    except Exception as e:
        return {"error": f"Flight search failed: {str(e)}"}