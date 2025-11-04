from typing import Optional, List, Any, Dict
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from app.models.invoice_models import (
    Invoice, InvoiceCreate, Payment, PaymentCreate,
    Account, AccountResponse, InvoiceStatus, Movement, InvoiceItemCreate, InvoiceItem
)


class InvoiceRepository:
    def __init__(self, mongo_db: Database):
        self.invoices_col = mongo_db["invoices"]
        self.items_col = mongo_db["invoice_items"]         # nueva colección para items
        self.payments_col = mongo_db["payments"]
        self.accounts_col = mongo_db["accounts"]

    # ---------------------------
    # Invoice CRUD
    # ---------------------------
    def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice and its invoice_items (if any)."""
        # transformar a dict y calcular total
        invoice_dict = invoice_data.model_dump()
        total = sum(item.subtotal for item in invoice_data.items) if invoice_data.items else 0.0
        invoice_dict["total"] = total
        invoice_dict["estado"] = InvoiceStatus.PENDING
        invoice_dict["fecha_emision"] = invoice_dict.get("fecha_emision") or datetime.utcnow().isoformat()

        # insertar factura
        result = self.invoices_col.insert_one(invoice_dict)
        invoice_id_str = str(result.inserted_id)

        # normalizar y devolver _id como string
        invoice_dict["_id"] = invoice_id_str

        # insertar items (si existieran) y vincularlos con invoice_id
        created_items = []
        if invoice_data.items:
            for item in invoice_data.items:
                # se espera que item tenga: process_id (opt), request_id (opt), process_name, cantidad, subtotal
                item_doc = {
                    "invoice_id": invoice_id_str,
                    "request_id": getattr(item, "request_id", None),
                    "process_id": getattr(item, "process_id", None),
                    "process_name": getattr(item, "process_name", None),
                    "cantidad": getattr(item, "cantidad", 1),
                    "subtotal": float(getattr(item, "subtotal", 0.0))
                }
                # fecha y metadatos
                item_doc["created_at"] = datetime.utcnow().isoformat()
                r = self.items_col.insert_one(item_doc)
                item_doc["_id"] = str(r.inserted_id)
                created_items.append(item_doc)

        # Update user account with charge
        self.add_account_movement(
            invoice_data.user_id,
            "cargo",
            total,
            f"Factura #{invoice_dict['_id']}",
            invoice_dict["_id"]
        )

        # agregar items al objeto retornado
        invoice_dict["items"] = created_items

        # retornar como model Invoice (su constructor puede necesitar adaptaciones)
        return Invoice(**invoice_dict)

    def create_invoice_item(self, invoice_id: str, item_data: InvoiceItemCreate) -> InvoiceItem:
        """Create an invoice item linked to an existing invoice."""
        item_doc = {
            "invoice_id": invoice_id,
            "request_id": getattr(item_data, "request_id", None),
            "process_id": getattr(item_data, "process_id", None),
            "process_name": getattr(item_data, "process_name", None),
            "cantidad": getattr(item_data, "cantidad", 1),
            "subtotal": float(getattr(item_data, "subtotal", 0.0)),
            "created_at": datetime.utcnow().isoformat()
        }
        r = self.items_col.insert_one(item_doc)
        item_doc["_id"] = str(r.inserted_id)

        # actualizar total de la invoice (suma simple)
        try:
            # convertimos a ObjectId para hacer $inc si usás numeric en DB
            self.invoices_col.update_one(
                {"_id": ObjectId(invoice_id)},
                {"$inc": {"total": item_doc["subtotal"]}}
            )
        except Exception:
            # si invoice_id no es ObjectId (por ejemplo ya se almacena como string),
            # intentar buscar por campo string
            self.invoices_col.update_one(
                {"_id": invoice_id},
                {"$inc": {"total": item_doc["subtotal"]}}
            )

        return InvoiceItem(**item_doc)

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID and attach its items."""
        try:
            invoice = self.invoices_col.find_one({"_id": ObjectId(invoice_id)})
            if invoice:
                # convertir _id a string
                invoice_id_str = str(invoice["_id"])
                invoice["_id"] = invoice_id_str

                # recuperar items asociados (almacenados con invoice_id string)
                items = []
                for item in self.items_col.find({"invoice_id": invoice_id_str}):
                    item["_id"] = str(item["_id"])
                    items.append(item)
                invoice["items"] = items

                return Invoice(**invoice)
        except Exception:
            # Intento alternativo si el ID ya fue guardado como string no convertible
            invoice = self.invoices_col.find_one({"_id": invoice_id})
            if invoice:
                invoice_id_str = invoice.get("_id")
                invoice["_id"] = str(invoice["_id"])
                items = []
                for item in self.items_col.find({"invoice_id": invoice_id_str}):
                    item["_id"] = str(item["_id"])
                    items.append(item)
                invoice["items"] = items
                return Invoice(**invoice)
        return None

    def get_user_invoices(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Get all invoices for a user (with embedded items)."""
        invoices = []
        cursor = self.invoices_col.find({"user_id": user_id}).sort("fecha_emision", -1).skip(skip).limit(limit)
        for invoice in cursor:
            invoice_id_str = str(invoice["_id"])
            invoice["_id"] = invoice_id_str

            # traer items
            items = []
            for item in self.items_col.find({"invoice_id": invoice_id_str}):
                item["_id"] = str(item["_id"])
                items.append(item)
            invoice["items"] = items

            invoices.append(Invoice(**invoice))
        return invoices

    def get_invoices_by_request(self, request_id: str) -> List[Invoice]:
        """Return invoices that include items with the given request_id."""
        invoices = []
        # buscamos items con el request_id y agrupamos invoice_id
        invoice_ids = self.items_col.distinct("invoice_id", {"request_id": request_id})
        for inv_id in invoice_ids:
            inv = self.invoices_col.find_one({"_id": ObjectId(inv_id)}) if ObjectId.is_valid(inv_id) else self.invoices_col.find_one({"_id": inv_id})
            if inv:
                inv_id_str = str(inv["_id"])
                inv["_id"] = inv_id_str
                # embed items for that invoice (we can filter by request_id if se quiere)
                items = []
                for item in self.items_col.find({"invoice_id": inv_id_str, "request_id": request_id}):
                    item["_id"] = str(item["_id"])
                    items.append(item)
                inv["items"] = items
                invoices.append(Invoice(**inv))
        return invoices

    def update_invoice_status(self, invoice_id: str, status: InvoiceStatus) -> bool:
        """Update invoice status"""
        try:
            result = self.invoices_col.update_one(
                {"_id": ObjectId(invoice_id)},
                {"$set": {"estado": status}}
            )
            return result.modified_count > 0
        except Exception:
            # fallback si el _id se guardó como string
            result = self.invoices_col.update_one(
                {"_id": invoice_id},
                {"$set": {"estado": status}}
            )
            return result.modified_count > 0

    # ---------------------------
    # Payment CRUD
    # ---------------------------
    def create_payment(self, invoice_id: str, payment_data: PaymentCreate) -> Payment:
        """Create a payment record"""
        payment_dict = {
            "invoice_id": invoice_id,
            "monto": payment_data.monto,
            "metodo": payment_data.metodo,
            "fecha": datetime.utcnow().isoformat()
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
        except Exception:
            return None
        return None

    def get_invoice_payments(self, invoice_id: str) -> List[Payment]:
        """Get all payments for an invoice"""
        payments = []
        for payment in self.payments_col.find({"invoice_id": invoice_id}):
            payment["_id"] = str(payment["_id"])
            payments.append(Payment(**payment))
        return payments

    # ---------------------------
    # Account CRUD
    # ---------------------------
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
