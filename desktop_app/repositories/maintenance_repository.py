from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from desktop_app.models.maintenance_models import (
    MaintenanceRecord, MaintenanceRecordCreate, MaintenanceRecordUpdate, MaintenanceStatus
)


class MaintenanceRepository:
    """Repository for maintenance/control records"""
    
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db["maintenance_records"]
        # Create indexes
        self.collection.create_index("sensor_id")
        self.collection.create_index("tecnico_id")
        self.collection.create_index("fecha_revision")
        self.collection.create_index([("sensor_id", 1), ("fecha_revision", -1)])
    
    def create(self, record_data: MaintenanceRecordCreate) -> MaintenanceRecord:
        """Create a new maintenance record"""
        record_dict = record_data.model_dump(exclude_none=True)
        record_dict["created_at"] = datetime.utcnow()
        
        result = self.collection.insert_one(record_dict)
        record_dict["_id"] = str(result.inserted_id)
        
        return MaintenanceRecord(**record_dict)
    
    def get_by_id(self, record_id: str) -> Optional[MaintenanceRecord]:
        """Get maintenance record by ID"""
        try:
            record = self.collection.find_one({"_id": ObjectId(record_id)})
            if record:
                record["_id"] = str(record["_id"])
                # Parse datetime fields
                if "fecha_revision" in record and record["fecha_revision"]:
                    if isinstance(record["fecha_revision"], str):
                        try:
                            record["fecha_revision"] = datetime.fromisoformat(record["fecha_revision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "proxima_revision" in record and record["proxima_revision"]:
                    if isinstance(record["proxima_revision"], str):
                        try:
                            record["proxima_revision"] = datetime.fromisoformat(record["proxima_revision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "created_at" in record and record["created_at"]:
                    if isinstance(record["created_at"], str):
                        try:
                            record["created_at"] = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                        except:
                            pass
                return MaintenanceRecord(**record)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting maintenance record {record_id}: {e}")
            return None
        return None
    
    def get_by_sensor(self, sensor_id: str, skip: int = 0, limit: int = 100) -> List[MaintenanceRecord]:
        """Get all maintenance records for a sensor"""
        records = []
        for record in self.collection.find({"sensor_id": sensor_id}).sort("fecha_revision", -1).skip(skip).limit(limit):
            try:
                record["_id"] = str(record["_id"])
                # Parse datetime fields
                if "fecha_revision" in record and record["fecha_revision"]:
                    if isinstance(record["fecha_revision"], str):
                        try:
                            record["fecha_revision"] = datetime.fromisoformat(record["fecha_revision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "proxima_revision" in record and record["proxima_revision"]:
                    if isinstance(record["proxima_revision"], str):
                        try:
                            record["proxima_revision"] = datetime.fromisoformat(record["proxima_revision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "created_at" in record and record["created_at"]:
                    if isinstance(record["created_at"], str):
                        try:
                            record["created_at"] = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                        except:
                            pass
                records.append(MaintenanceRecord(**record))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error parsing maintenance record {record.get('_id', 'unknown')}: {e}")
                continue
        return records
    
    def get_by_tecnico(self, tecnico_id: str, skip: int = 0, limit: int = 100) -> List[MaintenanceRecord]:
        """Get all maintenance records by a technician"""
        records = []
        for record in self.collection.find({"tecnico_id": tecnico_id}).sort("fecha_revision", -1).skip(skip).limit(limit):
            try:
                record["_id"] = str(record["_id"])
                # Parse datetime fields
                if "fecha_revision" in record and record["fecha_revision"]:
                    if isinstance(record["fecha_revision"], str):
                        try:
                            record["fecha_revision"] = datetime.fromisoformat(record["fecha_revision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "proxima_revision" in record and record["proxima_revision"]:
                    if isinstance(record["proxima_revision"], str):
                        try:
                            record["proxima_revision"] = datetime.fromisoformat(record["proxima_revision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "created_at" in record and record["created_at"]:
                    if isinstance(record["created_at"], str):
                        try:
                            record["created_at"] = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                        except:
                            pass
                records.append(MaintenanceRecord(**record))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error parsing maintenance record {record.get('_id', 'unknown')}: {e}")
                continue
        return records
    
    def get_latest_by_sensor(self, sensor_id: str) -> Optional[MaintenanceRecord]:
        """Get the latest maintenance record for a sensor"""
        record = self.collection.find_one(
            {"sensor_id": sensor_id},
            sort=[("fecha_revision", -1)]
        )
        if record:
            record["_id"] = str(record["_id"])
            # Parse datetime fields
            if "fecha_revision" in record and record["fecha_revision"]:
                if isinstance(record["fecha_revision"], str):
                    try:
                        record["fecha_revision"] = datetime.fromisoformat(record["fecha_revision"].replace("Z", "+00:00"))
                    except:
                        pass
            if "proxima_revision" in record and record["proxima_revision"]:
                if isinstance(record["proxima_revision"], str):
                    try:
                        record["proxima_revision"] = datetime.fromisoformat(record["proxima_revision"].replace("Z", "+00:00"))
                    except:
                        pass
            if "created_at" in record and record["created_at"]:
                if isinstance(record["created_at"], str):
                    try:
                        record["created_at"] = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                    except:
                        pass
            return MaintenanceRecord(**record)
        return None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[MaintenanceRecord]:
        """Get all maintenance records"""
        records = []
        for record in self.collection.find({}).sort("fecha_revision", -1).skip(skip).limit(limit):
            try:
                record["_id"] = str(record["_id"])
                # Parse datetime fields
                if "fecha_revision" in record and record["fecha_revision"]:
                    if isinstance(record["fecha_revision"], str):
                        try:
                            record["fecha_revision"] = datetime.fromisoformat(record["fecha_revision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "proxima_revision" in record and record["proxima_revision"]:
                    if isinstance(record["proxima_revision"], str):
                        try:
                            record["proxima_revision"] = datetime.fromisoformat(record["proxima_revision"].replace("Z", "+00:00"))
                        except:
                            pass
                if "created_at" in record and record["created_at"]:
                    if isinstance(record["created_at"], str):
                        try:
                            record["created_at"] = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
                        except:
                            pass
                records.append(MaintenanceRecord(**record))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error parsing maintenance record {record.get('_id', 'unknown')}: {e}")
                continue
        return records
    
    def update(self, record_id: str, update_data: MaintenanceRecordUpdate) -> bool:
        """Update a maintenance record"""
        try:
            update_dict = update_data.model_dump(exclude_none=True)
            result = self.collection.update_one(
                {"_id": ObjectId(record_id)},
                {"$set": update_dict}
            )
            return result.modified_count > 0
        except:
            return False
    
    def delete(self, record_id: str) -> bool:
        """Delete a maintenance record"""
        try:
            result = self.collection.delete_one({"_id": ObjectId(record_id)})
            return result.deleted_count > 0
        except:
            return False

