from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    # Change from UUID to String
    id = Column(String(36), primary_key=True)
    user_email = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship with ChatMessage
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'created_at': self.created_at,
            'last_updated': self.last_updated
        }


class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    # Change from UUID to String
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationship with ChatSession
    session = relationship("ChatSession", back_populates="messages")

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at
        }


# Pydantic models for request validation

class MessageCreate(BaseModel):
    role: str
    content: str


class SessionCreate(BaseModel):
    user_email: str


class SessionUpdate(BaseModel):
    last_updated: Optional[datetime] = None


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


class SessionResponse(BaseModel):
    id: str
    user_email: str
    created_at: datetime
    last_updated: datetime
    messages: Optional[List[MessageResponse]] = None

    class Config:
        orm_mode = True


class SessionWithPreview(BaseModel):
    id: str
    user_email: str
    created_at: datetime
    last_updated: datetime
    message_count: int
    first_message: Optional[str] = None

    class Config:
        orm_mode = True