from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from datetime import datetime, timedelta
import json
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
import boto3
import os

def download_from_s3(bucket_name, s3_key, local_path):
    """
    Download a file from AWS S3 to a local path
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Download the file
        s3_client.download_file(bucket_name, s3_key, local_path)
        print(f"Successfully downloaded {s3_key} from {bucket_name} to {local_path}")
        return local_path
    except Exception as e:
        print(f"Error downloading file from S3: {e}")
        raise

def download_hotel_data(**context):
    """
    Download hotel data from S3 bucket specified in DAG configuration
    """
    # Get S3 path from DAG configuration
    hotel_s3_bucket = context['dag_run'].conf.get('hotel_s3_bucket', 'default-bucket')
    hotel_s3_key = context['dag_run'].conf.get('hotel_s3_key', 'hotelsdata.json')
    
    # Local path to save the downloaded file
    local_path = f'/tmp/{hotel_s3_key}'
    
    # Download the file
    download_path = download_from_s3(hotel_s3_bucket, hotel_s3_key, local_path)
    
    # Return the local path for use in subsequent tasks
    return download_path

def process_hotel_data(**context):
    """
    Process the hotel JSON data from the downloaded file
    """
    # Get the local path of the downloaded file
    json_file_path = context['task_instance'].xcom_pull(task_ids='download_hotel_data')
    
    try:
        # Read and parse the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Determine the data structure
        if isinstance(data, dict) and "data" in data:
            hotels_list = data.get("data", [])
        elif isinstance(data, list):
            hotels_list = data
        else:
            print(f"Unexpected JSON structure: {type(data)}")
            hotels_list = []
            
        print(f"Processing {len(hotels_list)} hotel entries")
        
        # Process the data into a list of dictionaries
        processed_data = []
        for hotel in hotels_list:
            if not isinstance(hotel, dict):
                continue
                
            hotel_data = {
                "chain_code": hotel.get("chainCode"),
                "iata_code": hotel.get("iataCode"),
                "dupe_id": hotel.get("dupeId"),
                "name": hotel.get("name"),
                "hotel_id": hotel.get("hotelId"),
                "latitude": hotel.get("geoCode", {}).get("latitude"),
                "longitude": hotel.get("geoCode", {}).get("longitude"),
                "country_code": hotel.get("address", {}).get("countryCode"),
                "distance_value": hotel.get("distance", {}).get("value"),
                "distance_unit": hotel.get("distance", {}).get("unit"),
                "last_update": hotel.get("lastUpdate"),
                "is_sponsored": hotel.get("retailing", {}).get("sponsorship", {}).get("isSponsored", False)
            }
            processed_data.append(hotel_data)
        
        print(f"Successfully processed {len(processed_data)} hotel entries")
        return json.dumps(processed_data)
        
    except Exception as e:
        print(f"Error processing hotel data: {e}")
        return json.dumps([])

def load_hotels_to_snowflake(**context):
    """
    Load processed hotel data into Snowflake using SnowflakeHook
    """
    json_str = context['task_instance'].xcom_pull(task_ids='process_hotel_json')
    if not json_str:
        print("No hotel data to load")
        return
    
    # Parse the JSON string back to Python object
    hotels_data = json.loads(json_str)
    
    # Get Snowflake connection
    hook = SnowflakeHook(snowflake_conn_id='snowflake_conn')
    
    # Set up connection parameters
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    try:
        # Use warehouse, database and schema
        cursor.execute("USE WAREHOUSE COMPUTE_WH")
        cursor.execute("USE DATABASE HOTEL_PROJECT")
        cursor.execute("USE SCHEMA PUBLIC")
        
        # Prepare batches for insertion (to avoid too large SQL statements)
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(hotels_data), batch_size):
            batch = hotels_data[i:i+batch_size]
            
            # Prepare the insert statement
            insert_stmt = """
            INSERT INTO hotels (
                chain_code, iata_code, dupe_id, name, hotel_id, latitude, longitude,
                country_code, distance_value, distance_unit, last_update, is_sponsored
            ) VALUES 
            """
            
            values = []
            for hotel in batch:
                # Format each value properly, handling null values
                chain_code = f"'{hotel['chain_code']}'" if hotel['chain_code'] is not None else 'NULL'
                iata_code = f"'{hotel['iata_code']}'" if hotel['iata_code'] is not None else 'NULL'
                dupe_id = f"{hotel['dupe_id']}" if hotel['dupe_id'] is not None else 'NULL'
                name = f"'{hotel['name'].replace("'", "''")}'" if hotel['name'] is not None else 'NULL'
                hotel_id = f"'{hotel['hotel_id']}'" if hotel['hotel_id'] is not None else 'NULL'
                latitude = f"{hotel['latitude']}" if hotel['latitude'] is not None else 'NULL'
                longitude = f"{hotel['longitude']}" if hotel['longitude'] is not None else 'NULL'
                country_code = f"'{hotel['country_code']}'" if hotel['country_code'] is not None else 'NULL'
                distance_value = f"{hotel['distance_value']}" if hotel['distance_value'] is not None else 'NULL'
                distance_unit = f"'{hotel['distance_unit']}'" if hotel['distance_unit'] is not None else 'NULL'
                last_update = f"'{hotel['last_update']}'" if hotel['last_update'] is not None else 'NULL'
                is_sponsored = f"{'TRUE' if hotel['is_sponsored'] else 'FALSE'}" if hotel['is_sponsored'] is not None else 'NULL'
                
                row = f"({chain_code}, {iata_code}, {dupe_id}, {name}, {hotel_id}, {latitude}, {longitude}, {country_code}, {distance_value}, {distance_unit}, TO_TIMESTAMP_NTZ({last_update}), {is_sponsored})"
                values.append(row)
            
            # Complete the SQL statement with all values
            insert_stmt += ",\n".join(values)
            
            # Execute the batch insert
            cursor.execute(insert_stmt)
            total_inserted += len(batch)
            print(f"Inserted batch of {len(batch)} hotels. Total inserted: {total_inserted}")
        
        print(f"Successfully inserted {total_inserted} hotels into Snowflake")
        
    except Exception as e:
        print(f"Error loading hotels to Snowflake: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

hotelDag = DAG(
    'load_hotel',
    default_args=default_args,
    description='Load hotel data to Snowflake',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 4, 1),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=60),
    default_view='graph',
    tags=['hotel', 'snowflake', 'etl'],
) 

# Create database in Snowflake
init_database = SnowflakeOperator(
    task_id='init_database',
    snowflake_conn_id='snowflake_conn',
    sql="""
    USE ROLE ACCOUNTADMIN;
    USE WAREHOUSE COMPUTE_WH;
    CREATE DATABASE IF NOT EXISTS HOTEL_PROJECT;
    USE DATABASE HOTEL_PROJECT;
    CREATE SCHEMA IF NOT EXISTS PUBLIC;
    USE SCHEMA PUBLIC;
    """,
    dag=hotelDag
)

# Create hotels table
create_hotels_table = SnowflakeOperator(
    task_id='create_hotels_table',
    snowflake_conn_id='snowflake_conn',
    sql="""
    USE WAREHOUSE COMPUTE_WH;
    USE DATABASE HOTEL_PROJECT;
    USE SCHEMA PUBLIC;
    
    -- Create the main table
    CREATE TABLE IF NOT EXISTS hotels (
        chain_code VARCHAR,
        iata_code VARCHAR,
        dupe_id NUMBER,
        name VARCHAR,
        hotel_id VARCHAR,
        latitude FLOAT,
        longitude FLOAT,
        country_code VARCHAR,
        distance_value FLOAT,
        distance_unit VARCHAR,
        last_update TIMESTAMP_NTZ,
        is_sponsored BOOLEAN,
        load_date TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    dag=hotelDag
)

# Download data from S3
download_hotel_data = PythonOperator(
    task_id='download_hotel_data',
    python_callable=download_hotel_data,
    provide_context=True,
    dag=hotelDag
)

# Process hotel data
process_hotel_json = PythonOperator(
    task_id='process_hotel_json',
    python_callable=process_hotel_data,
    provide_context=True,
    dag=hotelDag
)

# Load hotel data to Snowflake with custom Python function
load_hotel_data = PythonOperator(
    task_id='load_hotel_data',
    python_callable=load_hotels_to_snowflake,
    provide_context=True,
    dag=hotelDag,
    retries=2,  # Add more retries for this task
    retry_delay=timedelta(minutes=1)  # Shorter retry delay for faster testing
)

# Add a task to log completion
completion_log = BashOperator(
    task_id='completion_log',
    bash_command='echo "Hotel data pipeline completed successfully"',
    dag=hotelDag,
    trigger_rule='none_failed'
)

# Set task dependencies
init_database >> create_hotels_table >> download_hotel_data >> process_hotel_json >> load_hotel_data >> completion_log

# This exposes the DAG
hotelDag