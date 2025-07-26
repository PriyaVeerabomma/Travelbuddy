from fastapi import APIRouter, Depends, HTTPException
import snowflake.connector
import os
from typing import List
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from fastapi import Query

router = APIRouter()

# Pydantic model for flight response with duration
class FlightResponse(BaseModel):
    flight_id: str
    price_raw: float
    price_formatted: str
    origin_id: str
    destination_id: str
    departure_time: datetime
    arrival_time: datetime
    airline_name: str
    flight_number: str
    load_date: datetime
    duration: str  # e.g., "20h 40m"

# Pydantic model for analysis response
class FlightAnalysis(BaseModel):
    cheapest_flight: FlightResponse
    average_price: float
    fastest_flight: FlightResponse
    price_range: dict[str, float]
    airline_count: int

# Dependency to get Snowflake connection
def get_snowflake_conn():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )
    try:
        yield conn
    finally:
        conn.close()

# Test endpoint to fetch flights
@router.get("/test", response_model=List[FlightResponse])
async def test_fetch_flights(conn: snowflake.connector.SnowflakeConnection = Depends(get_snowflake_conn)):
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM FINAL_PROJECT.PUBLIC.DAILY_FLIGHTS LIMIT 10")
        rows = cur.fetchall()
        columns = [desc[0].lower() for desc in cur.description]
        flights = [dict(zip(columns, row)) for row in rows]
        # Calculate duration
        for flight in flights:
            departure = flight['departure_time']
            arrival = flight['arrival_time']
            duration = arrival - departure
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes = remainder // 60
            flight['duration'] = f"{int(hours)}h {int(minutes)}m"
        return flights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching flights: {str(e)}")
    finally:
        cur.close()

# Search flights by origin, destination, and date
@router.get("/search", response_model=List[FlightResponse])
async def search_flights(
    origin_id: str = Query(..., description="Origin airport code (e.g., HYD)"),
    destination_id: str = Query(..., description="Destination airport code (e.g., MIA)"),
    departure_date: date = Query(..., description="Departure date (YYYY-MM-DD)"),
    conn: snowflake.connector.SnowflakeConnection = Depends(get_snowflake_conn)
):
    try:
        # Log the incoming request
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Searching flights from {origin_id} to {destination_id} on {departure_date}")
        
        # Prepare the query - being explicit about columns and using proper parameters
        query = """
            SELECT 
                FLIGHT_ID as flight_id,
                PRICE_RAW as price_raw,
                PRICE_FORMATTED as price_formatted,
                ORIGIN_ID as origin_id,
                DESTINATION_ID as destination_id,
                DEPARTURE_TIME as departure_time,
                ARRIVAL_TIME as arrival_time,
                AIRLINE_NAME as airline_name, 
                FLIGHT_NUMBER as flight_number,
                LOAD_DATE as load_date,
                DATEDIFF('minute', DEPARTURE_TIME, ARRIVAL_TIME) as duration_minutes
            FROM FINAL_PROJECT.PUBLIC.DAILY_FLIGHTS
            WHERE UPPER(ORIGIN_ID) = UPPER(%s)
            AND UPPER(DESTINATION_ID) = UPPER(%s)
            AND DATE(DEPARTURE_TIME) = %s
        """
        
        # Execute the query with parameters
        cur = conn.cursor()
        cur.execute(query, (origin_id.upper(), destination_id.upper(), departure_date))
        
        # Fetch the results
        rows = cur.fetchall()
        logger.info(f"Query returned {len(rows)} results")
        
        if not rows:
            # If no flights found in the database, return an empty list instead of 404
            logger.warning(f"No flights found from {origin_id} to {destination_id} on {departure_date}")
            return []
            
        # Get column names from cursor description
        columns = [desc[0].lower() for desc in cur.description]
        logger.debug(f"Columns: {columns}")
        
        # Create a list of flight dictionaries
        flights = []
        for row in rows:
            flight_dict = dict(zip(columns, row))
            
            # Calculate duration string from duration_minutes
            if 'duration_minutes' in flight_dict:
                minutes = flight_dict.pop('duration_minutes')  # Remove this field after using it
                if minutes is not None:
                    hours, mins = divmod(int(minutes), 60)
                    flight_dict['duration'] = f"{hours}h {mins}m"
                else:
                    flight_dict['duration'] = "Unknown"  # Fallback
            else:
                # Fallback calculation if duration_minutes field is missing
                departure = flight_dict.get('departure_time')
                arrival = flight_dict.get('arrival_time')
                if departure and arrival:
                    delta = arrival - departure
                    total_minutes = int(delta.total_seconds() / 60)
                    hours, mins = divmod(total_minutes, 60)
                    flight_dict['duration'] = f"{hours}h {mins}m"
                else:
                    flight_dict['duration'] = "Unknown"
            
            # Ensure price formatting is consistent
            if 'price_raw' in flight_dict and 'price_formatted' in flight_dict:
                price_raw = flight_dict['price_raw']
                # Only update price_formatted if it doesn't already start with $
                if not str(flight_dict['price_formatted']).startswith('$'):
                    flight_dict['price_formatted'] = f"${price_raw:.2f}"
            
            flights.append(flight_dict)
            
        logger.info(f"Processed {len(flights)} flights from {origin_id} to {destination_id} on {departure_date}")
        return flights
    
    except Exception as e:
        import traceback
        logger.error(f"Error fetching flights: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching flights: {str(e)}")
    
    finally:
        if 'cur' in locals():
            cur.close()

# Analyze flights
@router.get("/analysis", response_model=FlightAnalysis)
async def analyze_flights(
    origin_id: str = Query(..., description="Origin airport code"),
    destination_id: str = Query(..., description="Destination airport code"),
    departure_date: date = Query(..., description="Departure date (YYYY-MM-DD)"),
    conn: snowflake.connector.SnowflakeConnection = Depends(get_snowflake_conn)
):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM FINAL_PROJECT.PUBLIC.DAILY_FLIGHTS
            WHERE origin_id = %s
            AND destination_id = %s
            AND DATE(departure_time) = %s
        """, (origin_id.upper(), destination_id.upper(), departure_date))
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No flights found")
        columns = [desc[0].lower() for desc in cur.description]
        flights = [dict(zip(columns, row)) for row in rows]

        # Calculate duration for each flight
        for flight in flights:
            departure = flight['departure_time']
            arrival = flight['arrival_time']
            duration = arrival - departure
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes = remainder // 60
            flight['duration'] = f"{int(hours)}h {int(minutes)}m"

        # Analysis
        cheapest_flight = min(flights, key=lambda x: x['price_raw'])
        fastest_flight = min(flights, key=lambda x: (x['arrival_time'] - x['departure_time']).total_seconds())
        average_price = sum(flight['price_raw'] for flight in flights) / len(flights)
        price_range = {
            "min": min(flight['price_raw'] for flight in flights),
            "max": max(flight['price_raw'] for flight in flights)
        }
        airline_count = len(set(flight['airline_name'] for flight in flights))

        return {
            "cheapest_flight": cheapest_flight,
            "average_price": average_price,
            "fastest_flight": fastest_flight,
            "price_range": price_range,
            "airline_count": airline_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing flights: {str(e)}")
    finally:
        cur.close()