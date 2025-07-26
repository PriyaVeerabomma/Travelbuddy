from fastapi import HTTPException, Depends
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.llm_chat_historyModel import ChatSession, ChatMessage, MessageCreate, SessionCreate
from sqlalchemy import desc, func

class LLMChatHistoryController:
    def __init__(self, db: Session):
        self.db = db

    async def create_session(self, chat_id, user_email: str) -> Dict[str, Any]:
        try:
            new_session = ChatSession(id=chat_id ,user_email=user_email)
            self.db.add(new_session)
            self.db.commit()
            self.db.refresh(new_session)
            
            return {
                "status": "success",
                "session": new_session.to_dict()
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        try:
            
            session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
                
            return {
                "status": "success",
                "session": session.to_dict()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve chat session: {str(e)}")

    async def get_user_sessions(self, user_email: str) -> Dict[str, Any]:
        try:
            
            # Subquery to get message counts and first message for each session
            message_stats = self.db.query(
                ChatMessage.session_id,
                func.count(ChatMessage.id).label('message_count'),
                func.min(ChatMessage.content).filter(ChatMessage.role == 'user').label('first_message')
            ).group_by(ChatMessage.session_id).subquery()
            
            # Join with sessions and order by last updated
            result = self.db.query(
                ChatSession,
                message_stats.c.message_count,
                message_stats.c.first_message
            ).outerjoin(
                message_stats, 
                ChatSession.id == message_stats.c.session_id
            ).filter(
                ChatSession.user_email == user_email
            ).order_by(
                desc(ChatSession.last_updated)
            ).all()
            
            sessions = []
            for row in result:
                session, message_count, first_message = row
                session_dict = session.to_dict()
                session_dict['message_count'] = message_count or 0
                session_dict['first_message'] = first_message
                sessions.append(session_dict)
            
            return {
                "status": "success",
                "sessions": sessions
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve user chat sessions: {str(e)}")

    async def save_message(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        try:
            
            session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
                
            new_message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content
            )
            print (f"New message coming from line 116: {new_message}")
            session.last_updated = func.now()
            
            self.db.add(new_message)
            self.db.commit()
            self.db.refresh(new_message)
            
            return {
                "status": "success",
                "message": new_message.to_dict()
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

    async def get_chat_history(self, session_id: str) -> Dict[str, Any]:
        """Get all messages for a chat session"""
        try:
            session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(
                ChatMessage.created_at
            ).all()
            
            return {
                "status": "success",
                "session_id": session_id,
                "user_email": session.user_email,
                "messages": [message.to_dict() for message in messages]
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        try:
            
            session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
                
            self.db.delete(session)
            self.db.commit()
            
            return {
                "status": "success",
                "message": f"Chat session {session_id} deleted successfully"
            }
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {str(e)}")