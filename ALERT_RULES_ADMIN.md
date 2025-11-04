# Sistema de Reglas de Alertas - Documentación para Administradores

## Descripción General

Se ha implementado un sistema completo de **reglas de alertas configurables** que permite a los administradores:

1. **Crear reglas** que definan condiciones automáticas para generar alertas
2. **Modificar reglas** existentes
3. **Activar/Desactivar reglas** sin eliminarlas
4. **Eliminar reglas** cuando ya no sean necesarias
5. **Ver todas las reglas** configuradas con filtros

## Arquitectura Implementada

### 1. Modelos de Datos (`alert_rule_models.py`)

- **AlertRule**: Modelo completo de una regla de alerta
- **AlertRuleCreate**: Modelo para crear nuevas reglas
- **AlertRuleUpdate**: Modelo para actualizar reglas existentes
- **LocationScope**: Define el alcance geográfico (ciudad, región, país)
- **AlertRuleStatus**: Estado de la regla (activa/inactiva)

### 2. Repositorio (`alert_rule_repository.py`)

Gestiona las operaciones CRUD en MongoDB:

- `create()`: Crear nueva regla
- `get_by_id()`: Obtener regla por ID
- `get_all()`: Listar todas las reglas con filtros
- `get_active_rules()`: Obtener solo reglas activas
- `get_applicable_rules()`: Obtener reglas aplicables para una ubicación y fecha
- `update()`: Actualizar regla
- `update_status()`: Cambiar estado (activar/desactivar)
- `delete()`: Eliminar regla

### 3. Servicio (`alert_rule_service.py`)

Lógica de negocio que:

- Valida las reglas antes de crearlas/actualizarlas
- Verifica mediciones contra reglas activas
- Genera alertas automáticas cuando se violan las condiciones

### 4. API REST (`alert_rules.py`)

Endpoints disponibles solo para **administradores**:

#### POST `/api/alert-rules`

Crear una nueva regla de alerta.

**Ejemplo de body:**

```json
{
  "nombre": "Alerta ola de calor Buenos Aires",
  "descripcion": "Detecta temperaturas extremas en verano",
  "temp_min": 35.0,
  "temp_max": 50.0,
  "humidity_min": null,
  "humidity_max": null,
  "location_scope": "ciudad",
  "ciudad": "Buenos Aires",
  "region": null,
  "pais": "Argentina",
  "fecha_inicio": "2024-12-01T00:00:00",
  "fecha_fin": "2025-03-31T23:59:59",
  "estado": "activa",
  "prioridad": 4
}
```

#### GET `/api/alert-rules`

Obtener todas las reglas con filtros opcionales.

**Query params:**

- `skip`: Número de registros a omitir (paginación)
- `limit`: Número máximo de registros
- `estado`: Filtrar por estado (activa/inactiva)
- `pais`: Filtrar por país
- `ciudad`: Filtrar por ciudad

#### GET `/api/alert-rules/active`

Obtener solo las reglas activas.

#### GET `/api/alert-rules/summary`

Obtener resumen estadístico (total, activas, inactivas).

#### GET `/api/alert-rules/{rule_id}`

Obtener una regla específica por ID.

#### PUT `/api/alert-rules/{rule_id}`

Actualizar una regla existente.

**Ejemplo de body:**

```json
{
  "nombre": "Alerta ola de calor Buenos Aires (actualizada)",
  "temp_max": 45.0,
  "prioridad": 5
}
```

#### PATCH `/api/alert-rules/{rule_id}/activate`

Activar una regla.

#### PATCH `/api/alert-rules/{rule_id}/deactivate`

Desactivar una regla (sin eliminarla).

#### DELETE `/api/alert-rules/{rule_id}`

Eliminar permanentemente una regla.

## Funcionamiento Automático

### Verificación de Mediciones

Cuando un sensor registra una nueva medición (POST `/api/sensors/{sensor_id}/measurements`), el sistema:

1. Guarda la medición en Cassandra
2. Verifica los umbrales configurados en `config.py` (legacy)
3. **NUEVO**: Obtiene todas las reglas activas aplicables para esa ubicación y fecha
4. Evalúa si la medición viola alguna condición de las reglas
5. Si se viola una regla, crea automáticamente una alerta con:
   - Descripción detallada incluyendo el nombre de la regla
   - Prioridad de la regla
   - Valores medidos y umbrales violados
   - Ubicación donde ocurrió

### Ejemplo de Flujo

1. Admin crea regla: "Temperatura > 35°C en Buenos Aires en verano"
2. Un sensor en Buenos Aires registra 38°C
3. El sistema:
   - Identifica que la regla aplica (ciudad = Buenos Aires, fecha en rango)
   - Detecta que 38°C > 35°C
   - Genera alerta automática
   - Notifica a través de Redis Stream (tiempo real)

## Campos de una Regla

### Condiciones de Temperatura

- `temp_min`: Temperatura mínima (genera alerta si la medición es menor)
- `temp_max`: Temperatura máxima (genera alerta si la medición es mayor)

### Condiciones de Humedad

- `humidity_min`: Humedad mínima (0-100%)
- `humidity_max`: Humedad máxima (0-100%)

### Ubicación

- `location_scope`: Alcance geográfico
  - `"ciudad"`: Aplica solo a una ciudad específica
  - `"region"`: Aplica a una región/zona
  - `"pais"`: Aplica a todo un país
- `ciudad`: Nombre de la ciudad (requerido si scope = "ciudad")
- `region`: Nombre de la región (requerido si scope = "region")
- `pais`: Nombre del país (siempre requerido)

### Rango de Fechas

- `fecha_inicio`: Inicio de vigencia (opcional)
- `fecha_fin`: Fin de vigencia (opcional)
- Si ambos son null, la regla aplica siempre

### Metadatos

- `nombre`: Nombre descriptivo de la regla
- `descripcion`: Descripción detallada
- `prioridad`: Nivel de importancia (1=baja, 5=crítica)
- `estado`: "activa" o "inactiva"
- `creado_por`: Email del admin que creó la regla (se asigna automáticamente)

## Validaciones Implementadas

1. **Al menos una condición**: Debe definir temp_min/max o humidity_min/max
2. **Coherencia de rangos**: min no puede ser mayor que max
3. **Coherencia de fechas**: fecha_inicio no puede ser posterior a fecha_fin
4. **Campos según scope**:
   - Si scope = "ciudad", debe especificar ciudad
   - Si scope = "region", debe especificar región
5. **Solo administradores**: Todos los endpoints verifican rol de admin

## Ejemplos de Uso

### Ejemplo 1: Alerta de heladas en Patagonia

```json
{
  "nombre": "Alerta heladas Patagonia",
  "descripcion": "Detecta temperaturas bajo cero en invierno",
  "temp_min": -10.0,
  "temp_max": 0.0,
  "location_scope": "region",
  "region": "Patagonia",
  "pais": "Argentina",
  "fecha_inicio": "2025-06-01T00:00:00",
  "fecha_fin": "2025-09-30T23:59:59",
  "prioridad": 3
}
```

### Ejemplo 2: Humedad alta en todo el país

```json
{
  "nombre": "Humedad extrema Argentina",
  "descripcion": "Detecta humedad muy alta que puede causar problemas",
  "humidity_min": 90.0,
  "humidity_max": 100.0,
  "location_scope": "pais",
  "pais": "Argentina",
  "prioridad": 2
}
```

### Ejemplo 3: Ola de calor en ciudad específica

```json
{
  "nombre": "Ola de calor Córdoba",
  "descripcion": "Temperaturas extremas en Córdoba",
  "temp_min": 38.0,
  "temp_max": 50.0,
  "location_scope": "ciudad",
  "ciudad": "Córdoba",
  "pais": "Argentina",
  "fecha_inicio": "2025-01-01T00:00:00",
  "fecha_fin": "2025-02-28T23:59:59",
  "prioridad": 5
}
```

## Integración con Alertas Existentes

El sistema de reglas se integra perfectamente con el sistema de alertas existente:

1. Las alertas generadas por reglas tienen `tipo: "umbral"`
2. Se almacenan en MongoDB (colección `alerts`)
3. Se publican en Redis Stream para notificaciones en tiempo real
4. Los usuarios pueden verlas en `/api/alerts` (ya implementado)
5. Se pueden resolver/reconocer igual que las alertas normales

## Próximos Pasos (Frontend)

Para completar la funcionalidad, se necesitará en el frontend:

1. **Panel de administración de reglas**:

   - Listado de reglas con filtros
   - Formulario para crear nuevas reglas
   - Formulario para editar reglas existentes
   - Botones para activar/desactivar/eliminar

2. **Visualización de alertas para usuarios**:
   - Ya existe `/alerts`, solo asegurar que muestre todas las alertas
   - Filtrar por tipo, fecha, ubicación
   - Mostrar la prioridad de las alertas

## Seguridad

- ✅ Solo usuarios con rol "administrador" pueden gestionar reglas
- ✅ El campo `creado_por` se asigna automáticamente del token JWT
- ✅ Todas las operaciones están protegidas por autenticación
- ✅ Las validaciones previenen datos incoherentes

## Consultas y Pruebas

Para probar, puedes usar estos curl/Postman requests:

```bash
# 1. Login como admin
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Guarda el token recibido

# 2. Crear regla
curl -X POST http://localhost:8000/api/alert-rules \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 3. Listar reglas
curl http://localhost:8000/api/alert-rules \
  -H "Authorization: Bearer {TOKEN}"
```
