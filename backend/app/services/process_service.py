from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from app.repositories.invoice_repository import InvoiceRepository

from app.repositories.process_repository import ProcessRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.sensor_repository import SensorRepository
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
        invoice_repo: InvoiceRepository = None,
    ):
        self.process_repo = process_repo
        self.measurement_repo = measurement_repo
        self.sensor_repo = sensor_repo
        self.invoice_repo = invoice_repo

    
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

        try:
            costo = float(getattr(process, "costo", 0))
        except Exception:
            costo = 0.0
        
        if not self.invoice_repo:
            request.invoice_created = False
            return request

        
        cantidad = getattr(request, "cantidad", 1) or 1
        subtotal = round(costo * int(cantidad), 2)

        invoice_id = str(uuid4())
        item_id = str(uuid4())
        now = datetime.utcnow()

        invoice_doc = {
            "id": invoice_id,
            "user_id": user_id,
            "fecha_emision": now.isoformat(),
            "total": subtotal,
            "estado": "pendiente",
            "request_id": request.id,
            "created_at": now.isoformat(),
        }

        invoice_item_doc = {
            "id": item_id,
            "invoice_id": invoice_id,
            "request_id": request.id,
            "process_id": process.id,
            "process_name": getattr(process, "nombre", getattr(process, "name", "Proceso")),
            "cantidad": int(cantidad),
            "subtotal": subtotal,
        }

        self.invoice_repo.create_invoice(invoice_doc)
        self.invoice_repo.create_invoice_item(invoice_item_doc)

        request.invoice_id = invoice_id
        request.invoice_created = True

        
        # TODO: Trigger async execution
        # For now, mark as pending
        
        return request
    
    def get_user_requests(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ProcessRequest]:
        """Get all requests for a user"""
        return self.process_repo.get_user_requests(user_id, skip, limit)
    
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
    
    def grant_process_permission(self, user_id: str, process_id: str) -> bool:
        """Grant user permission to execute a process"""
        return self.process_repo.grant_process_permission(user_id, process_id)

