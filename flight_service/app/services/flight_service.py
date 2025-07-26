import httpx
import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.config.settings import Settings

class FlightService:
    """Service for fetching flight data from external APIs"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Default headers for SkyScanner API
        self.headers = {
            "X-RapidAPI-Key": settings.RAPID_API_KEY,
            "X-RapidAPI-Host": settings.SKYSCANNER_API_HOST
        }
        
        # Configure logger
        self.logger = logging.getLogger(__name__)
    
    async def fetch_flight_data(
        self, 
        source: str, 
        destination: str, 
        date: Optional[str] = None, 
        month: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch flight data from SkyScanner API using the search-one-way endpoint
        
        This function can be used for both:
        1. Daily data (when date is provided) - Example: departDate=2025-05-15
        2. Monthly data (when month is provided) - Example: wholeMonthDepart=2025-05
        
        Both use the same endpoint but with different parameters:
        - For daily: use departDate parameter
        - For monthly: use wholeMonthDepart parameter
        
        Example API call:
        curl --url 'https://sky-scanner3.p.rapidapi.com/flights/search-one-way?fromEntityId=PARI&toEntityId=BOS&departDate=2025-05-15&cabinClass=economy' 
        --header 'x-rapidapi-host: sky-scanner3.p.rapidapi.com' 
        --header 'x-rapidapi-key: YOUR_API_KEY'
        """
        # Log which type of request we're making
        if date:
            self.logger.info(f"Fetching daily flight data for {date} (source: {source}, destination: {destination})")
        elif month:
            self.logger.info(f"Fetching monthly flight data for {month} (source: {source}, destination: {destination})")
        
        # Both requests use the same endpoint: /flights/search-one-way
        url = self.settings.SKYSCANNER_SEARCH_URL
        
        # Base query parameters common to both request types
        querystring = {
            "fromEntityId": source,
            "toEntityId": destination,
            "market": self.settings.DEFAULT_MARKET,
            "locale": self.settings.DEFAULT_LOCALE,
            "currency": self.settings.DEFAULT_CURRENCY,
            "adults": str(self.settings.DEFAULT_ADULTS),
            "cabinClass": self.settings.DEFAULT_CABIN_CLASS
        }
        
        # Set either departDate (for daily) or wholeMonthDepart (for monthly)
        if date:
            querystring["departDate"] = date
            self.logger.debug(f"Using departDate={date} for daily request")
        elif month:
            querystring["wholeMonthDepart"] = month
            self.logger.debug(f"Using wholeMonthDepart={month} for monthly request")
        else:
            error_msg = "Either date or month must be provided"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Make the request to SkyScanner API
            async with httpx.AsyncClient() as client:
                self.logger.debug(f"Making request to {url} with params: {querystring}")
                response = await client.get(
                    url, 
                    headers=self.headers, 
                    params=querystring, 
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_msg = f"SkyScanner API error: {response.text}"
                    self.logger.error(error_msg)
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=error_msg
                    )
                
                self.logger.debug("Received response from SkyScanner API")
                data = response.json()
                
                # Check if we need to handle incomplete search
                # IMPORTANT: As per API documentation, we need to poll the search-incomplete
                # endpoint until the status changes from 'incomplete' to 'complete'
                status = data.get("data", {}).get("context", {}).get("status")
                
                if status == "incomplete":
                    search_id = data.get("data", {}).get("context", {}).get("searchId")
                    self.logger.info(f"Search status is incomplete, polling with searchId: {search_id}")
                    if search_id:
                        return await self.fetch_incomplete_search(search_id)
                
                self.logger.info("Search completed successfully")
                return data
                
        except httpx.TimeoutException:
            error_msg = "Timeout while connecting to SkyScanner API"
            self.logger.error(error_msg)
            raise HTTPException(status_code=504, detail=error_msg)
            
        except Exception as e:
            error_msg = f"Error fetching flight data: {str(e)}"
            self.logger.error(error_msg)
            raise

    async def fetch_incomplete_search(self, search_id: str) -> Dict[str, Any]:
        """
        Fetch the complete results for an incomplete search by polling
        the search-incomplete endpoint until the status is 'complete'
        
        As per SkyScanner API documentation:
        In case the status is 'incomplete', you need to use the /flights/search-incomplete 
        endpoint to get the full data until the status is 'complete'
        """
        url = self.settings.SKYSCANNER_INCOMPLETE_URL
        
        querystring = {"searchId": search_id}
        
        self.logger.info(f"Beginning poll for complete results with searchId: {search_id}")
        
        try:
            async with httpx.AsyncClient() as client:
                max_attempts = self.settings.MAX_POLLING_ATTEMPTS
                attempt = 0
                
                while attempt < max_attempts:
                    attempt += 1
                    self.logger.debug(f"Poll attempt {attempt}/{max_attempts}")
                    
                    response = await client.get(
                        url, 
                        headers=self.headers, 
                        params=querystring, 
                        timeout=30.0
                    )
                    
                    if response.status_code != 200:
                        error_msg = f"SkyScanner API error for incomplete search: {response.text}"
                        self.logger.error(error_msg)
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=error_msg
                        )
                    
                    data = response.json()
                    status = data.get("data", {}).get("context", {}).get("status")
                    
                    if status == "complete":
                        self.logger.info(f"Search completed successfully after {attempt} attempts")
                        return data
                    
                    # If still incomplete, wait briefly before polling again
                    # This is to respect API rate limits and give time for the search to complete
                    import asyncio
                    self.logger.debug(f"Search still incomplete, waiting {self.settings.POLLING_DELAY_SECONDS}s before next poll")
                    await asyncio.sleep(self.settings.POLLING_DELAY_SECONDS)
                
                # If we've exhausted our attempts but the search is still not complete,
                # return the most recent data with a warning
                self.logger.warning(f"Search ID {search_id} did not complete after {max_attempts} attempts. Returning partial results.")
                return data
                
        except httpx.TimeoutException:
            error_msg = "Timeout while polling for complete search results"
            self.logger.error(error_msg)
            raise HTTPException(status_code=504, detail=error_msg)
            
        except Exception as e:
            error_msg = f"Error polling for complete search results: {str(e)}"
            self.logger.error(error_msg)
            raise
            
    # Placeholder for Amadeus API integration
    async def fetch_amadeus_data(self, source: str, destination: str, date: str) -> Dict[str, Any]:
        """
        Placeholder for future Amadeus API integration
        This will be implemented later as per requirements
        """
        # This is just a placeholder, actual implementation will be added later
        return {
            "status": "placeholder",
            "message": "Amadeus API integration to be implemented"
        }