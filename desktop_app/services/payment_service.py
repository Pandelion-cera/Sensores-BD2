from typing import List, Optional
from datetime import datetime

from desktop_app.repositories.payment_repository import PaymentRepository
from desktop_app.repositories.invoice_repository import InvoiceRepository
from desktop_app.repositories.account_repository import AccountRepository
from desktop_app.models.invoice_models import (
    Payment, PaymentCreate, InvoiceStatus, Movement
)


class PaymentService:
    """Service for payment operations"""
    
    def __init__(
        self,
        payment_repo: PaymentRepository,
        invoice_repo: InvoiceRepository,
        account_repo: AccountRepository
    ):
        self.payment_repo = payment_repo
        self.invoice_repo = invoice_repo
        self.account_repo = account_repo
    
    def create_payment(self, invoice_id: str, payment_data: PaymentCreate) -> Payment:
        """Register payment for an invoice"""
        # Verify invoice exists
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        if invoice.estado == InvoiceStatus.PAID:
            raise ValueError("Invoice is already paid")
        
        if invoice.estado == InvoiceStatus.CANCELLED:
            raise ValueError("Invoice is cancelled")
        
        # Verify payment amount
        if payment_data.monto < invoice.total:
            raise ValueError(f"Payment amount ({payment_data.monto}) is less than invoice total ({invoice.total})")
        
        # Create payment record
        payment = self.payment_repo.create(invoice_id, payment_data)
        
        # Update invoice status
        self.invoice_repo.update_status(invoice_id, InvoiceStatus.PAID)
        
        # Update user account with charge (cargo) - user is paying, so balance decreases
        movement = Movement(
            fecha=datetime.utcnow(),
            tipo="cargo",
            monto=payment_data.monto,
            descripcion=f"Pago factura #{invoice_id}",
            referencia_id=payment.id
        )
        self.account_repo.add_movement(invoice.user_id, movement)
        
        return payment
    
    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        return self.payment_repo.get_by_id(payment_id)
    
    def get_by_invoice(self, invoice_id: str) -> List[Payment]:
        """Get all payments for an invoice"""
        return self.payment_repo.get_by_invoice(invoice_id)
    
    def get_by_user(self, user_id: str) -> List[Payment]:
        """Get all payments for a user"""
        # Get all user invoices first
        invoices = self.invoice_repo.get_by_user(user_id, skip=0, limit=1000)
        invoice_ids = [inv.id for inv in invoices if inv.id]
        
        # Get payments for all invoices
        all_payments = []
        for invoice_id in invoice_ids:
            payments = self.payment_repo.get_by_invoice(invoice_id)
            all_payments.extend(payments)
        
        # Sort by date (most recent first)
        all_payments.sort(key=lambda p: p.fecha_pago, reverse=True)
        return all_payments

