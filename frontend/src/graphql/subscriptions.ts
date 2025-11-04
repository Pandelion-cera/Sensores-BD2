import { gql } from '@apollo/client'

export const ALERTS_LIVE_SUBSCRIPTION = gql`
  subscription AlertsLive($estado: AlertStatus) {
    alertsLive(estado: $estado) {
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
