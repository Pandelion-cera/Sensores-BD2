"""
Controller encapsulating alert rule management.
"""
from __future__ import annotations

from typing import List, Optional

from desktop_app.models.alert_rule_models import (
    AlertRule,
    AlertRuleCreate,
    AlertRuleStatus,
    AlertRuleUpdate,
)
from desktop_app.services.factories import get_alert_rule_service


class AlertRuleController:
    """Provide CRUD functionality for alert rules."""

    def __init__(self) -> None:
        self._rule_service = get_alert_rule_service()

    def list_rules(
        self,
        *,
        skip: int = 0,
        limit: int = 1000,
        estado: Optional[AlertRuleStatus] = None,
        pais: Optional[str] = None,
        ciudad: Optional[str] = None,
    ) -> List[AlertRule]:
        """Return alert rules filtered by optional criteria."""
        return self._rule_service.get_all_rules(
            skip=skip,
            limit=limit,
            estado=estado,
            pais=pais,
            ciudad=ciudad,
        )

    def create_rule(self, payload: AlertRuleCreate, owner_email: str) -> AlertRule:
        """Create a new alert rule tied to the provided owner email."""
        return self._rule_service.create_rule(payload, owner_email)

    def update_rule(self, rule_id: str, payload: AlertRuleUpdate) -> AlertRule:
        """Update an existing rule by identifier."""
        return self._rule_service.update_rule(rule_id, payload)

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule, returning True if it existed."""
        return self._rule_service.delete_rule(rule_id)

    def activate_rule(self, rule_id: str) -> AlertRule:
        """Set a rule status to active."""
        return self._rule_service.activate_rule(rule_id)

    def deactivate_rule(self, rule_id: str) -> AlertRule:
        """Set a rule status to inactive."""
        return self._rule_service.deactivate_rule(rule_id)


