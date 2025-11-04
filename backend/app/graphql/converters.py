from typing import List, Optional
from app.graphql import types
from app.models import (
    User, Sensor, Measurement, Alert, AlertRule, Process, ProcessRequest,
    Execution, Invoice, Payment, Account, Message, Group, UserResponse,
    SensorResponse, MeasurementResponse, MessageResponse, GroupResponse,
    AccountResponse, InvoiceItem
)
from app.models.alert_models import AlertStatus, AlertType
from app.models.sensor_models import SensorStatus, SensorType
from app.models.process_models import ProcessStatus, ProcessType
from app.models.invoice_models import InvoiceStatus, PaymentMethod
from app.models.message_models import MessageType
from app.models.user_models import UserStatus
from app.models.alert_rule_models import AlertRuleStatus, LocationScope


def convert_user(pydantic_user: User) -> types.User:
    """Convert Pydantic User to Strawberry User"""
    return types.User(
        id=pydantic_user.id,
        nombre_completo=pydantic_user.nombre_completo,
        email=str(pydantic_user.email),
        estado=types.UserStatus(pydantic_user.estado.value) if isinstance(pydantic_user.estado, UserStatus) else types.UserStatus(pydantic_user.estado),
        fecha_registro=pydantic_user.fecha_registro
    )


def convert_user_response(pydantic_user: UserResponse) -> types.User:
    """Convert Pydantic UserResponse to Strawberry User"""
    return types.User(
        id=pydantic_user.id,
        nombre_completo=pydantic_user.nombre_completo,
        email=pydantic_user.email,
        estado=types.UserStatus(pydantic_user.estado.value) if hasattr(pydantic_user.estado, 'value') else types.UserStatus(pydantic_user.estado),
        fecha_registro=pydantic_user.fecha_registro
    )


def convert_sensor(pydantic_sensor: Sensor) -> types.Sensor:
    """Convert Pydantic Sensor to Strawberry Sensor"""
    return types.Sensor(
        id=pydantic_sensor.id,
        sensor_id=pydantic_sensor.sensor_id,
        nombre=pydantic_sensor.nombre,
        tipo=types.SensorType(pydantic_sensor.tipo.value) if isinstance(pydantic_sensor.tipo, SensorType) else types.SensorType(pydantic_sensor.tipo),
        latitud=pydantic_sensor.latitud,
        longitud=pydantic_sensor.longitud,
        ciudad=pydantic_sensor.ciudad,
        pais=pydantic_sensor.pais,
        estado=types.SensorStatus(pydantic_sensor.estado.value) if isinstance(pydantic_sensor.estado, SensorStatus) else types.SensorStatus(pydantic_sensor.estado),
        fecha_inicio_emision=pydantic_sensor.fecha_inicio_emision
    )


def convert_sensor_response(pydantic_sensor: SensorResponse) -> types.Sensor:
    """Convert Pydantic SensorResponse to Strawberry Sensor"""
    return types.Sensor(
        id=pydantic_sensor.id,
        sensor_id=pydantic_sensor.sensor_id,
        nombre=pydantic_sensor.nombre,
        tipo=types.SensorType(pydantic_sensor.tipo.value) if hasattr(pydantic_sensor.tipo, 'value') else types.SensorType(pydantic_sensor.tipo),
        latitud=pydantic_sensor.latitud,
        longitud=pydantic_sensor.longitud,
        ciudad=pydantic_sensor.ciudad,
        pais=pydantic_sensor.pais,
        estado=types.SensorStatus(pydantic_sensor.estado.value) if hasattr(pydantic_sensor.estado, 'value') else types.SensorStatus(pydantic_sensor.estado),
        fecha_inicio_emision=pydantic_sensor.fecha_inicio_emision
    )


def convert_measurement(pydantic_measurement: Measurement) -> types.Measurement:
    """Convert Pydantic Measurement to Strawberry Measurement"""
    return types.Measurement(
        sensor_id=pydantic_measurement.sensor_id,
        timestamp=pydantic_measurement.timestamp,
        temperature=pydantic_measurement.temperature,
        humidity=pydantic_measurement.humidity
    )


def convert_measurement_response(pydantic_measurement: MeasurementResponse) -> types.Measurement:
    """Convert Pydantic MeasurementResponse to Strawberry Measurement"""
    return types.Measurement(
        sensor_id=pydantic_measurement.sensor_id,
        timestamp=pydantic_measurement.timestamp,
        temperature=pydantic_measurement.temperature,
        humidity=pydantic_measurement.humidity
    )


def convert_alert(pydantic_alert: Alert) -> types.Alert:
    """Convert Pydantic Alert to Strawberry Alert"""
    return types.Alert(
        id=pydantic_alert.id,
        tipo=types.AlertType(pydantic_alert.tipo.value) if isinstance(pydantic_alert.tipo, AlertType) else types.AlertType(pydantic_alert.tipo),
        sensor_id=pydantic_alert.sensor_id,
        fecha_hora=pydantic_alert.fecha_hora,
        descripcion=pydantic_alert.descripcion,
        estado=types.AlertStatus(pydantic_alert.estado.value) if isinstance(pydantic_alert.estado, AlertStatus) else types.AlertStatus(pydantic_alert.estado),
        valor=pydantic_alert.valor,
        umbral=pydantic_alert.umbral,
        rule_id=pydantic_alert.rule_id,
        rule_name=pydantic_alert.rule_name,
        prioridad=pydantic_alert.prioridad
    )


def convert_alert_rule(pydantic_rule) -> types.AlertRule:
    """Convert Pydantic AlertRule to Strawberry AlertRule"""
    return types.AlertRule(
        id=pydantic_rule.id,
        nombre=pydantic_rule.nombre,
        descripcion=pydantic_rule.descripcion,
        temp_min=pydantic_rule.temp_min,
        temp_max=pydantic_rule.temp_max,
        humidity_min=pydantic_rule.humidity_min,
        humidity_max=pydantic_rule.humidity_max,
        location_scope=types.LocationScope(pydantic_rule.location_scope.value) if hasattr(pydantic_rule.location_scope, 'value') else types.LocationScope(pydantic_rule.location_scope),
        ciudad=pydantic_rule.ciudad,
        region=pydantic_rule.region,
        pais=pydantic_rule.pais,
        fecha_inicio=pydantic_rule.fecha_inicio,
        fecha_fin=pydantic_rule.fecha_fin,
        estado=types.AlertRuleStatus(pydantic_rule.estado.value) if hasattr(pydantic_rule.estado, 'value') else types.AlertRuleStatus(pydantic_rule.estado),
        prioridad=pydantic_rule.prioridad,
        creado_por=pydantic_rule.creado_por,
        fecha_creacion=pydantic_rule.fecha_creacion,
        fecha_modificacion=pydantic_rule.fecha_modificacion
    )


def convert_process(pydantic_process: Process) -> types.Process:
    """Convert Pydantic Process to Strawberry Process"""
    return types.Process(
        id=pydantic_process.id,
        nombre=pydantic_process.nombre,
        descripcion=pydantic_process.descripcion,
        tipo=types.ProcessType(pydantic_process.tipo.value) if isinstance(pydantic_process.tipo, ProcessType) else types.ProcessType(pydantic_process.tipo),
        costo=pydantic_process.costo,
        parametros_schema=pydantic_process.parametros_schema,
        activo=getattr(pydantic_process, 'activo', True)
    )


def convert_process_request(pydantic_request: ProcessRequest) -> types.ProcessRequest:
    """Convert Pydantic ProcessRequest to Strawberry ProcessRequest"""
    return types.ProcessRequest(
        id=pydantic_request.id,
        user_id=pydantic_request.user_id,
        process_id=pydantic_request.process_id,
        fecha_solicitud=pydantic_request.fecha_solicitud,
        estado=types.ProcessStatus(pydantic_request.estado.value) if isinstance(pydantic_request.estado, ProcessStatus) else types.ProcessStatus(pydantic_request.estado),
        parametros=pydantic_request.parametros,
        invoice_id=getattr(pydantic_request, 'invoice_id', None),
        invoice_created=getattr(pydantic_request, 'invoice_created', False)
    )


def convert_execution(pydantic_execution: Execution) -> types.Execution:
    """Convert Pydantic Execution to Strawberry Execution"""
    return types.Execution(
        id=pydantic_execution.id,
        request_id=pydantic_execution.request_id,
        fecha_ejecucion=pydantic_execution.fecha_ejecucion,
        estado=types.ProcessStatus(pydantic_execution.estado.value) if isinstance(pydantic_execution.estado, ProcessStatus) else types.ProcessStatus(pydantic_execution.estado),
        resultado=pydantic_execution.resultado,
        error_message=pydantic_execution.error_message
    )


def convert_invoice_item(pydantic_item: InvoiceItem) -> types.InvoiceItem:
    """Convert Pydantic InvoiceItem to Strawberry InvoiceItem"""
    return types.InvoiceItem(
        process_id=pydantic_item.process_id,
        process_name=pydantic_item.process_name,
        cantidad=pydantic_item.cantidad,
        precio_unitario=pydantic_item.precio_unitario,
        subtotal=pydantic_item.subtotal
    )


def convert_invoice(pydantic_invoice: Invoice) -> types.Invoice:
    """Convert Pydantic Invoice to Strawberry Invoice"""
    return types.Invoice(
        id=pydantic_invoice.id,
        user_id=pydantic_invoice.user_id,
        fecha_emision=pydantic_invoice.fecha_emision,
        items=[convert_invoice_item(item) for item in pydantic_invoice.items],
        total=pydantic_invoice.total,
        estado=types.InvoiceStatus(pydantic_invoice.estado.value) if hasattr(pydantic_invoice.estado, 'value') else types.InvoiceStatus(pydantic_invoice.estado),
        fecha_vencimiento=pydantic_invoice.fecha_vencimiento
    )


def convert_payment(pydantic_payment: Payment) -> types.Payment:
    """Convert Pydantic Payment to Strawberry Payment"""
    return types.Payment(
        id=pydantic_payment.id,
        invoice_id=pydantic_payment.invoice_id,
        fecha_pago=pydantic_payment.fecha_pago,
        monto=pydantic_payment.monto,
        metodo=types.PaymentMethod(pydantic_payment.metodo.value) if hasattr(pydantic_payment.metodo, 'value') else types.PaymentMethod(pydantic_payment.metodo)
    )


def convert_movement(pydantic_movement) -> types.Movement:
    """Convert Pydantic Movement to Strawberry Movement"""
    return types.Movement(
        fecha=pydantic_movement.fecha,
        tipo=pydantic_movement.tipo,
        monto=pydantic_movement.monto,
        descripcion=pydantic_movement.descripcion,
        referencia_id=pydantic_movement.referencia_id
    )


def convert_account(pydantic_account: Account) -> types.Account:
    """Convert Pydantic Account to Strawberry Account"""
    return types.Account(
        id=pydantic_account.id,
        user_id=pydantic_account.user_id,
        saldo=pydantic_account.saldo,
        movimientos=[convert_movement(mov) for mov in pydantic_account.movimientos],
        fecha_creacion=pydantic_account.fecha_creacion
    )


def convert_account_response(pydantic_account: AccountResponse) -> types.Account:
    """Convert Pydantic AccountResponse to Strawberry Account"""
    return types.Account(
        id=pydantic_account.id,
        user_id=pydantic_account.user_id,
        saldo=pydantic_account.saldo,
        movimientos=[convert_movement(mov) for mov in pydantic_account.movimientos],
        fecha_creacion=pydantic_account.fecha_creacion
    )


def convert_message(pydantic_message: Message) -> types.Message:
    """Convert Pydantic Message to Strawberry Message"""
    return types.Message(
        id=pydantic_message.id,
        sender_id=pydantic_message.sender_id,
        sender_name=getattr(pydantic_message, 'sender_name', None),
        recipient_type=types.MessageType(pydantic_message.recipient_type.value) if isinstance(pydantic_message.recipient_type, MessageType) else types.MessageType(pydantic_message.recipient_type),
        recipient_id=pydantic_message.recipient_id,
        recipient_name=getattr(pydantic_message, 'recipient_name', None),
        timestamp=pydantic_message.timestamp,
        content=pydantic_message.content
    )


def convert_message_response(pydantic_message: MessageResponse) -> types.Message:
    """Convert Pydantic MessageResponse to Strawberry Message"""
    return types.Message(
        id=pydantic_message.id,
        sender_id=pydantic_message.sender_id,
        sender_name=pydantic_message.sender_name,
        recipient_type=types.MessageType(pydantic_message.recipient_type.value) if hasattr(pydantic_message.recipient_type, 'value') else types.MessageType(pydantic_message.recipient_type),
        recipient_id=pydantic_message.recipient_id,
        recipient_name=pydantic_message.recipient_name,
        timestamp=pydantic_message.timestamp,
        content=pydantic_message.content
    )


def convert_group(pydantic_group: Group) -> types.Group:
    """Convert Pydantic Group to Strawberry Group"""
    return types.Group(
        id=pydantic_group.id,
        nombre=pydantic_group.nombre,
        miembros=pydantic_group.miembros,
        fecha_creacion=pydantic_group.fecha_creacion
    )


def convert_group_response(pydantic_group: GroupResponse) -> types.Group:
    """Convert Pydantic GroupResponse to Strawberry Group"""
    return types.Group(
        id=pydantic_group.id,
        nombre=pydantic_group.nombre,
        miembros=pydantic_group.miembros,
        fecha_creacion=pydantic_group.fecha_creacion
    )
