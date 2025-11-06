"""
Script to fix alerts that don't have fecha_hora set
"""
import sys
from pathlib import Path
from datetime import datetime

# Add scripts directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import db_manager


def fix_alerts_dates():
    """Add fecha_hora to alerts that don't have it"""
    print("=" * 60)
    print("FIXING ALERTS DATES")
    print("=" * 60)
    
    mongo_db = db_manager.get_mongo_db()
    alerts_col = mongo_db["alerts"]
    
    # Find alerts without fecha_hora or with null fecha_hora
    query = {
        "$or": [
            {"fecha_hora": {"$exists": False}},
            {"fecha_hora": None}
        ]
    }
    
    alerts = list(alerts_col.find(query))
    print(f"Found {len(alerts)} alerts without fecha_hora")
    
    if not alerts:
        print("No alerts to fix")
        db_manager.close_all()
        return
    
    updated = 0
    for alert in alerts:
        # Use current time as fecha_hora (or could use _id timestamp if available)
        # For better accuracy, we could use the ObjectId timestamp
        try:
            from bson import ObjectId
            alert_id = alert.get("_id")
            if alert_id:
                # ObjectId contains timestamp of creation
                object_id = ObjectId(alert_id) if isinstance(alert_id, str) else alert_id
                creation_time = object_id.generation_time
                fecha_hora = creation_time
            else:
                fecha_hora = datetime.utcnow()
        except:
            fecha_hora = datetime.utcnow()
        
        alerts_col.update_one(
            {"_id": alert["_id"]},
            {"$set": {"fecha_hora": fecha_hora}}
        )
        updated += 1
        print(f"  Updated alert {alert.get('_id')} with fecha_hora: {fecha_hora}")
    
    print(f"\nUpdated {updated} alerts")
    
    # Verify
    remaining = alerts_col.count_documents(query)
    print(f"Remaining alerts without fecha_hora: {remaining}")
    
    db_manager.close_all()


if __name__ == "__main__":
    fix_alerts_dates()

