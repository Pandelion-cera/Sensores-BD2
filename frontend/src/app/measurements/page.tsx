'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface LocationStats {
  temperatura_max: number
  temperatura_min: number
  temperatura_avg: number
  humedad_max: number
  humedad_min: number
  humedad_avg: number
  total_mediciones: number
}

interface Measurement {
  timestamp: string
  temperatura: number
  humedad: number
  sensor_id: string
}

export default function MeasurementsPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [pais, setPais] = useState('')
  const [ciudad, setCiudad] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [stats, setStats] = useState<LocationStats | null>(null)
  const [hasSearched, setHasSearched] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const measurementsPerPage = 50

  // Set default dates (last 7 days)
  useEffect(() => {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 7)
    
    setEndDate(end.toISOString().split('T')[0])
    setStartDate(start.toISOString().split('T')[0])
  }, [])

  const handleSearch = async () => {
    if (!pais || !ciudad) {
      alert('Por favor ingresa país y ciudad')
      return
    }

    try {
      setLoading(true)
      setHasSearched(true)
      setCurrentPage(1) // Reset to first page

      // Build params
      const params: any = {}
      if (startDate) params.start_date = new Date(startDate).toISOString()
      if (endDate) params.end_date = new Date(endDate).toISOString()

      // Load measurements
      const measurementsData = await api.getLocationMeasurements(pais, ciudad, params)
      setMeasurements(measurementsData)

      // Load stats
      const statsData = await api.getLocationStats(pais, ciudad, params)
      setStats(statsData)

    } catch (error: any) {
      console.error('Error loading measurements:', error)
      alert(error.response?.data?.detail || 'Error al cargar mediciones')
      setMeasurements([])
      setStats(null)
    } finally {
      setLoading(false)
    }
  }

  const formatChartData = () => {
    // Group by hour for better visualization
    const grouped = measurements.reduce((acc: any, m) => {
      const date = new Date(m.timestamp)
      const key = date.toISOString().substring(0, 13) // Group by hour
      
      if (!acc[key]) {
        acc[key] = {
          time: date.toLocaleString('es-ES', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit'
          }),
          temps: [],
          hums: []
        }
      }
      
      if (m.temperatura !== null && m.temperatura !== undefined) {
        acc[key].temps.push(m.temperatura)
      }
      if (m.humedad !== null && m.humedad !== undefined) {
        acc[key].hums.push(m.humedad)
      }
      
      return acc
    }, {})

    // Calculate averages
    return Object.values(grouped).map((g: any) => ({
      time: g.time,
      temperatura: g.temps.length > 0 
        ? Number((g.temps.reduce((a: number, b: number) => a + b, 0) / g.temps.length).toFixed(1))
        : null,
      humedad: g.hums.length > 0 
        ? Number((g.hums.reduce((a: number, b: number) => a + b, 0) / g.hums.length).toFixed(1))
        : null
    }))
  }

  const chartData = formatChartData()

  // Pagination logic
  const totalPages = Math.ceil(measurements.length / measurementsPerPage)
  const startIndex = (currentPage - 1) * measurementsPerPage
  const endIndex = startIndex + measurementsPerPage
  const currentMeasurements = measurements.slice(startIndex, endIndex)

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1)
    }
  }

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Mediciones por Ubicación
          </h1>
          <Button onClick={() => router.push('/dashboard')} variant="outline">
            Volver al Dashboard
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filtros */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Filtros de Búsqueda</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="pais">País</Label>
                <Input
                  id="pais"
                  placeholder="Ej: Argentina"
                  value={pais}
                  onChange={(e) => setPais(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="ciudad">Ciudad</Label>
                <Input
                  id="ciudad"
                  placeholder="Ej: Buenos Aires"
                  value={ciudad}
                  onChange={(e) => setCiudad(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="start">Fecha Inicio</Label>
                <Input
                  id="start"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="end">Fecha Fin</Label>
                <Input
                  id="end"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>
            <div className="mt-4">
              <Button onClick={handleSearch} disabled={loading}>
                {loading ? 'Buscando...' : 'Buscar Mediciones'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Estadísticas */}
        {hasSearched && stats && (
          <>
            <div className="mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                {ciudad}, {pais}
              </h2>
              <p className="text-sm text-gray-500">
                {stats.total_mediciones || 0} mediciones registradas
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Temperatura Stats */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Estadísticas de Temperatura</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Mínima</span>
                      <span className="text-2xl font-bold text-blue-600">
                        {stats.temperatura_min != null ? stats.temperatura_min.toFixed(1) : 'N/A'}°C
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Promedio</span>
                      <span className="text-2xl font-bold text-gray-900">
                        {stats.temperatura_avg != null ? stats.temperatura_avg.toFixed(1) : 'N/A'}°C
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Máxima</span>
                      <span className="text-2xl font-bold text-red-600">
                        {stats.temperatura_max != null ? stats.temperatura_max.toFixed(1) : 'N/A'}°C
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Humedad Stats */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Estadísticas de Humedad</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Mínima</span>
                      <span className="text-2xl font-bold text-blue-600">
                        {stats.humedad_min != null ? stats.humedad_min.toFixed(1) : 'N/A'}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Promedio</span>
                      <span className="text-2xl font-bold text-gray-900">
                        {stats.humedad_avg != null ? stats.humedad_avg.toFixed(1) : 'N/A'}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-500">Máxima</span>
                      <span className="text-2xl font-bold text-green-600">
                        {stats.humedad_max != null ? stats.humedad_max.toFixed(1) : 'N/A'}%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Gráfico de Temperatura */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Temperatura en el Tiempo</CardTitle>
              </CardHeader>
              <CardContent>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={350}>
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
                  <ResponsiveContainer width="100%" height={350}>
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

            {/* Tabla de Mediciones */}
            <Card>
              <CardHeader>
                <CardTitle>Mediciones Individuales</CardTitle>
                <p className="text-sm text-gray-500 mt-2">
                  Mostrando {startIndex + 1}-{Math.min(endIndex, measurements.length)} de {measurements.length} mediciones
                </p>
              </CardHeader>
              <CardContent>
                {currentMeasurements.length > 0 ? (
                  <>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left py-2 px-4">Fecha y Hora</th>
                            <th className="text-left py-2 px-4">Sensor ID</th>
                            <th className="text-right py-2 px-4">Temperatura</th>
                            <th className="text-right py-2 px-4">Humedad</th>
                          </tr>
                        </thead>
                        <tbody>
                          {currentMeasurements.map((m, idx) => (
                            <tr key={idx} className="border-b hover:bg-gray-50">
                              <td className="py-2 px-4">
                                {new Date(m.timestamp).toLocaleString('es-ES')}
                              </td>
                              <td className="py-2 px-4 text-xs font-mono">
                                {m.sensor_id}
                              </td>
                              <td className="text-right py-2 px-4 font-medium">
                                {m.temperatura != null ? `${m.temperatura.toFixed(1)}°C` : 'N/A'}
                              </td>
                              <td className="text-right py-2 px-4 font-medium">
                                {m.humedad != null ? `${m.humedad.toFixed(1)}%` : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex justify-between items-center mt-4">
                        <Button 
                          variant="outline" 
                          onClick={handlePrevPage}
                          disabled={currentPage === 1}
                        >
                          Anterior
                        </Button>
                        <span className="text-sm text-gray-600">
                          Página {currentPage} de {totalPages}
                        </span>
                        <Button 
                          variant="outline" 
                          onClick={handleNextPage}
                          disabled={currentPage === totalPages}
                        >
                          Siguiente
                        </Button>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-center text-gray-500 py-8">
                    No hay mediciones para mostrar
                  </p>
                )}
              </CardContent>
            </Card>
          </>
        )}

        {/* No results message */}
        {hasSearched && !loading && measurements.length === 0 && (
          <Card>
            <CardContent className="py-12">
              <p className="text-center text-gray-500">
                No se encontraron mediciones para la ubicación y período seleccionados.
              </p>
              <p className="text-center text-sm text-gray-400 mt-2">
                Intenta con otra ciudad o ajusta el rango de fechas.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Initial message */}
        {!hasSearched && (
          <Card>
            <CardContent className="py-12">
              <p className="text-center text-gray-500">
                Selecciona un país y ciudad para ver las mediciones
              </p>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}

