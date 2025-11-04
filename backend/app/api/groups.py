from fastapi import APIRouter, Depends, status
from typing import List, Dict, Any

from app.models.group_models import GroupResponse, GroupCreate
from app.repositories.group_repository import GroupRepository
from app.core.security import get_current_user_data, require_admin_role
from app.core.database import get_mongo_db, get_neo4j_driver

router = APIRouter()


def get_group_repository(
    mongo_db=Depends(get_mongo_db),
    neo4j_driver=Depends(get_neo4j_driver)
) -> GroupRepository:
    return GroupRepository(mongo_db, neo4j_driver)


@router.get("/my-groups", response_model=List[GroupResponse])
def get_my_groups(
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    group_repo: GroupRepository = Depends(get_group_repository)
):
    """Get groups that the current user belongs to"""
    user_id = current_user.get('user_id')
    groups = group_repo.get_user_groups(user_id)
    return groups


@router.get("", response_model=List[GroupResponse])
def get_all_groups(
    current_user: Dict[str, Any] = Depends(require_admin_role),
    group_repo: GroupRepository = Depends(get_group_repository)
):
    """Get all groups (admin only)"""
    groups = group_repo.get_all()
    return groups


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group_data: GroupCreate,
    current_user: Dict[str, Any] = Depends(require_admin_role),
    group_repo: GroupRepository = Depends(get_group_repository)
):
    """Create a new group (admin only)"""
    group = group_repo.create(group_data)
    return group


@router.put("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_group_member(
    group_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_role),
    group_repo: GroupRepository = Depends(get_group_repository)
):
    """Add a member to a group (admin only)"""
    success = group_repo.add_member(group_id, user_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add member to group"
        )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_group_member(
    group_id: str,
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_role),
    group_repo: GroupRepository = Depends(get_group_repository)
):
    """Remove a member from a group (admin only)"""
    success = group_repo.remove_member(group_id, user_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove member from group"
        )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_role),
    group_repo: GroupRepository = Depends(get_group_repository)
):
    """Delete a group (admin only)"""
    success = group_repo.delete(group_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )

