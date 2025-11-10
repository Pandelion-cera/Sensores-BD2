from __future__ import annotations

from typing import Iterable, List, Optional

from desktop_app.models.group_models import Group, GroupCreate
from desktop_app.repositories.group_repository import GroupRepository


class GroupService:
    """Service layer for group management."""

    def __init__(self, group_repo: GroupRepository):
        self._group_repo = group_repo

    def list_groups(self, *, skip: int = 0, limit: int = 100) -> List[Group]:
        return self._group_repo.get_all(skip=skip, limit=limit)

    def get_group(self, group_id: str) -> Optional[Group]:
        if not group_id:
            return None
        return self._group_repo.get_by_id(group_id)

    def create_group(self, payload: GroupCreate) -> Group:
        return self._group_repo.create(payload)

    def delete_group(self, group_id: str) -> bool:
        return self._group_repo.delete(group_id)

    def add_members(self, group_id: str, user_ids: Iterable[str]) -> int:
        added = 0
        for user_id in user_ids:
            if self._group_repo.add_member(group_id, user_id):
                added += 1
        return added

    def remove_members(self, group_id: str, user_ids: Iterable[str]) -> int:
        removed = 0
        for user_id in user_ids:
            if self._group_repo.remove_member(group_id, user_id):
                removed += 1
        return removed

    def get_user_groups(self, user_id: str) -> List[Group]:
        return self._group_repo.get_user_groups(user_id)


