import { gql } from '@apollo/client'

export const REGISTER = gql`
  mutation Register($input: UserCreateInput!) {
    register(input: $input) {
      user {
        id
        nombreCompleto
        email
        estado
        fechaRegistro
      }
      message
    }
  }
`

export const LOGIN = gql`
  mutation Login($input: UserLoginInput!) {
    login(input: $input) {
      accessToken
      tokenType
      user {
        id
        nombreCompleto
        email
        estado
        fechaRegistro
      }
      sessionId
    }
  }
`

export const LOGOUT = gql`
  mutation Logout {
    logout
  }
`

export const CREATE_SENSOR = gql`
  mutation CreateSensor($input: SensorCreateInput!) {
    createSensor(input: $input) {
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

export const UPDATE_SENSOR = gql`
  mutation UpdateSensor($id: String!, $input: SensorUpdateInput!) {
    updateSensor(id: $id, input: $input) {
      id
      sensorId
      nombre
      estado
    }
  }
`

export const DELETE_SENSOR = gql`
  mutation DeleteSensor($id: String!) {
    deleteSensor(id: $id)
  }
`

export const REGISTER_MEASUREMENT = gql`
  mutation RegisterMeasurement($sensorId: String!, $input: MeasurementCreateInput!) {
    registerMeasurement(sensorId: $sensorId, input: $input) {
      sensorId
      timestamp
      temperature
      humidity
    }
  }
`

export const CREATE_ALERT = gql`
  mutation CreateAlert($input: AlertCreateInput!) {
    createAlert(input: $input) {
      id
      tipo
      sensorId
      fechaHora
      descripcion
      estado
      valor
      umbral
    }
  }
`

export const RESOLVE_ALERT = gql`
  mutation ResolveAlert($id: String!) {
    resolveAlert(id: $id) {
      id
      estado
    }
  }
`

export const ACKNOWLEDGE_ALERT = gql`
  mutation AcknowledgeAlert($id: String!) {
    acknowledgeAlert(id: $id) {
      id
      estado
    }
  }
`

export const CREATE_ALERT_RULE = gql`
  mutation CreateAlertRule($input: AlertRuleCreateInput!) {
    createAlertRule(input: $input) {
      id
      nombre
      descripcion
      estado
    }
  }
`

export const UPDATE_ALERT_RULE = gql`
  mutation UpdateAlertRule($id: String!, $input: AlertRuleUpdateInput!) {
    updateAlertRule(id: $id, input: $input) {
      id
      nombre
      descripcion
      estado
    }
  }
`

export const ACTIVATE_ALERT_RULE = gql`
  mutation ActivateAlertRule($id: String!) {
    activateAlertRule(id: $id) {
      id
      estado
    }
  }
`

export const DEACTIVATE_ALERT_RULE = gql`
  mutation DeactivateAlertRule($id: String!) {
    deactivateAlertRule(id: $id) {
      id
      estado
    }
  }
`

export const DELETE_ALERT_RULE = gql`
  mutation DeleteAlertRule($id: String!) {
    deleteAlertRule(id: $id)
  }
`

export const REQUEST_PROCESS = gql`
  mutation RequestProcess($input: ProcessRequestCreateInput!) {
    requestProcess(input: $input) {
      id
      userId
      processId
      fechaSolicitud
      estado
      invoiceId
      invoiceCreated
    }
  }
`

export const EXECUTE_PROCESS = gql`
  mutation ExecuteProcess($requestId: String!) {
    executeProcess(requestId: $requestId) {
      id
      requestId
      estado
      resultado
    }
  }
`

export const PAY_INVOICE = gql`
  mutation PayInvoice($invoiceId: String!, $input: PaymentCreateInput!) {
    payInvoice(invoiceId: $invoiceId, input: $input) {
      id
      invoiceId
      fechaPago
      monto
      metodo
    }
  }
`

export const SEND_MESSAGE = gql`
  mutation SendMessage($input: MessageCreateInput!) {
    sendMessage(input: $input) {
      id
      senderId
      recipientType
      recipientId
      timestamp
      content
    }
  }
`

export const CREATE_GROUP = gql`
  mutation CreateGroup($input: GroupCreateInput!) {
    createGroup(input: $input) {
      id
      nombre
      miembros
      fechaCreacion
    }
  }
`

export const ADD_GROUP_MEMBER = gql`
  mutation AddGroupMember($groupId: String!, $userId: String!) {
    addGroupMember(groupId: $groupId, userId: $userId) {
      id
      miembros
    }
  }
`

export const REMOVE_GROUP_MEMBER = gql`
  mutation RemoveGroupMember($groupId: String!, $userId: String!) {
    removeGroupMember(groupId: $groupId, userId: $userId) {
      id
      miembros
    }
  }
`

export const DELETE_GROUP = gql`
  mutation DeleteGroup($id: String!) {
    deleteGroup(id: $id)
  }
`
