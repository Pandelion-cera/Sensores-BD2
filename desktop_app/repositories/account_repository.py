from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from desktop_app.models.invoice_models import Account, Movement


class AccountRepository:
    """Repository for account operations"""
    
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db["accounts"]
    
    def get_or_create(self, user_id: str) -> Account:
        """Get or create account for user"""
        account = self.collection.find_one({"user_id": user_id})
        
        if account:
            account["_id"] = str(account["_id"])
            # Ensure fecha_creacion is a datetime object if it exists
            if "fecha_creacion" in account and account["fecha_creacion"]:
                if isinstance(account["fecha_creacion"], str):
                    try:
                        account["fecha_creacion"] = datetime.fromisoformat(account["fecha_creacion"].replace("Z", "+00:00"))
                    except:
                        pass
            # Parse movements
            if "movimientos" in account and account["movimientos"]:
                parsed_movements = []
                for mov in account["movimientos"]:
                    try:
                        if isinstance(mov.get("fecha"), str):
                            mov["fecha"] = datetime.fromisoformat(mov["fecha"].replace("Z", "+00:00"))
                        parsed_movements.append(Movement(**mov))
                    except:
                        continue
                account["movimientos"] = parsed_movements
            return Account(**account)
        
        # Create new account
        account_dict = {
            "user_id": user_id,
            "saldo": 0.0,
            "movimientos": [],
            "fecha_creacion": datetime.utcnow()
        }
        
        result = self.collection.insert_one(account_dict)
        account_dict["_id"] = str(result.inserted_id)
        
        return Account(**account_dict)
    
    def get_by_user(self, user_id: str) -> Optional[Account]:
        """Get account for user"""
        return self.get_or_create(user_id)
    
    def add_movement(
        self,
        user_id: str,
        movement: Movement
    ) -> bool:
        """Add a movement to user account and update balance"""
        account = self.get_or_create(user_id)
        
        # Update balance
        if movement.tipo == "cargo":
            new_balance = account.saldo - movement.monto
        else:  # abono
            new_balance = account.saldo + movement.monto
        
        result = self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {"saldo": new_balance},
                "$push": {"movimientos": movement.model_dump()}
            }
        )
        
        return result.modified_count > 0
    
    def get_movements(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Movement]:
        """Get account movements for a user"""
        account = self.get_by_user(user_id)
        if not account:
            return []
        
        # Return movements in reverse chronological order (most recent first)
        movements = sorted(account.movimientos, key=lambda m: m.fecha, reverse=True)
        return movements[skip:skip+limit]
    
    def update_balance(self, user_id: str, new_balance: float) -> bool:
        """Update account balance directly"""
        result = self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"saldo": new_balance}}
        )
        return result.modified_count > 0

