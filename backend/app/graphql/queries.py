import strawberry
from typing import List, Optional
from datetime import datetime
from app.graphql import types
from app.graphql.context import GraphQLContext
from app.graphql.converters import (
    convert_user_response, convert_sensor, convert_sensor_response,
    convert_measurement_response, convert_alert, convert_alert_rule,
    convert_process, convert_process_request, convert_execution,
    convert_invoice, convert_account_response, convert_message_response,
    convert_group_response
)
from app.models.sensor_models import SensorStatus
from app.models.alert_models import AlertStatus, AlertType
from app.models.alert_rule_models import AlertRuleStatus


@strawberry.type
class Query:
    # User queries
    @strawberry.field
    def me(self, info: strawberry.Info[GraphQLContext]) -> types.User:
        """Get current authenticated user"""
        user = info.context.require_auth()
        user_obj = info.context.user_service.get_user(user["user_id"])
        if not user_obj:
            raise Exception("User not found")
        return convert_user_response(user_obj)
    
    @strawberry.field
    def users(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 100
    ) -> List[types.User]:
        """Get all users (admin only)"""
        info.context.require_role(["administrador"])
        users = info.context.user_service.get_all_users(skip, limit)
        return [convert_user_response(u) for u in users]
    
    @strawberry.field
    def user(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.User]:
        """Get user by ID"""
        info.context.require_auth()
        user_obj = info.context.user_service.get_user(id)
        return convert_user_response(user_obj) if user_obj else None
    
    # Sensor queries
    @strawberry.field
    def sensors(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 100,
        pais: Optional[str] = None,
        ciudad: Optional[str] = None,
        estado: Optional[types.SensorStatus] = None
    ) -> List[types.Sensor]:
        """Get all sensors with optional filters"""
        estado_filter = SensorStatus(estado.value) if estado else None
        sensors = info.context.sensor_service.get_all_sensors(
            skip, limit, pais, ciudad, estado_filter
        )
        return [convert_sensor(s) for s in sensors]
    
    @strawberry.field
    def sensor(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.Sensor]:
        """Get sensor by ID"""
        sensor = info.context.sensor_service.get_sensor(id)
        return convert_sensor(sensor) if sensor else None
    
    @strawberry.field
    def sensor_stats(
        self,
        info: strawberry.Info[GraphQLContext]
    ) -> types.SensorStats:
        """Get sensor statistics"""
        stats = info.context.sensor_service.get_dashboard_stats()
        return types.SensorStats(
            total=stats.get("total", 0),
            activos=stats.get("activos", 0),
            inactivos=stats.get("inactivos", 0),
            con_falla=stats.get("con_falla", 0)
        )
    
    # Measurement queries
    @strawberry.field
    def sensor_measurements(
        self,
        info: strawberry.Info[GraphQLContext],
        sensor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[types.Measurement]:
        """Get measurements for a sensor"""
        measurements = info.context.sensor_service.get_sensor_measurements(
            sensor_id, start_date, end_date
        )
        # Convert dict to MeasurementResponse format
        from app.models.measurement_models import MeasurementResponse
        results = []
        for m in measurements:
            results.append(types.Measurement(
                sensor_id=m["sensor_id"],
                timestamp=m["timestamp"],
                temperature=m.get("temperatura"),
                humidity=m.get("humedad")
            ))
        return results
    
    @strawberry.field
    def location_measurements(
        self,
        info: strawberry.Info[GraphQLContext],
        pais: str,
        ciudad: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[types.Measurement]:
        """Get measurements for a location"""
        measurements = info.context.sensor_service.get_location_measurements(
            pais, ciudad, start_date, end_date
        )
        results = []
        for m in measurements:
            results.append(types.Measurement(
                sensor_id=m["sensor_id"],
                timestamp=m["timestamp"],
                temperature=m.get("temperatura"),
                humidity=m.get("humedad")
            ))
        return results
    
    @strawberry.field
    def location_stats(
        self,
        info: strawberry.Info[GraphQLContext],
        pais: str,
        ciudad: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> types.LocationStats:
        """Get statistics for a location"""
        stats = info.context.sensor_service.get_location_stats(
            pais, ciudad, start_date, end_date
        )
        temp_stats = stats.get("temperatura", {})
        humidity_stats = stats.get("humedad", {})
        return types.LocationStats(
            temperatura_max=temp_stats.get("max"),
            temperatura_min=temp_stats.get("min"),
            temperatura_promedio=temp_stats.get("avg"),
            humedad_max=humidity_stats.get("max"),
            humedad_min=humidity_stats.get("min"),
            humedad_promedio=humidity_stats.get("avg"),
            total_mediciones=stats.get("count", 0)
        )
    
    # Alert queries
    @strawberry.field
    def alerts(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 100,
        estado: Optional[types.AlertStatus] = None,
        tipo: Optional[types.AlertType] = None,
        sensor_id: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[types.Alert]:
        """Get all alerts with optional filters"""
        estado_filter = AlertStatus(estado.value) if estado else None
        tipo_filter = AlertType(tipo.value).value if tipo else None
        alerts = info.context.alert_service.get_all_alerts(
            skip, limit, estado_filter, sensor_id, tipo_filter, fecha_desde, fecha_hasta
        )
        return [convert_alert(a) for a in alerts]
    
    @strawberry.field
    def active_alerts(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 100
    ) -> List[types.Alert]:
        """Get all active alerts"""
        alerts = info.context.alert_service.get_active_alerts(skip, limit)
        return [convert_alert(a) for a in alerts]
    
    @strawberry.field
    def alert(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.Alert]:
        """Get alert by ID"""
        alert = info.context.alert_service.get_alert(id)
        return convert_alert(alert) if alert else None
    
    @strawberry.field
    def alerts_by_location(
        self,
        info: strawberry.Info[GraphQLContext],
        pais: Optional[str] = None,
        ciudad: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[types.AlertStatus] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[types.Alert]:
        """Get alerts filtered by location"""
        estado_filter = AlertStatus(estado.value) if estado else None
        alerts = info.context.alert_service.get_alerts_by_location(
            pais, ciudad, skip, limit, estado_filter, fecha_desde, fecha_hasta
        )
        # Convert dict to Alert
        results = []
        for alert_dict in alerts:
            from app.models.alert_models import Alert
            alert = Alert(**alert_dict)
            results.append(convert_alert(alert))
        return results
    
    @strawberry.field
    def alerts_summary(
        self,
        info: strawberry.Info[GraphQLContext]
    ) -> types.AlertsSummary:
        """Get alerts summary statistics"""
        summary = info.context.alert_service.get_summary()
        return types.AlertsSummary(
            total=summary.get("total", 0),
            activas=summary.get("activas", 0),
            resueltas=summary.get("resueltas", 0),
            reconocidas=summary.get("reconocidas", 0)
        )
    
    # Alert Rule queries
    @strawberry.field
    def alert_rules(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 100,
        estado: Optional[types.AlertRuleStatus] = None
    ) -> List[types.AlertRule]:
        """Get all alert rules"""
        estado_filter = AlertRuleStatus(estado.value) if estado else None
        rules = info.context.alert_rule_service.get_all_rules(skip, limit, estado_filter)
        return [convert_alert_rule(r) for r in rules]
    
    @strawberry.field
    def alert_rule(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.AlertRule]:
        """Get alert rule by ID"""
        rule = info.context.alert_rule_service.get_rule(id)
        return convert_alert_rule(rule) if rule else None
    
    @strawberry.field
    def alert_rules_summary(
        self,
        info: strawberry.Info[GraphQLContext]
    ) -> types.AlertRulesSummary:
        """Get alert rules summary"""
        summary = info.context.alert_rule_service.get_summary()
        return types.AlertRulesSummary(
            total=summary.get("total", 0),
            activas=summary.get("activas", 0),
            inactivas=summary.get("inactivas", 0)
        )
    
    # Process queries
    @strawberry.field
    def processes(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 100
    ) -> List[types.Process]:
        """Get all available processes"""
        processes = info.context.process_service.get_all_processes(skip, limit)
        return [convert_process(p) for p in processes]
    
    @strawberry.field
    def process(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.Process]:
        """Get process by ID"""
        process = info.context.process_service.get_process(id)
        return convert_process(process) if process else None
    
    @strawberry.field
    def user_process_requests(
        self,
        info: strawberry.Info[GraphQLContext],
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[types.ProcessRequest]:
        """Get process requests for a user"""
        info.context.require_auth()
        # Verify user can access these requests
        current_user = info.context.user
        if current_user["user_id"] != user_id and current_user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        requests = info.context.process_service.get_user_requests(user_id, skip, limit)
        return [convert_process_request(r) for r in requests]
    
    @strawberry.field
    def execution(
        self,
        info: strawberry.Info[GraphQLContext],
        request_id: str
    ) -> Optional[types.Execution]:
        """Get execution result for a request"""
        info.context.require_auth()
        execution = info.context.process_service.get_execution(request_id)
        return convert_execution(execution) if execution else None
    
    # Invoice queries
    @strawberry.field
    def my_invoices(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 100
    ) -> List[types.Invoice]:
        """Get current user's invoices"""
        user = info.context.require_auth()
        invoices = info.context.invoice_service.get_user_invoices(
            user["user_id"], skip, limit
        )
        return [convert_invoice(inv) for inv in invoices]
    
    @strawberry.field
    def invoice(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.Invoice]:
        """Get invoice by ID"""
        user = info.context.require_auth()
        invoice = info.context.invoice_service.get_invoice(id)
        if not invoice:
            return None
        # Verify user owns invoice or is admin
        if invoice.user_id != user["user_id"] and user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        return convert_invoice(invoice)
    
    @strawberry.field
    def my_account(
        self,
        info: strawberry.Info[GraphQLContext]
    ) -> Optional[types.Account]:
        """Get current user's account"""
        user = info.context.require_auth()
        account = info.context.user_service.get_user_account(user["user_id"])
        return convert_account_response(account) if account else None
    
    # Message queries
    @strawberry.field
    def my_messages(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 50
    ) -> List[types.Message]:
        """Get current user's messages (private and group)"""
        user = info.context.require_auth()
        messages_data = info.context.message_service.get_all_user_messages(
            user["user_id"], skip, limit
        )
        # Combine private and group messages
        private = [convert_message_response(m) for m in messages_data.get("private", [])]
        group = [convert_message_response(m) for m in messages_data.get("group", [])]
        return private + group
    
    @strawberry.field
    def group_messages(
        self,
        info: strawberry.Info[GraphQLContext],
        group_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[types.Message]:
        """Get messages for a group"""
        info.context.require_auth()
        messages = info.context.message_service.get_group_messages(
            group_id, skip, limit
        )
        return [convert_message_response(m) for m in messages]
    
    # Group queries
    @strawberry.field
    def my_groups(
        self,
        info: strawberry.Info[GraphQLContext]
    ) -> List[types.Group]:
        """Get groups that current user belongs to"""
        user = info.context.require_auth()
        groups = info.context.group_repo.get_user_groups(user["user_id"])
        return [convert_group_response(g) for g in groups]
    
    @strawberry.field
    def all_groups(
        self,
        info: strawberry.Info[GraphQLContext],
        skip: int = 0,
        limit: int = 100
    ) -> List[types.Group]:
        """Get all groups (admin only)"""
        info.context.require_role(["administrador"])
        groups = info.context.group_repo.get_all(skip, limit)
        return [convert_group_response(g) for g in groups]
    
    @strawberry.field
    def group(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.Group]:
        """Get group by ID"""
        info.context.require_auth()
        group = info.context.group_repo.get_by_id(id)
        return convert_group_response(group) if group else None
