from fastapi import HTTPException, Depends
from typing import Dict, Any, List, Optional
import os
import logging
import uuid
import traceback

from middlewares.conn_database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel

from controllers.llm_chat_historyController import LLMChatHistoryController
from agents.rootAgent import root_agent

logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str
    content: str

class LLMController:
    def __init__(self, db: Session = Depends(get_db)):
        self.travel_keywords = self._load_keywords()
        self.travel_system_prompt = self._load_system_prompt()
        self.allowed_greetings = [
            "hi", "hello", "hey", "greetings", "good morning", 
            "good afternoon", "good evening", "howdy", "what's up",
            "how are you", "nice to meet you", "help", "start"
        ]

        logger.info(f"🔧 Loaded root agent: {root_agent.name}")
        for sa in getattr(root_agent, "sub_agents", []):
            logger.info(f"→ Sub-agent: {getattr(sa, 'name', 'MISSING NAME')} ({type(sa)})")
    
    def _load_keywords(self) -> List[str]:
        keywords_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'travel_keywords.txt')
        try:
            with open(keywords_path, 'r') as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            return ["travel", "vacation", "trip", "hotel", "flight", "destination"]
    
    def _load_system_prompt(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'travel_instructions.txt')
        try:
            with open(prompt_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            return "You are a Travel AI Assistant. Only answer travel-related questions."
    
    def is_pure_greeting(self, query: str) -> bool:
        query_lower = query.lower().strip()
        if query_lower in self.allowed_greetings:
            return True
        for greeting in self.allowed_greetings:
            if query_lower == greeting or query_lower == f"{greeting}!":
                return True
        return False
    
    def is_travel_related(self, query: str) -> bool:
        if self.is_pure_greeting(query):
            return True
        if len(query.strip().split()) <= 2:
            return False
        query_lower = query.lower()
        for keyword in self.travel_keywords:
            if keyword.lower() in query_lower:
                return True
        return False
    
    def _check_chat_history_context(self, chat_history: List[Message]) -> bool:
        if not chat_history:
            return False
        recent_messages = chat_history[-3:] if len(chat_history) > 3 else chat_history
        for message in recent_messages:
            content = message.content.lower()
            for keyword in self.travel_keywords:
                if keyword.lower() in content:
                    return True
        return False
    
    async def ensure_session_exists(self, chat_history_controller, chat_id, user_email):
        if not chat_history_controller or not user_email:
            return None
        if chat_id:
            try:
                verify_result = await chat_history_controller.get_session(chat_id)
                if verify_result and verify_result.get("status") == "success":
                    return chat_id
            except Exception:
                pass
        try:
            generated_id = str(uuid.uuid4())
            session_result = await chat_history_controller.create_session(generated_id, user_email)
            new_chat_id = session_result["session"]["id"]
            verify_result = await chat_history_controller.get_session(new_chat_id)
            if verify_result and verify_result.get("status") == "success":
                return new_chat_id
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
        return None
    
    async def save_message(self, chat_history_controller, chat_id, role, content):
        if not chat_id or not chat_history_controller:
            return None
        try:
            result = await chat_history_controller.save_message(chat_id, role, content)
            return result
        except Exception as e:
            logger.error(f"Error saving {role} message: {str(e)}")
            return None
    
    async def ask_question(
        self, 
        query: str, 
        chat_history: List[Message] = [], 
        chat_id: str = None, 
        user_email: str = None,
        db: Session = None
    ) -> Dict[str, Any]:
        chat_history_controller = LLMChatHistoryController(db) if db else None
        
        if chat_history_controller and user_email:
            chat_id = await self.ensure_session_exists(chat_history_controller, chat_id, user_email)
        
        if chat_id and chat_history_controller and not chat_history:
            try:
                history_result = await chat_history_controller.get_chat_history(chat_id)
                chat_history = [
                    Message(role=msg["role"], content=msg["content"]) 
                    for msg in history_result["messages"]
                ]
            except Exception:
                chat_history = []
        
        await self.save_message(chat_history_controller, chat_id, "user", query)
        
        is_travel = self.is_travel_related(query)
        context_is_travel = self._check_chat_history_context(chat_history)
        
        if not is_travel and not context_is_travel:
            response_text = "I'm your Travel AI Assistant and can only help with travel-related questions. Feel free to ask me about destinations, trip planning, accommodations, or any other travel topics!"
            await self.save_message(chat_history_controller, chat_id, "assistant", response_text)
            return {
                "status": "redirect",
                "answer": response_text,
                "model": "filter",
                "chat_id": chat_id
            }
        
        actual_query = (
            f"{query}. Please provide a brief introduction about yourself as a travel assistant."
            if self.is_pure_greeting(query) else query
        )
        
        context = ""
        if chat_history:
            for message in chat_history:
                role_prefix = "User: " if message.role == "user" else "Assistant: "
                context += f"{role_prefix}{message.content}\n\n"
        
        try:
            # For weather queries, we want to focus only on the current query, not the entire chat history
            is_weather_query = any(
                term in actual_query.lower() for term in ["weather", "forecast", "temperature", "rain", "sunny", "cloudy", "hot", "cold"]
            )
            
            if is_weather_query:
                # For weather queries, use only the current query without history
                logger.info(f"Detected potential weather query, using only current query: {actual_query}")
                agent_input = actual_query
            else:
                # For other queries, include chat history as context
                logger.info(f"Using full context with chat history for non-weather query")
                agent_input = f"Chat History:\n{context}\n\nCurrent Query: {actual_query}" if context else actual_query

            # ✅ Validate sub-agents before call
            for sa in getattr(root_agent, "sub_agents", []):
                if not hasattr(sa, "name"):
                    raise HTTPException(status_code=500, detail=f"Invalid sub-agent detected: {sa}")
            
            agent_response = await root_agent.ainvoke({"input": agent_input})
            logger.info(f"Agent response: {agent_response}")
            answer = agent_response.get("output", "I couldn't process your request at this time.")

            # Log the agent's response for debugging
            logger.info(f"Agent response: {answer[:100]}...")  # Log first 100 chars

            # Build the final response with API data if available
            response = {
                "status": "success",
                "answer": answer,
                "model": "agent",
                "chat_id": chat_id
            }
            
            # Check for and add API data to the response
            if "api_data" in agent_response:
                # If there's a structured api_data field, use it
                for data_type, data in agent_response["api_data"].items():
                    response[data_type] = data
            
            # Also check for direct data fields for backward compatibility
            for data_type in ["flights", "hotels", "restaurants", "attractions", "location"]:
                if data_type in agent_response and data_type not in response:
                    response[data_type] = agent_response[data_type]
            
            # Only store the text answer in chat history
            await self.save_message(chat_history_controller, chat_id, "assistant", answer)
            
            return response
            

        except Exception as e:
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error when calling agent: {str(e)}")