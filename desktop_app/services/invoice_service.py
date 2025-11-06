from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from desktop_app.repositories.invoice_repository import InvoiceRepository
from desktop_app.repositories.process_repository import ProcessRepository
from desktop_app.services.account_service import AccountService
from desktop_app.models.invoice_models import (
    Invoice, InvoiceCreate, InvoiceItem, InvoiceStatus
)


class InvoiceService:
    """Service for invoice operations only"""
    
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        process_repo: ProcessRepository,
        account_service: Optional[AccountService] = None
    ):
        self.invoice_repo = invoice_repo
        self.process_repo = process_repo
        self.account_service = account_service
    
    def create_invoice_for_user(
        self, 
        user_id: str, 
        process_ids: List[str],
        request_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        fecha_emision: Optional[datetime] = None
    ) -> Invoice:
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
                    subtotal=process.costo,
                    request_id=request_id,
                    execution_id=execution_id
                )
                items.append(item)
        
        if not items:
            raise ValueError("No valid processes found for invoice")
        
        # Use provided fecha_emision or current date
        if fecha_emision is None:
            fecha_emision = datetime.utcnow()
        
        # Set due date to 30 days from fecha_emision (not from now)
        fecha_vencimiento = fecha_emision + timedelta(days=30)
        
        invoice_data = InvoiceCreate(
            user_id=user_id,
            items=items,
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento
        )
        
        # Create invoice
        invoice = self.invoice_repo.create(invoice_data)
        
        # Note: We don't charge the account when creating an invoice
        # The account will only be charged when the invoice is paid
        
        return invoice
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        return self.invoice_repo.get_by_id(invoice_id)
    
    def get_user_invoices(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all invoices for a user"""
        return self.invoice_repo.get_by_user(user_id, skip, limit)
    
    def get_all_invoices(self, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all invoices"""
        return self.invoice_repo.get_all(skip, limit)
    
    def update_status(self, invoice_id: str, status: InvoiceStatus) -> bool:
        """Update invoice status"""
        return self.invoice_repo.update_status(invoice_id, status)
    
    def generate_monthly_invoices(self, month: int, year: int) -> List[Invoice]:
        """Generate invoices for all users for a given month"""
        # This would be called by a scheduled job
        # For now, return empty list
        # TODO: Implement monthly invoice generation
        return []

