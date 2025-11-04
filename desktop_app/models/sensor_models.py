from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class SensorType(str, Enum):
    TEMPERATURE = "temperatura"
    HUMIDITY = "humedad"
    BOTH = "temperatura_humedad"


class SensorStatus(str, Enum):
    ACTIVE = "activo"
    INACTIVE = "inactivo"
    FAILURE = "falla"


class Sensor(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    sensor_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    tipo: SensorType
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    ciudad: str
    pais: str
    estado: SensorStatus = SensorStatus.ACTIVE
    fecha_inicio_emision: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "nombre": "Sensor Buenos Aires Centro",
                "tipo": "temperatura_humedad",
                "latitud": -34.6037,
                "longitud": -58.3816,
                "ciudad": "Buenos Aires",
                "pais": "Argentina",
                "estado": "activo"
            }
        }


class SensorCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    tipo: SensorType
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    ciudad: str = Field(..., min_length=2)
    pais: str = Field(..., min_length=2)
    estado: SensorStatus = SensorStatus.ACTIVE


class SensorUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    estado: Optional[SensorStatus] = None
    tipo: Optional[SensorType] = None


class SensorResponse(BaseModel):
    id: str
    sensor_id: str
    nombre: str
    tipo: SensorType
    latitud: float
    longitud: float
    ciudad: str
    pais: str
    estado: SensorStatus
    fecha_inicio_emision: datetime
    
    class Config:
        populate_by_name = True

