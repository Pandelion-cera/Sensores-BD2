"""
Dashboard controller aggregating high-level metrics for the landing view.
"""
from __future__ import annotations

from typing import Dict
from datetime import datetime
from desktop_app.core.database import db_manager
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.core.config import settings

class DashboardController:
    """Expose aggregate metrics consumed by the dashboard widget."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        redis_client = db_manager.get_redis_client()
        cassandra_session = db_manager.get_cassandra_session()

        self._sensor_repo = SensorRepository(mongo_db)
        self._alert_repo = AlertRepository(mongo_db, redis_client)
        self._measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)

    def get_overview(self, sensor_limit: int = 1000, alert_limit: int = 1000) -> Dict[str, int]:
        """
        Return aggregated counts for sensors and active alerts.

        Args:
            sensor_limit: Maximum number of sensors to fetch.
            alert_limit: Maximum number of alerts to inspect.
        """
        sensors = self._sensor_repo.get_all(limit=sensor_limit)
        active_alerts = self._alert_repo.get_active_alerts(limit=alert_limit)

        total_sensors = len(sensors)
        active_sensors = len([sensor for sensor in sensors if sensor.estado == "activo"])

        return {
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "active_alerts": len(active_alerts),
        }


    def get_amount_of_measurements_by_date(self, start_date: datetime, end_date: datetime) -> int:
        """Get amount of measurements by date"""
        return self._measurement_repo.get_amount_of_measurements_by_date(start_date, end_date)
