from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AlertRuleStatus(str, Enum):
    ACTIVE = "activa"
    INACTIVE = "inactiva"


class LocationScope(str, Enum):
    CITY = "ciudad"
    REGION = "region"
    COUNTRY = "pais"


class AlertRule(BaseModel):
    """
    Modelo para reglas de alertas configurables por administradores.
    Define condiciones automáticas para generar alertas.
    """
    id: Optional[str] = Field(None, alias="_id")
    nombre: str = Field(..., description="Nombre descriptivo de la regla")
    descripcion: str = Field(..., description="Descripción de qué detecta esta regla")
    
    # Condiciones de temperatura
    temp_min: Optional[float] = Field(None, description="Temperatura mínima del rango")
    temp_max: Optional[float] = Field(None, description="Temperatura máxima del rango")
    
    # Condiciones de humedad
    humidity_min: Optional[float] = Field(None, ge=0, le=100, description="Humedad mínima del rango")
    humidity_max: Optional[float] = Field(None, ge=0, le=100, description="Humedad máxima del rango")
    
    # Ubicación
    location_scope: LocationScope = Field(..., description="Nivel geográfico de aplicación")
    ciudad: Optional[str] = Field(None, description="Ciudad específica (si scope es 'ciudad')")
    region: Optional[str] = Field(None, description="Región o zona (si scope es 'region')")
    pais: str = Field(..., description="País donde aplica la regla")
    
    # Rango de fechas
    fecha_inicio: Optional[datetime] = Field(None, description="Fecha de inicio de vigencia")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha de fin de vigencia")
    
    # Estado y metadatos
    estado: AlertRuleStatus = Field(default=AlertRuleStatus.ACTIVE)
    prioridad: int = Field(default=1, ge=1, le=5, description="Prioridad de la regla (1=baja, 5=crítica)")
    creado_por: str = Field(..., description="Email del admin que creó la regla")
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_modificacion: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "nombre": "Alerta ola de calor Buenos Aires",
                "descripcion": "Detecta temperaturas extremas en verano",
                "temp_min": 35.0,
                "temp_max": 50.0,
                "humidity_min": None,
                "humidity_max": None,
                "location_scope": "ciudad",
                "ciudad": "Buenos Aires",
                "region": None,
                "pais": "Argentina",
                "fecha_inicio": "2024-12-01T00:00:00",
                "fecha_fin": "2025-03-31T23:59:59",
                "estado": "activa",
                "prioridad": 4,
                "creado_por": "admin@example.com"
            }
        }


class AlertRuleCreate(BaseModel):
    """Modelo para crear una nueva regla de alerta"""
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: str = Field(..., min_length=10, max_length=500)
    
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    
    humidity_min: Optional[float] = Field(None, ge=0, le=100)
    humidity_max: Optional[float] = Field(None, ge=0, le=100)
    
    location_scope: LocationScope
    ciudad: Optional[str] = None
    region: Optional[str] = None
    pais: str = Field(..., min_length=2)
    
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    
    estado: AlertRuleStatus = AlertRuleStatus.ACTIVE
    prioridad: int = Field(default=1, ge=1, le=5)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Alerta heladas invierno",
                "descripcion": "Detecta temperaturas bajo cero en invierno",
                "temp_min": -10.0,
                "temp_max": 0.0,
                "location_scope": "region",
                "region": "Patagonia",
                "pais": "Argentina",
                "fecha_inicio": "2025-06-01T00:00:00",
                "fecha_fin": "2025-09-30T23:59:59",
                "prioridad": 3
            }
        }


class AlertRuleUpdate(BaseModel):
    """Modelo para actualizar una regla existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, min_length=10, max_length=500)
    
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    
    humidity_min: Optional[float] = Field(None, ge=0, le=100)
    humidity_max: Optional[float] = Field(None, ge=0, le=100)
    
    location_scope: Optional[LocationScope] = None
    ciudad: Optional[str] = None
    region: Optional[str] = None
    pais: Optional[str] = None
    
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    
    estado: Optional[AlertRuleStatus] = None
    prioridad: Optional[int] = Field(None, ge=1, le=5)


class AlertRuleResponse(BaseModel):
    """Modelo de respuesta para reglas de alerta"""
    id: str
    nombre: str
    descripcion: str
    temp_min: Optional[float]
    temp_max: Optional[float]
    humidity_min: Optional[float]
    humidity_max: Optional[float]
    location_scope: LocationScope
    ciudad: Optional[str]
    region: Optional[str]
    pais: str
    fecha_inicio: Optional[datetime]
    fecha_fin: Optional[datetime]
    estado: AlertRuleStatus
    prioridad: int
    creado_por: str
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime]
    
    class Config:
        populate_by_name = True
