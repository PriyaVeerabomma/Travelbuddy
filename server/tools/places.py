# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LangGraph tool wrapper to Google Maps Places API."""

import os
import requests
from typing import Dict, List, Any
from langchain_core.tools import tool


class PlacesService:
    """Wrapper to Places API."""

    def _check_key(self):
        if (
            not hasattr(self, "places_api_key") or not self.places_api_key
        ):
            self.places_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    def find_place_from_text(self, query: str) -> Dict[str, str]:
        """Fetches place details using a text query."""
        self._check_key()
        
        # Log the API key status (without revealing the key)
        if not self.places_api_key:
            print("WARNING: Google Places API key is not set!")
        else:
            print(f"Using Google Places API key: {self.places_api_key[:4]}...{self.places_api_key[-4:]}")
        
        # Use the more appropriate "textsearch" endpoint for category searches
        places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "fields": "place_id,formatted_address,name,photos,geometry",
            "key": self.places_api_key,
        }

        try:
            print(f"Making Places API request with query: '{query}'")
            response = requests.get(places_url, params=params)
            status_code = response.status_code
            print(f"Places API response status: {status_code}")
            
            response.raise_for_status()
            place_data = response.json()
            
            # Log the response status from the Places API
            api_status = place_data.get("status", "UNKNOWN")
            print(f"Places API status: {api_status}")
            
            if api_status != "OK":
                error_message = place_data.get("error_message", "Unknown error")
                print(f"Places API error: {error_message}")
                return {"error": f"API error: {api_status} - {error_message}"}

            if not place_data.get("results"):
                print(f"No places found for query: '{query}'")
                return {"error": "No places found."}

            place_details = place_data["results"][0]
            place_id = place_details["place_id"]
            place_name = place_details["name"]
            place_address = place_details["formatted_address"]
            photos = self.get_photo_urls(place_details.get("photos", []), maxwidth=400)
            map_url = self.get_map_url(place_id)
            location = place_details["geometry"]["location"]
            lat = str(location["lat"])
            lng = str(location["lng"])

            print(f"Found place: {place_name} at {place_address}")
            return {
                "place_id": place_id,
                "place_name": place_name,
                "place_address": place_address,
                "photos": photos,
                "map_url": map_url,
                "lat": lat,
                "lng": lng,
            }

        except requests.exceptions.RequestException as e:
            print(f"Request exception: {e}")
            return {"error": f"Error fetching place data: {e}"}
    def get_photo_urls(self, photos: List[Dict[str, Any]], maxwidth: int = 400) -> List[str]:
        """Extracts photo URLs from the 'photos' list."""
        photo_urls = []
        for photo in photos:
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={maxwidth}&photoreference={photo['photo_reference']}&key={self.places_api_key}"
            photo_urls.append(photo_url)
        return photo_urls

    def get_map_url(self, place_id: str) -> str:
        """Generates the Google Maps URL for a given place ID."""
        return f"https://www.google.com/maps/place/?q=place_id:{place_id}"


places_service = PlacesService()


@tool
def map_tool(state: Dict[str, Any], key: str) -> Dict[str, Any]:
    """
    Enriches POIs in state[key]['places'] with Google Maps geolocation data.

    Args:
        state: The LangGraph state object.
        key: The state key under which POIs are stored.

    Returns:
        Updated state with populated place_id, lat, lng, and map_url.
    """
    if key not in state:
        state[key] = {}

    if "places" not in state[key]:
        state[key]["places"] = []

    pois = state[key]["places"]
    for poi in pois:
        location = poi["place_name"] + ", " + poi["address"]
        result = places_service.find_place_from_text(location)
        poi["place_id"] = result.get("place_id")
        poi["map_url"] = result.get("map_url")
        if "lat" in result and "lng" in result:
            poi["lat"] = result["lat"]
            poi["long"] = result["lng"]

    return {key: {"places": pois}}
