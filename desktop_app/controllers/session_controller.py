"""
Controller for session history and user lookup.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from desktop_app.core.database import db_manager
from desktop_app.repositories.session_repository import SessionRepository
from desktop_app.repositories.user_repository import UserRepository


class SessionController:
    """Expose session history utilities for administrative views."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        redis_client = db_manager.get_redis_client()
        neo4j_driver = db_manager.get_neo4j_driver()

        self._session_repo = SessionRepository(redis_client, mongo_db, neo4j_driver)
        self._user_repo = UserRepository(mongo_db, neo4j_driver)

    def list_users(self, *, skip: int = 0, limit: int = 1000):
        """Return registered users."""
        return self._user_repo.get_all(skip=skip, limit=limit)

    def get_user(self, user_id: str):
        """Return a user by identifier."""
        if not user_id:
            return None
        return self._user_repo.get_by_id(user_id)

    def get_session_history(
        self,
        *,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[Dict[str, object]]:
        """Return session history records."""
        return self._session_repo.get_session_history(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )


