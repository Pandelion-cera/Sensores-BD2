"""
Account, invoice and payment controller.
"""
from __future__ import annotations

from typing import List, Optional

from desktop_app.models.invoice_models import (
    Account,
    Invoice,
    InvoiceStatus,
    Movement,
    PaymentCreate,
    Payment,
)
from desktop_app.services.factories import (
    get_account_service,
    get_invoice_service,
    get_payment_service,
)


class AccountController:
    """Provide cohesive access to account balances, invoices and payments."""

    def __init__(self) -> None:
        self._account_service = get_account_service()
        self._invoice_service = get_invoice_service()
        self._payment_service = get_payment_service()

    # Account --------------------------------------------------------------------
    def get_account(self, user_id: str) -> Account:
        """Return the account summary for the user."""
        return self._account_service.get_account(user_id)

    def list_movements(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Movement]:
        """Return recent account movements."""
        return self._account_service.get_movements(user_id, skip=skip, limit=limit)

    def add_balance(
        self,
        user_id: str,
        amount: float,
        description: str,
        reference_id: Optional[str] = None,
    ) -> None:
        """Record a positive movement on the user's account."""
        self._account_service.add_payment(user_id, amount, description, reference_id)

    # Invoices -------------------------------------------------------------------
    def list_invoices(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        """Return invoices associated with the user."""
        return self._invoice_service.get_user_invoices(user_id, skip=skip, limit=limit)

    def list_pending_invoices(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        """Return only pending invoices."""
        invoices = self.list_invoices(user_id, skip=skip, limit=limit)
        return [invoice for invoice in invoices if invoice.estado == InvoiceStatus.PENDING]

    # Payments -------------------------------------------------------------------
    def pay_invoice(self, invoice_id: str, payload: PaymentCreate) -> Payment:
        """Register a payment for the given invoice."""
        return self._payment_service.create_payment(invoice_id, payload)


