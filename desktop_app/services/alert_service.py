from typing import List, Optional, Dict, Any
from datetime import datetime

from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.models.alert_models import Alert, AlertCreate, AlertStatus, AlertType
from desktop_app.models.sensor_models import Sensor
from desktop_app.core.config import settings


class AlertService:
    def __init__(self, alert_repo: AlertRepository):
        self.alert_repo = alert_repo
    
    def create_alert(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert"""
        return self.alert_repo.create(alert_data)
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        return self.alert_repo.get_by_id(alert_id)
    
    def get_all_alerts(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[AlertStatus] = None,
        sensor_id: Optional[str] = None,
        tipo: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Alert]:
        """Get all alerts with filters"""
        return self.alert_repo.get_all(skip, limit, estado, sensor_id, tipo, fecha_desde, fecha_hasta)
    
    def get_alerts_by_location(
        self,
        pais: Optional[str] = None,
        ciudad: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[AlertStatus] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get alerts filtered by location"""
        return self.alert_repo.get_by_location(
            pais=pais,
            ciudad=ciudad,
            skip=skip,
            limit=limit,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
    
    def get_active_alerts(self, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get all active alerts"""
        return self.alert_repo.get_active_alerts(skip, limit)
    
    def update_alert_status(self, alert_id: str, status: AlertStatus) -> Optional[Alert]:
        """Update alert status"""
        return self.alert_repo.update_status(alert_id, status)
    
    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Mark alert as resolved"""
        return self.update_alert_status(alert_id, AlertStatus.RESOLVED)
    
    def acknowledge_alert(self, alert_id: str) -> Optional[Alert]:
        """Mark alert as acknowledged"""
        return self.update_alert_status(alert_id, AlertStatus.ACKNOWLEDGED)
    
    def check_measurement_thresholds(
        self,
        sensor: Sensor,
        temperature: Optional[float],
        humidity: Optional[float]
    ) -> List[Alert]:
        """Check if measurement values exceed thresholds and create alerts"""
        alerts = []
        
        # Check temperature thresholds
        if temperature is not None:
            if temperature < settings.TEMP_MIN_THRESHOLD:
                alert = self.create_alert(AlertCreate(
                    tipo=AlertType.THRESHOLD,
                    sensor_id=sensor.sensor_id,
                    descripcion=f"Temperatura muy baja detectada en {sensor.ciudad}, {sensor.pais}",
                    valor=temperature,
                    umbral=settings.TEMP_MIN_THRESHOLD
                ))
                alerts.append(alert)
            
            elif temperature > settings.TEMP_MAX_THRESHOLD:
                alert = self.create_alert(AlertCreate(
                    tipo=AlertType.THRESHOLD,
                    sensor_id=sensor.sensor_id,
                    descripcion=f"Temperatura muy alta detectada en {sensor.ciudad}, {sensor.pais}",
                    valor=temperature,
                    umbral=settings.TEMP_MAX_THRESHOLD
                ))
                alerts.append(alert)
        
        # Check humidity thresholds
        if humidity is not None:
            if humidity < settings.HUMIDITY_MIN_THRESHOLD:
                alert = self.create_alert(AlertCreate(
                    tipo=AlertType.THRESHOLD,
                    sensor_id=sensor.sensor_id,
                    descripcion=f"Humedad muy baja detectada en {sensor.ciudad}, {sensor.pais}",
                    valor=humidity,
                    umbral=settings.HUMIDITY_MIN_THRESHOLD
                ))
                alerts.append(alert)
            
            elif humidity > settings.HUMIDITY_MAX_THRESHOLD:
                alert = self.create_alert(AlertCreate(
                    tipo=AlertType.THRESHOLD,
                    sensor_id=sensor.sensor_id,
                    descripcion=f"Humedad muy alta detectada en {sensor.ciudad}, {sensor.pais}",
                    valor=humidity,
                    umbral=settings.HUMIDITY_MAX_THRESHOLD
                ))
                alerts.append(alert)
        
        return alerts
    
    def check_sensor_health(self, sensor: Sensor) -> Optional[Alert]:
        """Check sensor health and create alert if needed"""
        if sensor.estado == "falla":
            return self.create_alert(AlertCreate(
                tipo=AlertType.SENSOR_FAILURE,
                sensor_id=sensor.sensor_id,
                descripcion=f"Sensor {sensor.nombre} en {sensor.ciudad}, {sensor.pais} reporta falla"
            ))
        
        return None
    
    def read_alert_stream(self, count: int = 10, last_id: str = "0") -> List[Dict[str, Any]]:
        """Read alerts from Redis Stream for real-time notifications"""
        return self.alert_repo.read_alert_stream(count, last_id)

