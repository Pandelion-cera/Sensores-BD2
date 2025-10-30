from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.models.user_models import UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService
from app.core.security import get_current_user_data
from app.core.database import get_mongo_db, get_redis_client, get_neo4j_driver
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository

router = APIRouter()


def get_auth_service(
    mongo_db=Depends(get_mongo_db),
    redis_client=Depends(get_redis_client),
    neo4j_driver=Depends(get_neo4j_driver)
) -> AuthService:
    user_repo = UserRepository(mongo_db, neo4j_driver)
    session_repo = SessionRepository(redis_client)
    return AuthService(user_repo, session_repo)


@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        return auth_service.register(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Dict[str, Any])
def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login and get access token"""
    try:
        return auth_service.login(credentials)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
def logout(
    session_id: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout and delete session"""
    success = auth_service.logout(session_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user information"""
    user = auth_service.get_current_user(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(
        id=user.id,
        nombre_completo=user.nombre_completo,
        email=user.email,
        estado=user.estado,
        fecha_registro=user.fecha_registro
    )
