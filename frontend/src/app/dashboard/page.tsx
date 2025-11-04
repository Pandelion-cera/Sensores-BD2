'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        setUser(JSON.parse(userStr))
      }

      // Load stats
      const statsData = await api.getSensorStats()
      setStats(statsData)

      // Load active alerts
      const alertsData = await api.getActiveAlerts()
      setAlerts(alertsData.slice(0, 5)) // Show only 5 most recent

    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    const sessionId = localStorage.getItem('session_id')
    if (sessionId) {
      try {
        await api.logout(sessionId)
      } catch (error) {
        console.error('Error logging out:', error)
      }
    }
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('session_id')
    router.push('/login')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Cargando...</h2>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Sistema de Gestión de Sensores
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.nombre_completo} ({user?.role})
            </span>
            <Button onClick={handleLogout} variant="outline" size="sm">
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => router.push('/dashboard')}
              className="border-b-2 border-blue-500 py-4 px-1 text-sm font-medium text-blue-600"
            >
              Dashboard
            </button>
            <button
              onClick={() => router.push('/sensors')}
              className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
            >
              Sensores
            </button>
            <button
              onClick={() => router.push('/measurements')}
              className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
            >
              Mediciones
            </button>
            <button
              onClick={() => router.push('/processes')}
              className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
            >
              Procesos
            </button>
            <button
              onClick={() => router.push('/invoices')}
              className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
            >
              Facturas
            </button>
            <button
              onClick={() => router.push('/alerts')}
              className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
            >
              Alertas
            </button>
            <button
              onClick={() => router.push('/messages')}
              className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
            >
              Mensajes
            </button>
            {user?.role === 'administrador' && (
              <button
                onClick={() => router.push('/admin/groups')}
                className="border-b-2 border-transparent py-4 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                Admin Grupos
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
          <p className="mt-1 text-sm text-gray-600">
            Vista general del sistema de sensores climáticos
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Total Sensores</CardTitle>
              <CardDescription>Sensores registrados</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats?.total_sensors || 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Sensores Activos</CardTitle>
              <CardDescription>En funcionamiento</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {stats?.sensor_status?.activo || 0}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Con Fallas</CardTitle>
              <CardDescription>Requieren atención</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">
                {stats?.sensor_status?.falla || 0}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Países</CardTitle>
              <CardDescription>Cobertura global</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats?.total_countries || 0}</div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts Section */}
        <Card>
          <CardHeader>
            <CardTitle>Alertas Activas</CardTitle>
            <CardDescription>
              Alertas más recientes que requieren atención
            </CardDescription>
          </CardHeader>
          <CardContent>
            {alerts.length === 0 ? (
              <p className="text-gray-500">No hay alertas activas</p>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{alert.descripcion}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(alert.fecha_hora).toLocaleString('es-ES')}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      alert.tipo === 'sensor' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {alert.tipo}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/sensors')}>
            <CardHeader>
              <CardTitle>Ver Sensores</CardTitle>
              <CardDescription>Administrar y monitorear sensores</CardDescription>
            </CardHeader>
          </Card>

          <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/measurements')}>
            <CardHeader>
              <CardTitle>Ver Mediciones</CardTitle>
              <CardDescription>Analizar datos por ubicación</CardDescription>
            </CardHeader>
          </Card>

          <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/processes')}>
            <CardHeader>
              <CardTitle>Solicitar Proceso</CardTitle>
              <CardDescription>Ejecutar reportes y consultas</CardDescription>
            </CardHeader>
          </Card>

          <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/invoices')}>
            <CardHeader>
              <CardTitle>Ver Facturas</CardTitle>
              <CardDescription>Gestionar pagos y cuenta corriente</CardDescription>
            </CardHeader>
          </Card>

          <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/messages')}>
            <CardHeader>
              <CardTitle>Mensajes</CardTitle>
              <CardDescription>Ver y enviar mensajes</CardDescription>
            </CardHeader>
          </Card>

          {user?.role === 'administrador' && (
            <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => router.push('/admin/groups')}>
              <CardHeader>
                <CardTitle>Administrar Grupos</CardTitle>
                <CardDescription>Gestionar grupos y miembros</CardDescription>
              </CardHeader>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}

