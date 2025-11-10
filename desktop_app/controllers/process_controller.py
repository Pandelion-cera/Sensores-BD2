"""
Controller for process execution, requests and scheduling workflows.
"""
from __future__ import annotations

from typing import Dict, List, Optional

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
from desktop_app.services.factories import (
    get_process_service,
    get_scheduled_process_service,
)


class ProcessController:
    """Coordinate process-related use cases required by the UI."""

    def __init__(self) -> None:
        self._process_service = get_process_service()
        self._schedule_service = get_scheduled_process_service()

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


