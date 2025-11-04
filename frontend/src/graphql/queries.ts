import { gql } from '@apollo/client'

export const GET_SENSORS = gql`
  query GetSensors($skip: Int, $limit: Int, $pais: String, $ciudad: String, $estado: SensorStatus) {
    sensors(skip: $skip, limit: $limit, pais: $pais, ciudad: $ciudad, estado: $estado) {
      id
      sensorId
      nombre
      tipo
      latitud
      longitud
      ciudad
      pais
      estado
      fechaInicioEmision
    }
  }
`

export const GET_SENSOR = gql`
  query GetSensor($id: String!) {
    sensor(id: $id) {
      id
      sensorId
      nombre
      tipo
      latitud
      longitud
      ciudad
      pais
      estado
      fechaInicioEmision
    }
  }
`

export const GET_SENSOR_STATS = gql`
  query GetSensorStats {
    sensorStats {
      total
      activos
      inactivos
      conFalla
    }
  }
`

export const GET_SENSOR_MEASUREMENTS = gql`
  query GetSensorMeasurements($sensorId: String!, $startDate: DateTime, $endDate: DateTime) {
    sensorMeasurements(sensorId: $sensorId, startDate: $startDate, endDate: $endDate) {
      sensorId
      timestamp
      temperature
      humidity
    }
  }
`

export const GET_LOCATION_MEASUREMENTS = gql`
  query GetLocationMeasurements($pais: String!, $ciudad: String!, $startDate: DateTime, $endDate: DateTime) {
    locationMeasurements(pais: $pais, ciudad: $ciudad, startDate: $startDate, endDate: $endDate) {
      sensorId
      timestamp
      temperature
      humidity
    }
  }
`

export const GET_LOCATION_STATS = gql`
  query GetLocationStats($pais: String!, $ciudad: String!, $startDate: DateTime, $endDate: DateTime) {
    locationStats(pais: $pais, ciudad: $ciudad, startDate: $startDate, endDate: $endDate) {
      temperaturaMax
      temperaturaMin
      temperaturaPromedio
      humedadMax
      humedadMin
      humedadPromedio
      totalMediciones
    }
  }
`

export const GET_ALERTS = gql`
  query GetAlerts($skip: Int, $limit: Int, $estado: AlertStatus, $tipo: AlertType, $sensorId: String, $fechaDesde: DateTime, $fechaHasta: DateTime) {
    alerts(skip: $skip, limit: $limit, estado: $estado, tipo: $tipo, sensorId: $sensorId, fechaDesde: $fechaDesde, fechaHasta: $fechaHasta) {
      id
      tipo
      sensorId
      fechaHora
      descripcion
      estado
      valor
      umbral
      ruleId
      ruleName
      prioridad
    }
  }
`

export const GET_ACTIVE_ALERTS = gql`
  query GetActiveAlerts($skip: Int, $limit: Int) {
    activeAlerts(skip: $skip, limit: $limit) {
      id
      tipo
      sensorId
      fechaHora
      descripcion
      estado
      valor
      umbral
      ruleId
      ruleName
      prioridad
    }
  }
`

export const GET_ALERTS_BY_LOCATION = gql`
  query GetAlertsByLocation($pais: String, $ciudad: String, $skip: Int, $limit: Int, $estado: AlertStatus, $fechaDesde: DateTime, $fechaHasta: DateTime) {
    alertsByLocation(pais: $pais, ciudad: $ciudad, skip: $skip, limit: $limit, estado: $estado, fechaDesde: $fechaDesde, fechaHasta: $fechaHasta) {
      id
      tipo
      sensorId
      fechaHora
      descripcion
      estado
      valor
      umbral
      ruleId
      ruleName
      prioridad
    }
  }
`

export const GET_ALERTS_SUMMARY = gql`
  query GetAlertsSummary {
    alertsSummary {
      total
      activas
      resueltas
      reconocidas
    }
  }
`

export const GET_ALERT_RULES = gql`
  query GetAlertRules($skip: Int, $limit: Int, $estado: AlertRuleStatus) {
    alertRules(skip: $skip, limit: $limit, estado: $estado) {
      id
      nombre
      descripcion
      tempMin
      tempMax
      humidityMin
      humidityMax
      locationScope
      ciudad
      region
      pais
      fechaInicio
      fechaFin
      estado
      prioridad
      creadoPor
      fechaCreacion
      fechaModificacion
    }
  }
`

export const GET_ALERT_RULES_SUMMARY = gql`
  query GetAlertRulesSummary {
    alertRulesSummary {
      total
      activas
      inactivas
    }
  }
`

export const GET_PROCESSES = gql`
  query GetProcesses($skip: Int, $limit: Int) {
    processes(skip: $skip, limit: $limit) {
      id
      nombre
      descripcion
      tipo
      costo
      parametrosSchema
      activo
    }
  }
`

export const GET_PROCESS = gql`
  query GetProcess($id: String!) {
    process(id: $id) {
      id
      nombre
      descripcion
      tipo
      costo
      parametrosSchema
      activo
    }
  }
`

export const GET_USER_PROCESS_REQUESTS = gql`
  query GetUserProcessRequests($userId: String!, $skip: Int, $limit: Int) {
    userProcessRequests(userId: $userId, skip: $skip, limit: $limit) {
      id
      userId
      processId
      fechaSolicitud
      estado
      parametros
      invoiceId
      invoiceCreated
    }
  }
`

export const GET_EXECUTION = gql`
  query GetExecution($requestId: String!) {
    execution(requestId: $requestId) {
      id
      requestId
      fechaEjecucion
      estado
      resultado
      errorMessage
    }
  }
`

export const GET_MY_INVOICES = gql`
  query GetMyInvoices($skip: Int, $limit: Int) {
    myInvoices(skip: $skip, limit: $limit) {
      id
      userId
      fechaEmision
      items {
        processId
        processName
        cantidad
        precioUnitario
        subtotal
      }
      total
      estado
      fechaVencimiento
    }
  }
`

export const GET_INVOICE = gql`
  query GetInvoice($id: String!) {
    invoice(id: $id) {
      id
      userId
      fechaEmision
      items {
        processId
        processName
        cantidad
        precioUnitario
        subtotal
      }
      total
      estado
      fechaVencimiento
    }
  }
`

export const GET_MY_ACCOUNT = gql`
  query GetMyAccount {
    myAccount {
      id
      userId
      saldo
      movimientos {
        fecha
        tipo
        monto
        descripcion
        referenciaId
      }
      fechaCreacion
    }
  }
`

export const GET_MY_MESSAGES = gql`
  query GetMyMessages($skip: Int, $limit: Int) {
    myMessages(skip: $skip, limit: $limit) {
      id
      senderId
      senderName
      recipientType
      recipientId
      recipientName
      timestamp
      content
    }
  }
`

export const GET_GROUP_MESSAGES = gql`
  query GetGroupMessages($groupId: String!, $skip: Int, $limit: Int) {
    groupMessages(groupId: $groupId, skip: $skip, limit: $limit) {
      id
      senderId
      senderName
      recipientType
      recipientId
      recipientName
      timestamp
      content
    }
  }
`

export const GET_MY_GROUPS = gql`
  query GetMyGroups {
    myGroups {
      id
      nombre
      miembros
      fechaCreacion
    }
  }
`

export const GET_ALL_GROUPS = gql`
  query GetAllGroups($skip: Int, $limit: Int) {
    allGroups(skip: $skip, limit: $limit) {
      id
      nombre
      miembros
      fechaCreacion
    }
  }
`

export const GET_CURRENT_USER = gql`
  query GetCurrentUser {
    me {
      id
      nombreCompleto
      email
      estado
      fechaRegistro
    }
  }
`

export const GET_USERS = gql`
  query GetUsers($skip: Int, $limit: Int) {
    users(skip: $skip, limit: $limit) {
      id
      nombreCompleto
      email
      estado
      fechaRegistro
    }
  }
`
