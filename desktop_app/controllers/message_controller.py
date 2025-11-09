"""
Messaging controller bridging UI interactions with services.
"""
from __future__ import annotations

from typing import Dict, List

from desktop_app.core.database import db_manager
from desktop_app.models.group_models import Group
from desktop_app.models.message_models import MessageCreate, MessageResponse
from desktop_app.models.user_models import User
from desktop_app.repositories.account_repository import AccountRepository
from desktop_app.repositories.group_repository import GroupRepository
from desktop_app.repositories.message_repository import MessageRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.message_service import MessageService
from desktop_app.services.user_service import UserService


class MessageController:
    """Expose messaging capabilities to the UI layer."""

    def __init__(self) -> None:
        mongo_db = db_manager.get_mongo_db()
        neo4j_driver = db_manager.get_neo4j_driver()

        self._message_repo = MessageRepository(mongo_db)
        self._group_repo = GroupRepository(mongo_db, neo4j_driver)
        self._user_repo = UserRepository(mongo_db, neo4j_driver)
        self._account_repo = AccountRepository(mongo_db)

        self._message_service = MessageService(
            self._message_repo,
            self._group_repo,
            self._user_repo,
        )
        self._user_service = UserService(self._user_repo, self._account_repo)

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
    def list_users(self, *, skip: int = 0, limit: int = 200) -> List[User]:
        """List users for selection in messaging dialogs."""
        return self._user_service.get_all_users(skip=skip, limit=limit)

    def list_user_groups(self, user_id: str) -> List[Group]:
        """Return groups that the user belongs to."""
        return self._group_repo.get_user_groups(user_id)


