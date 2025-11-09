"""
Controller encapsulating alert rule management.
"""
from __future__ import annotations

from typing import List, Optional

from desktop_app.core.database import db_manager
from desktop_app.models.alert_rule_models import (
    AlertRule,
    AlertRuleCreate,
    AlertRuleStatus,
    AlertRuleUpdate,
)
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.repositories.alert_rule_repository import AlertRuleRepository
from desktop_app.services.alert_rule_service import AlertRuleService


class AlertRuleController:
    """Provide CRUD functionality for alert rules."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        redis_client = db_manager.get_redis_client()

        self._rule_repo = AlertRuleRepository(mongo_db)
        self._alert_repo = AlertRepository(mongo_db, redis_client)
        self._rule_service = AlertRuleService(self._rule_repo, self._alert_repo)

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


