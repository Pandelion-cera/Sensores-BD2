# Visualización de Alertas - Guía para Usuarios

## Descripción General

El sistema permite a los usuarios visualizar alertas generadas automáticamente por el sistema de monitoreo de sensores. Estas alertas pueden provenir de:

1. **Umbrales configurados**: Límites predefinidos en el sistema
2. **Reglas configuradas por administradores**: Condiciones personalizadas de temperatura/humedad por ubicación y fecha

## Endpoints Disponibles para Usuarios

Todos los endpoints requieren autenticación (token JWT).

### 1. Obtener Todas las Alertas

**GET** `/api/alerts`

Obtiene todas las alertas con filtros opcionales.

**Query Parameters:**

- `skip` (int): Número de registros a omitir para paginación (default: 0)
- `limit` (int): Número máximo de registros (default: 100, max: 500)
- `estado` (string): Filtrar por estado
  - `activa`: Alertas activas
  - `resuelta`: Alertas resueltas
  - `reconocida`: Alertas reconocidas
- `tipo` (string): Filtrar por tipo
  - `sensor`: Falla de sensor
  - `climatica`: Condición climática
  - `umbral`: Umbral excedido
- `sensor_id` (string): Filtrar por ID de sensor específico
- `fecha_desde` (string): Fecha inicio en formato ISO (ej: "2025-01-01T00:00:00Z")
- `fecha_hasta` (string): Fecha fin en formato ISO (ej: "2025-12-31T23:59:59Z")

**Ejemplo de uso:**

```bash
GET /api/alerts?estado=activa&limit=50
GET /api/alerts?fecha_desde=2025-01-01T00:00:00Z&fecha_hasta=2025-01-31T23:59:59Z
GET /api/alerts?tipo=umbral&estado=activa
```

**Respuesta:**

```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "tipo": "umbral",
    "sensor_id": "sensor-uuid-123",
    "fecha_hora": "2025-01-15T14:30:00Z",
    "descripcion": "Ola de calor Buenos Aires - Detecta temperaturas extremas en verano. Ubicación: Buenos Aires, Argentina. Temperatura 38.5°C por encima del máximo (35.0°C)",
    "estado": "activa",
    "valor": 38.5,
    "rule_name": "Ola de calor Buenos Aires",
    "prioridad": 4
  }
]
```

---

### 2. Obtener Alertas Activas

**GET** `/api/alerts/active`

Obtiene solo las alertas que están actualmente activas (sin resolver).

**Query Parameters:**

- `skip` (int): Paginación (default: 0)
- `limit` (int): Número máximo (default: 100, max: 500)

**Ejemplo de uso:**

```bash
GET /api/alerts/active
GET /api/alerts/active?limit=20
```

---

### 3. Obtener Alertas por Ubicación

**GET** `/api/alerts/by-location`

Filtra alertas por país y/o ciudad. Útil para usuarios que solo quieren ver alertas de su región.

**Query Parameters:**

- `pais` (string, opcional): Nombre del país
- `ciudad` (string, opcional): Nombre de la ciudad
- `skip` (int): Paginación (default: 0)
- `limit` (int): Número máximo (default: 100, max: 500)
- `estado` (string, opcional): Filtrar por estado
- `fecha_desde` (string, opcional): Fecha inicio
- `fecha_hasta` (string, opcional): Fecha fin

**Ejemplos de uso:**

```bash
# Alertas de Argentina
GET /api/alerts/by-location?pais=Argentina

# Alertas de Buenos Aires, Argentina
GET /api/alerts/by-location?pais=Argentina&ciudad=Buenos Aires

# Alertas activas de Córdoba en enero 2025
GET /api/alerts/by-location?ciudad=Córdoba&estado=activa&fecha_desde=2025-01-01T00:00:00Z&fecha_hasta=2025-01-31T23:59:59Z
```

**Respuesta:**

```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "tipo": "umbral",
    "sensor_id": "sensor-uuid-123",
    "fecha_hora": "2025-01-15T14:30:00Z",
    "descripcion": "Ola de calor Buenos Aires - Detecta temperaturas extremas en verano. Ubicación: Buenos Aires, Argentina. Temperatura 38.5°C por encima del máximo (35.0°C)",
    "estado": "activa",
    "valor": 38.5,
    "rule_name": "Ola de calor Buenos Aires",
    "prioridad": 4
  }
]
```

---

### 4. Obtener Resumen Estadístico

**GET** `/api/alerts/stats/summary`

Obtiene estadísticas resumidas de las alertas (conteos por estado y tipo).

**Query Parameters:**

- `pais` (string, opcional): Filtrar por país
- `ciudad` (string, opcional): Filtrar por ciudad
- `fecha_desde` (string, opcional): Fecha inicio
- `fecha_hasta` (string, opcional): Fecha fin

**Ejemplo de uso:**

```bash
GET /api/alerts/stats/summary
GET /api/alerts/stats/summary?pais=Argentina
GET /api/alerts/stats/summary?ciudad=Buenos Aires&fecha_desde=2025-01-01T00:00:00Z
```

**Respuesta:**

```json
{
  "total": 45,
  "por_estado": {
    "activa": 12,
    "resuelta": 28,
    "reconocida": 5
  },
  "por_tipo": {
    "umbral": 30,
    "sensor": 8,
    "climatica": 7
  },
  "filtros_aplicados": {
    "pais": "Argentina",
    "ciudad": null,
    "fecha_desde": null,
    "fecha_hasta": null
  }
}
```

---

### 5. Obtener Alerta Específica

**GET** `/api/alerts/{alert_id}`

Obtiene los detalles de una alerta específica por su ID.

**Ejemplo de uso:**

```bash
GET /api/alerts/507f1f77bcf86cd799439011
```

---

### 6. Reconocer Alerta

**PATCH** `/api/alerts/{alert_id}/acknowledge`

Marca una alerta como reconocida (el usuario ha visto la alerta).

**Ejemplo de uso:**

```bash
PATCH /api/alerts/507f1f77bcf86cd799439011/acknowledge
```

---

### 7. Stream en Tiempo Real (SSE)

**GET** `/api/alerts/stream/live`

Obtiene alertas en tiempo real mediante Server-Sent Events. Útil para dashboards que necesitan actualizaciones instantáneas.

**Ejemplo de uso en JavaScript:**

```javascript
const eventSource = new EventSource("/api/alerts/stream/live");

eventSource.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log("Nueva alerta:", alert);
  // Actualizar UI con la nueva alerta
};

eventSource.onerror = (error) => {
  console.error("Error en stream:", error);
};
```

---

## Campos de una Alerta

Cada alerta contiene la siguiente información:

| Campo         | Tipo     | Descripción                                           |
| ------------- | -------- | ----------------------------------------------------- |
| `_id`         | string   | ID único de la alerta                                 |
| `tipo`        | string   | Tipo: "sensor", "climatica", o "umbral"               |
| `sensor_id`   | string   | ID del sensor que generó la alerta                    |
| `fecha_hora`  | datetime | Fecha y hora cuando se creó la alerta                 |
| `descripcion` | string   | Descripción detallada de la alerta                    |
| `estado`      | string   | Estado: "activa", "resuelta", o "reconocida"          |
| `valor`       | float    | Valor medido que disparó la alerta                    |
| `umbral`      | float    | Umbral que fue excedido (si aplica)                   |
| `rule_name`   | string   | Nombre de la regla que generó esta alerta (si aplica) |
| `prioridad`   | int      | Nivel de prioridad (1=baja, 5=crítica)                |

---

## Niveles de Prioridad

Las alertas generadas por reglas incluyen un nivel de prioridad:

- **5 - Crítica**: Requiere atención inmediata
- **4 - Alta**: Importante, atender pronto
- **3 - Media**: Monitorear
- **2 - Baja**: Informativa
- **1 - Muy baja**: Solo registro

---

## Estados de Alertas

- **activa**: La alerta está activa y requiere atención
- **reconocida**: El usuario ha visto la alerta pero aún no está resuelta
- **resuelta**: La condición que causó la alerta ya no existe o fue corregida (solo admin/técnico puede resolver)

---

## Ejemplos de Uso Completos

### Ejemplo 1: Ver alertas activas de mi ciudad

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'

# Guardar el token recibido

# Obtener alertas activas de Buenos Aires
curl "http://localhost:8000/api/alerts/by-location?ciudad=Buenos%20Aires&estado=activa" \
  -H "Authorization: Bearer {TOKEN}"
```

### Ejemplo 2: Ver alertas del último mes

```bash
curl "http://localhost:8000/api/alerts?fecha_desde=2025-01-01T00:00:00Z&fecha_hasta=2025-01-31T23:59:59Z" \
  -H "Authorization: Bearer {TOKEN}"
```

### Ejemplo 3: Ver estadísticas de alertas

```bash
curl "http://localhost:8000/api/alerts/stats/summary?pais=Argentina" \
  -H "Authorization: Bearer {TOKEN}"
```

### Ejemplo 4: Reconocer una alerta

```bash
curl -X PATCH "http://localhost:8000/api/alerts/507f1f77bcf86cd799439011/acknowledge" \
  -H "Authorization: Bearer {TOKEN}"
```

---

## Integración con Frontend

### Componente React - Listado de Alertas

```typescript
import { useEffect, useState } from "react";

interface Alert {
  _id: string;
  tipo: string;
  descripcion: string;
  estado: string;
  fecha_hora: string;
  prioridad?: number;
  rule_name?: string;
}

export function AlertList() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/alerts/by-location?ciudad=Buenos Aires&estado=activa", {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
      .then((res) => res.json())
      .then((data) => {
        setAlerts(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Cargando alertas...</div>;

  return (
    <div>
      <h2>Alertas Activas</h2>
      {alerts.map((alert) => (
        <div key={alert._id} className={`alert priority-${alert.prioridad}`}>
          <h3>{alert.rule_name || alert.tipo}</h3>
          <p>{alert.descripcion}</p>
          <span>Estado: {alert.estado}</span>
          <span>Fecha: {new Date(alert.fecha_hora).toLocaleString()}</span>
          {alert.prioridad && <span>Prioridad: {alert.prioridad}/5</span>}
        </div>
      ))}
    </div>
  );
}
```

### Filtros Interactivos

```typescript
export function AlertFilters() {
  const [filters, setFilters] = useState({
    pais: "",
    ciudad: "",
    estado: "",
    fecha_desde: "",
    fecha_hasta: "",
  });

  const handleSearch = () => {
    const params = new URLSearchParams();
    if (filters.pais) params.append("pais", filters.pais);
    if (filters.ciudad) params.append("ciudad", filters.ciudad);
    if (filters.estado) params.append("estado", filters.estado);
    if (filters.fecha_desde) params.append("fecha_desde", filters.fecha_desde);
    if (filters.fecha_hasta) params.append("fecha_hasta", filters.fecha_hasta);

    fetch(`/api/alerts/by-location?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
      .then((res) => res.json())
      .then((data) => {
        // Actualizar lista de alertas
      });
  };

  return (
    <div>
      <input
        placeholder="País"
        value={filters.pais}
        onChange={(e) => setFilters({ ...filters, pais: e.target.value })}
      />
      <input
        placeholder="Ciudad"
        value={filters.ciudad}
        onChange={(e) => setFilters({ ...filters, ciudad: e.target.value })}
      />
      <select
        value={filters.estado}
        onChange={(e) => setFilters({ ...filters, estado: e.target.value })}
      >
        <option value="">Todos los estados</option>
        <option value="activa">Activa</option>
        <option value="reconocida">Reconocida</option>
        <option value="resuelta">Resuelta</option>
      </select>
      <button onClick={handleSearch}>Buscar</button>
    </div>
  );
}
```

---

## Permisos

### Usuarios Regulares Pueden:

- ✅ Ver todas las alertas
- ✅ Filtrar alertas por ubicación, fecha, estado, tipo
- ✅ Ver alertas activas
- ✅ Obtener estadísticas
- ✅ Ver detalles de alertas específicas
- ✅ Reconocer alertas (marcar como vistas)
- ✅ Recibir alertas en tiempo real (SSE)

### Usuarios Regulares NO Pueden:

- ❌ Crear alertas manualmente
- ❌ Resolver alertas (solo admin/técnico)
- ❌ Eliminar alertas
- ❌ Crear o modificar reglas de alertas

---

## Mejores Prácticas

1. **Usar filtros de ubicación**: Si solo te interesan alertas de tu región, usa `/api/alerts/by-location`
2. **Paginación**: Para grandes volúmenes, usa `skip` y `limit` para cargar datos en lotes
3. **Fechas**: Siempre especifica rangos de fechas razonables para mejorar el rendimiento
4. **Tiempo real**: Usa el endpoint de streaming solo cuando realmente necesites actualizaciones instantáneas
5. **Reconocer alertas**: Marca como reconocidas las alertas que ya has revisado para mantener un registro claro

---

## Diferencias con la Funcionalidad de Admin

| Funcionalidad             | Usuario | Administrador |
| ------------------------- | ------- | ------------- |
| Ver alertas               | ✅      | ✅            |
| Filtrar alertas           | ✅      | ✅            |
| Reconocer alertas         | ✅      | ✅            |
| Resolver alertas          | ❌      | ✅            |
| Crear alertas manualmente | ❌      | ✅            |
| Crear reglas de alertas   | ❌      | ✅            |
| Modificar reglas          | ❌      | ✅            |
| Eliminar reglas           | ❌      | ✅            |

---

## Soporte

Para cualquier duda sobre el uso de alertas, consulta la documentación completa o contacta al administrador del sistema.
