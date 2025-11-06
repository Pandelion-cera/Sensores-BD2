from typing import List, Optional
from datetime import datetime

from desktop_app.repositories.maintenance_repository import MaintenanceRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.models.maintenance_models import (
    MaintenanceRecord, MaintenanceRecordCreate, MaintenanceRecordUpdate
)


class MaintenanceService:
    """Service for maintenance/control operations"""
    
    def __init__(
        self,
        maintenance_repo: MaintenanceRepository,
        sensor_repo: SensorRepository,
        user_repo: UserRepository
    ):
        self.maintenance_repo = maintenance_repo
        self.sensor_repo = sensor_repo
        self.user_repo = user_repo
    
    def create_record(self, record_data: MaintenanceRecordCreate) -> MaintenanceRecord:
        """Create a new maintenance record"""
        # Verify sensor exists
        sensor = self.sensor_repo.get_by_id(record_data.sensor_id)
        if not sensor:
            raise ValueError("Sensor not found")
        
        # Verify technician exists
        tecnico = self.user_repo.get_by_id(record_data.tecnico_id)
        if not tecnico:
            raise ValueError("Technician not found")
        
        return self.maintenance_repo.create(record_data)
    
    def get_record(self, record_id: str) -> Optional[MaintenanceRecord]:
        """Get maintenance record by ID"""
        return self.maintenance_repo.get_by_id(record_id)
    
    def get_by_sensor(self, sensor_id: str, skip: int = 0, limit: int = 100) -> List[MaintenanceRecord]:
        """Get all maintenance records for a sensor"""
        return self.maintenance_repo.get_by_sensor(sensor_id, skip, limit)
    
    def get_by_tecnico(self, tecnico_id: str, skip: int = 0, limit: int = 100) -> List[MaintenanceRecord]:
        """Get all maintenance records by a technician"""
        return self.maintenance_repo.get_by_tecnico(tecnico_id, skip, limit)
    
    def get_latest_by_sensor(self, sensor_id: str) -> Optional[MaintenanceRecord]:
        """Get the latest maintenance record for a sensor"""
        return self.maintenance_repo.get_latest_by_sensor(sensor_id)
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[MaintenanceRecord]:
        """Get all maintenance records"""
        return self.maintenance_repo.get_all(skip, limit)
    
    def update_record(self, record_id: str, update_data: MaintenanceRecordUpdate) -> bool:
        """Update a maintenance record"""
        return self.maintenance_repo.update(record_id, update_data)
    
    def delete_record(self, record_id: str) -> bool:
        """Delete a maintenance record"""
        return self.maintenance_repo.delete(record_id)

