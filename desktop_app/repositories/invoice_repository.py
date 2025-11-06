from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from desktop_app.models.invoice_models import (
    Invoice, InvoiceCreate, InvoiceStatus
)


class InvoiceRepository:
    """Repository for invoice operations only"""
    
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db["invoices"]
    
    def create(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice"""
        invoice_dict = invoice_data.model_dump(exclude_none=True)
        total = sum(item.subtotal for item in invoice_data.items)
        invoice_dict["total"] = total
        invoice_dict["estado"] = InvoiceStatus.PENDING
        
        # Ensure fecha_emision is set (use provided or current date)
        if "fecha_emision" not in invoice_dict or invoice_dict["fecha_emision"] is None:
            invoice_dict["fecha_emision"] = datetime.utcnow()
        
        result = self.collection.insert_one(invoice_dict)
        invoice_dict["_id"] = str(result.inserted_id)
        
        return Invoice(**invoice_dict)
    
    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        try:
            invoice = self.collection.find_one({"_id": ObjectId(invoice_id)})
            if invoice:
                invoice["_id"] = str(invoice["_id"])
                # Ensure fecha_emision and fecha_vencimiento are datetime objects if they exist
                if "fecha_emision" in invoice and invoice["fecha_emision"]:
                    if isinstance(invoice["fecha_emision"], str):
                        try:
                            invoice["fecha_emision"] = datetime.fromisoformat(invoice["fecha_emision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "fecha_vencimiento" in invoice and invoice["fecha_vencimiento"]:
                    if isinstance(invoice["fecha_vencimiento"], str):
                        try:
                            invoice["fecha_vencimiento"] = datetime.fromisoformat(invoice["fecha_vencimiento"].replace("Z", "+00:00"))
                        except:
                            pass
                return Invoice(**invoice)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting invoice {invoice_id}: {e}")
            return None
        return None
    
    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all invoices for a user"""
        invoices = []
        for invoice in self.collection.find({"user_id": user_id}).sort("fecha_emision", -1).skip(skip).limit(limit):
            try:
                invoice["_id"] = str(invoice["_id"])
                # Ensure fecha_emision and fecha_vencimiento are datetime objects if they exist
                if "fecha_emision" in invoice and invoice["fecha_emision"]:
                    if isinstance(invoice["fecha_emision"], str):
                        try:
                            invoice["fecha_emision"] = datetime.fromisoformat(invoice["fecha_emision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "fecha_vencimiento" in invoice and invoice["fecha_vencimiento"]:
                    if isinstance(invoice["fecha_vencimiento"], str):
                        try:
                            invoice["fecha_vencimiento"] = datetime.fromisoformat(invoice["fecha_vencimiento"].replace("Z", "+00:00"))
                        except:
                            pass
                invoices.append(Invoice(**invoice))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error parsing invoice {invoice.get('_id', 'unknown')}: {e}")
                continue
        return invoices
    
    def update_status(self, invoice_id: str, status: InvoiceStatus) -> bool:
        """Update invoice status"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(invoice_id)},
                {"$set": {"estado": status}}
            )
            return result.modified_count > 0
        except:
            return False
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all invoices"""
        invoices = []
        for invoice in self.collection.find({}).sort("fecha_emision", -1).skip(skip).limit(limit):
            try:
                invoice["_id"] = str(invoice["_id"])
                # Ensure fecha_emision and fecha_vencimiento are datetime objects if they exist
                if "fecha_emision" in invoice and invoice["fecha_emision"]:
                    if isinstance(invoice["fecha_emision"], str):
                        try:
                            invoice["fecha_emision"] = datetime.fromisoformat(invoice["fecha_emision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "fecha_vencimiento" in invoice and invoice["fecha_vencimiento"]:
                    if isinstance(invoice["fecha_vencimiento"], str):
                        try:
                            invoice["fecha_vencimiento"] = datetime.fromisoformat(invoice["fecha_vencimiento"].replace("Z", "+00:00"))
                        except:
                            pass
                invoices.append(Invoice(**invoice))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error parsing invoice {invoice.get('_id', 'unknown')}: {e}")
                continue
        return invoices

