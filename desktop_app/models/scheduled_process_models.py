from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ScheduleType(str, Enum):
    DAILY = "diario"
    WEEKLY = "semanal"
    MONTHLY = "mensual"
    ANNUAL = "anual"


class ScheduleStatus(str, Enum):
    ACTIVE = "activo"
    PAUSED = "pausado"


class ScheduledProcess(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    process_id: str
    parametros: Dict[str, Any] = Field(default_factory=dict)
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any] = Field(default_factory=dict)
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    next_execution: datetime
    last_execution: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "process_id": "proc456",
                "parametros": {
                    "ciudad": "Buenos Aires",
                    "pais": "Argentina"
                },
                "schedule_type": "diario",
                "schedule_config": {
                    "hour": 9,
                    "minute": 0
                },
                "status": "activo",
                "next_execution": "2024-01-15T09:00:00Z"
            }
        }


class ScheduledProcessCreate(BaseModel):
    process_id: str
    parametros: Dict[str, Any] = Field(default_factory=dict)
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "process_id": "proc456",
                "parametros": {
                    "ciudad": "Buenos Aires",
                    "pais": "Argentina"
                },
                "schedule_type": "diario",
                "schedule_config": {
                    "hour": 9,
                    "minute": 0
                }
            }
        }


class ScheduledProcessUpdate(BaseModel):
    parametros: Optional[Dict[str, Any]] = None
    schedule_type: Optional[ScheduleType] = None
    schedule_config: Optional[Dict[str, Any]] = None
    status: Optional[ScheduleStatus] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "parametros": {
                    "ciudad": "Córdoba",
                    "pais": "Argentina"
                },
                "schedule_config": {
                    "hour": 10,
                    "minute": 30
                }
            }
        }

