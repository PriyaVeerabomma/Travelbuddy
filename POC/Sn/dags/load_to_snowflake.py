from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import json
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Function to download file from S3
def download_from_s3(bucket, key, local_path):

    def check_credentials(**context):
        """Verify environment variables are loaded"""
        print(f"AWS_ACCESS_KEY_ID exists: {bool(os.environ.get('AWS_ACCESS_KEY_ID'))}")
        print(f"AWS_SECRET_ACCESS_KEY exists: {bool(os.environ.get('AWS_SECRET_ACCESS_KEY'))}")
        
        # First few characters of each (don't print full credentials)
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            print(f"AWS_ACCESS_KEY_ID starts with: {os.environ.get('AWS_ACCESS_KEY_ID')[:4]}...")
        if os.environ.get('AWS_SECRET_ACCESS_KEY'):
            print(f"AWS_SECRET_ACCESS_KEY starts with: {os.environ.get('AWS_SECRET_ACCESS_KEY')[:4]}...")
        
        return True
    """
    Download a file from S3 to a local path
    """
    x=check_credentials()
    session = boto3.Session(
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name='us-east-2'  # match your bucket region
    )
    s3_client = session.client('s3')  # Add the correct region
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3_client.download_file(bucket, key, local_path)
    return local_path

def read_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.dumps(json.load(f))

def download_daily_data(**context):
    """
    Download daily flight data from S3 bucket specified in DAG configuration
    """
    # Get S3 path from DAG configuration
    daily_s3_bucket = context['dag_run'].conf.get('daily_s3_bucket', 'default-bucket')
    daily_s3_key = context['dag_run'].conf.get('daily_s3_key', 'data3.json')
    
    # Local path to save the downloaded file
    local_path = f'/tmp/{daily_s3_key}'
    
    # Download the file
    download_path = download_from_s3(daily_s3_bucket, daily_s3_key, local_path)
    
    # Return the local path for use in subsequent tasks
    return download_path

def download_monthly_data(**context):
    """
    Download monthly flight data from S3 bucket specified in DAG configuration
    """
    # Get S3 path from DAG configuration
    monthly_s3_bucket = context['dag_run'].conf.get('monthly_s3_bucket', 'default-bucket')
    monthly_s3_key = context['dag_run'].conf.get('monthly_s3_key', 'data2.json')
    
    # Local path to save the downloaded file
    local_path = f'/tmp/{monthly_s3_key}'
    
    # Download the file
    download_path = download_from_s3(monthly_s3_bucket, monthly_s3_key, local_path)
    
    # Return the local path for use in subsequent tasks
    return download_path

def process_daily_flights_data(**context):
    # Get the local path of the downloaded file
    json_file_path = context['task_instance'].xcom_pull(task_ids='download_daily_data')
    
    # Read and parse the JSON file
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Process the data into a list of dictionaries
    processed_data = []
    for itinerary in data.get("data", {}).get("itineraries", []):
        for leg in itinerary.get("legs", []):
            for carrier in leg.get("carriers", {}).get("marketing", []):
                for segment in leg.get("segments", []):
                    processed_data.append({
                        "flight_id": itinerary.get("id"),
                        "price_raw": itinerary.get("price", {}).get("raw"),
                        "price_formatted": itinerary.get("price", {}).get("formatted"),
                        "origin_id": leg.get("origin", {}).get("id"),
                        "destination_id": leg.get("destination", {}).get("id"),
                        "departure_time": leg.get("departure"),
                        "arrival_time": leg.get("arrival"),
                        "airline_name": carrier.get("name"),
                        "flight_number": segment.get("flightNumber")
                    })
    
    return json.dumps(processed_data)

def read_monthly_data(**context):
    # Get the local path of the downloaded file
    json_file_path = context['task_instance'].xcom_pull(task_ids='download_monthly_data')
    
    # Read and return the JSON file contents
    return read_json_file(json_file_path)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

extractDag = DAG(
    'load_to_snowflake',
    default_args=default_args,
    description='Load data to Snowflake',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
) 

# Create table in Snowflake
init_database = SnowflakeOperator(
    task_id='init_database',
    snowflake_conn_id='snowflake_conn',
    sql="""
    USE ROLE ACCOUNTADMIN;
    USE WAREHOUSE COMPUTE_WH;
    CREATE DATABASE IF NOT EXISTS FINAL_PROJECT;
    USE DATABASE FINAL_PROJECT;
    CREATE SCHEMA IF NOT EXISTS PUBLIC;
    USE SCHEMA PUBLIC;
    """,
    dag=extractDag
)

# Create daily flights table
create_daily_flights_table = SnowflakeOperator(
    task_id='create_daily_flights_table',
    snowflake_conn_id='snowflake_conn',
    sql="""
    USE WAREHOUSE COMPUTE_WH;
    USE DATABASE FINAL_PROJECT;
    USE SCHEMA PUBLIC;
    
    -- Create the main table if it doesn't exist
    CREATE TABLE IF NOT EXISTS daily_flights (
        flight_id VARCHAR,
        price_raw FLOAT,
        price_formatted VARCHAR,
        origin_id VARCHAR,
        destination_id VARCHAR,
        departure_time TIMESTAMP_NTZ,
        arrival_time TIMESTAMP_NTZ,
        airline_name VARCHAR,
        flight_number VARCHAR,
        load_date TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    dag=extractDag
)

# Create monthly flights table
create_monthly_flights_table = SnowflakeOperator(
    task_id='create_monthly_flights_table',
    snowflake_conn_id='snowflake_conn',
    sql="""
    USE WAREHOUSE COMPUTE_WH;
    USE DATABASE FINAL_PROJECT;
    USE SCHEMA PUBLIC;
    
    -- Create the main table if it doesn't exist
    CREATE TABLE IF NOT EXISTS monthly_flights (
        flight_id VARCHAR,
        price_raw FLOAT,
        price_formatted VARCHAR,
        origin_id VARCHAR,
        destination_id VARCHAR,
        departure_time TIMESTAMP,
        arrival_time TIMESTAMP,
        airline_name VARCHAR,
        flight_number VARCHAR,
        load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    dag=extractDag
)

# Download data from S3
download_daily_data = PythonOperator(
    task_id='download_daily_data',
    python_callable=download_daily_data,
    provide_context=True,
    dag=extractDag
)

download_monthly_data = PythonOperator(
    task_id='download_monthly_data',
    python_callable=download_monthly_data,
    provide_context=True,
    dag=extractDag
)

# Process daily flights data
process_daily_json = PythonOperator(
    task_id='process_daily_json',
    python_callable=process_daily_flights_data,
    provide_context=True,
    dag=extractDag
)

# Read monthly flights JSON
read_monthly_json = PythonOperator(
    task_id='read_monthly_json',
    python_callable=read_monthly_data,
    provide_context=True,
    dag=extractDag
)

# Load daily flights data
load_daily_flights = SnowflakeOperator(
    task_id='load_daily_flights',
    snowflake_conn_id='snowflake_conn',
    sql="""
    USE WAREHOUSE COMPUTE_WH;
    USE DATABASE FINAL_PROJECT;
    USE SCHEMA PUBLIC;
    
    -- Transform and load into final table
    INSERT INTO daily_flights (
        flight_id,
        price_raw,
        price_formatted,
        origin_id,
        destination_id,
        departure_time,
        arrival_time,
        airline_name,
        flight_number
    )
    WITH json_data AS (
        SELECT PARSE_JSON('{{ task_instance.xcom_pull(task_ids="process_daily_json") }}') as json
    )
    SELECT DISTINCT
        f.value:flight_id::VARCHAR as flight_id,
        f.value:price_raw::FLOAT as price_raw,
        f.value:price_formatted::VARCHAR as price_formatted,
        f.value:origin_id::VARCHAR as origin_id,
        f.value:destination_id::VARCHAR as destination_id,
        TO_TIMESTAMP_NTZ(f.value:departure_time::VARCHAR) as departure_time,
        TO_TIMESTAMP_NTZ(f.value:arrival_time::VARCHAR) as arrival_time,
        f.value:airline_name::VARCHAR as airline_name,
        f.value:flight_number::VARCHAR as flight_number
    FROM json_data,
    LATERAL FLATTEN(input => json) f;
    """,
    dag=extractDag
)

# Load monthly flights data
load_monthly_flights = SnowflakeOperator(
    task_id='load_monthly_flights',
    snowflake_conn_id='snowflake_conn',
    sql="""
    USE WAREHOUSE COMPUTE_WH;
    USE DATABASE FINAL_PROJECT;
    USE SCHEMA PUBLIC;
    
    -- Transform and load into final table
    INSERT INTO monthly_flights (
        flight_id,
        price_raw,
        price_formatted,
        origin_id,
        destination_id,
        departure_time,
        arrival_time,
        airline_name,
        flight_number
    )
    WITH json_data AS (
        SELECT PARSE_JSON('{{ task_instance.xcom_pull(task_ids="read_monthly_json") }}') as json
    )
    SELECT DISTINCT
        r.value:id::VARCHAR as flight_id,
        r.value:content:rawPrice::FLOAT as price_raw,
        r.value:content:price::VARCHAR as price_formatted,
        r.value:content:outboundLeg:originAirport:skyCode::VARCHAR as origin_id,
        r.value:content:outboundLeg:destinationAirport:skyCode::VARCHAR as destination_id,
        r.value:content:outboundLeg:localDepartureDate::TIMESTAMP as departure_time,
        r.value:content:outboundLeg:localDepartureDate::TIMESTAMP as arrival_time,
        SPLIT_PART(r.value:id::VARCHAR, '*', 7)::VARCHAR as airline_name,
        'N/A' as flight_number
    FROM json_data,
    LATERAL FLATTEN(input => json:data:flightQuotes:results) r
    WHERE r.value:type::VARCHAR = 'FLIGHT_QUOTE';
    """,
    dag=extractDag
)

# Set task dependencies
init_database >> [create_daily_flights_table, create_monthly_flights_table]
create_daily_flights_table >> download_daily_data >> process_daily_json >> load_daily_flights
create_monthly_flights_table >> download_monthly_data >> read_monthly_json >> load_monthly_flights

# This exposes the DAG
extractDag