'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

export default function SensorsPage() {
  const router = useRouter()
  const [sensors, setSensors] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ pais: '', ciudad: '', estado: '' })

  useEffect(() => {
    loadSensors()
  }, [])

  const loadSensors = async () => {
    try {
      const data = await api.getSensors(filters)
      setSensors(data)
    } catch (error) {
      console.error('Error loading sensors:', error)
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
          <h2 className="text-3xl font-bold text-gray-900">Sensores</h2>
          <p className="mt-1 text-sm text-gray-600">
            Gestión y monitoreo de sensores climáticos
          </p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Cargando sensores...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sensors.map((sensor) => (
              <Card key={sensor.id} className="hover:shadow-lg transition">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-lg">{sensor.nombre}</CardTitle>
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(sensor.estado)}`}>
                      {sensor.estado}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium">Ubicación:</span>{' '}
                      {sensor.ciudad}, {sensor.pais}
                    </div>
                    <div>
                      <span className="font-medium">Tipo:</span> {sensor.tipo}
                    </div>
                    <div>
                      <span className="font-medium">Coordenadas:</span>{' '}
                      {sensor.latitud.toFixed(4)}, {sensor.longitud.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-500 mt-3">
                      Activo desde: {new Date(sensor.fecha_inicio_emision).toLocaleDateString('es-ES')}
                    </div>
                  </div>
                  <Button 
                    className="w-full mt-4"
                    variant="outline"
                    onClick={() => router.push(`/sensors/${sensor.id}`)}
                  >
                    Ver Detalles
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!loading && sensors.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No se encontraron sensores</p>
          </div>
        )}
      </main>
    </div>
  )
}

