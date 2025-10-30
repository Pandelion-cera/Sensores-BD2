'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/utils'

export default function AlertsPage() {
  const router = useRouter()
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    try {
      const data = await api.getAlerts()
      setAlerts(data)
    } catch (error) {
      console.error('Error loading alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAcknowledge = async (alertId: string) => {
    try {
      await api.acknowledgeAlert(alertId)
      loadAlerts()
    } catch (error) {
      console.error('Error acknowledging alert:', error)
    }
  }

  const getTypeColor = (tipo: string) => {
    switch (tipo) {
      case 'sensor':
        return 'bg-red-100 text-red-800'
      case 'climatica':
        return 'bg-orange-100 text-orange-800'
      case 'umbral':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (estado: string) => {
    switch (estado) {
      case 'activa':
        return 'bg-red-500'
      case 'reconocida':
        return 'bg-yellow-500'
      case 'resuelta':
        return 'bg-green-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Sistema de Gestión de Sensores
          </h1>
          <Button onClick={() => router.push('/dashboard')} variant="outline">
            Volver al Dashboard
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Alertas del Sistema</h2>
            <p className="mt-1 text-sm text-gray-600">
              Monitoreo de alertas climáticas y de funcionamiento de sensores
            </p>
          </div>
          <Button onClick={loadAlerts} variant="outline">
            Actualizar
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Cargando alertas...</p>
          </div>
        ) : alerts.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No hay alertas registradas</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <Card key={alert.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(alert.estado)}`} />
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getTypeColor(alert.tipo)}`}>
                          {alert.tipo}
                        </span>
                        {alert.sensor_id && (
                          <span className="text-xs text-gray-500">
                            Sensor: {alert.sensor_id.slice(0, 8)}...
                          </span>
                        )}
                      </div>
                      
                      <p className="text-lg font-medium mb-2">{alert.descripcion}</p>
                      
                      <div className="flex gap-4 text-sm text-gray-600">
                        <div>{formatDate(alert.fecha_hora)}</div>
                        {alert.valor !== null && (
                          <div>Valor: {alert.valor}°C</div>
                        )}
                        {alert.umbral !== null && (
                          <div>Umbral: {alert.umbral}°C</div>
                        )}
                      </div>
                    </div>
                    
                    {alert.estado === 'activa' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleAcknowledge(alert.id)}
                      >
                        Reconocer
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

