from __future__ import annotations

from typing import Dict

from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.repositories.sensor_repository import SensorRepository


class DashboardService:
    """Service responsible for aggregating high-level dashboard metrics."""

    def __init__(
        self,
        sensor_repo: SensorRepository,
        alert_repo: AlertRepository,
    ):
        self._sensor_repo = sensor_repo
        self._alert_repo = alert_repo

    def get_overview(
        self,
        *,
        sensor_limit: int = 1000,
        alert_limit: int = 1000,
    ) -> Dict[str, int]:
        sensors = self._sensor_repo.get_all(limit=sensor_limit)
        active_alerts = self._alert_repo.get_active_alerts(limit=alert_limit)

        total_sensors = len(sensors)
        active_sensors = len([sensor for sensor in sensors if sensor.estado == "activo"])

        return {
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "active_alerts": len(active_alerts),
        }


