from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr
from controllers.llmController import LLMController, Message
from middlewares.conn_llm import get_openai_client
from middlewares.conn_database import get_db  # Make sure this is imported
from sqlalchemy.orm import Session
from openai import OpenAI
import logging

router = APIRouter()

class QuestionRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    user_email: Optional[EmailStr] = None
    chat_history: Optional[List[Message]] = []
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What are popular tourist destinations in Japan?",
                "chat_id": None,  # This will be filled in if continuing a conversation
                "user_email": "user@example.com",
                "chat_history": []  # This will be filled with previous messages if needed
            }
        }

@router.post("/ask-question")
async def ask_question(
    request: QuestionRequest,
    openai_client: OpenAI = Depends(get_openai_client),
    db: Session = Depends(get_db)  # Make sure this dependency is here
) -> Dict[str, Any]:
    # Log that we have a database connection
    logging.info(f"Database connection available: {db is not None}")
    
    controller = LLMController(openai_client)
    return await controller.ask_question(
        query=request.query,
        chat_history=request.chat_history,
        chat_id=request.chat_id,
        user_email=request.user_email,
        db=db  # Make sure this is being passed to the controller
    )