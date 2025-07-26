from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class FlightRequest(BaseModel):
    """Flight search request schema"""
    source: str = Field(..., description="Source airport code, e.g., 'PARI'")
    destination: str = Field(..., description="Destination airport code, e.g., 'BOS'")
    date: str = Field(..., description="Flight date in YYYY-MM-DD format")
    
    @validator('date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
            
    @validator('source', 'destination')
    def convert_to_uppercase(cls, v):
        return v.upper() if v else v
        
class Flight(BaseModel):
    """Individual flight schema"""
    flight_id: str
    price_raw: float
    price_formatted: str
    origin_id: str
    destination_id: str
    departure_time: str
    arrival_time: str
    airline_name: str
    flight_number: str
    load_date: str
    duration: str

class S3ObjectInfo(BaseModel):
    """Information about an object stored in S3"""
    bucket: str
    key: str
    url: str

class AirflowTriggerRequest(BaseModel):
    """Request to trigger Airflow DAG"""
    conf: Dict[str, Any]

class AirflowTriggerResponse(BaseModel):
    """Response from Airflow DAG trigger"""
    dag_run_id: Optional[str] = None
    status: str
    message: str

class FlightResponse(BaseModel):
    """Response with flight data information"""
    status: str
    daily_data_url: str
    monthly_data_url: str
    airflow_dag_run: Dict[str, Any]
    flights: Optional[List[Flight]] = []