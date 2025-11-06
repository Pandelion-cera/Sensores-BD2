from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Session(BaseModel):
    """Session model"""
    session_id: str
    user_id: str
    role: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    status: str = "activa"  # "activa" or "cerrada"
    
    class Config:
        populate_by_name = True


class SessionCreate(BaseModel):
    """Model for creating a session"""
    session_id: str
    user_id: str
    role: str
    login_time: datetime


class SessionUpdate(BaseModel):
    """Model for updating a session"""
    logout_time: Optional[datetime] = None
    status: Optional[str] = None

