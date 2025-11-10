"""
Controller for administrative group management operations.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from desktop_app.models.group_models import Group, GroupCreate
from desktop_app.models.user_models import User, UserResponse
from desktop_app.services.factories import get_group_service, get_user_service


class GroupController:
    """Wrap persistence logic for group CRUD and membership changes."""

    def __init__(self) -> None:
        self._group_service = get_group_service()
        self._user_service = get_user_service()

    def list_groups(self, *, skip: int = 0, limit: int = 100) -> List[Group]:
        """Return registered groups."""
        return self._group_service.list_groups(skip=skip, limit=limit)

    def get_group(self, group_id: str) -> Optional[Group]:
        """Fetch a single group by identifier."""
        if not group_id:
            return None
        return self._group_service.get_group(group_id)

    def create_group(self, payload: GroupCreate) -> Group:
        """Create a new group."""
        return self._group_service.create_group(payload)

    def delete_group(self, group_id: str) -> bool:
        """Delete the given group."""
        return self._group_service.delete_group(group_id)

    def add_members(self, group_id: str, user_ids: Iterable[str]) -> int:
        """Add members to a group, returning how many were appended."""
        return self._group_service.add_members(group_id, user_ids)

    def remove_members(self, group_id: str, user_ids: Iterable[str]) -> int:
        """Remove members from a group, returning how many were removed."""
        return self._group_service.remove_members(group_id, user_ids)

    def list_users(self, *, skip: int = 0, limit: int = 200) -> List[UserResponse]:
        """Return users for selection dialogs."""
        return self._user_service.get_all_users(skip=skip, limit=limit)

    def get_user(self, user_id: str) -> Optional[User]:
        """Fetch a single user by identifier."""
        if not user_id:
            return None
        return self._user_service.get_user(user_id)


