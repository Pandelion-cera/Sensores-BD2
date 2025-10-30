from typing import List, Optional
from bson import ObjectId

from app.repositories.message_repository import MessageRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.user_repository import UserRepository
from app.models.message_models import Message, MessageCreate, MessageResponse, MessageType


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        group_repo: GroupRepository,
        user_repo: UserRepository
    ):
        self.message_repo = message_repo
        self.group_repo = group_repo
        self.user_repo = user_repo
    
    def send_message(self, sender_id: str, message_data: MessageCreate) -> MessageResponse:
        """Send a message (private or group)"""
        # Validate recipient
        if message_data.recipient_type == MessageType.PRIVATE:
            recipient = self.user_repo.get_by_id(message_data.recipient_id)
            if not recipient:
                raise ValueError("Recipient user not found")
        else:  # GROUP
            group = self.group_repo.get_by_id(message_data.recipient_id)
            if not group:
                raise ValueError("Recipient group not found")
            
            # Check if sender is member of group
            if sender_id not in group.miembros:
                raise ValueError("You are not a member of this group")
        
        # Create message
        message = self.message_repo.create(sender_id, message_data)
        
        # Get sender info for response
        sender = self.user_repo.get_by_id(sender_id)
        
        return MessageResponse(
            id=message.id,
            sender_id=message.sender_id,
            sender_name=sender.nombre_completo if sender else None,
            recipient_type=message.recipient_type,
            recipient_id=message.recipient_id,
            timestamp=message.timestamp,
            content=message.content
        )
    
    def get_user_messages(self, user_id: str, skip: int = 0, limit: int = 50) -> List[MessageResponse]:
        """Get messages sent to a user"""
        messages = self.message_repo.get_user_messages(user_id, skip, limit)
        
        return self._enrich_messages(messages)
    
    def get_group_messages(self, group_id: str, user_id: str, skip: int = 0, limit: int = 50) -> List[MessageResponse]:
        """Get messages from a group"""
        # Verify user is member of group
        group = self.group_repo.get_by_id(group_id)
        if not group or user_id not in group.miembros:
            raise ValueError("Access denied to group messages")
        
        messages = self.message_repo.get_group_messages(group_id, skip, limit)
        
        return self._enrich_messages(messages)
    
    def get_conversation(
        self,
        user1_id: str,
        user2_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[MessageResponse]:
        """Get conversation between two users"""
        messages = self.message_repo.get_conversation(user1_id, user2_id, skip, limit)
        
        return self._enrich_messages(messages)
    
    def _enrich_messages(self, messages: List[Message]) -> List[MessageResponse]:
        """Enrich messages with sender names"""
        enriched = []
        
        for message in messages:
            sender = self.user_repo.get_by_id(message.sender_id)
            
            enriched.append(MessageResponse(
                id=message.id,
                sender_id=message.sender_id,
                sender_name=sender.nombre_completo if sender else "Unknown",
                recipient_type=message.recipient_type,
                recipient_id=message.recipient_id,
                timestamp=message.timestamp,
                content=message.content
            ))
        
        return enriched

