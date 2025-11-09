"""
Maintenance controller to mediate between UI and services.
"""
from __future__ import annotations

from typing import List, Optional

from desktop_app.core.database import db_manager
from desktop_app.models.maintenance_models import (
    MaintenanceRecord,
    MaintenanceRecordCreate,
    MaintenanceRecordUpdate,
)
from desktop_app.models.sensor_models import Sensor
from desktop_app.models.user_models import User
from desktop_app.repositories.maintenance_repository import MaintenanceRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.maintenance_service import MaintenanceService


class MaintenanceController:
    """Expose maintenance record CRUD operations."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        neo4j_driver = db_manager.get_neo4j_driver()

        self._maintenance_repo = MaintenanceRepository(mongo_db)
        self._sensor_repo = SensorRepository(mongo_db)
        self._user_repo = UserRepository(mongo_db, neo4j_driver)

        self._maintenance_service = MaintenanceService(
            self._maintenance_repo,
            self._sensor_repo,
            self._user_repo,
        )

    def list_records(self, *, skip: int = 0, limit: int = 100) -> List[MaintenanceRecord]:
        """Return maintenance records."""
        return self._maintenance_service.get_all(skip=skip, limit=limit)

    def create_record(self, payload: MaintenanceRecordCreate) -> MaintenanceRecord:
        """Create a new maintenance record."""
        return self._maintenance_service.create_record(payload)

    def update_record(self, record_id: str, payload: MaintenanceRecordUpdate) -> MaintenanceRecord:
        """Update an existing record."""
        return self._maintenance_service.update_record(record_id, payload)

    def delete_record(self, record_id: str) -> bool:
        """Remove a record."""
        self._maintenance_service.delete_record(record_id)
        return True

    def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Return sensor details for display."""
        if not sensor_id:
            return None
        return self._sensor_repo.get_by_id(sensor_id)

    def get_user(self, user_id: str) -> Optional[User]:
        """Return user details for display."""
        if not user_id:
            return None
        return self._user_repo.get_by_id(user_id)


