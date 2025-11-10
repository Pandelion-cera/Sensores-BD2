"""
Authentication controller bridging UI widgets with the auth service layer.

This module ensures the UI does not instantiate repositories or services
directly, keeping business logic centralized and easier to test.
"""
from __future__ import annotations

from typing import Any, Dict

from desktop_app.services.factories import get_auth_service
from desktop_app.models.user_models import UserCreate, UserLogin


class AuthController:
    """High-level operations for authentication workflows."""

    def __init__(self) -> None:
        self._auth_service = get_auth_service()

    def login(self, credentials: UserLogin) -> Dict[str, Any]:
        """
        Authenticate a user and return session metadata.

        Raises:
            ValueError: If credentials are invalid.
        """
        return self._auth_service.login(credentials)

    def register(self, payload: UserCreate) -> Dict[str, Any]:
        """
        Register a new user account.

        Raises:
            ValueError: If the payload violates business rules.
        """
        return self._auth_service.register(payload)

    def logout(self, session_id: str) -> None:
        """Invalidate the provided session if it exists."""
        if not session_id:
            return
        self._auth_service.logout(session_id)


