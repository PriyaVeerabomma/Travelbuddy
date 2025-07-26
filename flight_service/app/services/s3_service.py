import json
import boto3
from typing import Dict, Any
from fastapi import HTTPException
from app.config.settings import Settings
from app.models.schemas import S3ObjectInfo

class S3Service:
    """Service for handling S3 storage operations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )
    
    async def upload_json(self, bucket: str, key: str, data: Dict[str, Any]) -> S3ObjectInfo:
        """
        Upload JSON data to S3 bucket and return object information
        """
        try:
            # Convert data to JSON string
            json_data = json.dumps(data)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )
            
            # Generate S3 URL
            s3_url = f"s3://{bucket}/{key}"
            
            # Return object information
            return S3ObjectInfo(
                bucket=bucket,
                key=key,
                url=s3_url
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"S3 upload error: {str(e)}"
            )
    
    async def get_object_url(self, bucket: str, key: str) -> str:
        """
        Get the URL for an object in S3
        """
        return f"s3://{bucket}/{key}"