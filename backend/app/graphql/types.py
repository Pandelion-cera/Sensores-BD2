import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime


# Enums
@strawberry.enum
class UserStatus:
    ACTIVE = "activo"
    INACTIVE = "inactivo"


@strawberry.enum
class SensorType:
    TEMPERATURE = "temperatura"
    HUMIDITY = "humedad"
    BOTH = "temperatura_humedad"


@strawberry.enum
class SensorStatus:
    ACTIVE = "activo"
    INACTIVE = "inactivo"
    FAILURE = "falla"


@strawberry.enum
class AlertType:
    SENSOR_FAILURE = "sensor"
    CLIMATE = "climatica"
    THRESHOLD = "umbral"


@strawberry.enum
class AlertStatus:
    ACTIVE = "activa"
    RESOLVED = "resuelta"
    ACKNOWLEDGED = "reconocida"


@strawberry.enum
class AlertRuleStatus:
    ACTIVE = "activa"
    INACTIVE = "inactiva"


@strawberry.enum
class LocationScope:
    CITY = "ciudad"
    REGION = "region"
    COUNTRY = "pais"


@strawberry.enum
class ProcessType:
    TEMP_MAX_MIN_REPORT = "informe_max_min"
    TEMP_AVG_REPORT = "informe_promedio"
    ALERT_CONFIG = "configuracion_alertas"
    ONLINE_QUERY = "consulta_online"
    PERIODIC_REPORT = "reporte_periodico"


@strawberry.enum
class ProcessStatus:
    PENDING = "pendiente"
    EXECUTING = "ejecutando"
    COMPLETED = "completado"
    FAILED = "fallido"
    CANCELLED = "cancelado"


@strawberry.enum
class InvoiceStatus:
    PENDING = "pendiente"
    PAID = "pagada"
    OVERDUE = "vencida"
    CANCELLED = "cancelada"


@strawberry.enum
class PaymentMethod:
    CREDIT_CARD = "tarjeta_credito"
    DEBIT_CARD = "tarjeta_debito"
    BANK_TRANSFER = "transferencia"
    ACCOUNT_BALANCE = "saldo_cuenta"


@strawberry.enum
class MessageType:
    PRIVATE = "privado"
    GROUP = "grupal"


# Types
@strawberry.type
class User:
    id: Optional[str] = None
    nombre_completo: str
    email: str
    estado: UserStatus
    fecha_registro: datetime


@strawberry.type
class Sensor:
    id: Optional[str] = None
    sensor_id: str
    nombre: str
    tipo: SensorType
    latitud: float
    longitud: float
    ciudad: str
    pais: str
    estado: SensorStatus
    fecha_inicio_emision: datetime


@strawberry.type
class Measurement:
    sensor_id: str
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None


@strawberry.type
class Alert:
    id: Optional[str] = None
    tipo: AlertType
    sensor_id: Optional[str] = None
    fecha_hora: datetime
    descripcion: str
    estado: AlertStatus
    valor: Optional[float] = None
    umbral: Optional[float] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    prioridad: Optional[int] = None


@strawberry.type
class AlertRule:
    id: Optional[str] = None
    nombre: str
    descripcion: str
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    humidity_min: Optional[float] = None
    humidity_max: Optional[float] = None
    location_scope: LocationScope
    ciudad: Optional[str] = None
    region: Optional[str] = None
    pais: str
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: AlertRuleStatus
    prioridad: int
    creado_por: str
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime] = None


@strawberry.type
class Process:
    id: Optional[str] = None
    nombre: str
    descripcion: str
    tipo: ProcessType
    costo: float
    parametros_schema: Dict[str, Any]
    activo: bool = True


@strawberry.type
class ProcessRequest:
    id: Optional[str] = None
    user_id: str
    process_id: str
    fecha_solicitud: datetime
    estado: ProcessStatus
    parametros: Dict[str, Any]
    invoice_id: Optional[str] = None
    invoice_created: bool = False


@strawberry.type
class Execution:
    id: Optional[str] = None
    request_id: str
    fecha_ejecucion: Optional[datetime] = None
    estado: ProcessStatus
    resultado: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@strawberry.type
class InvoiceItem:
    process_id: str
    process_name: str
    cantidad: int
    precio_unitario: float
    subtotal: float


@strawberry.type
class Invoice:
    id: Optional[str] = None
    user_id: str
    fecha_emision: datetime
    items: List[InvoiceItem]
    total: float
    estado: InvoiceStatus
    fecha_vencimiento: Optional[datetime] = None


@strawberry.type
class Payment:
    id: Optional[str] = None
    invoice_id: str
    fecha_pago: datetime
    monto: float
    metodo: PaymentMethod


@strawberry.type
class Movement:
    fecha: datetime
    tipo: str
    monto: float
    descripcion: str
    referencia_id: Optional[str] = None


@strawberry.type
class Account:
    id: Optional[str] = None
    user_id: str
    saldo: float
    movimientos: List[Movement]
    fecha_creacion: datetime


@strawberry.type
class Message:
    id: Optional[str] = None
    sender_id: str
    sender_name: Optional[str] = None
    recipient_type: MessageType
    recipient_id: str
    recipient_name: Optional[str] = None
    timestamp: datetime
    content: str


@strawberry.type
class Group:
    id: Optional[str] = None
    nombre: str
    miembros: List[str]
    fecha_creacion: datetime


@strawberry.type
class SensorStats:
    total: int
    activos: int
    inactivos: int
    con_falla: int


@strawberry.type
class LocationStats:
    temperatura_max: Optional[float] = None
    temperatura_min: Optional[float] = None
    temperatura_promedio: Optional[float] = None
    humedad_max: Optional[float] = None
    humedad_min: Optional[float] = None
    humedad_promedio: Optional[float] = None
    total_mediciones: int


@strawberry.type
class AlertRulesSummary:
    total: int
    activas: int
    inactivas: int


@strawberry.type
class AlertsSummary:
    total: int
    activas: int
    resueltas: int
    reconocidas: int


# Input Types
@strawberry.input
class UserCreateInput:
    nombre_completo: str
    email: str
    password: str


@strawberry.input
class UserLoginInput:
    email: str
    password: str


@strawberry.input
class SensorCreateInput:
    nombre: str
    tipo: SensorType
    latitud: float
    longitud: float
    ciudad: str
    pais: str
    estado: Optional[SensorStatus] = SensorStatus.ACTIVE


@strawberry.input
class SensorUpdateInput:
    nombre: Optional[str] = None
    estado: Optional[SensorStatus] = None


@strawberry.input
class MeasurementCreateInput:
    temperature: Optional[float] = None
    humidity: Optional[float] = None


@strawberry.input
class AlertCreateInput:
    tipo: AlertType
    sensor_id: Optional[str] = None
    descripcion: str
    valor: Optional[float] = None
    umbral: Optional[float] = None


@strawberry.input
class AlertRuleCreateInput:
    nombre: str
    descripcion: str
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    humidity_min: Optional[float] = None
    humidity_max: Optional[float] = None
    location_scope: LocationScope
    ciudad: Optional[str] = None
    region: Optional[str] = None
    pais: str
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: Optional[AlertRuleStatus] = AlertRuleStatus.ACTIVE
    prioridad: Optional[int] = 1


@strawberry.input
class AlertRuleUpdateInput:
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    humidity_min: Optional[float] = None
    humidity_max: Optional[float] = None
    location_scope: Optional[LocationScope] = None
    ciudad: Optional[str] = None
    region: Optional[str] = None
    pais: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: Optional[AlertRuleStatus] = None
    prioridad: Optional[int] = None


@strawberry.input
class ProcessCreateInput:
    nombre: str
    descripcion: str
    tipo: ProcessType
    costo: float
    parametros_schema: Dict[str, Any]


@strawberry.input
class ProcessRequestCreateInput:
    process_id: str
    parametros: Dict[str, Any]


@strawberry.input
class PaymentCreateInput:
    monto: float
    metodo: PaymentMethod


@strawberry.input
class MessageCreateInput:
    recipient_type: MessageType
    recipient_id: str
    content: str


@strawberry.input
class GroupCreateInput:
    nombre: str
    miembros: List[str]


# Auth Response Types
@strawberry.type
class AuthResponse:
    access_token: str
    token_type: str
    user: User
    session_id: str


@strawberry.type
class RegisterResponse:
    user: User
    message: str
