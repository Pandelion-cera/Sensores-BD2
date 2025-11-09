"""
Controller factories for the desktop application.

The UI layer should depend exclusively on these helpers instead of
instantiating repositories or services directly.
"""
from functools import lru_cache

from .auth_controller import AuthController
from .dashboard_controller import DashboardController
from .sensor_controller import SensorController
from .alert_controller import AlertController
from .alert_rule_controller import AlertRuleController
from .message_controller import MessageController
from .group_controller import GroupController
from .account_controller import AccountController
from .process_controller import ProcessController
from .maintenance_controller import MaintenanceController
from .session_controller import SessionController


@lru_cache(maxsize=1)
def get_auth_controller() -> AuthController:
    """Return a singleton auth controller instance."""
    return AuthController()


@lru_cache(maxsize=1)
def get_dashboard_controller() -> DashboardController:
    """Return a singleton dashboard controller instance."""
    return DashboardController()


@lru_cache(maxsize=1)
def get_sensor_controller() -> SensorController:
    """Return a singleton sensor controller instance."""
    return SensorController()


@lru_cache(maxsize=1)
def get_alert_controller() -> AlertController:
    """Return a singleton alert controller instance."""
    return AlertController()


@lru_cache(maxsize=1)
def get_alert_rule_controller() -> AlertRuleController:
    """Return a singleton alert rule controller instance."""
    return AlertRuleController()


@lru_cache(maxsize=1)
def get_message_controller() -> MessageController:
    """Return a singleton message controller instance."""
    return MessageController()


@lru_cache(maxsize=1)
def get_group_controller() -> GroupController:
    """Return a singleton group controller instance."""
    return GroupController()


@lru_cache(maxsize=1)
def get_account_controller() -> AccountController:
    """Return a singleton account controller instance."""
    return AccountController()


@lru_cache(maxsize=1)
def get_process_controller() -> ProcessController:
    """Return a singleton process controller instance."""
    return ProcessController()


@lru_cache(maxsize=1)
def get_maintenance_controller() -> MaintenanceController:
    """Return a singleton maintenance controller instance."""
    return MaintenanceController()


@lru_cache(maxsize=1)
def get_session_controller() -> SessionController:
    """Return a singleton session controller instance."""
    return SessionController()


