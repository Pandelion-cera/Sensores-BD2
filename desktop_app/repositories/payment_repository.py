from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from desktop_app.models.invoice_models import Payment, PaymentCreate


class PaymentRepository:
    """Repository for payment operations"""
    
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db["payments"]
    
    def create(self, invoice_id: str, payment_data: PaymentCreate) -> Payment:
        """Create a new payment record"""
        payment_dict = {
            "invoice_id": invoice_id,
            "monto": payment_data.monto,
            "metodo": payment_data.metodo,
            "fecha_pago": datetime.utcnow()
        }
        
        result = self.collection.insert_one(payment_dict)
        payment_dict["_id"] = str(result.inserted_id)
        
        return Payment(**payment_dict)
    
    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        try:
            payment = self.collection.find_one({"_id": ObjectId(payment_id)})
            if payment:
                payment["_id"] = str(payment["_id"])
                # Ensure fecha_pago is a datetime object if it exists
                if "fecha_pago" in payment and payment["fecha_pago"]:
                    if isinstance(payment["fecha_pago"], str):
                        try:
                            payment["fecha_pago"] = datetime.fromisoformat(payment["fecha_pago"].replace("Z", "+00:00"))
                        except:
                            pass
                return Payment(**payment)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting payment {payment_id}: {e}")
            return None
        return None
    
    def get_by_invoice(self, invoice_id: str) -> List[Payment]:
        """Get all payments for an invoice"""
        payments = []
        for payment in self.collection.find({"invoice_id": invoice_id}).sort("fecha_pago", -1):
            try:
                payment["_id"] = str(payment["_id"])
                # Ensure fecha_pago is a datetime object if it exists
                if "fecha_pago" in payment and payment["fecha_pago"]:
                    if isinstance(payment["fecha_pago"], str):
                        try:
                            payment["fecha_pago"] = datetime.fromisoformat(payment["fecha_pago"].replace("Z", "+00:00"))
                        except:
                            pass
                payments.append(Payment(**payment))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error parsing payment {payment.get('_id', 'unknown')}: {e}")
                continue
        return payments
    
    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get all payments for a user (requires joining with invoices)"""
        # This would need to join with invoices collection
        # For now, return empty list - this method should be called from service layer
        # that has access to invoice repository
        return []

