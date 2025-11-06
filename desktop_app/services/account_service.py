from typing import List, Optional
from datetime import datetime

from desktop_app.repositories.account_repository import AccountRepository
from desktop_app.models.invoice_models import Account, Movement


class AccountService:
    """Service for account operations"""
    
    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo
    
    def get_account(self, user_id: str) -> Account:
        """Get user account information"""
        return self.account_repo.get_or_create(user_id)
    
    def add_charge(
        self,
        user_id: str,
        monto: float,
        descripcion: str,
        referencia_id: Optional[str] = None
    ) -> bool:
        """Add a charge (cargo) to user account"""
        movement = Movement(
            fecha=datetime.utcnow(),
            tipo="cargo",
            monto=monto,
            descripcion=descripcion,
            referencia_id=referencia_id
        )
        return self.account_repo.add_movement(user_id, movement)
    
    def add_payment(
        self,
        user_id: str,
        monto: float,
        descripcion: str,
        referencia_id: Optional[str] = None
    ) -> bool:
        """Add a payment (abono) to user account"""
        movement = Movement(
            fecha=datetime.utcnow(),
            tipo="abono",
            monto=monto,
            descripcion=descripcion,
            referencia_id=referencia_id
        )
        return self.account_repo.add_movement(user_id, movement)
    
    def get_movements(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Movement]:
        """Get account movements for a user"""
        return self.account_repo.get_movements(user_id, skip, limit)
    
    def get_balance(self, user_id: str) -> float:
        """Get current account balance"""
        account = self.account_repo.get_by_user(user_id)
        return account.saldo if account else 0.0

