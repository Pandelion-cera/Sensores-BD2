from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AlertType(str, Enum):
    SENSOR_FAILURE = "sensor"
    CLIMATE = "climatica"
    THRESHOLD = "umbral"


class AlertStatus(str, Enum):
    ACTIVE = "activa"
    RESOLVED = "resuelta"
    ACKNOWLEDGED = "reconocida"


class Alert(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    tipo: AlertType
    sensor_id: Optional[str] = None
    fecha_hora: datetime = Field(default_factory=datetime.utcnow)
    descripcion: str
    estado: AlertStatus = AlertStatus.ACTIVE
    valor: Optional[float] = None
    umbral: Optional[float] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "tipo": "climatica",
                "sensor_id": "sensor123",
                "descripcion": "Temperatura alta detectada",
                "estado": "activa",
                "valor": 45.0,
                "umbral": 40.0
            }
        }


class AlertCreate(BaseModel):
    tipo: AlertType
    sensor_id: Optional[str] = None
    descripcion: str
    valor: Optional[float] = None
    umbral: Optional[float] = None

