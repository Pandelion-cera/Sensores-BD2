from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database

from desktop_app.models.sensor_models import Sensor, SensorCreate, SensorUpdate, SensorStatus


class SensorRepository:
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db["sensors"]
        
    def create(self, sensor_data: SensorCreate) -> Sensor:
        """Create a new sensor"""
        import uuid
        from datetime import datetime
        
        sensor_dict = sensor_data.model_dump()
        
        # Generate sensor_id explicitly
        sensor_dict["sensor_id"] = str(uuid.uuid4())
        
        # Ensure estado is set
        if "estado" not in sensor_dict or sensor_dict["estado"] is None:
            sensor_dict["estado"] = "activo"
        
        # Ensure fecha_inicio_emision is set
        if "fecha_inicio_emision" not in sensor_dict:
            sensor_dict["fecha_inicio_emision"] = datetime.utcnow()
        
        result = self.collection.insert_one(sensor_dict)
        sensor_dict["_id"] = str(result.inserted_id)
        
        return Sensor(**sensor_dict)
    
    def get_by_id(self, sensor_id: str) -> Optional[Sensor]:
        """Get sensor by MongoDB ID"""
        try:
            sensor = self.collection.find_one({"_id": ObjectId(sensor_id)})
            if sensor:
                sensor["_id"] = str(sensor["_id"])
                return Sensor(**sensor)
        except:
            return None
        return None
    
    def get_by_sensor_id(self, sensor_id: str) -> Optional[Sensor]:
        """Get sensor by sensor_id (UUID)"""
        sensor = self.collection.find_one({"sensor_id": sensor_id})
        if sensor:
            sensor["_id"] = str(sensor["_id"])
            return Sensor(**sensor)
        return None
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        pais: Optional[str] = None,
        ciudad: Optional[str] = None,
        estado: Optional[SensorStatus] = None
    ) -> List[Sensor]:
        """Get all sensors with optional filters"""
        query = {}
        if pais:
            query["pais"] = pais
        if ciudad:
            query["ciudad"] = ciudad
        if estado:
            query["estado"] = estado
        
        sensors = []
        for sensor in self.collection.find(query).skip(skip).limit(limit):
            sensor["_id"] = str(sensor["_id"])
            sensors.append(Sensor(**sensor))
        return sensors
    
    def update(self, sensor_id: str, sensor_update: SensorUpdate) -> Optional[Sensor]:
        """Update sensor"""
        update_data = sensor_update.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_by_id(sensor_id)
        
        self.collection.update_one(
            {"_id": ObjectId(sensor_id)},
            {"$set": update_data}
        )
        
        return self.get_by_id(sensor_id)
    
    def delete(self, sensor_id: str) -> bool:
        """Delete sensor"""
        result = self.collection.delete_one({"_id": ObjectId(sensor_id)})
        return result.deleted_count > 0
    
    def count_by_status(self) -> dict:
        """Count sensors by status"""
        pipeline = [
            {"$group": {"_id": "$estado", "count": {"$sum": 1}}}
        ]
        result = self.collection.aggregate(pipeline)
        return {item["_id"]: item["count"] for item in result}
    
    def get_countries(self) -> List[str]:
        """Get unique list of countries"""
        return self.collection.distinct("pais")
    
    def get_cities_by_country(self, pais: str) -> List[str]:
        """Get unique list of cities for a country"""
        return self.collection.distinct("ciudad", {"pais": pais})

    def get_amount_of_sensors_by_country(self, pais: str) -> int:
        """Get amount of sensors by country"""
        return self.collection.count_documents({"pais": pais})

