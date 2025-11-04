from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from app.models.sensor_models import Sensor, SensorCreate, SensorUpdate, SensorResponse, SensorStatus
from app.models.measurement_models import MeasurementCreate
from app.services.sensor_service import SensorService
from app.services.alert_service import AlertService
from app.services.alert_rule_service import AlertRuleService
from app.core.security import get_current_user_data
from app.core.database import get_mongo_db, get_cassandra_session, get_redis_client
from app.repositories.sensor_repository import SensorRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.alert_rule_repository import AlertRuleRepository
from app.core.config import settings

router = APIRouter()


def get_sensor_service(
    mongo_db=Depends(get_mongo_db),
    cassandra_session=Depends(get_cassandra_session),
    redis_client=Depends(get_redis_client)
) -> SensorService:
    sensor_repo = SensorRepository(mongo_db)
    measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
    alert_repo = AlertRepository(mongo_db, redis_client)
    alert_service = AlertService(alert_repo)
    
    # Initialize alert rule service
    rule_repo = AlertRuleRepository(mongo_db)
    alert_rule_service = AlertRuleService(rule_repo, alert_repo)
    
    return SensorService(sensor_repo, measurement_repo, alert_service, alert_rule_service)


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    sensor_data: SensorCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Create a new sensor (admin/técnico only)"""
    # Check role
    if current_user.get("role") not in ["administrador", "tecnico"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    sensor = sensor_service.create_sensor(sensor_data)
    return SensorResponse(**sensor.model_dump(by_alias=False))


@router.get("", response_model=List[SensorResponse])
def get_sensors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    pais: Optional[str] = Query(None),
    ciudad: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Get all sensors with optional filters"""
    # Convert empty strings to None
    pais_filter = pais if pais and pais.strip() else None
    ciudad_filter = ciudad if ciudad and ciudad.strip() else None
    
    # Convert estado string to SensorStatus enum if provided
    estado_filter = None
    if estado and estado.strip():
        try:
            estado_filter = SensorStatus(estado)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=f"Invalid estado value. Must be one of: {[s.value for s in SensorStatus]}"
            )
    
    sensors = sensor_service.get_all_sensors(skip, limit, pais_filter, ciudad_filter, estado_filter)
    return [SensorResponse(**s.model_dump(by_alias=False)) for s in sensors]


@router.get("/stats")
def get_dashboard_stats(
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Get dashboard statistics"""
    return sensor_service.get_dashboard_stats()


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(
    sensor_id: str,
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Get sensor by ID"""
    sensor = sensor_service.get_sensor(sensor_id)
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    
    return SensorResponse(**sensor.model_dump(by_alias=False))


@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(
    sensor_id: str,
    sensor_update: SensorUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Update sensor (admin/técnico only)"""
    # Check role
    if current_user.get("role") not in ["administrador", "tecnico"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    sensor = sensor_service.update_sensor(sensor_id, sensor_update)
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    
    return SensorResponse(**sensor.model_dump(by_alias=False))


@router.delete("/{sensor_id}")
def delete_sensor(
    sensor_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Delete sensor (admin only)"""
    # Check role
    if current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    success = sensor_service.delete_sensor(sensor_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    
    return {"message": "Sensor deleted successfully"}


@router.post("/{sensor_id}/measurements")
def register_measurement(
    sensor_id: str,
    measurement_data: MeasurementCreate,
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Register a new measurement for a sensor"""
    try:
        return sensor_service.register_measurement(sensor_id, measurement_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

