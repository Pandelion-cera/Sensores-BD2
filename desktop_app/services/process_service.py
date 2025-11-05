from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from desktop_app.repositories.process_repository import ProcessRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.repositories.invoice_repository import InvoiceRepository
from desktop_app.services.invoice_service import InvoiceService
from desktop_app.models.process_models import (
    Process, ProcessCreate, ProcessRequest, ProcessRequestCreate,
    Execution, ExecutionCreate, ProcessStatus, ProcessType
)

logger = logging.getLogger(__name__)


class ProcessService:
    def __init__(
        self,
        process_repo: ProcessRepository,
        measurement_repo: MeasurementRepository,
        sensor_repo: SensorRepository,
        user_repo: Optional[UserRepository] = None,
        invoice_repo: Optional[InvoiceRepository] = None
    ):
        self.process_repo = process_repo
        self.measurement_repo = measurement_repo
        self.sensor_repo = sensor_repo
        self.user_repo = user_repo
        self.invoice_repo = invoice_repo
        # Initialize invoice service if invoice repo is provided
        self.invoice_service = None
        if invoice_repo:
            self.invoice_service = InvoiceService(invoice_repo, process_repo)
    
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
            # Ensure request has an id before processing
            if not request.id:
                logger.warning(f"Skipping request with no ID: {request}")
                continue
            
            request_dict = request.model_dump()
            
            # Ensure id is in the dict (should be from model_dump, but verify)
            if "id" not in request_dict or not request_dict["id"]:
                request_dict["id"] = request.id
            
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
        logger.info(f"Starting process execution for request_id: {request_id}")
        
        request = self.process_repo.get_request(request_id)
        if not request:
            logger.error(f"Request not found: {request_id}")
            raise ValueError("Request not found")
        
        logger.info(f"Found request: {request_id}, process_id: {request.process_id}, parameters: {request.parametros}")
        
        process = self.process_repo.get_process(request.process_id)
        if not process:
            logger.error(f"Process not found: {request.process_id}")
            raise ValueError("Process not found")
        
        logger.info(f"Executing process: {process.nombre} (type: {process.tipo.value})")
        
        # Update request status
        self.process_repo.update_request_status(request_id, ProcessStatus.IN_PROGRESS)
        logger.info(f"Request {request_id} status updated to IN_PROGRESS")
        
        try:
            # Execute based on process type
            logger.debug(f"Executing process type: {process.tipo.value}")
            if process.tipo == ProcessType.TEMP_MAX_MIN_REPORT:
                logger.debug("Executing max/min report")
                resultado = self._execute_max_min_report(request.parametros)
            elif process.tipo == ProcessType.TEMP_AVG_REPORT:
                logger.debug("Executing average report")
                resultado = self._execute_avg_report(request.parametros)
            elif process.tipo == ProcessType.ONLINE_QUERY:
                logger.debug("Executing online query")
                resultado = self._execute_online_query(request.parametros)
            else:
                logger.warning(f"Unknown process type: {process.tipo}")
                resultado = {"message": "Process type not implemented yet"}
            
            logger.info(f"Process execution completed. Result type: {type(resultado)}, has results: {bool(resultado)}")
            if isinstance(resultado, dict):
                logger.debug(f"Result keys: {list(resultado.keys())}")
            
            # Create execution record with explicit fecha_ejecucion
            # Ensure request_id is stored as string (matching the request.id format)
            request_id_str = str(request_id)
            execution_dict = {
                "request_id": request_id_str,
                "resultado": resultado,
                "estado": ProcessStatus.COMPLETED,
                "fecha_ejecucion": datetime.utcnow()
            }
            logger.debug(f"Creating execution record with request_id: {request_id_str}")
            execution = self.process_repo.create_execution(
                ExecutionCreate(**execution_dict)
            )
            logger.info(f"Execution record created. Execution ID: {execution.id}, request_id stored: {execution.request_id}")
            
            # Update request status
            self.process_repo.update_request_status(request_id, ProcessStatus.COMPLETED)
            logger.info(f"Request {request_id} status updated to COMPLETED")
            
            # Create invoice for the user after successful execution
            if self.invoice_service:
                try:
                    logger.info(f"Creating invoice for user {request.user_id} for process {request.process_id}")
                    invoice = self.invoice_service.create_invoice_for_user(
                        request.user_id,
                        [request.process_id],
                        request_id=request.id,
                        execution_id=execution.id
                    )
                    logger.info(f"Invoice created successfully. Invoice ID: {invoice.id}, Total: ${invoice.total:.2f}, Request ID: {request.id}, Execution ID: {execution.id}")
                except Exception as invoice_error:
                    # Don't fail execution if invoice creation fails
                    logger.error(f"Failed to create invoice for user {request.user_id} after process execution: {invoice_error}", exc_info=True)
            else:
                logger.debug("Invoice service not available, skipping invoice creation")
            
            return execution
            
        except Exception as e:
            logger.error(f"Error executing process {request_id}: {e}", exc_info=True)
            # Create failed execution record
            # Ensure request_id is stored as string
            request_id_str = str(request_id)
            execution_dict = {
                "request_id": request_id_str,
                "resultado": None,
                "estado": ProcessStatus.FAILED,
                "error_message": str(e),
                "fecha_ejecucion": datetime.utcnow()
            }
            execution = self.process_repo.create_execution(
                ExecutionCreate(**execution_dict)
            )
            logger.info(f"Failed execution record created. Execution ID: {execution.id}")
            
            # Update request status
            self.process_repo.update_request_status(request_id, ProcessStatus.FAILED)
            logger.info(f"Request {request_id} status updated to FAILED")
            
            return execution
    
    def get_execution(self, request_id: str) -> Optional[Execution]:
        """Get execution results for a request"""
        # Validate request_id
        if request_id is None:
            logger.warning(f"Invalid request_id provided: None")
            return None
        
        # Ensure request_id is a string for consistent querying
        request_id_str = str(request_id).strip()
        
        # Check for invalid values
        if not request_id_str or request_id_str.lower() in ['none', 'false', '', 'null']:
            logger.warning(f"Invalid request_id after conversion: '{request_id_str}' (original: {request_id}, type: {type(request_id)})")
            return None
        
        logger.debug(f"Looking for execution with request_id: {request_id_str}")
        executions = self.process_repo.get_executions_by_request(request_id_str)
        logger.info(f"Found {len(executions)} execution(s) for request_id: {request_id_str}")
        if executions:
            execution = executions[0]
            logger.debug(f"Returning execution ID: {execution.id}, estado: {execution.estado.value if execution.estado else 'N/A'}, has resultado: {execution.resultado is not None}")
            return execution
        logger.warning(f"No executions found for request_id: {request_id_str}")
        return None
    
    # Process execution implementations
    def _parse_date(self, date_value: Any) -> datetime:
        """Parse a date value that could be a string, datetime, or None"""
        if date_value is None:
            raise ValueError("Fecha no proporcionada")
        
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Try parsing ISO format
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except ValueError:
                # Try parsing common date formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Formato de fecha no válido: {date_value}")
        
        raise ValueError(f"Tipo de fecha no soportado: {type(date_value)}")
    
    def _execute_max_min_report(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Generate max/min temperature and humidity report"""
        logger.debug(f"Generating max/min report with parameters: {parametros}")
        pais = parametros.get("pais")
        ciudad = parametros.get("ciudad")
        
        fecha_inicio_str = parametros.get("fecha_inicio")
        fecha_fin_str = parametros.get("fecha_fin")
        
        if not fecha_inicio_str:
            raise ValueError("fecha_inicio es requerida")
        if not fecha_fin_str:
            raise ValueError("fecha_fin es requerida")
        
        fecha_inicio = self._parse_date(fecha_inicio_str)
        fecha_fin = self._parse_date(fecha_fin_str)
        logger.debug(f"Date range: {fecha_inicio} to {fecha_fin}")
        
        logger.info(f"Fetching statistics for location: {ciudad}, {pais}")
        stats = self.measurement_repo.get_stats_by_location(
            pais, ciudad, fecha_inicio, fecha_fin
        )
        logger.info(f"Statistics retrieved: count={stats.get('count', 0)}, has temp stats: {bool(stats.get('temperatura'))}, has hum stats: {bool(stats.get('humedad'))}")
        
        # Build results dict with stats embedded
        result = {
            "tipo": "reporte_max_min",
            "pais": pais,
            "ciudad": ciudad,
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "resultados": stats  # This contains temperatura, humedad, count, etc.
        }
        logger.debug(f"Report result structure: tipo={result['tipo']}, has resultados={bool(result.get('resultados'))}")
        return result
    
    def _execute_avg_report(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Generate average temperature and humidity report"""
        # Similar to max/min but focusing on averages
        return self._execute_max_min_report(parametros)
    
    def _execute_online_query(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Execute online query for sensor data"""
        logger.debug(f"Executing online query with parameters: {parametros}")
        pais = parametros.get("pais")
        ciudad = parametros.get("ciudad")
        
        fecha_inicio_str = parametros.get("fecha_inicio")
        fecha_fin_str = parametros.get("fecha_fin")
        
        if not fecha_inicio_str:
            raise ValueError("fecha_inicio es requerida")
        if not fecha_fin_str:
            raise ValueError("fecha_fin es requerida")
        
        fecha_inicio = self._parse_date(fecha_inicio_str)
        fecha_fin = self._parse_date(fecha_fin_str)
        logger.debug(f"Query date range: {fecha_inicio} to {fecha_fin}")
        
        logger.info(f"Fetching measurements for location: {ciudad}, {pais}")
        measurements = self.measurement_repo.get_by_location(
            pais, ciudad, fecha_inicio, fecha_fin
        )
        logger.info(f"Retrieved {len(measurements)} measurements")
        
        result = {
            "tipo": "consulta_online",
            "pais": pais,
            "ciudad": ciudad,
            "periodo": {
                "inicio": fecha_inicio.isoformat(),
                "fin": fecha_fin.isoformat()
            },
            "cantidad_mediciones": len(measurements),
            "mediciones": measurements  # Return all measurements, pagination handled in UI
        }
        logger.debug(f"Query result: {result['cantidad_mediciones']} measurements returned")
        return result
    
    def grant_process_permission(self, user_id: str, process_id: str) -> bool:
        """Grant user permission to execute a process"""
        return self.process_repo.grant_process_permission(user_id, process_id)

