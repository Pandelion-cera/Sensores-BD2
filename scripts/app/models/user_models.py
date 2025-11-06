from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "activo"
    INACTIVE = "inactivo"


class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    nombre_completo: str
    email: EmailStr
    password_hash: str
    estado: UserStatus = UserStatus.ACTIVE
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "nombre_completo": "Juan Pérez",
                "email": "juan@example.com",
                "estado": "activo"
            }
        }


class UserCreate(BaseModel):
    nombre_completo: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre_completo": "Juan Pérez",
                "email": "juan@example.com",
                "password": "securepass123"
            }
        }


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=100)
    estado: Optional[UserStatus] = None


class UserResponse(BaseModel):
    id: str
    nombre_completo: str
    email: EmailStr
    estado: UserStatus
    fecha_registro: datetime
    
    class Config:
        populate_by_name = True

