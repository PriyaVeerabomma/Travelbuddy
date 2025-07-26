import httpx
from typing import Dict, Any
from fastapi import HTTPException
from app.config.settings import Settings

class AirflowService:
    """Service for interacting with Airflow API"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    async def trigger_dag(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger an Airflow DAG run
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.settings.AIRFLOW_API_URL,
                    json=payload,
                    auth=(self.settings.AIRFLOW_USERNAME, self.settings.AIRFLOW_PASSWORD),
                    timeout=30.0
                )
                
                if response.status_code < 200 or response.status_code >= 300:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to trigger Airflow DAG: {response.text}"
                    )
                
                return {
                    "status": "success",
                    "dag_run_id": response.json().get("dag_run_id", None),
                    "message": "Successfully triggered Airflow DAG"
                }
        
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Timeout while connecting to Airflow API"
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error triggering Airflow DAG: {str(e)}"
            )