"""
Script to seed initial data into the databases
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add scripts directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import db_manager
from app.repositories.user_repository import UserRepository
from app.repositories.sensor_repository import SensorRepository
from app.repositories.process_repository import ProcessRepository
from app.repositories.group_repository import GroupRepository
from app.models.user_models import UserCreate
from app.models.sensor_models import SensorCreate, SensorType, SensorStatus
from app.models.process_models import ProcessCreate, ProcessType
from app.models.group_models import GroupCreate


def seed_users():
    """Create initial users"""
    print("Seeding users...")
    
    mongo_db = db_manager.get_mongo_db()
    neo4j_driver = db_manager.get_neo4j_driver()
    user_repo = UserRepository(mongo_db, neo4j_driver)
    
    users_data = [
        {
            "data": UserCreate(
                nombre_completo="Admin User",
                email="admin@test.com",
                password="admin123"
            ),
            "role": "administrador"
        },
        {
            "data": UserCreate(
                nombre_completo="Técnico User",
                email="tecnico@test.com",
                password="tecnico123"
            ),
            "role": "tecnico"
        },
        {
            "data": UserCreate(
                nombre_completo="Usuario Regular",
                email="user@test.com",
                password="user123"
            ),
            "role": "usuario"
        },
        {
            "data": UserCreate(
                nombre_completo="Juan Pérez",
                email="juan@test.com",
                password="juan123"
            ),
            "role": "usuario"
        },
        {
            "data": UserCreate(
                nombre_completo="María García",
                email="maria@test.com",
                password="maria123"
            ),
            "role": "usuario"
        }
    ]
    
    created_users = []
    for user_info in users_data:
        try:
            # Check if user exists
            existing = user_repo.get_by_email(user_info["data"].email)
            if existing:
                print(f"  User {user_info['data'].email} already exists")
                created_users.append(existing)
                continue
            
            user = user_repo.create(user_info["data"])
            
            # Assign role
            if user_info["role"] != "usuario":
                user_repo.assign_role(user.id, user_info["role"])
            
            created_users.append(user)
            print(f"  Created user: {user.email} with role {user_info['role']}")
        except Exception as e:
            print(f"  Error creating user {user_info['data'].email}: {e}")
    
    print(f"Seeded {len(created_users)} users")
    return created_users


def seed_sensors():
    """Create initial sensors"""
    print("Seeding sensors...")
    
    mongo_db = db_manager.get_mongo_db()
    sensor_repo = SensorRepository(mongo_db)
    
    # Cities data: (city, country, lat, lng)
    cities = [
        ("Buenos Aires", "Argentina", -34.6037, -58.3816),
        ("Córdoba", "Argentina", -31.4201, -64.1888),
        ("Mendoza", "Argentina", -32.8895, -68.8458),
        ("São Paulo", "Brasil", -23.5505, -46.6333),
        ("Rio de Janeiro", "Brasil", -22.9068, -43.1729),
        ("Santiago", "Chile", -33.4489, -70.6693),
        ("Lima", "Perú", -12.0464, -77.0428),
        ("Bogotá", "Colombia", 4.7110, -74.0721),
        ("Ciudad de México", "México", 19.4326, -99.1332),
        ("Madrid", "España", 40.4168, -3.7038),
        ("Barcelona", "España", 41.3851, 2.1734),
        ("París", "Francia", 48.8566, 2.3522),
        ("Londres", "Reino Unido", 51.5074, -0.1278),
        ("Berlín", "Alemania", 52.5200, 13.4050),
        ("Roma", "Italia", 41.9028, 12.4964),
        ("Tokio", "Japón", 35.6762, 139.6503),
        ("Seúl", "Corea del Sur", 37.5665, 126.9780),
        ("Beijing", "China", 39.9042, 116.4074),
        ("Sídney", "Australia", -33.8688, 151.2093),
        ("Nueva York", "Estados Unidos", 40.7128, -74.0060),
    ]
    
    created_sensors = []
    for i, (ciudad, pais, lat, lng) in enumerate(cities):
        # Create 2-3 sensors per city
        for j in range(2):
            try:
                sensor_data = SensorCreate(
                    nombre=f"Sensor {ciudad} {j+1}",
                    tipo=SensorType.BOTH,
                    latitud=lat + (j * 0.01),  # Slight variation
                    longitud=lng + (j * 0.01),
                    ciudad=ciudad,
                    pais=pais
                )
                
                sensor = sensor_repo.create(sensor_data)
                created_sensors.append(sensor)
                
            except Exception as e:
                print(f"  Error creating sensor for {ciudad}: {e}")
    
    print(f"Seeded {len(created_sensors)} sensors")
    return created_sensors


def seed_processes():
    """Create initial process definitions"""
    print("Seeding processes...")
    
    mongo_db = db_manager.get_mongo_db()
    neo4j_driver = db_manager.get_neo4j_driver()
    process_repo = ProcessRepository(mongo_db, neo4j_driver)
    
    processes_data = [
        {
            "nombre": "Informe Temperaturas Máximas y Mínimas",
            "descripcion": "Genera un informe de temperaturas máximas y mínimas por ciudad en un rango de fechas",
            "tipo": ProcessType.TEMP_MAX_MIN_REPORT,
            "costo": 15.00,
            "parametros_schema": {
                "pais": "string",
                "ciudad": "string",
                "fecha_inicio": "date",
                "fecha_fin": "date"
            }
        },
        {
            "nombre": "Informe Temperaturas Promedio",
            "descripcion": "Genera un informe de temperaturas promedio por ciudad en un rango de fechas",
            "tipo": ProcessType.TEMP_AVG_REPORT,
            "costo": 12.00,
            "parametros_schema": {
                "pais": "string",
                "ciudad": "string",
                "fecha_inicio": "date",
                "fecha_fin": "date"
            }
        },
        {
            "nombre": "Consulta Online de Sensores",
            "descripcion": "Consulta en línea de mediciones de sensores por ubicación",
            "tipo": ProcessType.ONLINE_QUERY,
            "costo": 5.00,
            "parametros_schema": {
                "pais": "string",
                "ciudad": "string",
                "fecha_inicio": "datetime",
                "fecha_fin": "datetime"
            }
        },
        {
            "nombre": "Configuración de Alertas",
            "descripcion": "Configura alertas de temperatura y humedad personalizadas",
            "tipo": ProcessType.ALERT_CONFIG,
            "costo": 8.00,
            "parametros_schema": {
                "pais": "string",
                "ciudad": "string",
                "temp_min": "float",
                "temp_max": "float",
                "humidity_min": "float",
                "humidity_max": "float"
            }
        },
        {
            "nombre": "Reporte Periódico Mensual",
            "descripcion": "Genera reportes periódicos mensuales automáticos",
            "tipo": ProcessType.PERIODIC_REPORT,
            "costo": 25.00,
            "parametros_schema": {
                "pais": "string",
                "ciudad": "string",
                "frecuencia": "string"
            }
        }
    ]
    
    created_processes = []
    for process_data in processes_data:
        try:
            process = process_repo.create_process(ProcessCreate(**process_data))
            created_processes.append(process)
            print(f"  Created process: {process.nombre}")
        except Exception as e:
            print(f"  Error creating process: {e}")
    
    print(f"Seeded {len(created_processes)} processes")
    return created_processes


def seed_groups(users):
    """Create initial groups"""
    print("Seeding groups...")
    
    if len(users) < 3:
        print("  Not enough users to create groups")
        return []
    
    mongo_db = db_manager.get_mongo_db()
    neo4j_driver = db_manager.get_neo4j_driver()
    group_repo = GroupRepository(mongo_db, neo4j_driver)
    
    groups_data = [
        {
            "nombre": "Equipo Técnico",
            "miembros": [users[0].id, users[1].id]  # admin + técnico
        },
        {
            "nombre": "Usuarios Generales",
            "miembros": [u.id for u in users[2:5]] if len(users) >= 5 else [u.id for u in users[2:]]
        }
    ]
    
    created_groups = []
    for group_data in groups_data:
        try:
            group = group_repo.create(GroupCreate(**group_data))
            created_groups.append(group)
            print(f"  Created group: {group.nombre}")
        except Exception as e:
            print(f"  Error creating group: {e}")
    
    print(f"Seeded {len(created_groups)} groups")
    return created_groups


def grant_process_permissions(users, processes):
    """Grant process execution permissions to users"""
    print("Granting process permissions...")
    
    mongo_db = db_manager.get_mongo_db()
    neo4j_driver = db_manager.get_neo4j_driver()
    process_repo = ProcessRepository(mongo_db, neo4j_driver)
    
    # Grant all processes to regular users (non-admin)
    regular_users = [u for u in users if "@test.com" in u.email and "admin" not in u.email]
    
    permissions_granted = 0
    for user in regular_users:
        for process in processes:
            try:
                process_repo.grant_process_permission(user.id, process.id)
                permissions_granted += 1
            except Exception as e:
                print(f"  Error granting permission: {e}")
    
    print(f"Granted {permissions_granted} permissions")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("DATABASE SEEDING")
    print("=" * 60)
    
    try:
        users = seed_users()
        print()
        
        sensors = seed_sensors()
        print()
        
        processes = seed_processes()
        print()
        
        groups = seed_groups(users)
        print()
        
        grant_process_permissions(users, processes)
        print()
        
        print("=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nTest users created:")
        print("  - admin@test.com / admin123 (Administrador)")
        print("  - tecnico@test.com / tecnico123 (Técnico)")
        print("  - user@test.com / user123 (Usuario)")
        print(f"\nSensors created: {len(sensors)}")
        print(f"Processes created: {len(processes)}")
        print(f"Groups created: {len(groups)}")
        
    except Exception as e:
        print(f"\nERROR during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db_manager.close_all()


if __name__ == "__main__":
    main()

