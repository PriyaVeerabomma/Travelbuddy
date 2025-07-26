from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    auth0id = Column(String, nullable=False, unique=True)
    email = Column(String)
    name = Column(String)
    addressLine1 = Column(String)
    addressLine2 = Column(String)
    city = Column(String)
    state = Column(String)
    zipCode = Column(String)
    country = Column(String)
    phone = Column(String)

    def to_dict(self):
        return {
            'id': self.id,
            'auth0id': self.auth0id,
            'email': self.email,
            'name': self.name,
            'addressLine1': self.addressLine1,
            'addressLine2': self.addressLine2,
            'city': self.city,
            'state': self.state,
            'zipCode': self.zipCode,
            'country': self.country,
            'phone': self.phone
        }


# Pydantic models for request validation
class UserCreate(BaseModel):
    auth0id: str
    email: Optional[str] = None
    name: Optional[str] = None
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    auth0id: str
    email: Optional[str] = None
    name: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        orm_mode = True