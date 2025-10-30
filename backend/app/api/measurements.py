from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.measurement_models import MeasurementResponse
from app.services.sensor_service import SensorService
from app.services.alert_service import AlertService
from app.core.database import get_mongo_db, get_cassandra_session, get_redis_client
from app.repositories.sensor_repository import SensorRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.alert_repository import AlertRepository
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
    return SensorService(sensor_repo, measurement_repo, alert_service)


@router.get("/sensor/{sensor_id}", response_model=List[MeasurementResponse])
def get_sensor_measurements(
    sensor_id: str,
    start_date: Optional[str] = Query(None, description="ISO format date"),
    end_date: Optional[str] = Query(None, description="ISO format date"),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Get measurements for a specific sensor"""
    # Handle ISO format with 'Z' suffix (UTC)
    start = None
    end = None
    
    if start_date:
        start_clean = start_date.replace('Z', '+00:00')
        start = datetime.fromisoformat(start_clean)
    
    if end_date:
        end_clean = end_date.replace('Z', '+00:00')
        end = datetime.fromisoformat(end_clean)
    
    try:
        return sensor_service.get_sensor_measurements(sensor_id, start, end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/location", response_model=List[Dict[str, Any]])
def get_location_measurements(
    pais: str,
    ciudad: str,
    start_date: Optional[str] = Query(None, description="ISO format date"),
    end_date: Optional[str] = Query(None, description="ISO format date"),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Get measurements for a specific location"""
    # Handle ISO format with 'Z' suffix (UTC)
    start = None
    end = None
    
    if start_date:
        start_clean = start_date.replace('Z', '+00:00')
        start = datetime.fromisoformat(start_clean)
    
    if end_date:
        end_clean = end_date.replace('Z', '+00:00')
        end = datetime.fromisoformat(end_clean)
    
    return sensor_service.get_location_measurements(pais, ciudad, start, end)


@router.get("/stats")
def get_location_stats(
    pais: str,
    ciudad: str,
    start_date: Optional[str] = Query(None, description="ISO format date"),
    end_date: Optional[str] = Query(None, description="ISO format date"),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    """Get statistics (max/min/avg) for a location"""
    # Handle ISO format with 'Z' suffix (UTC)
    start = None
    end = None
    
    if start_date:
        start_clean = start_date.replace('Z', '+00:00')
        start = datetime.fromisoformat(start_clean)
    
    if end_date:
        end_clean = end_date.replace('Z', '+00:00')
        end = datetime.fromisoformat(end_clean)
    
    return sensor_service.get_location_stats(pais, ciudad, start, end)

