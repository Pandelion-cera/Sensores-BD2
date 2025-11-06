from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AlertType(str, Enum):
    SENSOR_FAILURE = "sensor"
    CLIMATE = "climatica"
    THRESHOLD = "umbral"
    PROCESS_EXECUTED = "proceso_ejecutado"


class AlertStatus(str, Enum):
    ACTIVE = "activa"
    FINISHED = "finalizada"


class Alert(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    tipo: AlertType
    sensor_id: Optional[str] = None
    user_id: Optional[str] = Field(None, description="Usuario al que se dirige la alerta")
    fecha_hora: datetime = Field(default_factory=datetime.utcnow)
    descripcion: str
    estado: AlertStatus = AlertStatus.ACTIVE
    valor: Optional[float] = None
    umbral: Optional[float] = None
    # Información de la regla que generó esta alerta (si aplica)
    rule_id: Optional[str] = Field(None, description="ID de la regla que generó esta alerta")
    rule_name: Optional[str] = Field(None, description="Nombre de la regla que generó esta alerta")
    prioridad: Optional[int] = Field(None, ge=1, le=5, description="Prioridad de la alerta (heredada de la regla)")
    # Información adicional para alertas de procesos
    process_id: Optional[str] = Field(None, description="ID del proceso ejecutado")
    execution_id: Optional[str] = Field(None, description="ID de la ejecución")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "tipo": "umbral",
                "sensor_id": "sensor123",
                "descripcion": "Temperatura alta detectada",
                "estado": "activa",
                "valor": 45.0,
                "umbral": 40.0,
                "rule_name": "Ola de calor Buenos Aires",
                "prioridad": 4
            }
        }


class AlertCreate(BaseModel):
    tipo: AlertType
    sensor_id: Optional[str] = None
    user_id: Optional[str] = Field(None, description="Usuario al que se dirige la alerta")
    descripcion: str
    valor: Optional[float] = None
    umbral: Optional[float] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    prioridad: Optional[int] = Field(None, ge=1, le=5)
    process_id: Optional[str] = Field(None, description="ID del proceso ejecutado")
    execution_id: Optional[str] = Field(None, description="ID de la ejecución")

