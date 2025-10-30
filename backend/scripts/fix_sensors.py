"""
Script to fix existing sensors - add missing fields
"""
import sys
from pathlib import Path
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import db_manager
from datetime import datetime


def fix_sensors():
    """Add missing fields to existing sensors"""
    print("=" * 60)
    print("FIXING SENSORS")
    print("=" * 60)
    
    mongo_db = db_manager.get_mongo_db()
    sensors_col = mongo_db["sensors"]
    
    # Get all sensors
    sensors = list(sensors_col.find({}))
    print(f"Found {len(sensors)} sensors")
    
    updated = 0
    for sensor in sensors:
        update_fields = {}
        
        # Add estado if missing
        if "estado" not in sensor:
            update_fields["estado"] = "activo"
        
        # Add or fix sensor_id if missing or invalid
        sensor_id = sensor.get("sensor_id")
        needs_new_id = False
        
        if sensor_id is None:
            needs_new_id = True
        else:
            # Try to validate it as a UUID
            try:
                uuid.UUID(str(sensor_id))
            except (ValueError, AttributeError):
                needs_new_id = True
        
        if needs_new_id:
            update_fields["sensor_id"] = str(uuid.uuid4())
        
        # Add fecha_inicio_emision if missing
        if "fecha_inicio_emision" not in sensor:
            update_fields["fecha_inicio_emision"] = datetime.utcnow()
        
        if update_fields:
            sensors_col.update_one(
                {"_id": sensor["_id"]},
                {"$set": update_fields}
            )
            updated += 1
            print(f"  Updated sensor {sensor.get('nombre', 'Unknown')}")
    
    print(f"\nUpdated {updated} sensors")
    
    # Verify
    activos = sensors_col.count_documents({"estado": "activo"})
    print(f"Total sensors with estado=activo: {activos}")
    
    db_manager.close_all()


if __name__ == "__main__":
    fix_sensors()

