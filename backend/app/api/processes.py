from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any

from app.models.process_models import (
    Process, ProcessCreate, ProcessRequest, ProcessRequestCreate, Execution
)
from app.services.process_service import ProcessService
from app.core.security import get_current_user_data
from app.core.database import get_mongo_db, get_neo4j_driver, get_cassandra_session
from app.repositories.process_repository import ProcessRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.sensor_repository import SensorRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.core.config import settings

router = APIRouter()


def get_process_service(
    mongo_db=Depends(get_mongo_db),
    neo4j_driver=Depends(get_neo4j_driver),
    cassandra_session=Depends(get_cassandra_session)
) -> ProcessService:
    process_repo = ProcessRepository(mongo_db, neo4j_driver)
    measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
    sensor_repo = SensorRepository(mongo_db)
    invoice_repo = InvoiceRepository(mongo_db)

    return ProcessService(process_repo, measurement_repo, sensor_repo)


@router.post("", response_model=Process, status_code=status.HTTP_201_CREATED)
def create_process(
    process_data: ProcessCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    process_service: ProcessService = Depends(get_process_service)
):
    """Create a new process definition (admin only)"""
    if current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return process_service.create_process(process_data)


@router.get("", response_model=List[Process])
def get_processes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    process_service: ProcessService = Depends(get_process_service)
):
    """Get all available processes"""
    return process_service.get_all_processes(skip, limit)


@router.get("/{process_id}", response_model=Process)
def get_process(
    process_id: str,
    process_service: ProcessService = Depends(get_process_service)
):
    """Get process details"""
    process = process_service.get_process(process_id)
    if not process:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Process not found")
    
    return process


@router.post("/requests", response_model=ProcessRequest, status_code=status.HTTP_201_CREATED)
def request_process(
    request_data: ProcessRequestCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    process_service: ProcessService = Depends(get_process_service)
):
    """Request execution of a process"""
    try:
        return process_service.request_process(current_user["user_id"], request_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/requests/user/{user_id}", response_model=List[ProcessRequest])
def get_user_requests(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    process_service: ProcessService = Depends(get_process_service)
):
    """Get process requests for a user"""
    # Users can only view their own requests unless they're admin
    if user_id != current_user["user_id"] and current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return process_service.get_user_requests(user_id, skip, limit)


@router.post("/requests/{request_id}/execute", response_model=Execution)
def execute_process(
    request_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    process_service: ProcessService = Depends(get_process_service)
):
    """Execute a process request (admin/técnico only)"""
    if current_user.get("role") not in ["administrador", "tecnico"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    try:
        return process_service.execute_process(request_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/executions/{request_id}", response_model=Execution)
def get_execution(
    request_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_data),
    process_service: ProcessService = Depends(get_process_service)
):
    """Get execution results for a request"""
    # Verify request belongs to user or user is admin
    request = process_service.get_request(request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    if request.user_id != current_user["user_id"] and current_user.get("role") != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    execution = process_service.get_execution(request_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    
    return execution

