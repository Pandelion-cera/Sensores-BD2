from typing import List, Optional
from datetime import datetime
import logging

from app.repositories.alert_rule_repository import AlertRuleRepository
from app.repositories.alert_repository import AlertRepository
from app.models.alert_rule_models import (
    AlertRule,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleStatus,
    LocationScope
)
from app.models.alert_models import AlertCreate, AlertType

logger = logging.getLogger(__name__)


class AlertRuleService:
    """Servicio para gestionar reglas de alertas"""
    
    def __init__(
        self, 
        rule_repo: AlertRuleRepository,
        alert_repo: AlertRepository
    ):
        self.rule_repo = rule_repo
        self.alert_repo = alert_repo
    
    def create_rule(self, rule_data: AlertRuleCreate, created_by: str) -> AlertRule:
        """Crear una nueva regla de alerta"""
        # Validar que al menos una condición esté definida
        if (rule_data.temp_min is None and rule_data.temp_max is None and
            rule_data.humidity_min is None and rule_data.humidity_max is None):
            raise ValueError("Debe definir al menos una condición de temperatura o humedad")
        
        # Validar coherencia de rangos
        if rule_data.temp_min is not None and rule_data.temp_max is not None:
            if rule_data.temp_min > rule_data.temp_max:
                raise ValueError("temp_min no puede ser mayor que temp_max")
        
        if rule_data.humidity_min is not None and rule_data.humidity_max is not None:
            if rule_data.humidity_min > rule_data.humidity_max:
                raise ValueError("humidity_min no puede ser mayor que humidity_max")
        
        # Validar coherencia de fechas
        if rule_data.fecha_inicio and rule_data.fecha_fin:
            if rule_data.fecha_inicio > rule_data.fecha_fin:
                raise ValueError("fecha_inicio no puede ser posterior a fecha_fin")
        
        # Validar campos según scope
        if rule_data.location_scope == LocationScope.CITY and not rule_data.ciudad:
            raise ValueError("Debe especificar 'ciudad' cuando location_scope es 'ciudad'")
        
        if rule_data.location_scope == LocationScope.REGION and not rule_data.region:
            raise ValueError("Debe especificar 'region' cuando location_scope es 'region'")
        
        return self.rule_repo.create(rule_data, created_by)
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Obtener una regla por ID"""
        return self.rule_repo.get_by_id(rule_id)
    
    def get_all_rules(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[AlertRuleStatus] = None,
        pais: Optional[str] = None,
        ciudad: Optional[str] = None
    ) -> List[AlertRule]:
        """Obtener todas las reglas con filtros"""
        return self.rule_repo.get_all(skip, limit, estado, pais, ciudad)
    
    def get_active_rules(self) -> List[AlertRule]:
        """Obtener todas las reglas activas"""
        return self.rule_repo.get_active_rules()
    
    def update_rule(self, rule_id: str, rule_data: AlertRuleUpdate) -> Optional[AlertRule]:
        """Actualizar una regla existente"""
        # Validar que la regla existe
        existing_rule = self.rule_repo.get_by_id(rule_id)
        if not existing_rule:
            return None
        
        # Validar rangos si se están actualizando
        if rule_data.temp_min is not None and rule_data.temp_max is not None:
            if rule_data.temp_min > rule_data.temp_max:
                raise ValueError("temp_min no puede ser mayor que temp_max")
        
        if rule_data.humidity_min is not None and rule_data.humidity_max is not None:
            if rule_data.humidity_min > rule_data.humidity_max:
                raise ValueError("humidity_min no puede ser mayor que humidity_max")
        
        if rule_data.fecha_inicio and rule_data.fecha_fin:
            if rule_data.fecha_inicio > rule_data.fecha_fin:
                raise ValueError("fecha_inicio no puede ser posterior a fecha_fin")
        
        return self.rule_repo.update(rule_id, rule_data)
    
    def activate_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Activar una regla"""
        return self.rule_repo.update_status(rule_id, AlertRuleStatus.ACTIVE)
    
    def deactivate_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Desactivar una regla"""
        return self.rule_repo.update_status(rule_id, AlertRuleStatus.INACTIVE)
    
    def delete_rule(self, rule_id: str) -> bool:
        """Eliminar una regla"""
        return self.rule_repo.delete(rule_id)
    
    def check_measurement_against_rules(
        self,
        sensor_id: str,
        pais: str,
        ciudad: Optional[str],
        region: Optional[str],
        temperatura: Optional[float],
        humedad: Optional[float],
        fecha: Optional[datetime] = None
    ) -> List[dict]:
        """
        Verificar si una medición viola alguna regla activa
        y generar alertas correspondientes
        """
        if fecha is None:
            fecha = datetime.utcnow()
        
        # Obtener reglas aplicables para esta ubicación y fecha
        applicable_rules = self.rule_repo.get_applicable_rules(
            pais=pais,
            ciudad=ciudad,
            region=region,
            fecha=fecha
        )
        
        triggered_alerts = []
        
        for rule in applicable_rules:
            logger.debug(
                "Evaluating rule %s for sensor %s (temp=%s, hum=%s)",
                rule.id,
                sensor_id,
                temperatura,
                humedad
            )
            alert_triggered = False
            alert_description = []
            
            # Verificar condiciones de temperatura
            if temperatura is not None:
                if rule.temp_min is not None and temperatura < rule.temp_min:
                    alert_triggered = True
                    alert_description.append(
                        f"Temperatura {temperatura}°C por debajo del mínimo ({rule.temp_min}°C)"
                    )
                
                if rule.temp_max is not None and temperatura > rule.temp_max:
                    alert_triggered = True
                    alert_description.append(
                        f"Temperatura {temperatura}°C por encima del máximo ({rule.temp_max}°C)"
                    )
            
            # Verificar condiciones de humedad
            if humedad is not None:
                if rule.humidity_min is not None and humedad < rule.humidity_min:
                    alert_triggered = True
                    alert_description.append(
                        f"Humedad {humedad}% por debajo del mínimo ({rule.humidity_min}%)"
                    )
                
                if rule.humidity_max is not None and humedad > rule.humidity_max:
                    alert_triggered = True
                    alert_description.append(
                        f"Humedad {humedad}% por encima del máximo ({rule.humidity_max}%)"
                    )
            
            # Si se disparó la regla, crear alerta
            if alert_triggered:
                location_str = self._format_location(rule)
                full_description = (
                    f"{rule.nombre} - {rule.descripcion}. "
                    f"Ubicación: {location_str}. "
                    f"{' | '.join(alert_description)}"
                )
                
                alert = self.alert_repo.create(AlertCreate(
                    tipo=AlertType.THRESHOLD,
                    sensor_id=sensor_id,
                    user_id=rule.user_id,
                    descripcion=full_description,
                    valor=temperatura if temperatura is not None else humedad,
                    umbral=None,  # En este caso no hay un umbral único
                    rule_id=rule.id,
                    rule_name=rule.nombre,
                    prioridad=rule.prioridad
                ))
                logger.info(
                    "Alert triggered for user=%s rule=%s sensor=%s description=%s",
                    rule.user_id,
                    rule.id,
                    sensor_id,
                    full_description
                )
                
                triggered_alerts.append({
                    "rule_id": rule.id,
                    "rule_name": rule.nombre,
                    "alert": alert,
                    "prioridad": rule.prioridad
                })
        
        return triggered_alerts
    
    def _format_location(self, rule: AlertRule) -> str:
        """Formatear la ubicación de una regla para mostrar"""
        if rule.location_scope == LocationScope.CITY:
            return f"{rule.ciudad}, {rule.pais}"
        elif rule.location_scope == LocationScope.REGION:
            return f"{rule.region}, {rule.pais}"
        else:
            return rule.pais
    
    def get_rules_summary(self) -> dict:
        """Obtener resumen de reglas"""
        total = self.rule_repo.count()
        active = self.rule_repo.count(AlertRuleStatus.ACTIVE)
        inactive = self.rule_repo.count(AlertRuleStatus.INACTIVE)
        
        return {
            "total": total,
            "activas": active,
            "inactivas": inactive
        }
