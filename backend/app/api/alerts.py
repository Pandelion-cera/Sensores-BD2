from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import json
import asyncio

from app.models.alert_models import Alert, AlertCreate, AlertStatus, AlertType
from app.services.alert_service import AlertService
from app.core.security import get_current_user_data
from app.core.database import get_mongo_db, get_redis_client
from app.repositories.alert_repository import AlertRepository

router = APIRouter()


def get_alert_service(
    mongo_db=Depends(get_mongo_db),
    redis_client=Depends(get_redis_client)
) -> AlertService:
    alert_repo = AlertRepository(mongo_db, redis_client)
    return AlertService(alert_repo)


@router.post("", response_model=Alert, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    alert_service: AlertService = Depends(get_alert_service)
):
    """Create a new alert (admin/técnico only)"""
    if current_user.get("role") not in ["administrador", "tecnico"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return alert_service.create_alert(alert_data)


@router.get("", response_model=List[Alert])
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: Optional[AlertStatus] = None,
    tipo: Optional[AlertType] = None,
    sensor_id: Optional[str] = None,
    alert_service: AlertService = Depends(get_alert_service)
):
    """Get all alerts with optional filters"""
    return alert_service.get_all_alerts(skip, limit, estado, sensor_id)


@router.get("/active", response_model=List[Alert])
def get_active_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    alert_service: AlertService = Depends(get_alert_service)
):
    """Get all active alerts"""
    return alert_service.get_active_alerts(skip, limit)


@router.get("/{alert_id}", response_model=Alert)
def get_alert(
    alert_id: str,
    alert_service: AlertService = Depends(get_alert_service)
):
    """Get alert by ID"""
    alert = alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    return alert


@router.patch("/{alert_id}/resolve", response_model=Alert)
def resolve_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    alert_service: AlertService = Depends(get_alert_service)
):
    """Mark alert as resolved (admin/técnico only)"""
    if current_user.get("role") not in ["administrador", "tecnico"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    alert = alert_service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    return alert


@router.patch("/{alert_id}/acknowledge", response_model=Alert)
def acknowledge_alert(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    alert_service: AlertService = Depends(get_alert_service)
):
    """Mark alert as acknowledged"""
    alert = alert_service.acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    return alert


@router.get("/stream/live")
async def alert_stream(
    alert_service: AlertService = Depends(get_alert_service)
):
    """Server-Sent Events stream for real-time alerts"""
    async def event_generator():
        last_id = "0"
        while True:
            try:
                # Read alerts from Redis Stream
                alerts = alert_service.read_alert_stream(count=10, last_id=last_id)
                
                for alert in alerts:
                    if "stream_id" in alert:
                        last_id = alert["stream_id"]
                    
                    yield f"data: {json.dumps(alert)}\n\n"
                
                # Wait before next poll
                await asyncio.sleep(1)
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

