from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.repositories.sensor_repository import SensorRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.models.sensor_models import Sensor, SensorCreate, SensorUpdate, SensorStatus
from app.models.measurement_models import MeasurementCreate, MeasurementResponse
from app.services.alert_service import AlertService


class SensorService:
    def __init__(
        self,
        sensor_repo: SensorRepository,
        measurement_repo: MeasurementRepository,
        alert_service: AlertService
    ):
        self.sensor_repo = sensor_repo
        self.measurement_repo = measurement_repo
        self.alert_service = alert_service
    
    def create_sensor(self, sensor_data: SensorCreate) -> Sensor:
        """Create a new sensor"""
        return self.sensor_repo.create(sensor_data)
    
    def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Get sensor by ID"""
        return self.sensor_repo.get_by_id(sensor_id)
    
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
        # Get sensor info
        sensor = self.sensor_repo.get_by_id(sensor_id)
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
        
        # Check for alert conditions
        self.alert_service.check_measurement_thresholds(
            sensor,
            measurement_data.temperature,
            measurement_data.humidity
        )
        
        return {
            "sensor_id": sensor.sensor_id,
            "timestamp": measurement.timestamp,
            "temperature": measurement.temperature,
            "humidity": measurement.humidity
        }
    
    def get_sensor_measurements(
        self,
        sensor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MeasurementResponse]:
        """Get measurements for a sensor"""
        sensor = self.sensor_repo.get_by_id(sensor_id)
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
            MeasurementResponse(
                sensor_id=m.sensor_id,
                timestamp=m.timestamp,
                temperature=m.temperature,
                humidity=m.humidity,
                ciudad=sensor.ciudad,
                pais=sensor.pais
            )
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
        
        return self.measurement_repo.get_by_location(
            pais,
            ciudad,
            start_date,
            end_date
        )
    
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
        
        return self.measurement_repo.get_stats_by_location(
            pais,
            ciudad,
            start_date,
            end_date
        )
    
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

