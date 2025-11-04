import strawberry
from typing import Optional
from app.graphql import types
from app.graphql.context import GraphQLContext
from app.graphql.converters import (
    convert_user_response, convert_sensor, convert_alert, convert_alert_rule,
    convert_process, convert_process_request, convert_invoice, convert_message_response,
    convert_group_response
)
from app.models.sensor_models import SensorCreate, SensorUpdate, SensorStatus
from app.models.measurement_models import MeasurementCreate
from app.models.alert_models import AlertCreate, AlertStatus
from app.models.alert_rule_models import AlertRuleCreate, AlertRuleUpdate, AlertRuleStatus
from app.models.process_models import ProcessCreate, ProcessRequestCreate
from app.models.invoice_models import PaymentCreate, PaymentMethod
from app.models.message_models import MessageCreate, MessageType
from app.models.group_models import GroupCreate
from app.models.user_models import UserCreate, UserLogin


@strawberry.type
class Mutation:
    # Auth mutations
    @strawberry.mutation
    def register(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.UserCreateInput
    ) -> types.RegisterResponse:
        """Register a new user"""
        user_data = UserCreate(
            nombre_completo=input.nombre_completo,
            email=input.email,
            password=input.password
        )
        result = info.context.auth_service.register(user_data)
        user_obj = info.context.user_service.get_user(result["user"]["id"])
        return types.RegisterResponse(
            user=convert_user_response(user_obj),
            message=result.get("message", "User registered successfully")
        )
    
    @strawberry.mutation
    def login(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.UserLoginInput
    ) -> types.AuthResponse:
        """Login user"""
        login_data = UserLogin(email=input.email, password=input.password)
        result = info.context.auth_service.login(login_data)
        user_obj = info.context.user_service.get_user(result["user"]["id"])
        return types.AuthResponse(
            access_token=result["access_token"],
            token_type=result["token_type"],
            user=convert_user_response(user_obj),
            session_id=result["session_id"]
        )
    
    @strawberry.mutation
    def logout(
        self,
        info: strawberry.Info[GraphQLContext]
    ) -> bool:
        """Logout current user"""
        user = info.context.require_auth()
        info.context.auth_service.logout(user["session_id"])
        return True
    
    # Sensor mutations
    @strawberry.mutation
    def create_sensor(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.SensorCreateInput
    ) -> types.Sensor:
        """Create a new sensor (admin/técnico only)"""
        user = info.context.require_auth()
        if user.get("role") not in ["administrador", "tecnico"]:
            raise Exception("Insufficient permissions")
        
        sensor_data = SensorCreate(
            nombre=input.nombre,
            tipo=input.tipo.value,
            latitud=input.latitud,
            longitud=input.longitud,
            ciudad=input.ciudad,
            pais=input.pais,
            estado=input.estado.value if input.estado else SensorStatus.ACTIVE
        )
        sensor = info.context.sensor_service.create_sensor(sensor_data)
        return convert_sensor(sensor)
    
    @strawberry.mutation
    def update_sensor(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str,
        input: types.SensorUpdateInput
    ) -> Optional[types.Sensor]:
        """Update sensor (admin/técnico only)"""
        user = info.context.require_auth()
        if user.get("role") not in ["administrador", "tecnico"]:
            raise Exception("Insufficient permissions")
        
        update_data = SensorUpdate()
        if input.nombre is not None:
            update_data.nombre = input.nombre
        if input.estado is not None:
            update_data.estado = input.estado.value
        
        sensor = info.context.sensor_service.update_sensor(id, update_data)
        return convert_sensor(sensor) if sensor else None
    
    @strawberry.mutation
    def delete_sensor(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> bool:
        """Delete sensor (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        return info.context.sensor_service.delete_sensor(id)
    
    @strawberry.mutation
    def register_measurement(
        self,
        info: strawberry.Info[GraphQLContext],
        sensor_id: str,
        input: types.MeasurementCreateInput
    ) -> types.Measurement:
        """Register a new measurement for a sensor"""
        measurement_data = MeasurementCreate(
            temperature=input.temperature,
            humidity=input.humidity
        )
        result = info.context.sensor_service.register_measurement(sensor_id, measurement_data)
        # Convert dict result to Measurement
        return types.Measurement(
            sensor_id=result["sensor_id"],
            timestamp=result["timestamp"],
            temperature=result.get("temperatura"),
            humidity=result.get("humedad")
        )
    
    # Alert mutations
    @strawberry.mutation
    def create_alert(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.AlertCreateInput
    ) -> types.Alert:
        """Create a new alert (admin/técnico only)"""
        user = info.context.require_auth()
        if user.get("role") not in ["administrador", "tecnico"]:
            raise Exception("Insufficient permissions")
        
        alert_data = AlertCreate(
            tipo=input.tipo.value,
            sensor_id=input.sensor_id,
            descripcion=input.descripcion,
            valor=input.valor,
            umbral=input.umbral
        )
        alert = info.context.alert_service.create_alert(alert_data)
        return convert_alert(alert)
    
    @strawberry.mutation
    def resolve_alert(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.Alert]:
        """Resolve an alert"""
        info.context.require_auth()
        alert = info.context.alert_service.resolve_alert(id)
        return convert_alert(alert) if alert else None
    
    @strawberry.mutation
    def acknowledge_alert(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.Alert]:
        """Acknowledge an alert"""
        info.context.require_auth()
        alert = info.context.alert_service.acknowledge_alert(id)
        return convert_alert(alert) if alert else None
    
    # Alert Rule mutations
    @strawberry.mutation
    def create_alert_rule(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.AlertRuleCreateInput
    ) -> types.AlertRule:
        """Create a new alert rule (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        rule_data = AlertRuleCreate(
            nombre=input.nombre,
            descripcion=input.descripcion,
            temp_min=input.temp_min,
            temp_max=input.temp_max,
            humidity_min=input.humidity_min,
            humidity_max=input.humidity_max,
            location_scope=input.location_scope.value,
            ciudad=input.ciudad,
            region=input.region,
            pais=input.pais,
            fecha_inicio=input.fecha_inicio,
            fecha_fin=input.fecha_fin,
            estado=input.estado.value if input.estado else AlertRuleStatus.ACTIVE,
            prioridad=input.prioridad if input.prioridad else 1
        )
        # Get current user email for creado_por
        user_obj = info.context.user_service.get_user(user["user_id"])
        rule_data.creado_por = user_obj.email
        rule = info.context.alert_rule_service.create_rule(rule_data)
        return convert_alert_rule(rule)
    
    @strawberry.mutation
    def update_alert_rule(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str,
        input: types.AlertRuleUpdateInput
    ) -> Optional[types.AlertRule]:
        """Update an alert rule (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        update_data = AlertRuleUpdate()
        if input.nombre is not None:
            update_data.nombre = input.nombre
        if input.descripcion is not None:
            update_data.descripcion = input.descripcion
        if input.temp_min is not None:
            update_data.temp_min = input.temp_min
        if input.temp_max is not None:
            update_data.temp_max = input.temp_max
        if input.humidity_min is not None:
            update_data.humidity_min = input.humidity_min
        if input.humidity_max is not None:
            update_data.humidity_max = input.humidity_max
        if input.location_scope is not None:
            update_data.location_scope = input.location_scope.value
        if input.ciudad is not None:
            update_data.ciudad = input.ciudad
        if input.region is not None:
            update_data.region = input.region
        if input.pais is not None:
            update_data.pais = input.pais
        if input.fecha_inicio is not None:
            update_data.fecha_inicio = input.fecha_inicio
        if input.fecha_fin is not None:
            update_data.fecha_fin = input.fecha_fin
        if input.estado is not None:
            update_data.estado = input.estado.value
        if input.prioridad is not None:
            update_data.prioridad = input.prioridad
        
        rule = info.context.alert_rule_service.update_rule(id, update_data)
        return convert_alert_rule(rule) if rule else None
    
    @strawberry.mutation
    def activate_alert_rule(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.AlertRule]:
        """Activate an alert rule (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        rule = info.context.alert_rule_service.activate_rule(id)
        return convert_alert_rule(rule) if rule else None
    
    @strawberry.mutation
    def deactivate_alert_rule(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> Optional[types.AlertRule]:
        """Deactivate an alert rule (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        rule = info.context.alert_rule_service.deactivate_rule(id)
        return convert_alert_rule(rule) if rule else None
    
    @strawberry.mutation
    def delete_alert_rule(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> bool:
        """Delete an alert rule (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        return info.context.alert_rule_service.delete_rule(id)
    
    # Process mutations
    @strawberry.mutation
    def create_process(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.ProcessCreateInput
    ) -> types.Process:
        """Create a new process (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        process_data = ProcessCreate(
            nombre=input.nombre,
            descripcion=input.descripcion,
            tipo=input.tipo.value,
            costo=input.costo,
            parametros_schema=input.parametros_schema
        )
        process = info.context.process_service.create_process(process_data)
        return convert_process(process)
    
    @strawberry.mutation
    def request_process(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.ProcessRequestCreateInput
    ) -> types.ProcessRequest:
        """Request a process execution"""
        user = info.context.require_auth()
        request_data = ProcessRequestCreate(
            process_id=input.process_id,
            parametros=input.parametros
        )
        request = info.context.process_service.request_process(user["user_id"], request_data)
        return convert_process_request(request)
    
    @strawberry.mutation
    def execute_process(
        self,
        info: strawberry.Info[GraphQLContext],
        request_id: str
    ) -> Optional[types.Execution]:
        """Execute a process request (admin/técnico only)"""
        user = info.context.require_auth()
        if user.get("role") not in ["administrador", "tecnico"]:
            raise Exception("Insufficient permissions")
        
        execution = info.context.process_service.execute_process(request_id)
        from app.graphql.converters import convert_execution
        return convert_execution(execution) if execution else None
    
    # Invoice mutations
    @strawberry.mutation
    def pay_invoice(
        self,
        info: strawberry.Info[GraphQLContext],
        invoice_id: str,
        input: types.PaymentCreateInput
    ) -> Optional[types.Payment]:
        """Pay an invoice"""
        user = info.context.require_auth()
        payment_data = PaymentCreate(
            monto=input.monto,
            metodo=PaymentMethod(input.metodo.value)
        )
        payment = info.context.invoice_service.pay_invoice(
            user["user_id"], invoice_id, payment_data
        )
        from app.graphql.converters import convert_payment
        return convert_payment(payment) if payment else None
    
    # Message mutations
    @strawberry.mutation
    def send_message(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.MessageCreateInput
    ) -> types.Message:
        """Send a message (private or group)"""
        user = info.context.require_auth()
        message_data = MessageCreate(
            recipient_type=MessageType(input.recipient_type.value),
            recipient_id=input.recipient_id,
            content=input.content
        )
        result = info.context.message_service.send_message(user["user_id"], message_data)
        return convert_message_response(result)
    
    # Group mutations
    @strawberry.mutation
    def create_group(
        self,
        info: strawberry.Info[GraphQLContext],
        input: types.GroupCreateInput
    ) -> types.Group:
        """Create a new group (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        group_data = GroupCreate(nombre=input.nombre, miembros=input.miembros)
        group = info.context.group_repo.create(group_data)
        return convert_group_response(group)
    
    @strawberry.mutation
    def add_group_member(
        self,
        info: strawberry.Info[GraphQLContext],
        group_id: str,
        user_id: str
    ) -> Optional[types.Group]:
        """Add a member to a group (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        success = info.context.group_repo.add_member(group_id, user_id)
        if not success:
            return None
        group = info.context.group_repo.get_by_id(group_id)
        return convert_group_response(group) if group else None
    
    @strawberry.mutation
    def remove_group_member(
        self,
        info: strawberry.Info[GraphQLContext],
        group_id: str,
        user_id: str
    ) -> Optional[types.Group]:
        """Remove a member from a group (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        success = info.context.group_repo.remove_member(group_id, user_id)
        if not success:
            return None
        group = info.context.group_repo.get_by_id(group_id)
        return convert_group_response(group) if group else None
    
    @strawberry.mutation
    def delete_group(
        self,
        info: strawberry.Info[GraphQLContext],
        id: str
    ) -> bool:
        """Delete a group (admin only)"""
        user = info.context.require_auth()
        if user.get("role") != "administrador":
            raise Exception("Insufficient permissions")
        
        return info.context.group_repo.delete(id)
