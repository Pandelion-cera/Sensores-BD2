from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str = "mongodb://admin:admin123@localhost:27017/"
    MONGO_DB_NAME: str = "sensor_db"
    
    # Cassandra
    CASSANDRA_HOSTS: str = "localhost"
    CASSANDRA_KEYSPACE: str = "sensor_keyspace"
    CASSANDRA_REPLICATION_FACTOR: int = 1
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password123"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours
    
    # API
    API_TITLE: str = "Sensor Management API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API for managing climate sensors and measurements"
    
    # Alert thresholds
    TEMP_MIN_THRESHOLD: float = -50.0
    TEMP_MAX_THRESHOLD: float = 60.0
    HUMIDITY_MIN_THRESHOLD: float = 0.0
    HUMIDITY_MAX_THRESHOLD: float = 100.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

