from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo.database import Database
from neo4j import Driver

from app.models.process_models import (
    Process, ProcessCreate, ProcessRequest, ProcessRequestCreate,
    Execution, ExecutionCreate, ProcessStatus
)


class ProcessRepository:
    def __init__(self, mongo_db: Database, neo4j_driver: Driver):
        self.processes_col = mongo_db["processes"]
        self.requests_col = mongo_db["process_requests"]
        self.executions_col = mongo_db["executions"]
        self.neo4j_driver = neo4j_driver
        
    # Process CRUD
    def create_process(self, process_data: ProcessCreate) -> Process:
        """Create a new process definition"""
        process_dict = process_data.model_dump()
        
        result = self.processes_col.insert_one(process_dict)
        process_dict["_id"] = str(result.inserted_id)
        
        # Create process node in Neo4j
        with self.neo4j_driver.session() as session:
            session.run(
                "CREATE (p:Process {id: $id, name: $name, type: $type})",
                id=process_dict["_id"],
                name=process_data.nombre,
                type=process_data.tipo
            )
        
        return Process(**process_dict)
    
    def get_process(self, process_id: str) -> Optional[Process]:
        """Get process by ID"""
        try:
            process = self.processes_col.find_one({"_id": ObjectId(process_id)})
            if process:
                process["_id"] = str(process["_id"])
                return Process(**process)
        except:
            return None
        return None
    
    def get_all_processes(self, skip: int = 0, limit: int = 100) -> List[Process]:
        """Get all process definitions"""
        processes = []
        for process in self.processes_col.find().skip(skip).limit(limit):
            process["_id"] = str(process["_id"])
            processes.append(Process(**process))
        return processes
    
    # Process Request CRUD
    def create_request(self, user_id: str, request_data: ProcessRequestCreate) -> ProcessRequest:
        """Create a new process request"""
        request_dict = {
            "user_id": user_id,
            "process_id": request_data.process_id,
            "parametros": request_data.parametros,
            "estado": ProcessStatus.PENDING
        }
        
        result = self.requests_col.insert_one(request_dict)
        request_dict["_id"] = str(result.inserted_id)
        
        return ProcessRequest(**request_dict)
    
    def get_request(self, request_id: str) -> Optional[ProcessRequest]:
        """Get process request by ID"""
        try:
            request = self.requests_col.find_one({"_id": ObjectId(request_id)})
            if request:
                request["_id"] = str(request["_id"])
                return ProcessRequest(**request)
        except:
            return None
        return None
    
    def get_user_requests(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ProcessRequest]:
        """Get all requests for a user"""
        requests = []
        for request in self.requests_col.find({"user_id": user_id}).sort("fecha_solicitud", -1).skip(skip).limit(limit):
            request["_id"] = str(request["_id"])
            requests.append(ProcessRequest(**request))
        return requests
    
    def get_all_requests(
        self, 
        status: Optional[ProcessStatus] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ProcessRequest]:
        """Get all requests with optional status filter"""
        query = {}
        if status:
            query["estado"] = status
        
        requests = []
        for request in self.requests_col.find(query).sort("fecha_solicitud", -1).skip(skip).limit(limit):
            request["_id"] = str(request["_id"])
            requests.append(ProcessRequest(**request))
        return requests
    
    def update_request_status(self, request_id: str, status: ProcessStatus) -> bool:
        """Update request status"""
        result = self.requests_col.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"estado": status}}
        )
        return result.modified_count > 0
    
    # Execution CRUD
    def create_execution(self, execution_data: ExecutionCreate) -> Execution:
        """Create an execution record"""
        execution_dict = execution_data.model_dump()
        
        result = self.executions_col.insert_one(execution_dict)
        execution_dict["_id"] = str(result.inserted_id)
        
        return Execution(**execution_dict)
    
    def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get execution by ID"""
        try:
            execution = self.executions_col.find_one({"_id": ObjectId(execution_id)})
            if execution:
                execution["_id"] = str(execution["_id"])
                return Execution(**execution)
        except:
            return None
        return None
    
    def get_executions_by_request(self, request_id: str) -> List[Execution]:
        """Get all executions for a request"""
        executions = []
        for execution in self.executions_col.find({"request_id": request_id}).sort("fecha_ejecucion", -1):
            execution["_id"] = str(execution["_id"])
            executions.append(Execution(**execution))
        return executions
    
    def grant_process_permission(self, user_id: str, process_id: str) -> bool:
        """Grant user permission to execute a process"""
        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})
                MATCH (p:Process {id: $process_id})
                MERGE (u)-[:CAN_EXECUTE]->(p)
                RETURN u
                """,
                user_id=user_id,
                process_id=process_id
            )
            return result.single() is not None

