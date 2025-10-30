from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.process_repository import ProcessRepository
from app.models.invoice_models import (
    Invoice, InvoiceCreate, InvoiceItem, Payment, PaymentCreate,
    Account, InvoiceStatus
)


class InvoiceService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        process_repo: ProcessRepository
    ):
        self.invoice_repo = invoice_repo
        self.process_repo = process_repo
    
    def create_invoice_for_user(self, user_id: str, process_ids: List[str]) -> Invoice:
        """Create an invoice for a user based on executed processes"""
        items = []
        
        for process_id in process_ids:
            process = self.process_repo.get_process(process_id)
            if process:
                item = InvoiceItem(
                    process_id=process_id,
                    process_name=process.nombre,
                    cantidad=1,
                    precio_unitario=process.costo,
                    subtotal=process.costo
                )
                items.append(item)
        
        if not items:
            raise ValueError("No valid processes found for invoice")
        
        # Set due date to 30 days from now
        fecha_vencimiento = datetime.utcnow() + timedelta(days=30)
        
        invoice_data = InvoiceCreate(
            user_id=user_id,
            items=items,
            fecha_vencimiento=fecha_vencimiento
        )
        
        return self.invoice_repo.create_invoice(invoice_data)
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        return self.invoice_repo.get_invoice(invoice_id)
    
    def get_user_invoices(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all invoices for a user"""
        return self.invoice_repo.get_user_invoices(user_id, skip, limit)
    
    def pay_invoice(self, invoice_id: str, payment_data: PaymentCreate) -> Payment:
        """Register payment for an invoice"""
        invoice = self.invoice_repo.get_invoice(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        if invoice.estado == InvoiceStatus.PAID:
            raise ValueError("Invoice is already paid")
        
        if invoice.estado == InvoiceStatus.CANCELLED:
            raise ValueError("Invoice is cancelled")
        
        # Verify payment amount
        if payment_data.monto < invoice.total:
            raise ValueError(f"Payment amount ({payment_data.monto}) is less than invoice total ({invoice.total})")
        
        # Create payment
        payment = self.invoice_repo.create_payment(invoice_id, payment_data)
        
        return payment
    
    def get_invoice_payments(self, invoice_id: str) -> List[Payment]:
        """Get all payments for an invoice"""
        return self.invoice_repo.get_invoice_payments(invoice_id)
    
    def get_user_account(self, user_id: str) -> Account:
        """Get user account information"""
        return self.invoice_repo.get_account(user_id)
    
    def generate_monthly_invoices(self, month: int, year: int) -> List[Invoice]:
        """Generate invoices for all users for a given month"""
        # This would be called by a scheduled job
        # For now, return empty list
        # TODO: Implement monthly invoice generation
        return []
    
    def update_invoice_status(self, invoice_id: str, status: InvoiceStatus) -> bool:
        """Update invoice status"""
        return self.invoice_repo.update_invoice_status(invoice_id, status)

