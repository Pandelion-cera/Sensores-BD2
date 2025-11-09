"""
Authentication controller bridging UI widgets with the auth service layer.

This module ensures the UI does not instantiate repositories or services
directly, keeping business logic centralized and easier to test.
"""
from __future__ import annotations

from typing import Any, Dict

from desktop_app.core.database import db_manager
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.repositories.session_repository import SessionRepository
from desktop_app.services.auth_service import AuthService
from desktop_app.models.user_models import UserCreate, UserLogin


class AuthController:
    """High-level operations for authentication workflows."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        redis_client = db_manager.get_redis_client()
        neo4j_driver = db_manager.get_neo4j_driver()

        self._user_repo = UserRepository(mongo_db, neo4j_driver)
        self._session_repo = SessionRepository(redis_client, mongo_db)
        self._auth_service = AuthService(self._user_repo, self._session_repo)

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


