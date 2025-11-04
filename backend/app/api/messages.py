from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any

from app.models.message_models import MessageCreate, MessageResponse
from app.services.message_service import MessageService
from app.core.security import get_current_user_data
from app.core.database import get_mongo_db, get_neo4j_driver
from app.repositories.message_repository import MessageRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.user_repository import UserRepository

router = APIRouter()


def get_message_service(
    mongo_db=Depends(get_mongo_db),
    neo4j_driver=Depends(get_neo4j_driver)
) -> MessageService:
    message_repo = MessageRepository(mongo_db)
    group_repo = GroupRepository(mongo_db, neo4j_driver)
    user_repo = UserRepository(mongo_db, neo4j_driver)
    return MessageService(message_repo, group_repo, user_repo)


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    message_data: MessageCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    message_service: MessageService = Depends(get_message_service)
):
    """Send a message (private or group)"""
    try:
        sender_id = current_user.get('user_id')
        print(f"[DEBUG] POST /api/messages - sender_id={sender_id} (from JWT), recipient_type={message_data.recipient_type}, recipient_id={message_data.recipient_id}")
        result = message_service.send_message(sender_id, message_data)
        print(f"[DEBUG] Message sent successfully, message_id={result.id}")
        return result
    except ValueError as e:
        print(f"[DEBUG] ValueError in send_message: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("")
def get_my_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    message_service: MessageService = Depends(get_message_service)
):
    """Get all messages for current user (private and group)"""
    return message_service.get_all_user_messages(current_user["user_id"], skip, limit)


@router.get("/groups/{group_id}", response_model=List[MessageResponse])
def get_group_messages(
    group_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    message_service: MessageService = Depends(get_message_service)
):
    """Get messages from a group"""
    try:
        return message_service.get_group_messages(group_id, current_user["user_id"], skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/conversation/{other_user_id}", response_model=List[MessageResponse])
def get_conversation(
    other_user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    message_service: MessageService = Depends(get_message_service)
):
    """Get conversation with another user"""
    return message_service.get_conversation(current_user["user_id"], other_user_id, skip, limit)

