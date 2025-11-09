from typing import List, Optional, Dict, Any
from datetime import datetime

from app.repositories.process_repository import ProcessRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.sensor_repository import SensorRepository
from app.repositories.user_repository import UserRepository
from app.services.alert_rule_service import AlertRuleService
from app.models.alert_rule_models import AlertRuleCreate, LocationScope
from app.models.process_models import (
    Process, ProcessCreate, ProcessRequest, ProcessRequestCreate,
    Execution, ExecutionCreate, ProcessStatus, ProcessType
)


class ProcessService:
    def __init__(
        self,
        process_repo: ProcessRepository,
        measurement_repo: MeasurementRepository,
        sensor_repo: SensorRepository,
        user_repo: Optional[UserRepository] = None,
        alert_rule_service: Optional[AlertRuleService] = None
    ):
        self.process_repo = process_repo
        self.measurement_repo = measurement_repo
        self.sensor_repo = sensor_repo
        self.user_repo = user_repo
        self.alert_rule_service = alert_rule_service
    
    # Process Definition Management
    def create_process(self, process_data: ProcessCreate) -> Process:
        """Create a new process definition"""
        return self.process_repo.create_process(process_data)
    
    def get_process(self, process_id: str) -> Optional[Process]:
        """Get process by ID"""
        return self.process_repo.get_process(process_id)
    
    def get_all_processes(self, skip: int = 0, limit: int = 100) -> List[Process]:
        """Get all available processes"""
        return self.process_repo.get_all_processes(skip, limit)
    
    # Process Request Management
    def request_process(self, user_id: str, request_data: ProcessRequestCreate) -> ProcessRequest:
        """Request execution of a process"""
        # Verify process exists
        process = self.process_repo.get_process(request_data.process_id)
        if not process:
            raise ValueError("Process not found")
        
        # Create request
        request = self.process_repo.create_request(user_id, request_data)
        
        # TODO: Trigger async execution
        # For now, mark as pending
        
        return request
    
    def get_user_requests(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ProcessRequest]:
        """Get all requests for a user"""
        return self.process_repo.get_user_requests(user_id, skip, limit)
    
    def get_all_requests(
        self, 
        status: Optional[ProcessStatus] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all requests with optional status filter, enriched with user and process info"""
        requests = self.process_repo.get_all_requests(status, skip, limit)
        
        # Enrich requests with user and process information
        enriched_requests = []
        for request in requests:
            request_dict = request.model_dump()
            
            # Get user information
            if self.user_repo:
                user = self.user_repo.get_by_id(request.user_id)
                if user:
                    request_dict["user"] = {
                        "id": user.id,
                        "nombre_completo": user.nombre_completo,
                        "email": user.email
                    }
            
            # Get process information
            process = self.process_repo.get_process(request.process_id)
            if process:
                request_dict["process"] = {
                    "id": process.id,
                    "nombre": process.nombre,
                    "descripcion": process.descripcion,
                    "costo": process.costo
                }
            
            enriched_requests.append(request_dict)
        
        return enriched_requests
    
    def get_request(self, request_id: str) -> Optional[ProcessRequest]:
        """Get process request by ID"""
        return self.process_repo.get_request(request_id)
    
    # Process Execution
    def execute_process(self, request_id: str) -> Execution:
        """Execute a process request"""
        request = self.process_repo.get_request(request_id)
        if not request:
            raise ValueError("Request not found")
        
        process = self.process_repo.get_process(request.process_id)
        if not process:
            raise ValueError("Process not found")
        
        # Update request status
        self.process_repo.update_request_status(request_id, ProcessStatus.IN_PROGRESS)
        
        try:
            # Execute based on process type
            if process.tipo == ProcessType.TEMP_MAX_MIN_REPORT:
                resultado = self._execute_max_min_report(request.parametros)
            elif process.tipo == ProcessType.TEMP_AVG_REPORT:
                resultado = self._execute_avg_report(request.parametros)
            elif process.tipo == ProcessType.ONLINE_QUERY:
                resultado = self._execute_online_query(request.parametros)
            elif process.tipo == ProcessType.ALERT_CONFIG:
                resultado = self._execute_alert_configuration(request)
            else:
                resultado = {"message": "Process type not implemented yet"}
            
            # Create execution record
            execution = self.process_repo.create_execution(
                ExecutionCreate(
                    request_id=request_id,
                    resultado=resultado,
                    estado=ProcessStatus.COMPLETED
                )
            )
            
            # Update request status
            self.process_repo.update_request_status(request_id, ProcessStatus.COMPLETED)
            
            return execution
            
        except Exception as e:
            # Create failed execution record
            execution = self.process_repo.create_execution(
                ExecutionCreate(
                    request_id=request_id,
                    resultado=None,
                    estado=ProcessStatus.FAILED,
                    error_message=str(e)
                )
            )
            
            # Update request status
            self.process_repo.update_request_status(request_id, ProcessStatus.FAILED)
            
            return execution
    
    def get_execution(self, request_id: str) -> Optional[Execution]:
        """Get execution results for a request"""
        executions = self.process_repo.get_executions_by_request(request_id)
        return executions[0] if executions else None
    
    # Process execution implementations
    def _execute_max_min_report(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Generate max/min temperature and humidity report"""
        pais = parametros.get("pais")
        ciudad = parametros.get("ciudad")
        fecha_inicio = datetime.fromisoformat(parametros.get("fecha_inicio"))
        fecha_fin = datetime.fromisoformat(parametros.get("fecha_fin"))
        
        stats = self.measurement_repo.get_stats_by_location(
            pais, ciudad, fecha_inicio, fecha_fin
        )
        
        return {
            "tipo": "reporte_max_min",
            "pais": pais,
            "ciudad": ciudad,
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "resultados": stats
        }
    
    def _execute_avg_report(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Generate average temperature and humidity report"""
        # Similar to max/min but focusing on averages
        return self._execute_max_min_report(parametros)
    
    def _execute_online_query(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Execute online query for sensor data"""
        pais = parametros.get("pais")
        ciudad = parametros.get("ciudad")
        fecha_inicio = datetime.fromisoformat(parametros.get("fecha_inicio"))
        fecha_fin = datetime.fromisoformat(parametros.get("fecha_fin"))
        
        measurements = self.measurement_repo.get_by_location(
            pais, ciudad, fecha_inicio, fecha_fin
        )
        
        return {
            "tipo": "consulta_online",
            "pais": pais,
            "ciudad": ciudad,
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "cantidad_mediciones": len(measurements),
            "mediciones": measurements[:100]  # Limit to 100 for response size
        }
    
    def _execute_alert_configuration(self, request: ProcessRequest) -> Dict[str, Any]:
        """Create a user-specific alert rule based on process parameters"""
        if not self.alert_rule_service:
            raise ValueError("Alert rule service is not available")
        
        parametros = request.parametros or {}
        nombre = (parametros.get("nombre") or "").strip()
        descripcion = (parametros.get("descripcion") or "").strip()
        if len(nombre) < 3:
            raise ValueError("El nombre de la regla debe tener al menos 3 caracteres")
        if len(descripcion) < 10:
            raise ValueError("La descripción debe tener al menos 10 caracteres")
        
        def _parse_float(value: Any, field_name: str) -> Optional[float]:
            if value in (None, "", "null"):
                return None
            try:
                return float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"El valor de '{field_name}' no es válido") from exc
        
        temp_min = _parse_float(parametros.get("temp_min"), "temp_min")
        temp_max = _parse_float(parametros.get("temp_max"), "temp_max")
        hum_min = _parse_float(parametros.get("humidity_min"), "humidity_min")
        hum_max = _parse_float(parametros.get("humidity_max"), "humidity_max")
        
        if all(v is None for v in (temp_min, temp_max, hum_min, hum_max)):
            raise ValueError("Debe definir al menos una condición de temperatura u humedad")
        if temp_min is not None and temp_max is not None and temp_min > temp_max:
            raise ValueError("La temperatura mínima no puede ser mayor que la máxima")
        if hum_min is not None and hum_max is not None and hum_min > hum_max:
            raise ValueError("La humedad mínima no puede ser mayor que la máxima")
        
        scope_str = parametros.get("location_scope") or LocationScope.COUNTRY.value
        location_scope = LocationScope(scope_str)
        
        pais = (parametros.get("pais") or "").strip()
        ciudad = (parametros.get("ciudad") or "").strip()
        region = (parametros.get("region") or "").strip()
        if not pais:
            raise ValueError("Debe indicar el país donde aplica la regla")
        if location_scope == LocationScope.CITY and not ciudad:
            raise ValueError("Debe indicar la ciudad para el ámbito 'ciudad'")
        if location_scope == LocationScope.REGION and not region:
            raise ValueError("Debe indicar la región para el ámbito 'region'")
        
        fecha_inicio = parametros.get("fecha_inicio")
        fecha_fin = parametros.get("fecha_fin")
        fecha_inicio_dt = datetime.fromisoformat(fecha_inicio) if fecha_inicio else None
        fecha_fin_dt = datetime.fromisoformat(fecha_fin) if fecha_fin else None
        if fecha_inicio_dt and fecha_fin_dt and fecha_inicio_dt > fecha_fin_dt:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin")
        
        prioridad = int(parametros.get("prioridad") or 1)
        
        rule_data = AlertRuleCreate(
            nombre=nombre,
            descripcion=descripcion,
            temp_min=temp_min,
            temp_max=temp_max,
            humidity_min=hum_min,
            humidity_max=hum_max,
            location_scope=location_scope,
            ciudad=ciudad if location_scope == LocationScope.CITY else None,
            region=region if location_scope == LocationScope.REGION else None,
            pais=pais,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            prioridad=prioridad,
            user_id=request.user_id
        )
        
        creado_por = request.user_id or "process_user"
        rule = self.alert_rule_service.create_rule(rule_data, creado_por)
        
        return {
            "tipo": "configuracion_alertas",
            "mensaje": "Regla de alerta creada exitosamente",
            "rule_id": rule.id,
            "regla": rule.model_dump()
        }
    
    def grant_process_permission(self, user_id: str, process_id: str) -> bool:
        """Grant user permission to execute a process"""
        return self.process_repo.grant_process_permission(user_id, process_id)

