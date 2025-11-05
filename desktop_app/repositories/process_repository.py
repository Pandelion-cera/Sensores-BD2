from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from neo4j import Driver
from datetime import datetime

from desktop_app.models.process_models import (
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
            "estado": ProcessStatus.PENDING,
            "fecha_solicitud": datetime.utcnow()
        }
        
        result = self.requests_col.insert_one(request_dict)
        # Ensure _id is properly set
        if result.inserted_id:
            request_dict["_id"] = str(result.inserted_id)
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get inserted_id from MongoDB insert operation")
            raise ValueError("Failed to create request - no ID returned")
        
        process_request = ProcessRequest(**request_dict)
        
        # Verify the id was set
        if not process_request.id:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"ProcessRequest created with no id: {request_dict}")
            raise ValueError("ProcessRequest created without ID")
        
        return process_request
    
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
            # Ensure _id exists and convert to string
            if "_id" not in request or request["_id"] is None:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Request document missing _id: {request}")
                continue
            request["_id"] = str(request["_id"])
            try:
                process_request = ProcessRequest(**request)
                # Verify the id was set correctly
                if not process_request.id:
                    logger.warning(f"ProcessRequest created with no id from document: {request}")
                    continue
                requests.append(process_request)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating ProcessRequest from document: {e}, document: {request}")
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
            # Ensure _id exists and convert to string
            if "_id" not in request or request["_id"] is None:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Request document missing _id: {request}")
                continue
            request["_id"] = str(request["_id"])
            try:
                process_request = ProcessRequest(**request)
                # Verify the id was set correctly
                if not process_request.id:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"ProcessRequest created with no id from document: {request}")
                    continue
                requests.append(process_request)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating ProcessRequest from document: {e}, document: {request}")
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
        execution_dict = execution_data.model_dump(exclude_none=False)
        
        # Ensure fecha_ejecucion is set if not provided
        if "fecha_ejecucion" not in execution_dict or execution_dict["fecha_ejecucion"] is None:
            from datetime import datetime
            execution_dict["fecha_ejecucion"] = datetime.utcnow()
        
        # Ensure resultado is properly stored (MongoDB can handle dicts directly)
        # But ensure it's not None if it's an empty dict
        if "resultado" not in execution_dict:
            execution_dict["resultado"] = None
        
        result = self.executions_col.insert_one(execution_dict)
        execution_dict["_id"] = str(result.inserted_id)
        
        return Execution(**execution_dict)
    
    def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get execution by ID"""
        try:
            execution = self.executions_col.find_one({"_id": ObjectId(execution_id)})
            if execution:
                execution["_id"] = str(execution["_id"])
                # Ensure resultado is properly handled (MongoDB might store it differently)
                if "resultado" in execution and execution["resultado"] is not None:
                    # resultado should already be a dict, but ensure it's properly formatted
                    if not isinstance(execution["resultado"], dict):
                        # Try to parse if it's a string
                        import json
                        try:
                            execution["resultado"] = json.loads(execution["resultado"]) if isinstance(execution["resultado"], str) else execution["resultado"]
                        except:
                            pass
                return Execution(**execution)
        except Exception as e:
            print(f"Error getting execution: {e}")
            return None
        return None
    
    def get_executions_by_request(self, request_id: str) -> List[Execution]:
        """Get all executions for a request"""
        executions = []
        
        # Try querying with request_id as string first
        query = {"request_id": request_id}
        found_executions = list(self.executions_col.find(query))
        
        # If not found, try as ObjectId (in case request_id was stored as ObjectId)
        if not found_executions:
            try:
                if len(request_id) == 24:  # MongoDB ObjectId string length
                    query_oid = {"request_id": ObjectId(request_id)}
                    found_executions = list(self.executions_col.find(query_oid))
            except:
                pass
        
        # If still not found, try reverse lookup - find all executions and check their request_id
        if not found_executions:
            all_executions = list(self.executions_col.find({}))
            for exec in all_executions:
                stored_request_id = exec.get("request_id")
                # Compare as strings
                if str(stored_request_id) == str(request_id):
                    found_executions.append(exec)
        
        for execution in found_executions:
            execution["_id"] = str(execution["_id"])
            # Ensure resultado is properly handled
            if "resultado" in execution and execution["resultado"] is not None:
                if not isinstance(execution["resultado"], dict):
                    import json
                    try:
                        execution["resultado"] = json.loads(execution["resultado"]) if isinstance(execution["resultado"], str) else execution["resultado"]
                    except:
                        pass
            executions.append(Execution(**execution))
        
        # Sort by fecha_ejecucion descending
        executions.sort(key=lambda x: x.fecha_ejecucion if x.fecha_ejecucion else datetime.min, reverse=True)
        
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

