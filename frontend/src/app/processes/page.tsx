'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function ProcessesPage() {
  const router = useRouter()
  const [processes, setProcesses] = useState<any[]>([])
  const [requests, setRequests] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const userData = JSON.parse(userStr)
        setUser(userData)

        // Load available processes
        const processesData = await api.getProcesses()
        setProcesses(processesData)

        // Load user's requests
        const requestsData = await api.getUserProcessRequests(userData.id)
        setRequests(requestsData)
      }
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completado':
        return 'bg-green-100 text-green-800'
      case 'pendiente':
        return 'bg-yellow-100 text-yellow-800'
      case 'en_progreso':
        return 'bg-blue-100 text-blue-800'
      case 'fallido':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
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
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Procesos y Reportes</h2>
          <p className="mt-1 text-sm text-gray-600">
            Ejecuta reportes y consultas sobre los datos de sensores
          </p>
        </div>

        {/* Available Processes */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Procesos Disponibles</CardTitle>
            <CardDescription>Selecciona un proceso para solicitar su ejecución</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-gray-500">Cargando procesos...</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {processes.map((process) => (
                  <div key={process.id} className="border rounded-lg p-4 hover:shadow-md transition">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">{process.nombre}</h3>
                      <span className="text-lg font-bold text-green-600">
                        {formatCurrency(process.costo)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{process.descripcion}</p>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-500">Tipo: {process.tipo}</span>
                      <Button size="sm" onClick={() => alert('Funcionalidad de solicitud en desarrollo')}>
                        Solicitar
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* User's Process Requests */}
        <Card>
          <CardHeader>
            <CardTitle>Mis Solicitudes</CardTitle>
            <CardDescription>Historial de procesos solicitados</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-gray-500">Cargando solicitudes...</p>
            ) : requests.length === 0 ? (
              <p className="text-gray-500">No has solicitado ningún proceso aún</p>
            ) : (
              <div className="space-y-3">
                {requests.map((request) => (
                  <div key={request.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">Proceso ID: {request.process_id}</div>
                      <div className="text-sm text-gray-500">
                        Solicitado: {formatDate(request.fecha_solicitud)}
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(request.estado)}`}>
                      {request.estado}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

