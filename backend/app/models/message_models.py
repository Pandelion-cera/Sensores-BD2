from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    PRIVATE = "privado"
    GROUP = "grupal"


class Message(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    sender_id: str
    recipient_type: MessageType
    recipient_id: str  # user_id or group_id
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: str
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "sender_id": "user123",
                "recipient_type": "privado",
                "recipient_id": "user456",
                "content": "Hola, ¿cómo estás?"
            }
        }


class MessageCreate(BaseModel):
    recipient_type: MessageType
    recipient_id: str
    content: str = Field(..., min_length=1, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "recipient_type": "privado",
                "recipient_id": "user456",
                "content": "Hola, ¿cómo estás?"
            }
        }


class MessageResponse(BaseModel):
    id: str
    sender_id: str
    sender_name: Optional[str] = None
    recipient_type: MessageType
    recipient_id: str
    timestamp: datetime
    content: str
    
    class Config:
        populate_by_name = True

