"""
Maintenance controller to mediate between UI and services.
"""
from __future__ import annotations

from typing import List, Optional

from desktop_app.models.maintenance_models import (
    MaintenanceRecord,
    MaintenanceRecordCreate,
    MaintenanceRecordUpdate,
)
from desktop_app.models.sensor_models import Sensor
from desktop_app.models.user_models import User
from desktop_app.services.factories import (
    get_maintenance_service,
    get_sensor_service,
    get_user_service,
)


class MaintenanceController:
    """Expose maintenance record CRUD operations."""

    def __init__(self) -> None:
        self._maintenance_service = get_maintenance_service()
        self._sensor_service = get_sensor_service()
        self._user_service = get_user_service()

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
        return self._sensor_service.get_sensor(sensor_id)

    def get_user(self, user_id: str) -> Optional[User]:
        """Return user details for display."""
        if not user_id:
            return None
        return self._user_service.get_user(user_id)


