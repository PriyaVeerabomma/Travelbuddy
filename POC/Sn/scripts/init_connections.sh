#!/bin/bash

# Wait for Airflow to be ready
echo "Waiting for Airflow webserver to be ready..."
sleep 30

# Run the Python script to set up connections
echo "Setting up Snowflake connection..."
docker-compose exec airflow-webserver python /opt/airflow/scripts/setup_connections.py

echo "Connection setup completed!" 