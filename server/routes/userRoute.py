from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict

from middlewares.conn_database import get_db
from models.userModel import User, UserCreate, UserUpdate, UserResponse
from controllers.userController import user_controller
from middlewares.auth import auth

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_current_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user if it doesn't exist
    """
    return await user_controller.create_user(user_data, db)

@router.get("/", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(auth.get_current_user)):
    """
    Get current user details
    """
    return await user_controller.get_user(current_user)

@router.put("/", response_model=Dict[str, str])
async def update_user(
    user_data: UserUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user details
    """
    return await user_controller.update_user(user_data, current_user, db)