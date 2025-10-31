'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog } from '@/components/ui/dialog'
import { Select, SelectOption } from '@/components/ui/select'
import { api } from '@/lib/api'

export default function SensorsPage() {
  const router = useRouter()
  const [sensors, setSensors] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ pais: '', ciudad: '', estado: '' })
  const [user, setUser] = useState<any>(null)
  
  // Modal states
  const [sensorModalOpen, setSensorModalOpen] = useState(false)
  const [editingSensor, setEditingSensor] = useState<any>(null)
  const [formData, setFormData] = useState({
    nombre: '',
    tipo: 'temperatura_humedad',
    latitud: '',
    longitud: '',
    ciudad: '',
    pais: '',
    estado: 'activo'
  })
  const [submitting, setSubmitting] = useState(false)

  const tipoOptions: SelectOption[] = [
    { value: 'temperatura', label: 'Temperatura' },
    { value: 'humedad', label: 'Humedad' },
    { value: 'temperatura_humedad', label: 'Temperatura y Humedad' }
  ]

  const estadoOptions: SelectOption[] = [
    { value: 'activo', label: 'Activo' },
    { value: 'inactivo', label: 'Inactivo' },
    { value: 'falla', label: 'Falla' }
  ]

  useEffect(() => {
    loadSensors()
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
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

  const handleCreateClick = () => {
    setEditingSensor(null)
    setFormData({
      nombre: '',
      tipo: 'temperatura_humedad',
      latitud: '',
      longitud: '',
      ciudad: '',
      pais: '',
      estado: 'activo'
    })
    setSensorModalOpen(true)
  }

  const handleEditClick = (sensor: any) => {
    setEditingSensor(sensor)
    setFormData({
      nombre: sensor.nombre,
      tipo: sensor.tipo,
      latitud: sensor.latitud.toString(),
      longitud: sensor.longitud.toString(),
      ciudad: sensor.ciudad,
      pais: sensor.pais,
      estado: sensor.estado
    })
    setSensorModalOpen(true)
  }

  const handleDeleteClick = async (sensor: any) => {
    if (!confirm(`¿Estás seguro de eliminar el sensor "${sensor.nombre}"?`)) {
      return
    }

    try {
      await api.deleteSensor(sensor.id)
      alert('Sensor eliminado exitosamente')
      loadSensors()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al eliminar sensor')
    }
  }

  const handleSubmit = async () => {
    // Validate
    if (!formData.nombre || formData.nombre.length < 3) {
      alert('El nombre debe tener al menos 3 caracteres')
      return
    }

    const lat = parseFloat(formData.latitud)
    const lng = parseFloat(formData.longitud)
    
    if (isNaN(lat) || lat < -90 || lat > 90) {
      alert('La latitud debe estar entre -90 y 90')
      return
    }
    
    if (isNaN(lng) || lng < -180 || lng > 180) {
      alert('La longitud debe estar entre -180 y 180')
      return
    }

    if (!formData.ciudad || formData.ciudad.length < 2) {
      alert('La ciudad debe tener al menos 2 caracteres')
      return
    }

    if (!formData.pais || formData.pais.length < 2) {
      alert('El país debe tener al menos 2 caracteres')
      return
    }

    try {
      setSubmitting(true)
      const sensorData = {
        ...formData,
        latitud: lat,
        longitud: lng
      }

      if (editingSensor) {
        await api.updateSensor(editingSensor.id, sensorData)
        alert('Sensor actualizado exitosamente')
      } else {
        await api.createSensor(sensorData)
        alert('Sensor creado exitosamente')
      }
      
      setSensorModalOpen(false)
      loadSensors()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar sensor')
    } finally {
      setSubmitting(false)
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

  const isAdminOrTecnico = user?.role === 'administrador' || user?.role === 'tecnico'
  const isAdmin = user?.role === 'administrador'

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
            <h2 className="text-3xl font-bold text-gray-900">Sensores</h2>
            <p className="mt-1 text-sm text-gray-600">
              Gestión y monitoreo de sensores climáticos
            </p>
          </div>
          {isAdminOrTecnico && (
            <Button onClick={handleCreateClick}>
              Crear Sensor
            </Button>
          )}
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
                  <div className="flex gap-2 mt-4">
                    <Button 
                      className="flex-1"
                      variant="outline"
                      onClick={() => router.push(`/sensors/${sensor.id}`)}
                    >
                      Ver
                    </Button>
                    {isAdminOrTecnico && (
                      <>
                        <Button 
                          size="sm"
                          variant="outline"
                          onClick={() => handleEditClick(sensor)}
                        >
                          Editar
                        </Button>
                        {isAdmin && (
                          <Button 
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDeleteClick(sensor)}
                          >
                            Eliminar
                          </Button>
                        )}
                      </>
                    )}
                  </div>
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

      {/* Sensor Modal */}
      <Dialog 
        open={sensorModalOpen} 
        onOpenChange={setSensorModalOpen}
        title={editingSensor ? 'Editar Sensor' : 'Crear Sensor'}
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="nombre">Nombre</Label>
            <Input
              id="nombre"
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              placeholder="Ej: Sensor Buenos Aires Centro"
            />
          </div>

          <div>
            <Label htmlFor="tipo">Tipo</Label>
            <Select
              id="tipo"
              options={tipoOptions}
              value={formData.tipo}
              onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="latitud">Latitud</Label>
              <Input
                id="latitud"
                type="number"
                step="0.0001"
                value={formData.latitud}
                onChange={(e) => setFormData({ ...formData, latitud: e.target.value })}
                placeholder="-90 a 90"
              />
            </div>
            <div>
              <Label htmlFor="longitud">Longitud</Label>
              <Input
                id="longitud"
                type="number"
                step="0.0001"
                value={formData.longitud}
                onChange={(e) => setFormData({ ...formData, longitud: e.target.value })}
                placeholder="-180 a 180"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="ciudad">Ciudad</Label>
            <Input
              id="ciudad"
              value={formData.ciudad}
              onChange={(e) => setFormData({ ...formData, ciudad: e.target.value })}
              placeholder="Ej: Buenos Aires"
            />
          </div>

          <div>
            <Label htmlFor="pais">País</Label>
            <Input
              id="pais"
              value={formData.pais}
              onChange={(e) => setFormData({ ...formData, pais: e.target.value })}
              placeholder="Ej: Argentina"
            />
          </div>

          {editingSensor && (
            <div>
              <Label htmlFor="estado">Estado</Label>
              <Select
                id="estado"
                options={estadoOptions}
                value={formData.estado}
                onChange={(e) => setFormData({ ...formData, estado: e.target.value })}
              />
            </div>
          )}

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setSensorModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting ? 'Guardando...' : editingSensor ? 'Actualizar' : 'Crear'}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
