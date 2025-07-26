import os
import logging
from functools import lru_cache
from pydantic_settings import BaseSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Settings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "Flight Data Service"
    
    # API Keys
    RAPID_API_KEY: str = os.getenv("RAPID_API_KEY", "")
    
    # AWS Configuration
    AWS_ACCESS_KEY: str = os.getenv("AWS_ACCESS_KEY", "")
    AWS_SECRET_KEY: str = os.getenv("AWS_SECRET_KEY", "")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "finalprojectdamg")
    
    # Airflow Configuration
    AIRFLOW_API_URL: str = os.getenv("AIRFLOW_API_URL", "http://159.89.95.178:8080/api/v1/dags/load_to_snowflake/dagRuns")
    AIRFLOW_USERNAME: str = os.getenv("AIRFLOW_USERNAME", "airflow")
    AIRFLOW_PASSWORD: str = os.getenv("AIRFLOW_PASSWORD", "airflow")
    
    # API Endpoints - SkyScanner
    SKYSCANNER_API_HOST: str = "sky-scanner3.p.rapidapi.com"
    SKYSCANNER_SEARCH_URL: str = "https://sky-scanner3.p.rapidapi.com/flights/search-one-way"
    SKYSCANNER_INCOMPLETE_URL: str = "https://sky-scanner3.p.rapidapi.com/flights/search-incomplete"
    
    # SkyScanner default search parameters
    DEFAULT_MARKET: str = "US"
    DEFAULT_LOCALE: str = "en-US"
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_ADULTS: int = 1
    DEFAULT_CABIN_CLASS: str = "economy"
    
    # Polling configuration for incomplete searches
    MAX_POLLING_ATTEMPTS: int = 10
    POLLING_DELAY_SECONDS: float = 1.0

    # Add this field
    rapid_api_host: str = 'sky-scanner3.p.rapidapi.com'

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    """
    Return cached settings
    """
    return Settings()