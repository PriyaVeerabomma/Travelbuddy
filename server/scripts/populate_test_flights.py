"""
Script to populate the Snowflake DAILY_FLIGHTS table with sample data.
This ensures there's test data available for the application.
"""

import os
import sys
import uuid
import random
import datetime
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airport codes
AIRPORTS = [
    "BOS", "JFK", "LAX", "SFO", "ORD", "DFW", "MIA", "ATL", "LAS", "SEA",
    "DEN", "IAD", "HOU", "PHX", "CLT", "PHL", "DCA", "HYD", "DEL", "BOM",
    "MAA", "BLR", "CCU", "LON", "PAR", "FRA", "AMS", "MAD", "ROM", "BCN"
]

# Airlines
AIRLINES = [
    "Delta Air Lines", "American Airlines", "United Airlines", "Southwest Airlines",
    "JetBlue Airways", "Alaska Airlines", "British Airways", "Air France",
    "Lufthansa", "Emirates", "Singapore Airlines", "Air India", "IndiGo"
]

def generate_flight_number(airline_name):
    """Generate a realistic flight number based on airline name."""
    prefix = ''.join([word[0] for word in airline_name.split()[:2]]).upper()
    number = random.randint(1000, 9999)
    return f"{prefix}{number}"

def format_price(price):
    """Format price as currency string."""
    return f"${price:.2f}"

def generate_sample_flights(count=100):
    """Generate sample flight data."""
    flights = []
    
    # Base date is today
    base_date = datetime.datetime.now().date()
    
    # Generate flights for the next 30 days
    for day in range(0, 30):
        flight_date = base_date + datetime.timedelta(days=day)
        
        # Generate flights for different origin-destination pairs
        for _ in range(count // 30):  # Distribute flights across days
            # Select random airports for origin and destination
            origin = random.choice(AIRPORTS)
            destination = random.choice([a for a in AIRPORTS if a != origin])
            
            # Random departure time between 5 AM and 10 PM
            departure_hour = random.randint(5, 22)
            departure_minute = random.choice([0, 15, 30, 45])
            departure_time = datetime.datetime.combine(
                flight_date, 
                datetime.time(departure_hour, departure_minute)
            )
            
            # Flight duration between 1 and 12 hours
            duration_hours = random.randint(1, 12)
            duration_minutes = random.choice([0, 15, 30, 45])
            duration = datetime.timedelta(hours=duration_hours, minutes=duration_minutes)
            
            # Calculate arrival time
            arrival_time = departure_time + duration
            
            # Price between $100 and $2000
            price_raw = round(random.uniform(100, 2000), 2)
            price_formatted = format_price(price_raw)
            
            # Select airline
            airline_name = random.choice(AIRLINES)
            flight_number = generate_flight_number(airline_name)
            
            # Generate unique flight ID
            flight_id = str(uuid.uuid4())[:16]
            
            # Current timestamp for load_date
            load_date = datetime.datetime.now()
            
            flights.append({
                "flight_id": flight_id,
                "price_raw": price_raw,
                "price_formatted": price_formatted,
                "origin_id": origin,
                "destination_id": destination,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "airline_name": airline_name,
                "flight_number": flight_number,
                "load_date": load_date
            })
    
    return flights

def insert_flights_to_snowflake(flights):
    """Insert flight data into Snowflake."""
    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )
        
        # Create cursor
        cur = conn.cursor()
        
        # Insert data
        insert_query = """
        INSERT INTO FINAL_PROJECT.PUBLIC.DAILY_FLIGHTS (
            FLIGHT_ID, PRICE_RAW, PRICE_FORMATTED, ORIGIN_ID, DESTINATION_ID,
            DEPARTURE_TIME, ARRIVAL_TIME, AIRLINE_NAME, FLIGHT_NUMBER, LOAD_DATE
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # First check if table already has data
        cur.execute("SELECT COUNT(*) FROM FINAL_PROJECT.PUBLIC.DAILY_FLIGHTS")
        count = cur.fetchone()[0]
        
        if count > 0:
            print(f"Table already has {count} rows. Do you want to add more test data? (y/n)")
            response = input().lower()
            if response != 'y':
                print("Operation cancelled.")
                return
        
        # Insert each flight
        for flight in flights:
            cur.execute(
                insert_query,
                (
                    flight["flight_id"],
                    flight["price_raw"],
                    flight["price_formatted"],
                    flight["origin_id"],
                    flight["destination_id"],
                    flight["departure_time"],
                    flight["arrival_time"],
                    flight["airline_name"],
                    flight["flight_number"],
                    flight["load_date"]
                )
            )
        
        # Commit the transaction
        conn.commit()
        
        print(f"Successfully inserted {len(flights)} flights into Snowflake.")
        
    except Exception as e:
        print(f"Error inserting data into Snowflake: {str(e)}")
        sys.exit(1)
    
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Generating sample flight data...")
    num_flights = int(input("Enter the number of sample flights to generate (default: 100): ") or 100)
    flights = generate_sample_flights(num_flights)
    print(f"Generated {len(flights)} sample flights.")
    
    print("Inserting data into Snowflake...")
    insert_flights_to_snowflake(flights)
