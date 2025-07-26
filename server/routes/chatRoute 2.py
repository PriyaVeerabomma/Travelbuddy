# # routes/chatRoute.py
# from fastapi import APIRouter, Request
# from pydantic import BaseModel

# router = APIRouter()

# class ChatRequest(BaseModel):
#     message: str

# @router.post("/chat")
# async def chat_endpoint(payload: ChatRequest):
#     # For now, just echo back the message
#     return {s
#         "response": f"Received: {payload.message}"
#     }


#last try - working

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