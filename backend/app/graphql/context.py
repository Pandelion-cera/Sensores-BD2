from typing import Optional, Dict, Any
from strawberry.fastapi import BaseContext
from fastapi import Request
from app.core.security import decode_access_token
from app.core.database import db_manager

# Import all service dependencies
from app.repositories.sensor_repository import SensorRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.alert_rule_repository import AlertRuleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.process_repository import ProcessRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.session_repository import SessionRepository

from app.services.sensor_service import SensorService
from app.services.alert_service import AlertService
from app.services.alert_rule_service import AlertRuleService
from app.services.auth_service import AuthService
from app.services.process_service import ProcessService
from app.services.invoice_service import InvoiceService
from app.services.user_service import UserService
from app.services.message_service import MessageService
from app.core.config import settings


class GraphQLContext(BaseContext):
    def __init__(self, request: Request):
        self.request = request
        self.user: Optional[Dict[str, Any]] = None
        self._auth_service: Optional[AuthService] = None
        self._sensor_service: Optional[SensorService] = None
        self._alert_service: Optional[AlertService] = None
        self._alert_rule_service: Optional[AlertRuleService] = None
        self._process_service: Optional[ProcessService] = None
        self._invoice_service: Optional[InvoiceService] = None
        self._user_service: Optional[UserService] = None
        self._message_service: Optional[MessageService] = None
        self._group_repo: Optional[GroupRepository] = None
        
        # Extract and decode JWT token from headers
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                self.user = decode_access_token(token)
            except Exception:
                self.user = None
    
    @property
    def user_id(self) -> Optional[str]:
        """Get current user ID"""
        return self.user.get("user_id") if self.user else None
    
    @property
    def role(self) -> Optional[str]:
        """Get current user role"""
        return self.user.get("role") if self.user else None
    
    def require_auth(self):
        """Require authentication"""
        if not self.user:
            raise Exception("Authentication required")
        return self.user
    
    def require_role(self, allowed_roles: list):
        """Require specific role"""
        user = self.require_auth()
        if user.get("role") not in allowed_roles:
            raise Exception(f"Insufficient permissions. Required roles: {allowed_roles}")
        return user
    
    @property
    def auth_service(self) -> AuthService:
        """Get auth service instance"""
        if self._auth_service is None:
            user_repo = UserRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())
            session_repo = SessionRepository(db_manager.get_redis_client())
            self._auth_service = AuthService(user_repo, session_repo)
        return self._auth_service
    
    @property
    def sensor_service(self) -> SensorService:
        """Get sensor service instance"""
        if self._sensor_service is None:
            sensor_repo = SensorRepository(db_manager.get_mongo_db())
            measurement_repo = MeasurementRepository(db_manager.get_cassandra_session(), settings.CASSANDRA_KEYSPACE)
            alert_repo = AlertRepository(db_manager.get_mongo_db(), db_manager.get_redis_client())
            alert_service = AlertService(alert_repo)
            rule_repo = AlertRuleRepository(db_manager.get_mongo_db())
            alert_rule_service = AlertRuleService(rule_repo, alert_repo)
            self._sensor_service = SensorService(sensor_repo, measurement_repo, alert_service, alert_rule_service)
        return self._sensor_service
    
    @property
    def alert_service(self) -> AlertService:
        """Get alert service instance"""
        if self._alert_service is None:
            alert_repo = AlertRepository(db_manager.get_mongo_db(), db_manager.get_redis_client())
            self._alert_service = AlertService(alert_repo)
        return self._alert_service
    
    @property
    def alert_rule_service(self) -> AlertRuleService:
        """Get alert rule service instance"""
        if self._alert_rule_service is None:
            rule_repo = AlertRuleRepository(db_manager.get_mongo_db())
            alert_repo = AlertRepository(db_manager.get_mongo_db(), db_manager.get_redis_client())
            self._alert_rule_service = AlertRuleService(rule_repo, alert_repo)
        return self._alert_rule_service
    
    @property
    def process_service(self) -> ProcessService:
        """Get process service instance"""
        if self._process_service is None:
            process_repo = ProcessRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())
            measurement_repo = MeasurementRepository(db_manager.get_cassandra_session(), settings.CASSANDRA_KEYSPACE)
            sensor_repo = SensorRepository(db_manager.get_mongo_db())
            self._process_service = ProcessService(process_repo, measurement_repo, sensor_repo)
        return self._process_service
    
    @property
    def invoice_service(self) -> InvoiceService:
        """Get invoice service instance"""
        if self._invoice_service is None:
            invoice_repo = InvoiceRepository(db_manager.get_mongo_db())
            process_repo = ProcessRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())
            self._invoice_service = InvoiceService(invoice_repo, process_repo)
        return self._invoice_service
    
    @property
    def user_service(self) -> UserService:
        """Get user service instance"""
        if self._user_service is None:
            user_repo = UserRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())
            invoice_repo = InvoiceRepository(db_manager.get_mongo_db())
            self._user_service = UserService(user_repo, invoice_repo)
        return self._user_service
    
    @property
    def message_service(self) -> MessageService:
        """Get message service instance"""
        if self._message_service is None:
            message_repo = MessageRepository(db_manager.get_mongo_db())
            group_repo = GroupRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())
            user_repo = UserRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())
            self._message_service = MessageService(message_repo, group_repo, user_repo)
        return self._message_service
    
    @property
    def group_repo(self) -> GroupRepository:
        """Get group repository instance"""
        if self._group_repo is None:
            self._group_repo = GroupRepository(db_manager.get_mongo_db(), db_manager.get_neo4j_driver())
        return self._group_repo


def get_context(request: Request) -> GraphQLContext:
    """Get GraphQL context from request"""
    return GraphQLContext(request)
