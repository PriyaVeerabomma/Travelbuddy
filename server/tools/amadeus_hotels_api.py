# amadeus_hotels_api.py

from typing import Dict, Any
import os, time, json, httpx, logging, datetime, re

logger = logging.getLogger("amadeus_hotels_api")
logging.basicConfig(level=logging.INFO)

CITY_CODE_CACHE = {}

class RateLimiter:
    def __init__(self, max_calls=10, time_frame=1):
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.call_timestamps = []
        self.last_429_time = None
        self.backoff_time = 5

    def wait_time(self):
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

def get_amadeus_access_token() -> str:
    wait = rate_limiter.wait_time()
    if wait > 0: time.sleep(wait)

    payload = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("AMADEUS_CLIENT_ID"),
        "client_secret": os.getenv("AMADEUS_CLIENT_SECRET")
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"

    try:
        rate_limiter.record_call()
        res = httpx.post(url, data=payload, headers=headers, timeout=30)
        if res.status_code == 429:
            rate_limiter.record_429()
            if hasattr(get_amadeus_access_token, "last_valid_token"):
                return get_amadeus_access_token.last_valid_token
            raise Exception("Rate limited and no fallback token.")
        res.raise_for_status()
        token = res.json()["access_token"]
        get_amadeus_access_token.last_valid_token = token
        return token
    except Exception as e:
        logger.error(f"❌ Token error: {e}")
        if hasattr(get_amadeus_access_token, "last_valid_token"):
            return get_amadeus_access_token.last_valid_token
        raise

def get_city_code(city: str, token: str) -> str:
    key = city.lower().strip()

    common_cities = {
        "new york": "NYC", "los angeles": "LAX", "chicago": "CHI", "london": "LON", "paris": "PAR",
        "tokyo": "TYO", "beijing": "BJS", "sydney": "SYD", "san francisco": "SFO", "washington": "WAS",
        "boston": "BOS", "miami": "MIA", "seattle": "SEA", "dallas": "DFW", "toronto": "YTO",
        "frankfurt": "FRA", "rome": "ROM", "madrid": "MAD", "berlin": "BER", "amsterdam": "AMS"
    }

    if key in CITY_CODE_CACHE:
        return CITY_CODE_CACHE[key]

    if key in common_cities:
        code = common_cities[key]
        CITY_CODE_CACHE[key] = code
        logger.info(f"🔍 Using hardcoded city code for {city}: {code}")
        return code

    wait = rate_limiter.wait_time()
    if wait > 0:
        time.sleep(wait)

    try:
        rate_limiter.record_call()
        res = httpx.get(
            "https://test.api.amadeus.com/v1/reference-data/locations",
            headers={"Authorization": f"Bearer {token}"},
            params={"keyword": city, "subType": "CITY"},
            timeout=30
        )
        if res.status_code == 429:
            rate_limiter.record_429()
            return city[:3].upper()
        res.raise_for_status()
        city_code = res.json()["data"][0]["iataCode"]
        CITY_CODE_CACHE[key] = city_code
        return city_code
    except Exception as e:
        logger.error(f"❌ Failed to fetch city code for {city}: {e}")
        return city[:3].upper()

def fix_date(date_str: str) -> str:
    try:
        if "-" in date_str: return date_str
        return datetime.datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
    except Exception:
        return datetime.datetime.now().strftime("%Y-%m-%d")

def perform_hotel_search_api(params: Dict[str, Any]) -> Dict[str, Any]:
    required = ["city", "checkInDate", "checkOutDate", "adults"]
    if missing := [k for k in required if not params.get(k)]:
        return {"error": f"Missing required params: {', '.join(missing)}"}

    token = get_amadeus_access_token()
    city_code = get_city_code(params["city"], token)
    checkin = fix_date(params["checkInDate"])
    checkout = fix_date(params["checkOutDate"])
    adults = int(params.get("adults", 1))

    url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
    query = {"cityCode": city_code}
    headers = {"Authorization": f"Bearer {token}"}

    wait = rate_limiter.wait_time()
    if wait > 0: time.sleep(wait)

    try:
        rate_limiter.record_call()
        res = httpx.get(url, headers=headers, params=query, timeout=60)
        if res.status_code == 429:
            rate_limiter.record_429()
            return {"error": "Rate limit exceeded. Please retry shortly."}
        res.raise_for_status()
        hotels = res.json()
        hotels["request"] = {
            "checkInDate": checkin,
            "checkOutDate": checkout,
            "adults": adults
        }
        return {"hotels": hotels}
    except Exception as e:
        logger.error(f"❌ Hotel search error: {e}")
        return {"error": f"Hotel search failed: {str(e)}"}
