from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from app.models.alert_rule_models import (
    AlertRule,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertRuleStatus,
    LocationScope
)
from app.services.alert_rule_service import AlertRuleService
from app.core.security import get_current_user_data
from app.core.database import get_mongo_db, get_redis_client
from app.repositories.alert_rule_repository import AlertRuleRepository
from app.repositories.alert_repository import AlertRepository

router = APIRouter()


def get_alert_rule_service(
    mongo_db=Depends(get_mongo_db),
    redis_client=Depends(get_redis_client)
) -> AlertRuleService:
    """Dependencia para obtener el servicio de reglas de alertas"""
    rule_repo = AlertRuleRepository(mongo_db)
    alert_repo = AlertRepository(mongo_db, redis_client)
    return AlertRuleService(rule_repo, alert_repo)


@router.post("", response_model=AlertRule, status_code=status.HTTP_201_CREATED)
def create_alert_rule(
    rule_data: AlertRuleCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Crear una nueva regla de alerta (solo administradores).
    
    Las reglas permiten configurar condiciones automáticas para generar alertas
    basadas en rangos de temperatura/humedad, ubicación y fechas.
    """
    # Solo administradores pueden crear reglas
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear reglas de alertas"
        )
    
    try:
        created_by = current_user.get("email", "unknown")
        rule = rule_service.create_rule(rule_data, created_by)
        return rule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[AlertRule])
def get_alert_rules(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    estado: Optional[AlertRuleStatus] = Query(None, description="Filtrar por estado"),
    pais: Optional[str] = Query(None, description="Filtrar por país"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Obtener todas las reglas de alertas con filtros opcionales.
    Solo administradores pueden ver todas las reglas.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver las reglas de alertas"
        )
    
    return rule_service.get_all_rules(skip, limit, estado, pais, ciudad)


@router.get("/active", response_model=List[AlertRule])
def get_active_alert_rules(
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Obtener todas las reglas activas.
    Solo administradores pueden ver las reglas.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver las reglas de alertas"
        )
    
    return rule_service.get_active_rules()


@router.get("/summary")
def get_rules_summary(
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Obtener resumen estadístico de las reglas.
    Solo administradores.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver el resumen de reglas"
        )
    
    return rule_service.get_rules_summary()


@router.get("/{rule_id}", response_model=AlertRule)
def get_alert_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Obtener una regla específica por ID.
    Solo administradores.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver las reglas de alertas"
        )
    
    rule = rule_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla de alerta no encontrada"
        )
    
    return rule


@router.put("/{rule_id}", response_model=AlertRule)
def update_alert_rule(
    rule_id: str,
    rule_data: AlertRuleUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Actualizar una regla de alerta existente.
    Solo administradores pueden modificar reglas.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden modificar reglas de alertas"
        )
    
    try:
        rule = rule_service.update_rule(rule_id, rule_data)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regla de alerta no encontrada"
            )
        return rule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{rule_id}/activate", response_model=AlertRule)
def activate_alert_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Activar una regla de alerta.
    Solo administradores.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden activar reglas"
        )
    
    rule = rule_service.activate_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla de alerta no encontrada"
        )
    
    return rule


@router.patch("/{rule_id}/deactivate", response_model=AlertRule)
def deactivate_alert_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Desactivar una regla de alerta.
    Solo administradores.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden desactivar reglas"
        )
    
    rule = rule_service.deactivate_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla de alerta no encontrada"
        )
    
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    rule_service: AlertRuleService = Depends(get_alert_rule_service)
):
    """
    Eliminar una regla de alerta.
    Solo administradores pueden eliminar reglas.
    """
    if current_user.get("role") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar reglas de alertas"
        )
    
    success = rule_service.delete_rule(rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla de alerta no encontrada"
        )
    
    return None
