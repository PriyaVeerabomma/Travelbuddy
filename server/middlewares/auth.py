from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import os
from dotenv import load_dotenv
from models.userModel import User
from middlewares.conn_database import get_db

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

security = HTTPBearer()

class Auth:
    async def get_token_auth_header(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authorization header provided",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials.credentials

    async def verify_jwt(self, token: str = Depends(get_token_auth_header)):
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_user_from_token(self, 
                                  token_data: dict = Depends(verify_jwt), 
                                  db: Session = Depends(get_db)):
        auth0id = token_data.get("sub")
        if not auth0id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(User).filter(User.auth0id == auth0id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        return {"user": user, "auth0id": auth0id}

    # Dependency to be used in routes
    async def get_current_user(self, 
                               auth_result: dict = Depends(get_user_from_token)):
        return auth_result["user"]

auth = Auth()