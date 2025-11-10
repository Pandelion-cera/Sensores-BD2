"""
Dashboard controller aggregating high-level metrics for the landing view.
"""
from __future__ import annotations

from typing import Dict

from desktop_app.services.factories import get_dashboard_service


class DashboardController:
    """Expose aggregate metrics consumed by the dashboard widget."""

    def __init__(self) -> None:
        self._dashboard_service = get_dashboard_service()

    def get_overview(self, sensor_limit: int = 1000, alert_limit: int = 1000) -> Dict[str, int]:
        """
        Return aggregated counts for sensors and active alerts.

        Args:
            sensor_limit: Maximum number of sensors to fetch.
            alert_limit: Maximum number of alerts to inspect.
        """
        return self._dashboard_service.get_overview(
            sensor_limit=sensor_limit,
            alert_limit=alert_limit,
        )


