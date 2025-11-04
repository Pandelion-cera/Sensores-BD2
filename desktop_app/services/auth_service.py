from typing import Optional, Dict, Any
from datetime import timedelta
import uuid

from desktop_app.repositories.user_repository import UserRepository
from desktop_app.repositories.session_repository import SessionRepository
from desktop_app.models.user_models import UserCreate, UserLogin, User
from desktop_app.core.security import verify_password, create_access_token
from desktop_app.core.config import settings


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
    
    def register(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Create user
        user = self.user_repo.create(user_data)
        
        return {
            "id": user.id,
            "email": user.email,
            "nombre_completo": user.nombre_completo
        }
    
    def login(self, credentials: UserLogin) -> Dict[str, Any]:
        """Authenticate user and create session"""
        # Get user
        user = self.user_repo.get_by_email(credentials.email)
        if not user:
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if user.estado != "activo":
            raise ValueError("User account is inactive")
        
        # Get user role
        roles = self.user_repo.get_user_roles(user.id)
        primary_role = roles[0] if roles else "usuario"
        
        # Create JWT token
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": primary_role
        }
        
        access_token = create_access_token(
            token_data,
            timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
        )
        
        # Create session in Redis
        session_id = str(uuid.uuid4())
        self.session_repo.create_session(
            session_id,
            user.id,
            primary_role,
            ttl=settings.JWT_EXPIRATION_MINUTES * 60
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "session_id": session_id,
            "user": {
                "id": user.id,
                "email": user.email,
                "nombre_completo": user.nombre_completo,
                "role": primary_role
            }
        }
    
    def logout(self, session_id: str) -> bool:
        """Logout user and delete session"""
        return self.session_repo.delete_session(session_id)
    
    def get_current_user(self, user_id: str) -> Optional[User]:
        """Get current authenticated user"""
        return self.user_repo.get_by_id(user_id)
    
    def verify_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Verify if session is active"""
        return self.session_repo.get_session(session_id)

