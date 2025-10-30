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
        return message_service.send_message(current_user["user_id"], message_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[MessageResponse])
def get_my_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    message_service: MessageService = Depends(get_message_service)
):
    """Get messages sent to current user"""
    return message_service.get_user_messages(current_user["user_id"], skip, limit)


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

