from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.controllers.flight_controller import FlightController
from app.models.schemas import FlightResponse, FlightRequest
from app.config.settings import get_settings, Settings
import logging

router = APIRouter(prefix="/flights", tags=["flights"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# POST endpoint for flight data
@router.post("/", response_model=FlightResponse)
async def post_flight_data(
    request: FlightRequest = Body(...),  # Explicitly use Body parameter
    settings: Settings = Depends(get_settings)
):
    """Get flight data for a specific route and date (POST method)"""
    logger.info(f"Received POST request: {request}")
    try:
        # Initialize controller
        controller = FlightController(settings)
        
        # Process request - pass the request object directly
        response = await controller.process_flight_request(request)
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing flight data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing flight data: {str(e)}")

# GET endpoint for flight data (to match frontend requirements)
@router.get("/search", response_model=FlightResponse)
async def get_flight_data(
    origin_id: str = Query(..., description="Origin airport code"),
    destination_id: str = Query(..., description="Destination airport code"),
    departure_date: str = Query(..., description="Departure date in YYYY-MM-DD format"),
    settings: Settings = Depends(get_settings)
):
    """Get flight data for a specific route and date (GET method)"""
    logger.info(f"Received GET request - origin: {origin_id}, destination: {destination_id}, date: {departure_date}")
    try:
        # Convert parameters to FlightRequest object
        request = FlightRequest(
            source=origin_id.upper(),
            destination=destination_id.upper(),
            date=departure_date
        )
        
        # Initialize controller
        controller = FlightController(settings)
        
        # Process request
        response = await controller.process_flight_request(request)
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing flight data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing flight data: {str(e)}")


@router.post("/test", response_model=dict)
async def test_endpoint(request: FlightRequest = Body(...)):
    """Test endpoint to verify request body parsing"""
    return {"received": {"source": request.source, 
                        "destination": request.destination, 
                        "date": request.date}}