from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any

from app.models.user_models import UserUpdate, UserResponse
from app.models.invoice_models import AccountResponse
from app.services.user_service import UserService
from app.core.security import get_current_user_data
from app.core.database import get_mongo_db, get_neo4j_driver
from app.repositories.user_repository import UserRepository
from app.repositories.invoice_repository import InvoiceRepository

router = APIRouter()


def get_user_service(
    mongo_db=Depends(get_mongo_db),
    neo4j_driver=Depends(get_neo4j_driver)
) -> UserService:
    user_repo = UserRepository(mongo_db, neo4j_driver)
    invoice_repo = InvoiceRepository(mongo_db)
    return UserService(user_repo, invoice_repo)


@router.get("", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    user_service: UserService = Depends(get_user_service)
):
    """Get all users (admin only)"""
    if current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return user_service.get_all_users(skip, limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID"""
    # Users can only view their own data unless they're admin
    if user_id != current_user["user_id"] and current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(
        id=user.id,
        nombre_completo=user.nombre_completo,
        email=user.email,
        estado=user.estado,
        fecha_registro=user.fecha_registro
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    user_service: UserService = Depends(get_user_service)
):
    """Update user"""
    # Users can only update their own data unless they're admin
    if user_id != current_user["user_id"] and current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    user = user_service.update_user(user_id, user_update)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(
        id=user.id,
        nombre_completo=user.nombre_completo,
        email=user.email,
        estado=user.estado,
        fecha_registro=user.fecha_registro
    )


@router.get("/{user_id}/roles")
def get_user_roles(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    user_service: UserService = Depends(get_user_service)
):
    """Get user roles"""
    if user_id != current_user["user_id"] and current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    roles = user_service.get_user_roles(user_id)
    return {"user_id": user_id, "roles": roles}


@router.post("/{user_id}/roles/{role_name}")
def assign_role(
    user_id: str,
    role_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    user_service: UserService = Depends(get_user_service)
):
    """Assign role to user (admin only)"""
    if current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    success = user_service.assign_role(user_id, role_name)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to assign role")
    
    return {"message": f"Role {role_name} assigned to user {user_id}"}


@router.get("/{user_id}/account", response_model=AccountResponse)
def get_user_account(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    user_service: UserService = Depends(get_user_service)
):
    """Get user account information"""
    if user_id != current_user["user_id"] and current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return user_service.get_user_account(user_id)

