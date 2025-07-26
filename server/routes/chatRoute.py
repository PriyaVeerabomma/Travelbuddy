from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

@router.post("/chatmaps")
async def chat_endpoint(payload: ChatRequest):
    user_message = next((m.content for m in payload.messages if m.role == "user"), "")
    return {
        "role": "assistant",
        "content": f"Received: {user_message}"
    }