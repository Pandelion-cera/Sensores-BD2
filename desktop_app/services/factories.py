from __future__ import annotations

from functools import lru_cache

from desktop_app.core.config import settings
from desktop_app.core.database import db_manager
from desktop_app.repositories.account_repository import AccountRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.repositories.alert_rule_repository import AlertRuleRepository
from desktop_app.repositories.group_repository import GroupRepository
from desktop_app.repositories.invoice_repository import InvoiceRepository
from desktop_app.repositories.maintenance_repository import MaintenanceRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.message_repository import MessageRepository
from desktop_app.repositories.payment_repository import PaymentRepository
from desktop_app.repositories.process_repository import ProcessRepository
from desktop_app.repositories.scheduled_process_repository import ScheduledProcessRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.session_repository import SessionRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.account_service import AccountService
from desktop_app.services.alert_rule_service import AlertRuleService
from desktop_app.services.alert_service import AlertService
from desktop_app.services.auth_service import AuthService
from desktop_app.services.dashboard_service import DashboardService
from desktop_app.services.group_service import GroupService
from desktop_app.services.invoice_service import InvoiceService
from desktop_app.services.maintenance_service import MaintenanceService
from desktop_app.services.message_service import MessageService
from desktop_app.services.payment_service import PaymentService
from desktop_app.services.process_scheduler_service import ProcessSchedulerService
from desktop_app.services.process_service import ProcessService
from desktop_app.services.scheduled_process_service import ScheduledProcessService
from desktop_app.services.sensor_service import SensorService
from desktop_app.services.session_service import SessionService
from desktop_app.services.user_service import UserService


# ---------------------------------------------------------------------------
# Repository factories
# ---------------------------------------------------------------------------


@lru_cache
def get_sensor_repository() -> SensorRepository:
    return SensorRepository(db_manager.get_mongo_db())


@lru_cache
def get_measurement_repository() -> MeasurementRepository:
    return MeasurementRepository(
        db_manager.get_cassandra_session(),
        settings.CASSANDRA_KEYSPACE,
    )


@lru_cache
def get_alert_repository() -> AlertRepository:
    return AlertRepository(db_manager.get_mongo_db(), db_manager.get_redis_client())


@lru_cache
def get_alert_rule_repository() -> AlertRuleRepository:
    return AlertRuleRepository(db_manager.get_mongo_db())


@lru_cache
def get_user_repository() -> UserRepository:
    return UserRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())


@lru_cache
def get_session_repository() -> SessionRepository:
    return SessionRepository(db_manager.get_redis_client(), db_manager.get_mongo_db())


@lru_cache
def get_account_repository() -> AccountRepository:
    return AccountRepository(db_manager.get_mongo_db())


@lru_cache
def get_invoice_repository() -> InvoiceRepository:
    return InvoiceRepository(db_manager.get_mongo_db())


@lru_cache
def get_payment_repository() -> PaymentRepository:
    return PaymentRepository(db_manager.get_mongo_db())


@lru_cache
def get_process_repository() -> ProcessRepository:
    return ProcessRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())


@lru_cache
def get_scheduled_process_repository() -> ScheduledProcessRepository:
    return ScheduledProcessRepository(db_manager.get_mongo_db())


@lru_cache
def get_group_repository() -> GroupRepository:
    return GroupRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())


@lru_cache
def get_message_repository() -> MessageRepository:
    return MessageRepository(db_manager.get_mongo_db())


@lru_cache
def get_maintenance_repository() -> MaintenanceRepository:
    return MaintenanceRepository(db_manager.get_mongo_db())


# ---------------------------------------------------------------------------
# Service factories
# ---------------------------------------------------------------------------


@lru_cache
def get_alert_service() -> AlertService:
    return AlertService(get_alert_repository())


@lru_cache
def get_alert_rule_service() -> AlertRuleService:
    return AlertRuleService(get_alert_rule_repository(), get_alert_repository())


@lru_cache
def get_user_service() -> UserService:
    return UserService(get_user_repository(), get_account_repository())


@lru_cache
def get_sensor_service() -> SensorService:
    return SensorService(
        get_sensor_repository(),
        get_measurement_repository(),
        get_alert_service(),
        alert_rule_service=get_alert_rule_service(),
        user_repo=get_user_repository(),
    )


@lru_cache
def get_account_service() -> AccountService:
    return AccountService(get_account_repository())


@lru_cache
def get_invoice_service() -> InvoiceService:
    return InvoiceService(
        get_invoice_repository(),
        get_process_repository(),
        get_account_service(),
    )


@lru_cache
def get_payment_service() -> PaymentService:
    return PaymentService(
        get_payment_repository(),
        get_invoice_repository(),
        get_account_repository(),
    )


@lru_cache
def get_process_service() -> ProcessService:
    return ProcessService(
        get_process_repository(),
        get_measurement_repository(),
        get_sensor_repository(),
        get_user_repository(),
        get_invoice_repository(),
        get_account_service(),
        get_alert_service(),
        get_alert_rule_service(),
    )


@lru_cache
def get_scheduled_process_service() -> ScheduledProcessService:
    return ScheduledProcessService(get_scheduled_process_repository())


@lru_cache
def get_process_scheduler_service() -> ProcessSchedulerService:
    return ProcessSchedulerService(
        get_scheduled_process_repository(),
        get_scheduled_process_service(),
        get_process_service(),
    )


@lru_cache
def get_message_service() -> MessageService:
    return MessageService(
        get_message_repository(),
        get_group_repository(),
        get_user_repository(),
    )


@lru_cache
def get_group_service() -> GroupService:
    return GroupService(get_group_repository())


@lru_cache
def get_maintenance_service() -> MaintenanceService:
    return MaintenanceService(
        get_maintenance_repository(),
        get_sensor_repository(),
        get_user_repository(),
    )


@lru_cache
def get_session_service() -> SessionService:
    return SessionService(get_session_repository())


@lru_cache
def get_dashboard_service() -> DashboardService:
    return DashboardService(
        get_sensor_repository(),
        get_alert_repository(),
    )


@lru_cache
def get_auth_service() -> AuthService:
    return AuthService(
        get_user_repository(),
        get_session_repository(),
    )


