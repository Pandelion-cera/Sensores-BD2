from pymongo import MongoClient
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from neo4j import GraphDatabase
import redis
from typing import Optional
import time
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Singleton manager for all database connections"""
    
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._mongo_client: Optional[MongoClient] = None
        self._cassandra_cluster: Optional[Cluster] = None
        self._cassandra_session = None
        self._neo4j_driver = None
        self._redis_client: Optional[redis.Redis] = None
        self._initialized = True
    
    def get_mongo_client(self) -> MongoClient:
        """Get MongoDB client (lazy initialization)"""
        if self._mongo_client is None:
            try:
                self._mongo_client = MongoClient(settings.MONGO_URI)
                # Test connection
                self._mongo_client.admin.command('ping')
                logger.info("MongoDB connection established")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
        return self._mongo_client
    
    def get_mongo_db(self):
        """Get MongoDB database"""
        client = self.get_mongo_client()
        return client[settings.MONGO_DB_NAME]
    
    def get_cassandra_session(self):
        """Get Cassandra session (lazy initialization)"""
        if self._cassandra_session is None:
            try:
                hosts = settings.CASSANDRA_HOSTS.split(',')
                self._cassandra_cluster = Cluster(hosts)
                self._cassandra_session = self._cassandra_cluster.connect()
                logger.info("Cassandra connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Cassandra: {e}")
                raise
        return self._cassandra_session
    
    def get_neo4j_driver(self):
        """Get Neo4j driver (lazy initialization)"""
        if self._neo4j_driver is None:
            try:
                self._neo4j_driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                # Test connection
                with self._neo4j_driver.session() as session:
                    session.run("RETURN 1")
                logger.info("Neo4j connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
        return self._neo4j_driver
    
    def get_redis_client(self) -> redis.Redis:
        """Get Redis client (lazy initialization)"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._redis_client
    
    def close_all(self):
        """Close all database connections"""
        if self._mongo_client:
            self._mongo_client.close()
            logger.info("MongoDB connection closed")
        
        if self._cassandra_cluster:
            self._cassandra_cluster.shutdown()
            logger.info("Cassandra connection closed")
        
        if self._neo4j_driver:
            self._neo4j_driver.close()
            logger.info("Neo4j connection closed")
        
        if self._redis_client:
            self._redis_client.close()
            logger.info("Redis connection closed")


# Global instance
db_manager = DatabaseManager()


# Dependency functions for FastAPI
def get_mongo_db():
    return db_manager.get_mongo_db()


def get_cassandra_session():
    return db_manager.get_cassandra_session()


def get_neo4j_driver():
    return db_manager.get_neo4j_driver()


def get_redis_client():
    return db_manager.get_redis_client()

