import os
from openai import OpenAI
from fastapi import HTTPException
from functools import lru_cache

@lru_cache()
def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
  
    client = OpenAI(api_key=api_key)
    
    return client