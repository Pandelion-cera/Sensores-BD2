from __future__ import annotations

from typing import Dict, List, Optional

from desktop_app.repositories.session_repository import SessionRepository


class SessionService:
    """Service to expose session history and management operations."""

    def __init__(self, session_repo: SessionRepository):
        self._session_repo = session_repo

    def get_session_history(
        self,
        *,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[Dict[str, object]]:
        return self._session_repo.get_session_history(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    def get_active_sessions(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, object]]:
        return self._session_repo.get_all_active_sessions(user_id=user_id)


