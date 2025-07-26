from fastapi import APIRouter, HTTPException, Query
import httpx
import os
from dotenv import load_dotenv
import logging
import traceback
import json

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Google Maps API Key from environment
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

@router.get("/geocode")
async def geocode_address(
    address: str = Query(..., description="The address to geocode"),
    key: str = Query(None, description="Optional API key to override the default")
):
    """
    Proxy endpoint for Google Maps Geocoding API
    This avoids CORS issues when making requests from the frontend
    """
    try:
        # Log the request for debugging
        logger.info(f"Geocoding request received for address: {address}")
        
        # Use provided key or fall back to environment variable
        api_key = key or GOOGLE_MAPS_API_KEY
        
        # Log if we're using the provided key or environment key
        if key:
            logger.info("Using provided API key")
        else:
            logger.info(f"Using environment API key: {GOOGLE_MAPS_API_KEY[:4]}...{GOOGLE_MAPS_API_KEY[-4:] if GOOGLE_MAPS_API_KEY else 'None'}")
        
        if not api_key:
            logger.error("API key is missing. Check your .env file.")
            raise HTTPException(status_code=400, detail="API key is required. Check your .env file configuration.")
        
        # Make request to Google Maps API
        logger.info("Making request to Google Maps API")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": address,
                    "key": api_key
                }
            )
            
            # Check if request was successful
            if response.status_code != 200:
                logger.error(f"Google Maps API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Google Maps API request failed: {response.text}"
                )
            
            # Parse the response
            result = response.json()
            logger.info(f"Google Maps API response status: {result.get('status')}")
            
            # Check for API-level errors even with 200 status code
            if result.get('status') != 'OK':
                logger.error(f"Google Maps API returned non-OK status: {result.get('status')}")
                logger.error(f"Error message: {result.get('error_message', 'No specific error message')}")
                return {
                    "status": result.get('status'),
                    "error_message": result.get('error_message', 'Geocoding failed'),
                    "results": []
                }
            
            # Return the Google Maps API response
            logger.info(f"Successfully geocoded address: {address}")
            return result
            
    except httpx.RequestError as e:
        logger.error(f"Error making request to Google Maps API: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error making request to Google Maps API: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in geocode endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        # Return a fallback response for any error
        return {
            "status": "FALLBACK_ERROR",
            "error_message": f"Server error: {str(e)}",
            "results": [{
                "formatted_address": f"{address} (Fallback)",
                "geometry": {
                    "location": {
                        "lat": 0,
                        "lng": 0
                    }
                },
                "place_id": "fallback_place_id",
                "is_fallback": True
            }]
        }