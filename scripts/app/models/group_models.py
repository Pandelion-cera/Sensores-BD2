from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Group(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    nombre: str
    miembros: List[str] = Field(default_factory=list)  # list of user_ids
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "nombre": "Equipo Técnico",
                "miembros": ["user123", "user456"]
            }
        }


class GroupCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    miembros: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Equipo Técnico",
                "miembros": ["user123", "user456"]
            }
        }


class GroupResponse(BaseModel):
    id: str
    nombre: str
    miembros: List[str]
    fecha_creacion: datetime
    
    class Config:
        populate_by_name = True

