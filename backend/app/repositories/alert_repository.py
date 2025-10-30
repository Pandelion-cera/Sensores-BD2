from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo.database import Database
import redis
import json
from datetime import datetime

from app.models.alert_models import Alert, AlertCreate, AlertStatus


class AlertRepository:
    def __init__(self, mongo_db: Database, redis_client: redis.Redis):
        self.collection = mongo_db["alerts"]
        self.redis = redis_client
        self.stream_key = "alerts:stream"
        
    def create(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert in MongoDB and publish to Redis Stream"""
        alert_dict = alert_data.model_dump()
        alert_dict["estado"] = AlertStatus.ACTIVE
        
        result = self.collection.insert_one(alert_dict)
        alert_dict["_id"] = str(result.inserted_id)
        
        # Publish to Redis Stream for real-time notifications
        self.publish_alert(alert_dict)
        
        return Alert(**alert_dict)
    
    def publish_alert(self, alert_dict: Dict[str, Any]) -> str:
        """Publish alert to Redis Stream"""
        # Convert datetime to ISO format for JSON serialization
        if "fecha_hora" in alert_dict and isinstance(alert_dict["fecha_hora"], datetime):
            alert_dict["fecha_hora"] = alert_dict["fecha_hora"].isoformat()
        
        # Add to Redis Stream
        message_id = self.redis.xadd(
            self.stream_key,
            {"data": json.dumps(alert_dict)}
        )
        
        return message_id
    
    def get_by_id(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        try:
            alert = self.collection.find_one({"_id": ObjectId(alert_id)})
            if alert:
                alert["_id"] = str(alert["_id"])
                return Alert(**alert)
        except:
            return None
        return None
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[AlertStatus] = None,
        sensor_id: Optional[str] = None
    ) -> List[Alert]:
        """Get all alerts with optional filters"""
        query = {}
        if estado:
            query["estado"] = estado
        if sensor_id:
            query["sensor_id"] = sensor_id
        
        alerts = []
        for alert in self.collection.find(query).sort("fecha_hora", -1).skip(skip).limit(limit):
            alert["_id"] = str(alert["_id"])
            alerts.append(Alert(**alert))
        
        return alerts
    
    def update_status(self, alert_id: str, status: AlertStatus) -> Optional[Alert]:
        """Update alert status"""
        self.collection.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"estado": status}}
        )
        
        return self.get_by_id(alert_id)
    
    def get_active_alerts(self, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get all active alerts"""
        return self.get_all(skip=skip, limit=limit, estado=AlertStatus.ACTIVE)
    
    def read_alert_stream(self, count: int = 10, last_id: str = "0") -> List[Dict[str, Any]]:
        """Read alerts from Redis Stream"""
        messages = self.redis.xread({self.stream_key: last_id}, count=count, block=1000)
        
        alerts = []
        for stream, entries in messages:
            for entry_id, entry_data in entries:
                alert_data = json.loads(entry_data[b"data"])
                alert_data["stream_id"] = entry_id
                alerts.append(alert_data)
        
        return alerts
    
    def delete(self, alert_id: str) -> bool:
        """Delete an alert"""
        result = self.collection.delete_one({"_id": ObjectId(alert_id)})
        return result.deleted_count > 0

