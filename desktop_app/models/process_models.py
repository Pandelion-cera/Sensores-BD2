from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ProcessType(str, Enum):
    TEMP_MAX_MIN_REPORT = "informe_max_min"
    TEMP_AVG_REPORT = "informe_promedio"
    ALERT_CONFIG = "configuracion_alertas"
    ONLINE_QUERY = "consulta_online"
    PERIODIC_REPORT = "reporte_periodico"


class ProcessStatus(str, Enum):
    PENDING = "pendiente"
    IN_PROGRESS = "en_progreso"
    COMPLETED = "completado"
    FAILED = "fallido"


class Process(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    nombre: str
    descripcion: str
    tipo: ProcessType
    costo: float = Field(..., ge=0)
    parametros_schema: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "nombre": "Reporte Temperatura Máxima/Mínima",
                "descripcion": "Genera un informe de temperaturas máximas y mínimas",
                "tipo": "informe_max_min",
                "costo": 10.50
            }
        }


class ProcessCreate(BaseModel):
    nombre: str = Field(..., min_length=3)
    descripcion: str
    tipo: ProcessType
    costo: float = Field(..., ge=0)
    parametros_schema: Dict[str, Any] = Field(default_factory=dict)


class ProcessRequest(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    process_id: str
    fecha_solicitud: datetime = Field(default_factory=datetime.utcnow)
    estado: ProcessStatus = ProcessStatus.PENDING
    parametros: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True


class ProcessRequestCreate(BaseModel):
    process_id: str
    parametros: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "process_id": "proc123",
                "parametros": {
                    "ciudad": "Buenos Aires",
                    "fecha_inicio": "2024-01-01",
                    "fecha_fin": "2024-12-31"
                }
            }
        }


class Execution(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    request_id: str
    fecha_ejecucion: datetime = Field(default_factory=datetime.utcnow)
    resultado: Optional[Dict[str, Any]] = None
    estado: ProcessStatus = ProcessStatus.PENDING
    error_message: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ExecutionCreate(BaseModel):
    request_id: str
    resultado: Optional[Dict[str, Any]] = None
    estado: ProcessStatus
    error_message: Optional[str] = None

