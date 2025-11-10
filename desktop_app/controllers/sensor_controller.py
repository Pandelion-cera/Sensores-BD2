"""
Controller exposing sensor and measurement operations to the UI layer.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from desktop_app.models.measurement_models import MeasurementCreate
from desktop_app.models.sensor_models import (
    Sensor,
    SensorCreate,
    SensorStatus,
    SensorUpdate,
)
from desktop_app.services.factories import get_sensor_service


class SensorController:
    """Coordinate sensor CRUD and measurement workflows."""

    def __init__(self) -> None:
        self._sensor_service = get_sensor_service()

    # Sensor CRUD ----------------------------------------------------------------
    def list_sensors(
        self,
        *,
        skip: int = 0,
        limit: int = 1000,
        pais: Optional[str] = None,
        ciudad: Optional[str] = None,
        estado: Optional[SensorStatus] = None,
    ) -> List[Sensor]:
        """Return sensors filtered by optional criteria."""
        return self._sensor_service.get_all_sensors(
            skip=skip,
            limit=limit,
            pais=pais,
            ciudad=ciudad,
            estado=estado,
        )

    def create_sensor(self, data: SensorCreate) -> Sensor:
        """Create a new sensor."""
        return self._sensor_service.create_sensor(data)

    def update_sensor(self, sensor_id: str, payload: SensorUpdate) -> Sensor:
        """Update an existing sensor."""
        return self._sensor_service.update_sensor(sensor_id, payload)

    def delete_sensor(self, sensor_id: str) -> bool:
        """Delete a sensor by identifier."""
        return self._sensor_service.delete_sensor(sensor_id)

    # Measurements ----------------------------------------------------------------
    def get_sensor_measurements(
        self,
        sensor_id: str,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Return measurements for a specific sensor."""
        return self._sensor_service.get_sensor_measurements(
            sensor_id=sensor_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_location_measurements(
        self,
        *,
        pais: str,
        ciudad: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Return measurements filtered by location and timeframe."""
        return self._sensor_service.get_location_measurements(
            pais=pais,
            ciudad=ciudad,
            start_date=start_date,
            end_date=end_date,
        )

    def register_measurement(
        self,
        sensor_id: str,
        payload: MeasurementCreate,
    ) -> Dict[str, Any]:
        """Persist a measurement and forward any triggered alerts."""
        return self._sensor_service.register_measurement(sensor_id, payload)


