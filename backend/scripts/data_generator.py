"""
Script to generate simulated sensor measurements continuously
"""
import sys
from pathlib import Path
import time
import random
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import db_manager
from app.core.config import settings
from app.repositories.sensor_repository import SensorRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.models.measurement_models import MeasurementCreate
from app.models.sensor_models import SensorStatus
from app.services.alert_service import AlertService
from app.repositories.alert_repository import AlertRepository


# Temperature ranges by season (Northern hemisphere approximation)
TEMP_RANGES = {
    "winter": (-5, 15),
    "spring": (10, 25),
    "summer": (20, 40),
    "fall": (5, 20)
}


def get_season(month):
    """Get season based on month (Northern hemisphere)"""
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"


def generate_temperature(lat, base_temp=None):
    """Generate realistic temperature based on latitude"""
    # Closer to equator = warmer
    month = datetime.now().month
    season = get_season(month)
    
    # Adjust for hemisphere
    if lat < 0:  # Southern hemisphere - reverse seasons
        if season == "winter":
            season = "summer"
        elif season == "summer":
            season = "winter"
    
    min_temp, max_temp = TEMP_RANGES[season]
    
    # Adjust based on latitude (tropical regions are warmer)
    if abs(lat) < 23.5:  # Tropics
        min_temp += 10
        max_temp += 10
    
    if base_temp is None:
        temp = random.uniform(min_temp, max_temp)
    else:
        # Small variation from previous reading
        temp = base_temp + random.uniform(-2, 2)
        temp = max(min_temp, min(max_temp, temp))  # Clamp to range
    
    return round(temp, 2)


def generate_humidity(temperature):
    """Generate realistic humidity correlated with temperature"""
    # Generally, higher temps = lower humidity (simplified)
    if temperature > 30:
        base_humidity = random.uniform(30, 60)
    elif temperature > 20:
        base_humidity = random.uniform(40, 75)
    elif temperature > 10:
        base_humidity = random.uniform(50, 85)
    else:
        base_humidity = random.uniform(60, 95)
    
    return round(base_humidity, 2)


def generate_measurements_batch(sensor_repo, measurement_repo, alert_service):
    """Generate one batch of measurements for all active sensors"""
    
    # Get all active sensors
    sensors = sensor_repo.get_all(skip=0, limit=1000, estado=SensorStatus.ACTIVE)
    
    if not sensors:
        print("No active sensors found")
        return 0
    
    count = 0
    for sensor in sensors:
        try:
            # Generate temperature
            temperature = generate_temperature(sensor.latitud)
            
            # Generate humidity
            humidity = generate_humidity(temperature)
            
            # Create measurement
            measurement_data = MeasurementCreate(
                temperature=temperature,
                humidity=humidity
            )
            
            # Save to Cassandra
            measurement_repo.create(
                sensor.sensor_id,
                measurement_data,
                sensor.ciudad,
                sensor.pais
            )
            
            # Check for alerts
            alerts = alert_service.check_measurement_thresholds(
                sensor,
                temperature,
                humidity
            )
            
            count += 1
            
            if alerts:
                print(f"  ⚠️  Alert generated for sensor {sensor.nombre}: {temperature}°C, {humidity}%")
            
        except Exception as e:
            print(f"Error generating measurement for sensor {sensor.nombre}: {e}")
    
    return count


def main():
    """Main generator loop"""
    print("=" * 60)
    print("SENSOR DATA GENERATOR")
    print("=" * 60)
    print()
    
    # Initialize connections
    mongo_db = db_manager.get_mongo_db()
    cassandra_session = db_manager.get_cassandra_session()
    redis_client = db_manager.get_redis_client()
    
    sensor_repo = SensorRepository(mongo_db)
    measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
    alert_repo = AlertRepository(mongo_db, redis_client)
    alert_service = AlertService(alert_repo)
    
    print(f"Configuration:")
    print(f"  Cassandra Keyspace: {settings.CASSANDRA_KEYSPACE}")
    print(f"  Temperature thresholds: {settings.TEMP_MIN_THRESHOLD}°C to {settings.TEMP_MAX_THRESHOLD}°C")
    print(f"  Humidity thresholds: {settings.HUMIDITY_MIN_THRESHOLD}% to {settings.HUMIDITY_MAX_THRESHOLD}%")
    print()
    
    # Get sensor count
    sensors = sensor_repo.get_all(skip=0, limit=1000, estado=SensorStatus.ACTIVE)
    print(f"Found {len(sensors)} active sensors")
    print()
    
    if not sensors:
        print("ERROR: No active sensors found. Please run seed_data.py first.")
        return
    
    print("Starting data generation... (Press Ctrl+C to stop)")
    print()
    
    iteration = 0
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate measurements for all sensors
            count = generate_measurements_batch(sensor_repo, measurement_repo, alert_service)
            
            print(f"[{timestamp}] Iteration {iteration}: Generated {count} measurements")
            
            # Wait 5 seconds before next batch
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\nStopping data generator...")
        print(f"Total iterations: {iteration}")
        print(f"Approximate measurements generated: {iteration * len(sensors)}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db_manager.close_all()
        print("\nData generator stopped.")


if __name__ == "__main__":
    main()

