# Arquitectura del Sistema - TP Persistencia Políglota

## Visión General

Sistema de gestión de sensores climáticos con arquitectura de persistencia políglota, utilizando 4 bases de datos especializadas según los patrones de acceso y requisitos de cada dominio.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 14)                     │
│                    http://localhost:3000                         │
│  - Login/Register  - Dashboard  - Sensores  - Procesos          │
│  - Facturas  - Alertas  - Mensajería                            │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST + SSE
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                         │
│                    http://localhost:8000                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Services   │  │ Repositories │  │   Models     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────┬─────────┬────────────┬────────────┬───────────────────┘
         │         │            │            │
    ┌────▼───┐ ┌──▼────┐ ┌────▼─────┐ ┌───▼─────┐
    │MongoDB │ │Cassand│ │  Neo4j   │ │  Redis  │
    │:27017  │ │ra:9042│ │:7474/7687│ │  :6379  │
    └────────┘ └───────┘ └──────────┘ └─────────┘
```

## Decisiones de Diseño por Base de Datos

### 1. MongoDB (Documento)

**Uso**: Usuarios, Grupos, Mensajes, Procesos, Solicitudes, Ejecuciones, Facturas, Pagos, Cuentas Corrientes, Sensores, Control de Funcionamiento

**Justificación**:
- ✅ **ACID a nivel documento**: Garantiza consistencia en operaciones complejas como facturas
- ✅ **Esquema flexible**: Ideal para documentos con estructura variable (ej: mensajes privados vs grupales)
- ✅ **Índices compuestos**: Búsquedas eficientes por múltiples criterios (user_id + estado + fecha)
- ✅ **Modelo natural**: Facturas con ítems anidados, cuentas con movimientos

**Alternativas descartadas**:
- ❌ PostgreSQL: Demasiado rígido para facturas con ítems variables
- ❌ Redis: No persistente para datos críticos de negocio

**Esquema ejemplo**:
```javascript
// Invoice
{
  "_id": ObjectId,
  "user_id": "...",
  "fecha_emision": ISODate,
  "items": [
    { "process_id": "...", "process_name": "...", "precio": 15.00 }
  ],
  "total": 15.00,
  "estado": "pendiente"
}
```

### 2. Cassandra (Columnar/Time-Series)

**Uso**: Mediciones de sensores (temperatura y humedad)

**Justificación**:
- ✅ **Escrituras masivas**: Optimizado para millones de mediciones por día
- ✅ **Particionamiento por tiempo**: sensor_id + date_partition distribuye carga
- ✅ **Clustering por timestamp**: Consultas por rango ultra-rápidas
- ✅ **Desnormalización eficiente**: Dos tablas optimizadas para diferentes consultas

**Alternativas descartadas**:
- ❌ MongoDB: Menos eficiente para time-series a gran escala
- ❌ InfluxDB: Funcionalidad SQL limitada, menos maduro

**Esquema**:
```cql
-- Por sensor (consultas individuales)
CREATE TABLE measurements_by_sensor (
    sensor_id UUID,
    date_partition TEXT,      -- 'YYYYMMDD'
    timestamp TIMESTAMP,
    temperature DOUBLE,
    humidity DOUBLE,
    PRIMARY KEY ((sensor_id, date_partition), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);

-- Por ubicación (análisis agregados)
CREATE TABLE measurements_by_location (
    country TEXT,
    city TEXT,
    date_partition TEXT,
    timestamp TIMESTAMP,
    sensor_id UUID,
    temperature DOUBLE,
    humidity DOUBLE,
    PRIMARY KEY ((country, city, date_partition), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);
```

**Patrón Write-Write**: Duplicamos datos en dos tablas para optimizar diferentes patrones de lectura sin JOINs costosos.

### 3. Neo4j (Grafo)

**Uso**: Roles, Permisos, Relaciones User-Role-Process, Grupos, Dependencias

**Justificación**:
- ✅ **Traversal eficiente**: Consultas de permisos en O(log n) vs O(n²) en SQL
- ✅ **Naturaleza relacional**: "¿Qué usuarios pueden ejecutar proceso X?" es un grafo
- ✅ **Jerarquías**: Grupos dentro de grupos, herencia de permisos
- ✅ **Consultas complejas**: Path finding para dependencias entre procesos

**Alternativas descartadas**:
- ❌ PostgreSQL con tablas de permisos: JOINs múltiples lentos
- ❌ MongoDB con referencias: Sin capacidad de traversal eficiente

**Modelo de grafo**:
```cypher
// Nodos
(:User {id, email})
(:Role {name, description})
(:Group {id, name})
(:Process {id, name})

// Relaciones
(:User)-[:HAS_ROLE]->(:Role)
(:User)-[:MEMBER_OF]->(:Group)
(:User)-[:CAN_EXECUTE]->(:Process)
(:Process)-[:DEPENDS_ON]->(:Process)
```

**Consulta ejemplo**:
```cypher
// ¿Qué usuarios pueden ejecutar este proceso?
MATCH (u:User)-[:CAN_EXECUTE]->(p:Process {id: $processId})
RETURN u

// Performance: O(log n) con índices vs O(n²) con JOINs SQL
```

### 4. Redis (In-Memory Key-Value)

**Uso**: Sesiones activas, Streams de alertas, Cache de consultas

**Justificación**:
- ✅ **Latencia sub-ms**: Crítico para sesiones (cada request verifica auth)
- ✅ **TTL automático**: Sesiones expiran sin lógica adicional
- ✅ **Redis Streams**: Pub/Sub para alertas en tiempo real
- ✅ **Estructuras avanzadas**: Hashes, Lists, Sorted Sets

**Alternativas descartadas**:
- ❌ MongoDB: Latencia 10-50ms vs <1ms de Redis
- ❌ Memcached: Sin persistencia ni estructuras avanzadas

**Estructuras**:
```redis
# Sesión con TTL
SETEX session:{uuid} 86400 '{"user_id": "...", "role": "admin"}'

# Stream de alertas
XADD alerts:stream * data '{"tipo": "climatica", ...}'

# Cache de consulta
SETEX cache:stats:BA 3600 '{"temp_max": 32, ...}'
```

## Flujo de Datos End-to-End

### Ingesta de Mediciones

```
Sensor → POST /api/sensors/{id}/measurements → Backend
                                                  ↓
                                    ┌─────────────┴─────────────┐
                                    ↓                           ↓
                           Cassandra (2 tablas)          Redis Stream
                           measurements_by_sensor        (alertas)
                           measurements_by_location
```

### Autenticación y Sesión

```
User → POST /api/auth/login → Backend
                                ↓
                    ┌───────────┼───────────┐
                    ↓           ↓           ↓
                 MongoDB     Neo4j      Redis
                 (user)     (roles)   (session)
                                ↓
                            JWT Token
```

### Solicitud de Proceso

```
User → POST /api/processes/requests → Backend
                                         ↓
                                ┌────────┴────────┐
                                ↓                 ↓
                            MongoDB           Neo4j
                         (crear request)   (verificar permisos)
                                ↓
                        Background Worker
                                ↓
                        ┌───────┴───────┐
                        ↓               ↓
                    Cassandra        MongoDB
                   (leer mediciones) (guardar resultado)
```

### Alertas en Tiempo Real

```
Medición → check_thresholds() → Redis Stream XADD
                                      ↓
                              ┌───────┴───────┐
                              ↓               ↓
                          MongoDB         Frontend
                        (persistir)       (SSE stream)
```

## Patrones de Diseño Implementados

### 1. Repository Pattern

Abstrae el acceso a datos de cada BD:

```python
class UserRepository:
    def __init__(self, mongo_db, neo4j_driver):
        self.collection = mongo_db["users"]
        self.neo4j_driver = neo4j_driver
    
    def create(self, user_data):
        # Guarda en MongoDB
        result = self.collection.insert_one(...)
        # Crea nodo en Neo4j
        with self.neo4j_driver.session() as session:
            session.run("CREATE (u:User ...)")
```

### 2. Service Layer

Encapsula lógica de negocio:

```python
class ProcessService:
    def execute_process(self, request_id):
        # 1. Verificar permisos (Neo4j)
        # 2. Leer mediciones (Cassandra)
        # 3. Procesar datos (PySpark)
        # 4. Guardar resultado (MongoDB)
        # 5. Crear factura (MongoDB)
```

### 3. CQRS Lite

Separación de lecturas y escrituras en Cassandra:

- **Command**: Escribe en ambas tablas
- **Query**: Lee de tabla optimizada para el patrón específico

### 4. Event Sourcing (Parcial)

Redis Streams como log de eventos de alertas:

```python
# Producer
redis.xadd("alerts:stream", {"data": alert_json})

# Consumer
messages = redis.xread({"alerts:stream": last_id})
```

## Escalabilidad

### Cassandra
- **Horizontal**: Añadir nodos al cluster
- **Replication Factor**: Configurable (default: 1 para dev)
- **Particionamiento**: Automático por partition key

### MongoDB
- **Sharding**: Por user_id para distribuir carga
- **Replication**: Replica sets para HA

### Neo4j
- **Causal Clustering**: Multiple read replicas
- **Índices**: En todos los nodos para traversal rápido

### Redis
- **Redis Cluster**: Sharding automático
- **Sentinel**: HA con failover automático

## Seguridad

### Autenticación
- JWT tokens (HS256) con expiración 24h
- Sesiones en Redis con TTL
- Passwords hasheados con bcrypt

### Autorización
- RBAC con Neo4j (roles: usuario, técnico, administrador)
- Verificación por endpoint en middleware FastAPI
- Permisos granulares por proceso

### Datos
- MongoDB: Authentication habilitada
- Neo4j: Usuario/contraseña
- Redis: Sin password en dev (usar Redis AUTH en prod)
- Cassandra: PlainTextAuthProvider en prod

## Monitoreo y Observabilidad

### Logs
- FastAPI: uvicorn logs
- Aplicación: Python logging
- Docker: `docker-compose logs -f [service]`

### Métricas
- `/health` endpoint: Estado de todas las BD
- Cassandra: nodetool status
- Neo4j: Browser UI con query stats
- Redis: INFO command

### Alertas
- Stream de Redis para alertas operacionales
- SSE endpoint para frontend en tiempo real

## Testing

### Unit Tests
```python
# test_repositories.py
def test_user_repository_create():
    user_repo = UserRepository(mock_mongo, mock_neo4j)
    user = user_repo.create(UserCreate(...))
    assert user.id is not None
```

### Integration Tests
```python
# test_api.py
def test_login_endpoint():
    response = client.post("/api/auth/login", json={...})
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Deployment

### Desarrollo (Docker Compose)
```bash
docker-compose up -d
```

### Producción (Recomendaciones)
- **Kubernetes**: Helm charts para cada BD
- **AWS**: DocumentDB (MongoDB), Keyspaces (Cassandra), Neptune (grafo), ElastiCache (Redis)
- **GCP**: Firestore, Bigtable, Cloud Neo4j, Memorystore
- **Backup**: Snapshots diarios de todas las BD
- **Secrets**: Vault o Secrets Manager para credenciales

## Conclusión

La arquitectura de persistencia políglota permite:

1. ✅ **Performance óptimo**: Cada BD hace lo que mejor sabe hacer
2. ✅ **Escalabilidad independiente**: Escala solo lo que necesitas
3. ✅ **Flexibilidad**: Cambia una BD sin afectar las demás
4. ✅ **Costo-eficiencia**: No sobredimensionar una sola BD

**Trade-offs**:
- ❌ Complejidad operacional (más BDs = más monitoreo)
- ❌ Consistencia eventual entre BDs
- ❌ Transacciones distribuidas limitadas

Para este caso de uso (sensores IoT + transaccional + permisos), los beneficios superan ampliamente los costos.

