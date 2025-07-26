from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from models.userModel import User, UserCreate, UserUpdate, UserResponse

class UserController:
    @staticmethod
    async def create_user(user_data: UserCreate, db: Session):
        """
        Create a new user if it doesn't exist
        """
        try:
            # Check if user exists
            existing_user = db.query(User).filter(User.auth0id == user_data.auth0id).first()
            if existing_user:
                return existing_user
            
            # Create new user
            new_user = User(**user_data.dict())
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        
        except Exception as e:
            db.rollback()
            print(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user"
            )
    
    @staticmethod
    async def get_user(current_user: User):
        """
        Get current user details
        """
        return current_user
    
    @staticmethod
    async def update_user(user_data: UserUpdate, current_user: User, db: Session) -> Dict[str, str]:
        """
        Update user details
        """
        try:
            # Update user fields
            for key, value in user_data.dict(exclude_unset=True).items():
                setattr(current_user, key, value)
            
            db.commit()
            db.refresh(current_user)
            
            return {"message": "User updated successfully"}
        
        except Exception as e:
            db.rollback()
            print(f"Error updating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating user"
            )

user_controller = UserController()