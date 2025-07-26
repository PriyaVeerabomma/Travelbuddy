from fastapi import FastAPI
from app.api.routes import flight_routes
from app.config.settings import get_settings

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    settings = get_settings()
    
    application = FastAPI(
        title=settings.APP_NAME,
        description="Flight Data API Service",
        version="1.0.0"
    )
    
    # Include routers
    application.include_router(flight_routes.router)
    
    return application

app = create_application()

@app.get("/")
def health_check():
    """Root endpoint for health checks"""
    return {"status": "healthy", "message": "Flight Data Service API is running"}