from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any

from app.models.invoice_models import Invoice, Payment, PaymentCreate, Account
from app.services.invoice_service import InvoiceService
from app.core.security import get_current_user_data
from app.core.database import get_mongo_db, get_neo4j_driver
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.process_repository import ProcessRepository

router = APIRouter()


def get_invoice_service(
    mongo_db=Depends(get_mongo_db),
    neo4j_driver=Depends(get_neo4j_driver)
) -> InvoiceService:
    invoice_repo = InvoiceRepository(mongo_db)
    process_repo = ProcessRepository(mongo_db, neo4j_driver)
    return InvoiceService(invoice_repo, process_repo)


@router.get("", response_model=List[Invoice])
def get_my_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Get invoices for current user"""
    return invoice_service.get_user_invoices(current_user["user_id"], skip, limit)


@router.get("/{invoice_id}", response_model=Invoice)
def get_invoice(
    invoice_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Get invoice details"""
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    # Verify invoice belongs to user or user is admin
    if invoice.user_id != current_user["user_id"] and current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return invoice


@router.post("/{invoice_id}/pay", response_model=Payment)
def pay_invoice(
    invoice_id: str,
    payment_data: PaymentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Pay an invoice"""
    # Verify invoice belongs to user
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    if invoice.user_id != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    try:
        return invoice_service.pay_invoice(invoice_id, payment_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{invoice_id}/payments", response_model=List[Payment])
def get_invoice_payments(
    invoice_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Get payments for an invoice"""
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    # Verify invoice belongs to user or user is admin
    if invoice.user_id != current_user["user_id"] and current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return invoice_service.get_invoice_payments(invoice_id)


@router.get("/account/me", response_model=Account)
def get_my_account(
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Get current user's account"""
    return invoice_service.get_user_account(current_user["user_id"])

