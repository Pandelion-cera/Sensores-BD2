from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from desktop_app.models.invoice_models import (
    Invoice, InvoiceCreate, Payment, PaymentCreate,
    Account, AccountResponse, InvoiceStatus, Movement
)


class InvoiceRepository:
    def __init__(self, mongo_db: Database):
        self.invoices_col = mongo_db["invoices"]
        self.payments_col = mongo_db["payments"]
        self.accounts_col = mongo_db["accounts"]
        
    # Invoice CRUD
    def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice"""
        invoice_dict = invoice_data.model_dump()
        total = sum(item.subtotal for item in invoice_data.items)
        invoice_dict["total"] = total
        invoice_dict["estado"] = InvoiceStatus.PENDING
        
        result = self.invoices_col.insert_one(invoice_dict)
        invoice_dict["_id"] = str(result.inserted_id)
        
        # Update user account with charge
        self.add_account_movement(
            invoice_data.user_id,
            "cargo",
            total,
            f"Factura #{invoice_dict['_id']}",
            invoice_dict["_id"]
        )
        
        return Invoice(**invoice_dict)
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        try:
            invoice = self.invoices_col.find_one({"_id": ObjectId(invoice_id)})
            if invoice:
                invoice["_id"] = str(invoice["_id"])
                return Invoice(**invoice)
        except:
            return None
        return None
    
    def get_user_invoices(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all invoices for a user"""
        invoices = []
        for invoice in self.invoices_col.find({"user_id": user_id}).sort("fecha_emision", -1).skip(skip).limit(limit):
            invoice["_id"] = str(invoice["_id"])
            invoices.append(Invoice(**invoice))
        return invoices
    
    def update_invoice_status(self, invoice_id: str, status: InvoiceStatus) -> bool:
        """Update invoice status"""
        result = self.invoices_col.update_one(
            {"_id": ObjectId(invoice_id)},
            {"$set": {"estado": status}}
        )
        return result.modified_count > 0
    
    # Payment CRUD
    def create_payment(self, invoice_id: str, payment_data: PaymentCreate) -> Payment:
        """Create a payment record"""
        payment_dict = {
            "invoice_id": invoice_id,
            "monto": payment_data.monto,
            "metodo": payment_data.metodo
        }
        
        result = self.payments_col.insert_one(payment_dict)
        payment_dict["_id"] = str(result.inserted_id)
        
        # Update invoice status
        self.update_invoice_status(invoice_id, InvoiceStatus.PAID)
        
        # Get invoice to update account
        invoice = self.get_invoice(invoice_id)
        if invoice:
            self.add_account_movement(
                invoice.user_id,
                "abono",
                payment_data.monto,
                f"Pago factura #{invoice_id}",
                payment_dict["_id"]
            )
        
        return Payment(**payment_dict)
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        try:
            payment = self.payments_col.find_one({"_id": ObjectId(payment_id)})
            if payment:
                payment["_id"] = str(payment["_id"])
                return Payment(**payment)
        except:
            return None
        return None
    
    def get_invoice_payments(self, invoice_id: str) -> List[Payment]:
        """Get all payments for an invoice"""
        payments = []
        for payment in self.payments_col.find({"invoice_id": invoice_id}):
            payment["_id"] = str(payment["_id"])
            payments.append(Payment(**payment))
        return payments
    
    # Account CRUD
    def get_or_create_account(self, user_id: str) -> Account:
        """Get or create account for user"""
        account = self.accounts_col.find_one({"user_id": user_id})
        
        if account:
            account["_id"] = str(account["_id"])
            return Account(**account)
        
        # Create new account
        account_dict = {
            "user_id": user_id,
            "saldo": 0.0,
            "movimientos": []
        }
        
        result = self.accounts_col.insert_one(account_dict)
        account_dict["_id"] = str(result.inserted_id)
        
        return Account(**account_dict)
    
    def add_account_movement(
        self,
        user_id: str,
        tipo: str,
        monto: float,
        descripcion: str,
        referencia_id: Optional[str] = None
    ) -> bool:
        """Add a movement to user account"""
        account = self.get_or_create_account(user_id)
        
        movement = Movement(
            fecha=datetime.utcnow(),
            tipo=tipo,
            monto=monto,
            descripcion=descripcion,
            referencia_id=referencia_id
        )
        
        # Update balance
        if tipo == "cargo":
            new_balance = account.saldo - monto
        else:  # abono
            new_balance = account.saldo + monto
        
        result = self.accounts_col.update_one(
            {"user_id": user_id},
            {
                "$set": {"saldo": new_balance},
                "$push": {"movimientos": movement.model_dump()}
            }
        )
        
        return result.modified_count > 0
    
    def get_account(self, user_id: str) -> Optional[Account]:
        """Get account for user"""
        return self.get_or_create_account(user_id)

