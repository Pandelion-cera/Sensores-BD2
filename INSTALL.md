# Guía de Instalación Rápida - TP Persistencia Políglota

## Requisitos Previos

- Docker Desktop instalado (Windows/Mac) o Docker + Docker Compose (Linux)
- Al menos 8GB de RAM disponible
- 10GB de espacio en disco

## Instalación Paso a Paso

### 1. Verificar Docker

```bash
docker --version
docker-compose --version
```

### 2. Levantar los Servicios

Desde la raíz del proyecto:

```bash
docker-compose up -d
```

**Tiempo estimado**: 3-5 minutos (dependiendo de tu conexión a internet)

### 3. Verificar Estado de los Servicios

```bash
docker-compose ps
```

Todos deben mostrar "Up" o "healthy". Si Cassandra muestra "starting", espera 1-2 minutos más.

### 4. Inicializar las Bases de Datos

Desde la raíz del proyecto, ejecuta:

```bash
python scripts/init_databases.py
```

**Nota**: Asegúrate de tener Python 3.8+ instalado y las dependencias necesarias (ver `backend/requirements.txt` o instala con `pip install -r backend/requirements.txt`).

Este comando:
- Crea keyspace y tablas en Cassandra
- Crea índices en MongoDB
- Crea constraints y roles en Neo4j
- Verifica Redis

**Salida esperada**: Mensajes de éxito para cada base de datos

### 5. Cargar Datos de Prueba

```bash
python scripts/seed_data.py
```

Este comando crea:
- 5 usuarios (admin, técnico, usuarios)
- 40+ sensores en diferentes ciudades
- 5 procesos disponibles
- 2 grupos de mensajería

**Salida esperada**: Lista de usuarios, sensores y procesos creados

### 6. (Opcional) Iniciar el Simulador de Datos

En una terminal nueva:

```bash
python scripts/data_generator.py
```

Para detenerlo, presiona `Ctrl+C`.

## Acceso a la Aplicación

### Aplicación de Escritorio

Ejecuta la aplicación de escritorio desde el directorio `desktop_app`:

```bash
cd desktop_app
python main.py
```

**Usuarios de prueba**:
- Admin: `admin@test.com` / `admin123`
- Usuario: `user@test.com` / `user123`

### Interfaces de Bases de Datos

- **Neo4j Browser**: http://localhost:7474 (neo4j / password123)
- **MongoDB**: Usar Compass con `mongodb://admin:admin123@localhost:27017/`

## Solución de Problemas Comunes

### "Cannot connect to Docker daemon"

Asegúrate de que Docker Desktop esté corriendo.

### Cassandra no inicia

1. Aumenta la memoria de Docker a 8GB en Docker Desktop > Settings > Resources
2. Reinicia Docker Desktop
3. Espera 2-3 minutos después de `docker-compose up`

### Scripts no funcionan

Asegúrate de tener instaladas las dependencias de Python:

```bash
pip install pymongo cassandra-driver neo4j redis pydantic pydantic-settings
```

O instala manualmente:
- pymongo
- cassandra-driver
- neo4j
- redis
- pydantic
- pydantic-settings

### Limpiar todo y empezar de nuevo

```bash
docker-compose down -v
docker-compose up -d
# Luego ejecutar pasos 4 y 5 nuevamente
```

## Comandos Útiles

```bash
# Ver logs de un servicio de base de datos
docker-compose logs -f mongodb
docker-compose logs -f cassandra
docker-compose logs -f neo4j

# Reiniciar un servicio
docker-compose restart mongodb

# Detener todo
docker-compose stop

# Eliminar todo (incluyendo volúmenes)
docker-compose down -v

# Ver estado
docker-compose ps
```

## Próximos Pasos

1. Inicia la aplicación de escritorio desde `desktop_app/main.py`
2. Inicia sesión con uno de los usuarios de prueba
3. Explora el dashboard
4. Ve a la sección de Sensores para ver los sensores creados
5. Solicita un proceso en la sección de Procesos
6. Revisa las alertas en tiempo real

## Soporte

Si encuentras problemas:
1. Revisa los logs de las bases de datos: `docker-compose logs [servicio]`
2. Consulta el README.md completo
3. Verifica que todos los puertos estén disponibles (27017, 9042, 7474, 7687, 6379)
4. Asegúrate de que las bases de datos estén corriendo: `docker-compose ps`

