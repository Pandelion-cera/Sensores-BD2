"""
Controller encapsulating alert retrieval and mutation flows.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from desktop_app.models.alert_models import Alert, AlertStatus
from desktop_app.models.process_models import Process
from desktop_app.models.sensor_models import Sensor
from desktop_app.models.user_models import User
from desktop_app.services.factories import (
    get_alert_service,
    get_process_service,
    get_sensor_service,
    get_user_service,
)


class AlertController:
    """Exposes alert-centric use cases to the presentation layer."""

    def __init__(self) -> None:
        self._alert_service = get_alert_service()
        self._sensor_service = get_sensor_service()
        self._process_service = get_process_service()
        self._user_service = get_user_service()

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
        return self._alert_service.update_alert_status(alert_id, AlertStatus.FINISHED) is not None

    # Related entities -----------------------------------------------------------
    def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Return sensor details associated with an alert."""
        if not sensor_id:
            return None
        return self._sensor_service.get_sensor(sensor_id)

    def get_process(self, process_id: str) -> Optional[Process]:
        """Return process details associated with an alert."""
        if not process_id:
            return None
        return self._process_service.get_process(process_id)

    def get_user(self, user_id: str) -> Optional[User]:
        """Return user details for auditing alert ownership."""
        if not user_id:
            return None
        return self._user_service.get_user(user_id)


