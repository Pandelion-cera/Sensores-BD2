from typing import List, Optional, Dict
from bson import ObjectId

from desktop_app.repositories.message_repository import MessageRepository
from desktop_app.repositories.group_repository import GroupRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.models.message_models import Message, MessageCreate, MessageResponse, MessageType


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
        recipient_id = message_data.recipient_id
        
        # Validate recipient and resolve email to ID if needed
        if message_data.recipient_type == MessageType.PRIVATE:
            recipient = None
            try:
                # Try as ObjectId first
                ObjectId(message_data.recipient_id)  # Validate ObjectId format
                recipient = self.user_repo.get_by_id(message_data.recipient_id)
            except Exception:
                # Not a valid ObjectId, try as email
                print(f"[DEBUG] Trying to find user by email: {message_data.recipient_id}")
                recipient = self.user_repo.get_by_email(message_data.recipient_id)
                if recipient:
                    recipient_id = recipient.id  # Use the resolved ID
                    print(f"[DEBUG] Found user by email, resolved ID: {recipient_id}")
            
            if not recipient:
                raise ValueError(f"Recipient user not found (searched by ID/email: {message_data.recipient_id})")
        else:  # GROUP
            group = self.group_repo.get_by_id(message_data.recipient_id)
            if not group:
                raise ValueError("Recipient group not found")
            
            # Check if sender is member of group
            if sender_id not in group.miembros:
                raise ValueError("You are not a member of this group")
        
        # Create message with resolved recipient_id
        message_dict = message_data.model_dump()
        message_dict["recipient_id"] = recipient_id
        message_data_resolved = MessageCreate(**message_dict)
        
        # Create message
        message = self.message_repo.create(sender_id, message_data_resolved)
        
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
    
    def get_all_user_messages(self, user_id: str, skip: int = 0, limit: int = 50) -> Dict[str, List[MessageResponse]]:
        """Get all messages for a user: private and group messages"""
        # Get private messages
        private_messages = self.message_repo.get_user_messages(user_id, skip, limit)
        enriched_private = self._enrich_messages(private_messages)
        
        # Get user's groups
        user_groups = self.group_repo.get_user_groups(user_id)
        
        # Get group messages
        group_messages = []
        for group in user_groups:
            group_msgs = self.message_repo.get_group_messages(group.id, skip, limit)
            group_messages.extend(group_msgs)
        
        # Sort group messages by timestamp (most recent first)
        group_messages.sort(key=lambda m: m.timestamp, reverse=True)
        enriched_group = self._enrich_messages(group_messages)
        
        return {
            "private": enriched_private,
            "group": enriched_group
        }
    
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
        """Enrich messages with sender names and recipient names"""
        enriched = []
        
        for message in messages:
            sender = self.user_repo.get_by_id(message.sender_id)
            sender_name = sender.nombre_completo if sender else "Unknown"
            
            # Get recipient name (group name or user name)
            recipient_name = None
            if message.recipient_type == MessageType.GROUP:
                group = self.group_repo.get_by_id(message.recipient_id)
                recipient_name = group.nombre if group else None
            else:  # PRIVATE
                recipient = self.user_repo.get_by_id(message.recipient_id)
                recipient_name = recipient.nombre_completo if recipient else None
            
            enriched.append(MessageResponse(
                id=message.id,
                sender_id=message.sender_id,
                sender_name=sender_name,
                recipient_type=message.recipient_type,
                recipient_id=message.recipient_id,
                recipient_name=recipient_name,
                timestamp=message.timestamp,
                content=message.content
            ))
        
        return enriched

