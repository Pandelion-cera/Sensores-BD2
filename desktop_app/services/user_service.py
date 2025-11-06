from typing import Optional, List

from desktop_app.repositories.user_repository import UserRepository
from desktop_app.repositories.account_repository import AccountRepository
from desktop_app.models.user_models import User, UserUpdate, UserResponse
from desktop_app.models.invoice_models import AccountResponse


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        account_repo: AccountRepository
    ):
        self.user_repo = user_repo
        self.account_repo = account_repo
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.user_repo.get_by_id(user_id)
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users"""
        users = self.user_repo.get_all(skip, limit)
        return [
            UserResponse(
                id=u.id,
                nombre_completo=u.nombre_completo,
                email=u.email,
                estado=u.estado,
                fecha_registro=u.fecha_registro
            )
            for u in users
        ]
    
    def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user"""
        return self.user_repo.update(user_id, user_update)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        return self.user_repo.delete(user_id)
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles"""
        return self.user_repo.get_user_roles(user_id)
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        return self.user_repo.assign_role(user_id, role_name)
    
    def get_user_account(self, user_id: str) -> AccountResponse:
        """Get user account information"""
        account = self.account_repo.get_by_user(user_id)
        if not account:
            # Return empty account if not found
            from datetime import datetime
            return AccountResponse(
                id="",
                user_id=user_id,
                saldo=0.0,
                movimientos=[],
                fecha_creacion=datetime.utcnow()
            )
        return AccountResponse(
            id=account.id or "",
            user_id=account.user_id,
            saldo=account.saldo,
            movimientos=account.movimientos,
            fecha_creacion=account.fecha_creacion
        )
    
    def can_execute_process(self, user_id: str, process_id: str) -> bool:
        """Check if user can execute a process"""
        # Admins can execute all processes
        roles = self.user_repo.get_user_roles(user_id)
        if "administrador" in roles:
            return True
        
        # Check specific permission
        return self.user_repo.can_execute_process(user_id, process_id)

