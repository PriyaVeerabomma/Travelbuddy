# google_restaurant_api.py

import os
import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("google_restaurant_api")
logging.basicConfig(level=logging.INFO)

GOOGLE_PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"

def perform_google_restaurant_search(location: str, api_key: str) -> Dict[str, Any]:
    params = {
        "query": f"best restaurants in {location}",
        "type": "restaurant",
        "key": api_key
    }

    try:
        logger.info(f"🍽️ Searching restaurants in: {location}")
        response = httpx.get(GOOGLE_PLACES_SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        results = response.json().get("results", [])[:10]

        restaurants = []
        for place in results:
            name = place.get("name")
            address = place.get("formatted_address")
            rating = place.get("rating", 0.0)
            total_ratings = place.get("user_ratings_total", 0)
            types = place.get("types", [])
            location_data = place.get("geometry", {}).get("location", {})

            # Construct photo URL
            photo_url = None
            if photos := place.get("photos"):
                photo_ref = photos[0].get("photo_reference")
                photo_url = f"{GOOGLE_PHOTO_URL}?maxwidth=400&photoreference={photo_ref}&key={api_key}"

            restaurants.append({
                "name": name,
                "address": address,
                "rating": rating,
                "total_ratings": total_ratings,
                "photo_url": photo_url,
                "location": location_data,
                "types": types
            })

        return {
            "location": location,
            "restaurants": restaurants
        }

    except Exception as e:
        logger.error(f"❌ Failed to fetch restaurants for {location}: {e}")
        return {"error": f"Failed to fetch restaurants for {location}: {str(e)}"}
