"""
Controller for process execution, requests and scheduling workflows.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from desktop_app.core.config import settings
from desktop_app.core.database import db_manager
from desktop_app.models.process_models import (
    Execution,
    Process,
    ProcessRequest,
    ProcessRequestCreate,
    ProcessStatus,
)
from desktop_app.models.scheduled_process_models import (
    ScheduledProcess,
    ScheduledProcessCreate,
    ScheduledProcessUpdate,
)
from desktop_app.repositories.account_repository import AccountRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.repositories.alert_rule_repository import AlertRuleRepository
from desktop_app.repositories.invoice_repository import InvoiceRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.process_repository import ProcessRepository
from desktop_app.repositories.scheduled_process_repository import ScheduledProcessRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.account_service import AccountService
from desktop_app.services.alert_rule_service import AlertRuleService
from desktop_app.services.alert_service import AlertService
from desktop_app.services.process_service import ProcessService
from desktop_app.services.scheduled_process_service import ScheduledProcessService


class ProcessController:
    """Coordinate process-related use cases required by the UI."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        cassandra_session = db_manager.get_cassandra_session()
        neo4j_driver = db_manager.get_neo4j_driver()
        redis_client = db_manager.get_redis_client()

        self._process_repo = ProcessRepository(mongo_db, neo4j_driver)
        self._measurement_repo = MeasurementRepository(
            cassandra_session,
            settings.CASSANDRA_KEYSPACE,
        )
        self._sensor_repo = SensorRepository(mongo_db)
        self._user_repo = UserRepository(mongo_db, neo4j_driver)
        self._invoice_repo = InvoiceRepository(mongo_db)
        self._account_repo = AccountRepository(mongo_db)
        self._account_service = AccountService(self._account_repo)
        self._alert_repo = AlertRepository(mongo_db, redis_client)
        self._alert_service = AlertService(self._alert_repo)
        self._alert_rule_repo = AlertRuleRepository(mongo_db)
        self._alert_rule_service = AlertRuleService(self._alert_rule_repo, self._alert_repo)

        self._process_service = ProcessService(
            self._process_repo,
            self._measurement_repo,
            self._sensor_repo,
            self._user_repo,
            self._invoice_repo,
            self._account_service,
            self._alert_service,
            self._alert_rule_service,
        )

        self._schedule_repo = ScheduledProcessRepository(mongo_db)
        self._schedule_service = ScheduledProcessService(self._schedule_repo)

    # Processes ------------------------------------------------------------------
    def list_processes(self, *, skip: int = 0, limit: int = 100) -> List[Process]:
        """Return catalogued processes."""
        return self._process_service.get_all_processes(skip=skip, limit=limit)

    def get_process(self, process_id: str) -> Optional[Process]:
        """Fetch process details."""
        return self._process_service.get_process(process_id)

    # Requests -------------------------------------------------------------------
    def request_process(self, user_id: str, payload: ProcessRequestCreate) -> ProcessRequest:
        """Create a new process request on behalf of a user."""
        return self._process_service.request_process(user_id, payload)

    def get_user_requests(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProcessRequest]:
        """Return process requests submitted by the user."""
        return self._process_service.get_user_requests(user_id, skip=skip, limit=limit)

    def get_request(self, request_id: str) -> Optional[ProcessRequest]:
        """Fetch a specific process request."""
        return self._process_service.get_request(request_id)

    def execute_request(self, request_id: str) -> Execution:
        """Execute a pending process request and return its execution metadata."""
        return self._process_service.execute_process(request_id)

    def get_execution(self, request_id: str) -> Optional[Execution]:
        """Return the execution record for the given request."""
        return self._process_service.get_execution(request_id)

    def list_all_requests(
        self,
        *,
        status: Optional[ProcessStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, object]]:
        """Return all requests, typically for administrative views."""
        return self._process_service.get_all_requests(status=status, skip=skip, limit=limit)

    # Scheduling -----------------------------------------------------------------
    def list_schedules(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ScheduledProcess]:
        """Return scheduled processes for a user."""
        return self._schedule_service.get_user_schedules(user_id, skip=skip, limit=limit)

    def create_schedule(
        self,
        user_id: str,
        payload: ScheduledProcessCreate,
    ) -> ScheduledProcess:
        """Persist a new scheduled process."""
        return self._schedule_service.create_schedule(user_id, payload)

    def update_schedule(
        self,
        schedule_id: str,
        payload: ScheduledProcessUpdate,
    ) -> ScheduledProcess:
        """Update an existing scheduled process."""
        return self._schedule_service.update_schedule(schedule_id, payload)

    def pause_schedule(self, schedule_id: str) -> ScheduledProcess:
        """Pause a scheduled process."""
        return self._schedule_service.pause_schedule(schedule_id)

    def resume_schedule(self, schedule_id: str) -> ScheduledProcess:
        """Resume a scheduled process."""
        return self._schedule_service.resume_schedule(schedule_id)

    def delete_schedule(self, schedule_id: str) -> bool:
        """Remove a scheduled process."""
        self._schedule_service.delete_schedule(schedule_id)
        return True


