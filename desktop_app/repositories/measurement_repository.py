from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from cassandra.cluster import Session
from cassandra.query import SimpleStatement
import uuid

from desktop_app.models.measurement_models import Measurement, MeasurementCreate


class MeasurementRepository:
    def __init__(self, cassandra_session: Session, keyspace: str):
        self.session = cassandra_session
        self.keyspace = keyspace
        
        # Set keyspace
        self.session.set_keyspace(keyspace)
        
        # Prepared statements for better performance
        self.insert_by_sensor_stmt = self.session.prepare(
            """
            INSERT INTO measurements_by_sensor 
            (sensor_id, date_partition, timestamp, temperature, humidity)
            VALUES (?, ?, ?, ?, ?)
            """
        )
        
        self.insert_by_location_stmt = self.session.prepare(
            """
            INSERT INTO measurements_by_location
            (country, city, date_partition, timestamp, sensor_id, temperature, humidity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        )

        self.insert_by_date_stmt = self.session.prepare(
            """
            INSERT INTO measurements_by_date
            (date_partition, timestamp, sensor_id, temperature, humidity)
            VALUES (?, ?, ?, ?, ?)
            """
        )

    def create(
        self, 
        sensor_id: str, 
        measurement: MeasurementCreate,
        ciudad: str,
        pais: str
    ) -> Measurement:
        """Insert measurement into both Cassandra tables"""
        timestamp = datetime.utcnow()
        date_partition = timestamp.strftime("%Y%m%d")
        
        # Insert into measurements_by_sensor
        self.session.execute(
            self.insert_by_sensor_stmt,
            (
                uuid.UUID(sensor_id),
                date_partition,
                timestamp,
                measurement.temperature,
                measurement.humidity
            )
        )
        
        # Insert into measurements_by_location
        self.session.execute(
            self.insert_by_location_stmt,
            (
                pais,
                ciudad,
                date_partition,
                timestamp,
                uuid.UUID(sensor_id),
                measurement.temperature,
                measurement.humidity
            )
        )
        
        # Insert into measurements_by_date
        self.session.execute(
            self.insert_by_date_stmt,
            (
                date_partition,
                timestamp,
                uuid.UUID(sensor_id),
                measurement.temperature,
                measurement.humidity
            )
        )
        
        return Measurement(
            sensor_id=sensor_id,
            timestamp=timestamp,
            temperature=measurement.temperature,
            humidity=measurement.humidity
        )
    
    def get_by_sensor(
        self,
        sensor_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Measurement]:
        """Get measurements for a sensor in a date range"""
        measurements = []
        
        # Generate date partitions
        current_date = start_date
        while current_date <= end_date:
            date_partition = current_date.strftime("%Y%m%d")
            
            query = """
                SELECT sensor_id, timestamp, temperature, humidity
                FROM measurements_by_sensor
                WHERE sensor_id = %s AND date_partition = %s
                AND timestamp >= %s AND timestamp <= %s
            """
            
            rows = self.session.execute(
                query,
                (uuid.UUID(sensor_id), date_partition, start_date, end_date)
            )
            
            for row in rows:
                measurements.append(Measurement(
                    sensor_id=str(row.sensor_id),
                    timestamp=row.timestamp,
                    temperature=row.temperature,
                    humidity=row.humidity
                ))
            
            current_date += timedelta(days=1)
        
        return measurements
    
    def get_by_location(
        self,
        pais: str,
        ciudad: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get measurements for a location in a date range"""
        measurements = []
        
        # Generate date partitions
        current_date = start_date
        while current_date <= end_date:
            date_partition = current_date.strftime("%Y%m%d")
            
            query = """
                SELECT country, city, timestamp, sensor_id, temperature, humidity
                FROM measurements_by_location
                WHERE country = %s AND city = %s AND date_partition = %s
                AND timestamp >= %s AND timestamp <= %s
            """
            
            rows = self.session.execute(
                query,
                (pais, ciudad, date_partition, start_date, end_date)
            )
            
            for row in rows:
                measurements.append({
                    "pais": row.country,
                    "ciudad": row.city,
                    "sensor_id": str(row.sensor_id),
                    "timestamp": row.timestamp,
                    "temperature": row.temperature,
                    "humidity": row.humidity
                })
            
            current_date += timedelta(days=1)
        
        return measurements
    
    def get_stats_by_location(
        self,
        pais: str,
        ciudad: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get statistics (max, min, avg) for a location"""
        measurements = self.get_by_location(pais, ciudad, start_date, end_date)
        
        if not measurements:
            return {
                "pais": pais,
                "ciudad": ciudad,
                "count": 0,
                "temperatura": {},
                "humedad": {}
            }
        
        temps = [m["temperature"] for m in measurements if m["temperature"] is not None]
        humidities = [m["humidity"] for m in measurements if m["humidity"] is not None]
        
        return {
            "pais": pais,
            "ciudad": ciudad,
            "count": len(measurements),
            "temperatura": {
                "max": max(temps) if temps else None,
                "min": min(temps) if temps else None,
                "avg": sum(temps) / len(temps) if temps else None
            },
            "humedad": {
                "max": max(humidities) if humidities else None,
                "min": min(humidities) if humidities else None,
                "avg": sum(humidities) / len(humidities) if humidities else None
            }
        }

    def get_amount_of_measurements_by_date(self, start_date: datetime, end_date: datetime) -> int:
        total = 0
        current_date = start_date.date()
        end_date_date = end_date.date()

        while current_date <= end_date_date:
            partition = current_date.strftime("%Y%m%d")
            rows = self.session.execute(
                """
                SELECT COUNT(*)
                FROM measurements_by_date
                WHERE date_partition = %s
                  AND timestamp >= %s AND timestamp <= %s
                """,
                (partition, start_date, end_date),
            )
            total += rows.one()[0]
            current_date += timedelta(days=1)
        return total

