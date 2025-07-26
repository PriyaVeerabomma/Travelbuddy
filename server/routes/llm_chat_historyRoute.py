from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr
from controllers.llm_chat_historyController import LLMChatHistoryController
from middlewares.conn_database import get_db
from sqlalchemy.orm import Session

# Create the router
router = APIRouter()

# Define request models
class CreateSessionRequest(BaseModel):
    user_email: EmailStr
    
    class Config:
        schema_extra = {
            "example": {
                "user_email": "user@example.com"
            }
        }

class SaveMessageRequest(BaseModel):
    role: str
    content: str
    
    class Config:
        schema_extra = {
            "example": {
                "role": "user",
                "content": "What are the best destinations to visit in Europe?"
            }
        }

# Endpoint to create a new chat session
@router.post("/chat-history", status_code=201)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    controller = LLMChatHistoryController(db)
    return await controller.create_session(user_email=request.user_email)

# Endpoint to get a specific chat session
@router.get("/chat-history/{session_id}")
async def get_session(
    session_id: str = Path(..., description="The ID of the chat session"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    controller = LLMChatHistoryController(db)
    return await controller.get_session(session_id=session_id)

# Endpoint to get all chat sessions for a user
@router.get("/chat-history")
async def get_user_sessions(
    user_email: EmailStr = Query(..., description="The email of the user"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    controller = LLMChatHistoryController(db)
    return await controller.get_user_sessions(user_email=user_email)

# Endpoint to save a message to a chat session
@router.post("/chat-history/{session_id}/messages")
async def save_message(
    request: SaveMessageRequest,
    session_id: str = Path(..., description="The ID of the chat session"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    controller = LLMChatHistoryController(db)
    return await controller.save_message(
        session_id=session_id, 
        role=request.role, 
        content=request.content
    )

# Endpoint to get chat history for a session
@router.get("/chat-history/{session_id}/messages")
async def get_chat_history(
    session_id: str = Path(..., description="The ID of the chat session"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    controller = LLMChatHistoryController(db)
    return await controller.get_chat_history(session_id=session_id)

# Endpoint to delete a chat session
@router.delete("/chat-history/{session_id}")
async def delete_session(
    session_id: str = Path(..., description="The ID of the chat session"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    controller = LLMChatHistoryController(db)
    return await controller.delete_session(session_id=session_id)