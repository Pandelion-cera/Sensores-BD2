from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from desktop_app.models.scheduled_process_models import (
    ScheduledProcess, ScheduledProcessCreate, ScheduledProcessUpdate,
    ScheduleStatus
)


class ScheduledProcessRepository:
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db["scheduled_processes"]
    
    def create(self, user_id: str, schedule_data: ScheduledProcessCreate, next_execution: datetime) -> ScheduledProcess:
        """Create a new scheduled process"""
        schedule_dict = {
            "user_id": user_id,
            "process_id": schedule_data.process_id,
            "parametros": schedule_data.parametros,
            "schedule_type": schedule_data.schedule_type,
            "schedule_config": schedule_data.schedule_config,
            "status": ScheduleStatus.ACTIVE,
            "next_execution": next_execution,
            "last_execution": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = self.collection.insert_one(schedule_dict)
        schedule_dict["_id"] = str(result.inserted_id)
        
        return ScheduledProcess(**schedule_dict)
    
    def get_by_id(self, schedule_id: str) -> Optional[ScheduledProcess]:
        """Get scheduled process by ID"""
        try:
            schedule = self.collection.find_one({"_id": ObjectId(schedule_id)})
            if schedule:
                schedule["_id"] = str(schedule["_id"])
                return ScheduledProcess(**schedule)
        except Exception as e:
            print(f"[DEBUG] Error in get_by_id for schedule_id '{schedule_id}': {e}")
            return None
        return None
    
    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ScheduledProcess]:
        """Get all scheduled processes for a user"""
        schedules = []
        query = {"user_id": user_id}
        
        for schedule in self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit):
            schedule["_id"] = str(schedule["_id"])
            schedules.append(ScheduledProcess(**schedule))
        
        return schedules
    
    def get_active_schedules(self, before_date: Optional[datetime] = None) -> List[ScheduledProcess]:
        """Get all active schedules that need to be executed"""
        query = {"status": ScheduleStatus.ACTIVE}
        
        if before_date:
            query["next_execution"] = {"$lte": before_date}
        
        schedules = []
        for schedule in self.collection.find(query).sort("next_execution", 1):
            schedule["_id"] = str(schedule["_id"])
            schedules.append(ScheduledProcess(**schedule))
        
        return schedules
    
    def update(self, schedule_id: str, update_data: ScheduledProcessUpdate) -> Optional[ScheduledProcess]:
        """Update a scheduled process"""
        update_dict = {"updated_at": datetime.utcnow()}
        
        if update_data.parametros is not None:
            update_dict["parametros"] = update_data.parametros
        if update_data.schedule_type is not None:
            update_dict["schedule_type"] = update_data.schedule_type
        if update_data.schedule_config is not None:
            update_dict["schedule_config"] = update_data.schedule_config
        if update_data.status is not None:
            update_dict["status"] = update_data.status
        
        result = self.collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return self.get_by_id(schedule_id)
        return None
    
    def update_next_execution(self, schedule_id: str, next_execution: datetime) -> bool:
        """Update the next execution time for a schedule"""
        result = self.collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {
                "$set": {
                    "next_execution": next_execution,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    def update_last_execution(self, schedule_id: str, last_execution: datetime) -> bool:
        """Update the last execution time for a schedule"""
        result = self.collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {
                "$set": {
                    "last_execution": last_execution,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    def update_status(self, schedule_id: str, status: ScheduleStatus) -> bool:
        """Update the status of a scheduled process"""
        result = self.collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    def delete(self, schedule_id: str) -> bool:
        """Delete a scheduled process"""
        result = self.collection.delete_one({"_id": ObjectId(schedule_id)})
        return result.deleted_count > 0

