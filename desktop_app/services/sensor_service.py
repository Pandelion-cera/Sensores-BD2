from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.alert_rule_repository import AlertRuleRepository
from desktop_app.models.sensor_models import Sensor, SensorCreate, SensorUpdate, SensorStatus
from desktop_app.models.measurement_models import MeasurementCreate, MeasurementResponse
from desktop_app.services.alert_service import AlertService
from desktop_app.services.alert_rule_service import AlertRuleService


class SensorService:
    def __init__(
        self,
        sensor_repo: SensorRepository,
        measurement_repo: MeasurementRepository,
        alert_service: AlertService,
        alert_rule_service: Optional[AlertRuleService] = None
    ):
        self.sensor_repo = sensor_repo
        self.measurement_repo = measurement_repo
        self.alert_service = alert_service
        self.alert_rule_service = alert_rule_service
    
    def create_sensor(self, sensor_data: SensorCreate) -> Sensor:
        """Create a new sensor"""
        return self.sensor_repo.create(sensor_data)
    
    def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Get sensor by ID (tries both _id and sensor_id)"""
        sensor = self.sensor_repo.get_by_id(sensor_id)
        if not sensor:
            sensor = self.sensor_repo.get_by_sensor_id(sensor_id)
        return sensor
    
    def get_all_sensors(
        self,
        skip: int = 0,
        limit: int = 100,
        pais: Optional[str] = None,
        ciudad: Optional[str] = None,
        estado: Optional[SensorStatus] = None
    ) -> List[Sensor]:
        """Get all sensors with filters"""
        return self.sensor_repo.get_all(skip, limit, pais, ciudad, estado)
    
    def update_sensor(self, sensor_id: str, sensor_update: SensorUpdate) -> Optional[Sensor]:
        """Update sensor"""
        return self.sensor_repo.update(sensor_id, sensor_update)
    
    def delete_sensor(self, sensor_id: str) -> bool:
        """Delete sensor"""
        return self.sensor_repo.delete(sensor_id)
    
    def register_measurement(
        self,
        sensor_id: str,
        measurement_data: MeasurementCreate
    ) -> Dict[str, Any]:
        """Register a new measurement for a sensor"""
        # Get sensor info - try by _id first, then by sensor_id (UUID)
        sensor = self.sensor_repo.get_by_id(sensor_id)
        if not sensor:
            sensor = self.sensor_repo.get_by_sensor_id(sensor_id)
        
        if not sensor:
            raise ValueError("Sensor not found")
        
        if sensor.estado != SensorStatus.ACTIVE:
            raise ValueError("Sensor is not active")
        
        # Save measurement to Cassandra
        measurement = self.measurement_repo.create(
            sensor.sensor_id,
            measurement_data,
            sensor.ciudad,
            sensor.pais
        )
        
        # Check for alert conditions (legacy thresholds from config)
        self.alert_service.check_measurement_thresholds(
            sensor,
            measurement_data.temperature,
            measurement_data.humidity
        )
        
        # Check against configured alert rules if service is available
        triggered_rules = []
        if self.alert_rule_service:
            try:
                triggered_rules = self.alert_rule_service.check_measurement_against_rules(
                    sensor_id=sensor.sensor_id,
                    pais=sensor.pais,
                    ciudad=sensor.ciudad,
                    region=None,  # Could be added to sensor model if needed
                    temperatura=measurement_data.temperature,
                    humedad=measurement_data.humidity,
                    fecha=measurement.timestamp
                )
            except Exception as e:
                print(f"Error checking alert rules: {e}")
        
        result = {
            "sensor_id": sensor.sensor_id,
            "timestamp": measurement.timestamp,
            "temperature": measurement.temperature,
            "humidity": measurement.humidity
        }
        
        # Add triggered rules info if any
        if triggered_rules:
            result["triggered_alerts"] = [
                {
                    "rule_name": tr["rule_name"],
                    "prioridad": tr["prioridad"],
                    "alert_id": tr["alert"].id
                }
                for tr in triggered_rules
            ]
        
        return result
    
    def get_sensor_measurements(
        self,
        sensor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get measurements for a sensor"""
        # Try to get sensor by MongoDB _id first, then by sensor_id (UUID)
        sensor = self.sensor_repo.get_by_id(sensor_id)
        if not sensor:
            # If not found by _id, try by sensor_id (UUID)
            sensor = self.sensor_repo.get_by_sensor_id(sensor_id)
        
        if not sensor:
            raise ValueError("Sensor not found")
        
        # Default to last 24 hours
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        measurements = self.measurement_repo.get_by_sensor(
            sensor.sensor_id,
            start_date,
            end_date
        )
        
        return [
            {
                "sensor_id": m.sensor_id,
                "timestamp": m.timestamp,
                "temperatura": m.temperature,
                "humedad": m.humidity,
                "ciudad": sensor.ciudad,
                "pais": sensor.pais
            }
            for m in measurements
        ]
    
    def get_location_measurements(
        self,
        pais: str,
        ciudad: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get measurements for a location"""
        # Default to last 24 hours
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        measurements = self.measurement_repo.get_by_location(
            pais,
            ciudad,
            start_date,
            end_date
        )
        
        # Map fields to Spanish
        return [
            {
                "sensor_id": m["sensor_id"],
                "timestamp": m["timestamp"],
                "temperatura": m.get("temperature"),
                "humedad": m.get("humidity"),
                "ciudad": m.get("ciudad"),
                "pais": m.get("pais")
            }
            for m in measurements
        ]
    
    def get_location_stats(
        self,
        pais: str,
        ciudad: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistics for a location"""
        # Default to last 24 hours
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        stats = self.measurement_repo.get_stats_by_location(
            pais,
            ciudad,
            start_date,
            end_date
        )
        
        # Flatten the stats structure to match frontend expectations
        if "temperatura" in stats and isinstance(stats["temperatura"], dict):
            stats["temperatura_max"] = stats["temperatura"].get("max")
            stats["temperatura_min"] = stats["temperatura"].get("min")
            stats["temperatura_avg"] = stats["temperatura"].get("avg")
            del stats["temperatura"]
        
        if "humedad" in stats and isinstance(stats["humedad"], dict):
            stats["humedad_max"] = stats["humedad"].get("max")
            stats["humedad_min"] = stats["humedad"].get("min")
            stats["humedad_avg"] = stats["humedad"].get("avg")
            del stats["humedad"]
        
        # Rename count to total_mediciones
        if "count" in stats:
            stats["total_mediciones"] = stats["count"]
            del stats["count"]
        
        return stats
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        sensor_counts = self.sensor_repo.count_by_status()
        countries = self.sensor_repo.get_countries()
        
        return {
            "total_sensors": sum(sensor_counts.values()),
            "sensor_status": sensor_counts,
            "countries": countries,
            "total_countries": len(countries)
        }

