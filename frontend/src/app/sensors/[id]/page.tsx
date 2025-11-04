'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface Sensor {
  id: string
  sensor_id: string
  nombre: string
  tipo: string
  latitud: number
  longitud: number
  ciudad: string
  pais: string
  estado: string
  fecha_inicio_emision: string
}

interface Measurement {
  timestamp: string
  temperatura: number
  humedad: number
}

export default function SensorDetailPage() {
  const router = useRouter()
  const params = useParams()
  const sensorId = params.id as string

  const [sensor, setSensor] = useState<Sensor | null>(null)
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h')

  useEffect(() => {
    if (sensorId) {
      loadSensorData()
    }
  }, [sensorId, timeRange])

  const loadSensorData = async () => {
    try {
      setLoading(true)
      
      // Load sensor info
      const sensorData = await api.getSensor(sensorId)
      setSensor(sensorData)

      // Calculate date range
      const endDate = new Date()
      const startDate = new Date()
      
      switch (timeRange) {
        case '24h':
          startDate.setHours(startDate.getHours() - 24)
          break
        case '7d':
          startDate.setDate(startDate.getDate() - 7)
          break
        case '30d':
          startDate.setDate(startDate.getDate() - 30)
          break
      }

      // Load measurements
      const measurementsData = await api.getSensorMeasurements(
        sensorData.sensor_id,
        {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      )
      
      setMeasurements(measurementsData)
    } catch (error) {
      console.error('Error loading sensor data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'activo':
        return 'bg-green-100 text-green-800'
      case 'inactivo':
        return 'bg-gray-100 text-gray-800'
      case 'falla':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatChartData = () => {
    return measurements.map((m) => ({
      time: new Date(m.timestamp).toLocaleString('es-ES', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }),
      temperatura: m.temperatura?.toFixed(1) || 0,
      humedad: m.humedad?.toFixed(1) || 0,
    }))
  }

  const getStats = () => {
    if (measurements.length === 0) {
      return {
        tempMin: 0,
        tempMax: 0,
        tempAvg: 0,
        humMin: 0,
        humMax: 0,
        humAvg: 0
      }
    }

    const temps = measurements.map(m => m.temperatura).filter(t => t !== null && t !== undefined)
    const hums = measurements.map(m => m.humedad).filter(h => h !== null && h !== undefined)

    return {
      tempMin: Math.min(...temps),
      tempMax: Math.max(...temps),
      tempAvg: temps.reduce((a, b) => a + b, 0) / temps.length,
      humMin: Math.min(...hums),
      humMax: Math.max(...hums),
      humAvg: hums.reduce((a, b) => a + b, 0) / hums.length
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Cargando datos del sensor...</p>
      </div>
    )
  }

  if (!sensor) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">Sensor no encontrado</p>
          <Button onClick={() => router.push('/sensors')}>Volver a Sensores</Button>
        </div>
      </div>
    )
  }

  const stats = getStats()
  const chartData = formatChartData()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Detalle del Sensor</h1>
          <Button onClick={() => router.push('/sensors')} variant="outline">
            Volver a Sensores
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Información del Sensor */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-2xl">{sensor.nombre}</CardTitle>
                <p className="text-sm text-gray-500 mt-1">ID: {sensor.sensor_id}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(sensor.estado)}`}>
                {sensor.estado}
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500">Ubicación</p>
                <p className="font-medium">{sensor.ciudad}, {sensor.pais}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Coordenadas</p>
                <p className="font-medium">{sensor.latitud.toFixed(4)}, {sensor.longitud.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Tipo</p>
                <p className="font-medium capitalize">{sensor.tipo.replace('_', ' ')}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Activo desde</p>
                <p className="font-medium">
                  {new Date(sensor.fecha_inicio_emision).toLocaleDateString('es-ES', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Estadísticas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Temperatura</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Mínima</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.tempMin.toFixed(1)}°C</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Promedio</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.tempAvg.toFixed(1)}°C</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Máxima</p>
                  <p className="text-2xl font-bold text-red-600">{stats.tempMax.toFixed(1)}°C</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Humedad</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Mínima</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.humMin.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Promedio</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.humAvg.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Máxima</p>
                  <p className="text-2xl font-bold text-green-600">{stats.humMax.toFixed(1)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Selector de Rango */}
        <div className="mb-4 flex gap-2">
          <Button
            variant={timeRange === '24h' ? 'default' : 'outline'}
            onClick={() => setTimeRange('24h')}
          >
            Últimas 24h
          </Button>
          <Button
            variant={timeRange === '7d' ? 'default' : 'outline'}
            onClick={() => setTimeRange('7d')}
          >
            Últimos 7 días
          </Button>
          <Button
            variant={timeRange === '30d' ? 'default' : 'outline'}
            onClick={() => setTimeRange('30d')}
          >
            Últimos 30 días
          </Button>
        </div>

        {/* Gráfico de Temperatura */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Temperatura en el Tiempo</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="time" 
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis label={{ value: '°C', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="temperatura" 
                    stroke="#ef4444" 
                    strokeWidth={2}
                    name="Temperatura (°C)"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-gray-500 py-8">No hay datos disponibles</p>
            )}
          </CardContent>
        </Card>

        {/* Gráfico de Humedad */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Humedad en el Tiempo</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="time" 
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis label={{ value: '%', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="humedad" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    name="Humedad (%)"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-gray-500 py-8">No hay datos disponibles</p>
            )}
          </CardContent>
        </Card>

        {/* Últimas Mediciones */}
        <Card>
          <CardHeader>
            <CardTitle>Últimas Mediciones</CardTitle>
          </CardHeader>
          <CardContent>
            {measurements.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4">Fecha y Hora</th>
                      <th className="text-right py-2 px-4">Temperatura</th>
                      <th className="text-right py-2 px-4">Humedad</th>
                    </tr>
                  </thead>
                  <tbody>
                    {measurements.slice(0, 20).map((m, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="py-2 px-4">
                          {new Date(m.timestamp).toLocaleString('es-ES')}
                        </td>
                        <td className="text-right py-2 px-4 font-medium">
                          {m.temperatura?.toFixed(1) || 'N/A'}°C
                        </td>
                        <td className="text-right py-2 px-4 font-medium">
                          {m.humedad?.toFixed(1) || 'N/A'}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center text-gray-500 py-8">No hay mediciones registradas</p>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}







