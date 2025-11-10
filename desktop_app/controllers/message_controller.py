"""
Messaging controller bridging UI interactions with services.
"""
from __future__ import annotations

from typing import Dict, List

from desktop_app.models.group_models import Group
from desktop_app.models.message_models import MessageCreate, MessageResponse
from desktop_app.models.user_models import User, UserResponse
from desktop_app.services.factories import (
    get_group_service,
    get_message_service,
    get_user_service,
)


class MessageController:
    """Expose messaging capabilities to the UI layer."""

    def __init__(self) -> None:
        self._message_service = get_message_service()
        self._user_service = get_user_service()
        self._group_service = get_group_service()

    # Messages -------------------------------------------------------------------
    def get_user_messages(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 200,
    ) -> Dict[str, List[MessageResponse]]:
        """Return the user's private and group messages."""
        return self._message_service.get_all_user_messages(user_id, skip=skip, limit=limit)

    def send_message(self, sender_id: str, payload: MessageCreate) -> MessageResponse:
        """Send a message on behalf of the given user."""
        return self._message_service.send_message(sender_id, payload)

    # Recipients -----------------------------------------------------------------
    def list_users(self, *, skip: int = 0, limit: int = 200) -> List[UserResponse]:
        """List users for selection in messaging dialogs."""
        return self._user_service.get_all_users(skip=skip, limit=limit)

    def list_user_groups(self, user_id: str) -> List[Group]:
        """Return groups that the user belongs to."""
        return self._group_service.get_user_groups(user_id)


