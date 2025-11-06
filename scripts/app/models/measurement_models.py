from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Measurement(BaseModel):
    sensor_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: Optional[float] = Field(None, ge=-100, le=100)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "550e8400-e29b-41d4-a716-446655440000",
                "temperature": 22.5,
                "humidity": 65.3
            }
        }


class MeasurementCreate(BaseModel):
    temperature: Optional[float] = Field(None, ge=-100, le=100)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 22.5,
                "humidity": 65.3
            }
        }


class MeasurementResponse(BaseModel):
    sensor_id: str
    timestamp: datetime
    temperatura: Optional[float] = Field(None, alias="temperature")
    humedad: Optional[float] = Field(None, alias="humidity")
    ciudad: Optional[str] = None
    pais: Optional[str] = None
    
    class Config:
        populate_by_name = True

