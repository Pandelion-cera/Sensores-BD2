from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database

from app.models.message_models import Message, MessageCreate, MessageType


class MessageRepository:
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db["messages"]
        
    def create(self, sender_id: str, message_data: MessageCreate) -> Message:
        """Create a new message"""
        message_dict = {
            "sender_id": sender_id,
            "recipient_type": message_data.recipient_type,
            "recipient_id": message_data.recipient_id,
            "content": message_data.content
        }
        
        result = self.collection.insert_one(message_dict)
        message_dict["_id"] = str(result.inserted_id)
        
        return Message(**message_dict)
    
    def get_by_id(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        try:
            message = self.collection.find_one({"_id": ObjectId(message_id)})
            if message:
                message["_id"] = str(message["_id"])
                return Message(**message)
        except:
            return None
        return None
    
    def get_user_messages(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Message]:
        """Get messages sent to a user (private messages)"""
        messages = []
        query = {
            "recipient_type": MessageType.PRIVATE,
            "recipient_id": user_id
        }
        
        for message in self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit):
            message["_id"] = str(message["_id"])
            messages.append(Message(**message))
        
        return messages
    
    def get_group_messages(self, group_id: str, skip: int = 0, limit: int = 50) -> List[Message]:
        """Get messages sent to a group"""
        messages = []
        query = {
            "recipient_type": MessageType.GROUP,
            "recipient_id": group_id
        }
        
        for message in self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit):
            message["_id"] = str(message["_id"])
            messages.append(Message(**message))
        
        return messages
    
    def get_conversation(self, user1_id: str, user2_id: str, skip: int = 0, limit: int = 50) -> List[Message]:
        """Get conversation between two users"""
        messages = []
        query = {
            "$or": [
                {"sender_id": user1_id, "recipient_id": user2_id},
                {"sender_id": user2_id, "recipient_id": user1_id}
            ],
            "recipient_type": MessageType.PRIVATE
        }
        
        for message in self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit):
            message["_id"] = str(message["_id"])
            messages.append(Message(**message))
        
        return messages
    
    def delete(self, message_id: str) -> bool:
        """Delete a message"""
        result = self.collection.delete_one({"_id": ObjectId(message_id)})
        return result.deleted_count > 0

