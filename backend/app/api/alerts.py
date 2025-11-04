from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime

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
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    estado: Optional[AlertStatus] = Query(None, description="Filtrar por estado (activa/resuelta/reconocida)"),
    tipo: Optional[AlertType] = Query(None, description="Filtrar por tipo (sensor/climatica/umbral)"),
    sensor_id: Optional[str] = Query(None, description="Filtrar por ID de sensor"),
    fecha_desde: Optional[str] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha fin (ISO format)"),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get all alerts with optional filters.
    Accessible by all authenticated users.
    """
    # Parse dates if provided
    start_date = None
    end_date = None
    
    if fecha_desde:
        try:
            fecha_desde_clean = fecha_desde.replace('Z', '+00:00')
            start_date = datetime.fromisoformat(fecha_desde_clean)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_desde must be in ISO format"
            )
    
    if fecha_hasta:
        try:
            fecha_hasta_clean = fecha_hasta.replace('Z', '+00:00')
            end_date = datetime.fromisoformat(fecha_hasta_clean)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_hasta must be in ISO format"
            )
    
    return alert_service.get_all_alerts(
        skip=skip,
        limit=limit,
        estado=estado,
        sensor_id=sensor_id,
        tipo=tipo.value if tipo else None,
        fecha_desde=start_date,
        fecha_hasta=end_date
    )


@router.get("/active", response_model=List[Alert])
def get_active_alerts(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get all active alerts.
    Accessible by all authenticated users.
    """
    return alert_service.get_active_alerts(skip, limit)


@router.get("/by-location", response_model=List[Dict[str, Any]])
def get_alerts_by_location(
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    estado: Optional[AlertStatus] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[str] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha fin (ISO format)"),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get alerts filtered by location (country and/or city).
    Useful for users who want to see alerts in their area.
    Accessible by all authenticated users.
    """
    # Parse dates if provided
    start_date = None
    end_date = None
    
    if fecha_desde:
        try:
            fecha_desde_clean = fecha_desde.replace('Z', '+00:00')
            start_date = datetime.fromisoformat(fecha_desde_clean)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_desde must be in ISO format"
            )
    
    if fecha_hasta:
        try:
            fecha_hasta_clean = fecha_hasta.replace('Z', '+00:00')
            end_date = datetime.fromisoformat(fecha_hasta_clean)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_hasta must be in ISO format"
            )
    
    return alert_service.get_alerts_by_location(
        pais=pais,
        ciudad=ciudad,
        skip=skip,
        limit=limit,
        estado=estado,
        fecha_desde=start_date,
        fecha_hasta=end_date
    )


@router.get("/stats/summary")
def get_alerts_summary(
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    fecha_desde: Optional[str] = Query(None, description="Fecha inicio (ISO format)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha fin (ISO format)"),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get summary statistics of alerts.
    Returns counts by status and type.
    Accessible by all authenticated users.
    """
    # Parse dates if provided
    start_date = None
    end_date = None
    
    if fecha_desde:
        try:
            fecha_desde_clean = fecha_desde.replace('Z', '+00:00')
            start_date = datetime.fromisoformat(fecha_desde_clean)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_desde must be in ISO format"
            )
    
    if fecha_hasta:
        try:
            fecha_hasta_clean = fecha_hasta.replace('Z', '+00:00')
            end_date = datetime.fromisoformat(fecha_hasta_clean)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_hasta must be in ISO format"
            )
    
    # Get alerts based on location filter
    if pais or ciudad:
        alerts = alert_service.get_alerts_by_location(
            pais=pais,
            ciudad=ciudad,
            skip=0,
            limit=1000,  # Get a large sample
            fecha_desde=start_date,
            fecha_hasta=end_date
        )
    else:
        alerts = alert_service.get_all_alerts(
            skip=0,
            limit=1000,
            fecha_desde=start_date,
            fecha_hasta=end_date
        )
    
    # Calculate statistics
    total = len(alerts)
    by_status = {}
    by_type = {}
    
    for alert in alerts:
        # Count by status
        status_key = alert.get("estado") if isinstance(alert, dict) else alert.estado
        by_status[status_key] = by_status.get(status_key, 0) + 1
        
        # Count by type
        type_key = alert.get("tipo") if isinstance(alert, dict) else alert.tipo
        by_type[type_key] = by_type.get(type_key, 0) + 1
    
    return {
        "total": total,
        "por_estado": by_status,
        "por_tipo": by_type,
        "filtros_aplicados": {
            "pais": pais,
            "ciudad": ciudad,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta
        }
    }


@router.get("/{alert_id}", response_model=Alert)
def get_alert(
    alert_id: str,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get alert by ID.
    Accessible by all authenticated users.
    """
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

