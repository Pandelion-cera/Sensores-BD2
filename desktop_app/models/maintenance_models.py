from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MaintenanceStatus(str, Enum):
    """Maintenance status"""
    OK = "ok"
    REPAIR_NEEDED = "reparacion_necesaria"
    REPLACEMENT_NEEDED = "reemplazo_necesario"
    OUT_OF_SERVICE = "fuera_de_servicio"


class MaintenanceRecord(BaseModel):
    """Maintenance/control record for sensors"""
    id: Optional[str] = Field(None, alias="_id")
    sensor_id: str
    tecnico_id: str  # User ID of the technician
    fecha_revision: datetime
    estado: MaintenanceStatus
    observaciones: Optional[str] = None
    acciones_realizadas: Optional[str] = None
    proxima_revision: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class MaintenanceRecordCreate(BaseModel):
    """Model for creating a maintenance record"""
    sensor_id: str
    tecnico_id: str
    fecha_revision: datetime
    estado: MaintenanceStatus
    observaciones: Optional[str] = None
    acciones_realizadas: Optional[str] = None
    proxima_revision: Optional[datetime] = None


class MaintenanceRecordUpdate(BaseModel):
    """Model for updating a maintenance record"""
    estado: Optional[MaintenanceStatus] = None
    observaciones: Optional[str] = None
    acciones_realizadas: Optional[str] = None
    proxima_revision: Optional[datetime] = None

