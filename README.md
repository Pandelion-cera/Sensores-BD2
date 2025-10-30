# TP Persistencia Políglota - Sistema de Gestión de Sensores Climáticos

Sistema de gestión de sensores climáticos con arquitectura de persistencia políglota utilizando MongoDB, Cassandra, Neo4j y Redis.

## Arquitectura

### Bases de Datos

1. **MongoDB** (Puerto 27017)
   - Usuarios, Grupos, Mensajes
   - Procesos, Solicitudes, Ejecuciones
   - Facturas, Pagos, Cuentas Corrientes
   - Sensores, Control de Funcionamiento
   - **Justificación**: Transacciones ACID por documento, flexible para estructuras variables (facturas con ítems, mensajes con diferentes destinatarios)

2. **Cassandra** (Puerto 9042)
   - Mediciones de sensores (time-series)
   - Tabla `measurements_by_sensor`: particionada por sensor_id + fecha
   - Tabla `measurements_by_location`: particionada por país + ciudad + fecha
   - **Justificación**: Optimizada para escrituras masivas, particionamiento eficiente por tiempo, clustering por timestamp para consultas rápidas

3. **Neo4j** (Puerto 7474/7687)
   - Roles y permisos (RBAC)
   - Relaciones User-Role, User-Group, User-Process
   - Dependencias entre procesos
   - **Justificación**: Traversal eficiente para control de acceso, consultas "qué usuarios pueden ejecutar X", jerarquías de grupos

4. **Redis** (Puerto 6379)
   - Sesiones activas (TTL 24h)
   - Stream de alertas en tiempo real
   - Cache de consultas frecuentes
   - **Justificación**: Latencia sub-milisegundo, ideal para sesiones y alertas push, estructuras de datos avanzadas (Streams)

### Backend (FastAPI)

- **Python 3.11** con FastAPI
- Patrón Repository para abstracción de datos
- Servicios para lógica de negocio
- JWT para autenticación
- Endpoints REST documentados con Swagger

### Frontend (Next.js 14)

- React con TypeScript
- App Router de Next.js 14
- Tailwind CSS + Shadcn UI
- Axios para comunicación con API

## Requisitos Previos

- Docker y Docker Compose
- Al menos 8GB de RAM disponible
- Puertos disponibles: 3000, 8000, 27017, 9042, 7474, 7687, 6379

## Instalación y Ejecución

### 1. Clonar el Repositorio

```bash
cd BD2-TPO
```

### 2. Levantar Todos los Servicios

```bash
docker-compose up -d
```

Esto iniciará:
- MongoDB
- Cassandra
- Neo4j
- Redis
- Backend (FastAPI)
- Frontend (Next.js)

**Nota**: Cassandra puede tardar 1-2 minutos en estar completamente listo.

### 3. Verificar que los Servicios Estén Activos

```bash
docker-compose ps
```

Todos los servicios deben mostrar estado "Up" o "healthy".

### 4. Inicializar las Bases de Datos

```bash
docker-compose exec backend python scripts/init_databases.py
```

Este script:
- Crea el keyspace y tablas en Cassandra
- Crea índices en MongoDB
- Crea constraints y roles iniciales en Neo4j
- Verifica conexión a Redis

### 5. Cargar Datos de Prueba

```bash
docker-compose exec backend python scripts/seed_data.py
```

Este script crea:
- 5 usuarios de prueba (incluye admin, técnico, usuarios)
- 40+ sensores en diferentes ciudades del mundo
- 5 tipos de procesos
- 2 grupos de mensajería
- Permisos de ejecución de procesos

### 6. Iniciar el Generador de Datos (Opcional)

Para simular mediciones en tiempo real:

```bash
docker-compose exec backend python scripts/data_generator.py
```

El generador:
- Genera mediciones cada 5 segundos para todos los sensores activos
- Simula temperaturas realistas según ubicación geográfica y estación
- Genera alertas cuando se superan umbrales
- Publica a Redis Stream para notificaciones en tiempo real

Para detenerlo, presiona `Ctrl+C`.

## Acceso a la Aplicación

### Frontend Web

**URL**: http://localhost:3000

**Usuarios de prueba**:
- Administrador: `admin@test.com` / `admin123`
- Técnico: `tecnico@test.com` / `tecnico123`
- Usuario: `user@test.com` / `user123`

### API Backend

**URL**: http://localhost:8000
**Documentación Swagger**: http://localhost:8000/docs
**Health Check**: http://localhost:8000/health

### Interfaces de Bases de Datos

- **Neo4j Browser**: http://localhost:7474
  - Usuario: `neo4j`
  - Contraseña: `password123`

- **MongoDB**: `mongodb://admin:admin123@localhost:27017/`
  - Usar MongoDB Compass o similar

## Endpoints Principales de la API

### Autenticación

- `POST /api/auth/register` - Registrar nuevo usuario
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/logout` - Cerrar sesión
- `GET /api/auth/me` - Obtener usuario actual

### Sensores

- `GET /api/sensors` - Listar sensores (filtros: país, ciudad, estado)
- `POST /api/sensors` - Crear sensor (admin/técnico)
- `GET /api/sensors/{id}` - Detalle de sensor
- `PUT /api/sensors/{id}` - Actualizar sensor
- `POST /api/sensors/{id}/measurements` - Registrar medición

### Mediciones

- `GET /api/measurements/sensor/{sensor_id}` - Mediciones de un sensor
- `GET /api/measurements/location` - Mediciones por ubicación
- `GET /api/measurements/stats` - Estadísticas (max/min/avg)

### Procesos

- `GET /api/processes` - Listar procesos disponibles
- `POST /api/processes/requests` - Solicitar ejecución
- `GET /api/processes/requests/user/{user_id}` - Solicitudes de usuario
- `POST /api/processes/requests/{id}/execute` - Ejecutar proceso
- `GET /api/processes/executions/{request_id}` - Ver resultado

### Facturas

- `GET /api/invoices` - Listar facturas del usuario
- `GET /api/invoices/{id}` - Detalle de factura
- `POST /api/invoices/{id}/pay` - Pagar factura
- `GET /api/invoices/account/me` - Ver cuenta corriente

### Alertas

- `GET /api/alerts` - Listar alertas
- `GET /api/alerts/active` - Alertas activas
- `GET /api/alerts/stream/live` - Stream SSE de alertas en tiempo real
- `PATCH /api/alerts/{id}/resolve` - Resolver alerta

## Tipos de Procesos Disponibles

1. **Informe Temperaturas Máximas y Mínimas** ($15.00)
   - Genera reporte de temperaturas extremas por ciudad/país en rango de fechas

2. **Informe Temperaturas Promedio** ($12.00)
   - Calcula promedios de temperatura y humedad

3. **Consulta Online de Sensores** ($5.00)
   - Consulta en línea de mediciones recientes

4. **Configuración de Alertas** ($8.00)
   - Configura umbrales personalizados de alerta

5. **Reporte Periódico Mensual** ($25.00)
   - Genera reportes automáticos mensuales

## Flujo de Datos

1. **Ingesta**: Mediciones → Cassandra (ambas tablas) + Redis Stream (alertas)
2. **Alertas**: Worker evalúa umbrales → Redis Pub/Sub → Frontend (SSE)
3. **Transaccional**: Usuarios/Procesos/Facturas → MongoDB
4. **Permisos**: Verificación de acceso → Neo4j
5. **Reportes**: PySpark agrega datos de Cassandra → MongoDB (resultados)

## Comandos Útiles

### Ver logs de un servicio

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Reiniciar un servicio

```bash
docker-compose restart backend
```

### Acceder al shell del backend

```bash
docker-compose exec backend /bin/bash
```

### Limpiar todo y empezar de nuevo

```bash
docker-compose down -v
docker-compose up -d
# Luego ejecutar init_databases.py y seed_data.py nuevamente
```

## Estructura del Proyecto

```
BD2-TPO/
├── backend/
│   ├── app/
│   │   ├── api/              # Endpoints REST
│   │   ├── core/             # Config, database, security
│   │   ├── models/           # Modelos Pydantic
│   │   ├── repositories/     # Acceso a BD
│   │   ├── services/         # Lógica de negocio
│   │   └── main.py           # Aplicación FastAPI
│   ├── scripts/
│   │   ├── init_databases.py # Inicialización
│   │   ├── seed_data.py      # Datos de prueba
│   │   └── data_generator.py # Simulador
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Páginas Next.js
│   │   ├── components/       # Componentes UI
│   │   └── lib/              # API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Justificaciones Técnicas (Para la Presentación)

### ¿Por qué MongoDB?
- ACID a nivel documento garantiza consistencia en facturas
- Flexible para documentos con estructura variable
- Índices compuestos para búsquedas eficientes por usuario/estado/fecha
- Natural para modelos documentales (invoice con líneas de procesos)

### ¿Por qué Cassandra?
- Escrituras masivas optimizadas para time-series
- Particionamiento por sensor+fecha distribuye carga
- Clustering por timestamp permite consultas rápidas por rango
- Desnormalización (dos tablas) optimiza diferentes patrones de consulta

### ¿Por qué Neo4j?
- Traversal eficiente para RBAC (¿qué usuarios pueden ejecutar X?)
- Consultas de permisos en grafos son más naturales que JOINs
- Jerarquías de grupos y dependencias de procesos
- Performance óptima para "caminos" y relaciones

### ¿Por qué Redis?
- Latencia sub-milisegundo crítica para sesiones
- Streams ideales para alertas push en tiempo real
- TTL automático para sesiones temporales
- Cache elimina consultas repetitivas a otras BD

## Troubleshooting

### Cassandra no inicia
- Aumentar memoria Docker a 8GB mínimo
- Esperar 2-3 minutos después de `docker-compose up`
- Verificar logs: `docker-compose logs cassandra`

### Backend no conecta a las BD
- Verificar que todos los contenedores estén "Up"
- Reiniciar backend: `docker-compose restart backend`
- Ver logs: `docker-compose logs backend`

### Frontend no carga
- Verificar que backend esté respondiendo en puerto 8000
- Limpiar caché del navegador
- Ver logs: `docker-compose logs frontend`

### Error "Session not found"
- Las sesiones expiran después de 24 horas
- Cerrar sesión y volver a iniciar

## Autores

[Nombres de los integrantes del grupo]

## Fecha de Entrega

[Fecha correspondiente según cronograma]

