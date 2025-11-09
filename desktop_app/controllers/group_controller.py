"""
Controller for administrative group management operations.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from desktop_app.core.database import db_manager
from desktop_app.models.group_models import Group, GroupCreate
from desktop_app.models.user_models import User
from desktop_app.repositories.account_repository import AccountRepository
from desktop_app.repositories.group_repository import GroupRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.user_service import UserService


class GroupController:
    """Wrap persistence logic for group CRUD and membership changes."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        neo4j_driver = db_manager.get_neo4j_driver()

        self._group_repo = GroupRepository(mongo_db, neo4j_driver)
        self._user_repo = UserRepository(mongo_db, neo4j_driver)
        self._account_repo = AccountRepository(mongo_db)
        self._user_service = UserService(self._user_repo, self._account_repo)

    def list_groups(self, *, skip: int = 0, limit: int = 100) -> List[Group]:
        """Return registered groups."""
        return self._group_repo.get_all(skip=skip, limit=limit)

    def get_group(self, group_id: str) -> Optional[Group]:
        """Fetch a single group by identifier."""
        if not group_id:
            return None
        return self._group_repo.get_by_id(group_id)

    def create_group(self, payload: GroupCreate) -> Group:
        """Create a new group."""
        return self._group_repo.create(payload)

    def delete_group(self, group_id: str) -> bool:
        """Delete the given group."""
        return self._group_repo.delete(group_id)

    def add_members(self, group_id: str, user_ids: Iterable[str]) -> int:
        """Add members to a group, returning how many were appended."""
        added = 0
        for user_id in user_ids:
            if self._group_repo.add_member(group_id, user_id):
                added += 1
        return added

    def remove_members(self, group_id: str, user_ids: Iterable[str]) -> int:
        """Remove members from a group, returning how many were removed."""
        removed = 0
        for user_id in user_ids:
            if self._group_repo.remove_member(group_id, user_id):
                removed += 1
        return removed

    def list_users(self, *, skip: int = 0, limit: int = 200) -> List[User]:
        """Return users for selection dialogs."""
        return self._user_service.get_all_users(skip=skip, limit=limit)

    def get_user(self, user_id: str) -> Optional[User]:
        """Fetch a single user by identifier."""
        if not user_id:
            return None
        return self._user_repo.get_by_id(user_id)


