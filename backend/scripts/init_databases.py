"""
Script to initialize all databases with schemas, indexes, and initial data
"""
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import db_manager
from app.core.config import settings
from cassandra.query import SimpleStatement


def init_mongodb():
    """Initialize MongoDB collections and indexes"""
    print("Initializing MongoDB...")
    
    db = db_manager.get_mongo_db()
    
    # Create indexes
    print("Creating indexes...")
    
    # Users
    db.users.create_index("email", unique=True)
    db.users.create_index("estado")
    
    # Sensors
    db.sensors.create_index("sensor_id", unique=True)
    db.sensors.create_index([("pais", 1), ("ciudad", 1)])
    db.sensors.create_index("estado")
    
    # Messages
    db.messages.create_index([("recipient_type", 1), ("recipient_id", 1), ("timestamp", -1)])
    db.messages.create_index([("sender_id", 1), ("timestamp", -1)])
    
    # Process requests
    db.process_requests.create_index([("user_id", 1), ("estado", 1), ("fecha_solicitud", -1)])
    
    # Invoices
    db.invoices.create_index([("user_id", 1), ("fecha_emision", -1)])
    db.invoices.create_index([("estado", 1)])
    
    # Payments
    db.payments.create_index("invoice_id")
    
    # Accounts
    db.accounts.create_index("user_id", unique=True)
    
    # Alerts
    db.alerts.create_index([("estado", 1), ("fecha_hora", -1)])
    db.alerts.create_index("sensor_id")
    
    print("MongoDB indexes created successfully")


def init_cassandra():
    """Initialize Cassandra keyspace and tables"""
    print("Initializing Cassandra...")
    
    session = db_manager.get_cassandra_session()
    keyspace = settings.CASSANDRA_KEYSPACE
    replication_factor = settings.CASSANDRA_REPLICATION_FACTOR
    
    # Wait for Cassandra to be ready
    max_retries = 10
    for i in range(max_retries):
        try:
            session.execute("SELECT now() FROM system.local")
            break
        except Exception as e:
            if i == max_retries - 1:
                raise
            print(f"Waiting for Cassandra to be ready... ({i+1}/{max_retries})")
            time.sleep(5)
    
    # Create keyspace
    print(f"Creating keyspace {keyspace}...")
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH replication = {{
            'class': 'SimpleStrategy',
            'replication_factor': {replication_factor}
        }}
    """)
    
    # Set keyspace
    session.set_keyspace(keyspace)
    
    # Create measurements_by_sensor table
    print("Creating measurements_by_sensor table...")
    session.execute("""
        CREATE TABLE IF NOT EXISTS measurements_by_sensor (
            sensor_id UUID,
            date_partition TEXT,
            timestamp TIMESTAMP,
            temperature DOUBLE,
            humidity DOUBLE,
            PRIMARY KEY ((sensor_id, date_partition), timestamp)
        ) WITH CLUSTERING ORDER BY (timestamp DESC)
    """)
    
    # Create measurements_by_location table
    print("Creating measurements_by_location table...")
    session.execute("""
        CREATE TABLE IF NOT EXISTS measurements_by_location (
            country TEXT,
            city TEXT,
            date_partition TEXT,
            timestamp TIMESTAMP,
            sensor_id UUID,
            temperature DOUBLE,
            humidity DOUBLE,
            PRIMARY KEY ((country, city, date_partition), timestamp)
        ) WITH CLUSTERING ORDER BY (timestamp DESC)
    """)
    
    print("Cassandra tables created successfully")


def init_neo4j():
    """Initialize Neo4j constraints and initial nodes"""
    print("Initializing Neo4j...")
    
    driver = db_manager.get_neo4j_driver()
    
    with driver.session() as session:
        # Create constraints
        print("Creating constraints...")
        
        try:
            session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT role_name IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE")
            session.run("CREATE CONSTRAINT group_id IF NOT EXISTS FOR (g:Group) REQUIRE g.id IS UNIQUE")
            session.run("CREATE CONSTRAINT process_id IF NOT EXISTS FOR (p:Process) REQUIRE p.id IS UNIQUE")
        except Exception as e:
            print(f"Note: Some constraints may already exist - {e}")
        
        # Create initial roles
        print("Creating initial roles...")
        roles = [
            {"name": "usuario", "description": "Usuario regular del sistema"},
            {"name": "tecnico", "description": "Técnico de mantenimiento"},
            {"name": "administrador", "description": "Administrador del sistema"}
        ]
        
        for role in roles:
            session.run(
                """
                MERGE (r:Role {name: $name})
                ON CREATE SET r.description = $description
                """,
                name=role["name"],
                description=role["description"]
            )
        
        print("Neo4j initialization completed successfully")


def init_redis():
    """Initialize Redis (clear any existing data if needed)"""
    print("Initializing Redis...")
    
    redis_client = db_manager.get_redis_client()
    
    # Redis doesn't need schema initialization
    # Just verify connection
    redis_client.ping()
    
    print("Redis connection verified")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    
    try:
        init_mongodb()
        print()
        
        init_cassandra()
        print()
        
        init_neo4j()
        print()
        
        init_redis()
        print()
        
        print("=" * 60)
        print("ALL DATABASES INITIALIZED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db_manager.close_all()


if __name__ == "__main__":
    main()

