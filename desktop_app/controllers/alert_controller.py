"""
Controller encapsulating alert retrieval and mutation flows.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from desktop_app.core.database import db_manager
from desktop_app.models.alert_models import Alert, AlertStatus
from desktop_app.models.process_models import Process
from desktop_app.models.sensor_models import Sensor
from desktop_app.models.user_models import User
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.repositories.process_repository import ProcessRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.alert_service import AlertService


class AlertController:
    """Exposes alert-centric use cases to the presentation layer."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        redis_client = db_manager.get_redis_client()
        neo4j_driver = db_manager.get_neo4j_driver()

        self._alert_repo = AlertRepository(mongo_db, redis_client)
        self._alert_service = AlertService(self._alert_repo)
        self._sensor_repo = SensorRepository(mongo_db)
        self._process_repo = ProcessRepository(mongo_db, neo4j_driver)
        self._user_repo = UserRepository(mongo_db, neo4j_driver)

    def list_alerts(
        self,
        *,
        skip: int = 0,
        limit: int = 1000,
        estado: Optional[AlertStatus] = None,
        tipo: Optional[str] = None,
        sensor_id: Optional[str] = None,
        user_id: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> List[Alert]:
        """Return alerts filtered by the requested criteria."""
        return self._alert_service.get_all_alerts(
            skip=skip,
            limit=limit,
            estado=estado,
            tipo=tipo,
            sensor_id=sensor_id,
            user_id=user_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Fetch a single alert by identifier."""
        return self._alert_service.get_alert(alert_id)

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as finished."""
        return self._alert_repo.update_status(alert_id, AlertStatus.FINISHED)

    # Related entities -----------------------------------------------------------
    def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Return sensor details associated with an alert."""
        if not sensor_id:
            return None
        return self._sensor_repo.get_by_sensor_id(sensor_id)

    def get_process(self, process_id: str) -> Optional[Process]:
        """Return process details associated with an alert."""
        if not process_id:
            return None
        return self._process_repo.get_process(process_id)

    def get_user(self, user_id: str) -> Optional[User]:
        """Return user details for auditing alert ownership."""
        if not user_id:
            return None
        return self._user_repo.get_by_id(user_id)


