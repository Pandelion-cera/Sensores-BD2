"""
Controller for session history and user lookup.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from desktop_app.models.user_models import UserResponse
from desktop_app.services.factories import (
    get_session_service,
    get_user_service,
)


class SessionController:
    """Expose session history utilities for administrative views."""

    def __init__(self) -> None:
        self._session_service = get_session_service()
        self._user_service = get_user_service()

    def list_users(self, *, skip: int = 0, limit: int = 1000) -> List[UserResponse]:
        """Return registered users."""
        return self._user_service.get_all_users(skip=skip, limit=limit)

    def get_user(self, user_id: str):
        """Return a user by identifier."""
        if not user_id:
            return None
        return self._user_service.get_user(user_id)

    def get_session_history(
        self,
        *,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[Dict[str, object]]:
        """Return session history records."""
        return self._session_service.get_session_history(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )


