from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class InvoiceStatus(str, Enum):
    PENDING = "pendiente"
    PAID = "pagada"
    OVERDUE = "vencida"
    CANCELLED = "cancelada"


class InvoiceItem(BaseModel):
    process_id: str
    process_name: str
    cantidad: int = 1
    precio_unitario: float
    subtotal: float


class Invoice(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    fecha_emision: datetime = Field(default_factory=datetime.utcnow)
    items: List[InvoiceItem] = Field(default_factory=list)
    total: float = 0.0
    estado: InvoiceStatus = InvoiceStatus.PENDING
    fecha_vencimiento: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class InvoiceCreate(BaseModel):
    user_id: str
    items: List[InvoiceItem]
    fecha_vencimiento: Optional[datetime] = None


class PaymentMethod(str, Enum):
    CREDIT_CARD = "tarjeta_credito"
    DEBIT_CARD = "tarjeta_debito"
    BANK_TRANSFER = "transferencia"
    ACCOUNT_BALANCE = "saldo_cuenta"


class Payment(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    invoice_id: str
    fecha_pago: datetime = Field(default_factory=datetime.utcnow)
    monto: float
    metodo: PaymentMethod
    
    class Config:
        populate_by_name = True


class PaymentCreate(BaseModel):
    monto: float = Field(..., gt=0)
    metodo: PaymentMethod
    
    class Config:
        json_schema_extra = {
            "example": {
                "monto": 50.00,
                "metodo": "tarjeta_credito"
            }
        }


class Movement(BaseModel):
    fecha: datetime
    tipo: str  # "cargo" or "abono"
    monto: float
    descripcion: str
    referencia_id: Optional[str] = None


class Account(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    saldo: float = 0.0
    movimientos: List[Movement] = Field(default_factory=list)
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class AccountResponse(BaseModel):
    id: str
    user_id: str
    saldo: float
    movimientos: List[Movement]
    fecha_creacion: datetime

