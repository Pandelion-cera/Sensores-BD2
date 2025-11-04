'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function ProcessesPage() {
  const router = useRouter()
  const [processes, setProcesses] = useState<any[]>([])
  const [requests, setRequests] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)
  
  // Modal states
  const [requestModalOpen, setRequestModalOpen] = useState(false)
  const [resultModalOpen, setResultModalOpen] = useState(false)
  const [selectedProcess, setSelectedProcess] = useState<any>(null)
  const [selectedProcessId, setSelectedProcessId] = useState<string | null>(null)
  const [selectedRequest, setSelectedRequest] = useState<any>(null)
  const [execution, setExecution] = useState<any>(null)
  const [formParams, setFormParams] = useState<{ [key: string]: string }>({})
  const [submitting, setSubmitting] = useState(false)

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

  const handleRequestClick = (process: any) => {
    setSelectedProcess(process)
    setSelectedProcessId(process.id || process._id)
    setFormParams({})
    setRequestModalOpen(true)
  }

  const handleSubmitRequest = async () => {
    if (!selectedProcessId) {
      alert('Error: No se seleccionó un proceso')
      return
    }
    
    try {
      setSubmitting(true)
      const requestData = {
        process_id: selectedProcessId,
        parametros: formParams
      }
      await api.requestProcess(requestData)
      alert('Solicitud enviada exitosamente')
      setRequestModalOpen(false)
      loadData()
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || error?.response?.data || 'Error al enviar solicitud'
      alert(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage))
    } finally {
      setSubmitting(false)
    }
  }

  const handleViewResult = async (request: any) => {
    try {
      setSelectedRequest(request)
      const requestId = request.id || request._id
      const executionData = await api.getExecution(requestId)
      setExecution(executionData)
      setResultModalOpen(true)
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || 'Error al cargar resultado'
      alert(errorMessage)
    }
  }

  const handleExecute = async (request: any) => {
    try {
      setSubmitting(true)
      const requestId = request.id || request._id
      const executionData = await api.executeProcess(requestId)
      setExecution(executionData)
      setSelectedRequest(request)
      setResultModalOpen(true)
      loadData()
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || 'Error al ejecutar proceso'
      alert(errorMessage)
    } finally {
      setSubmitting(false)
    }
  }

  const renderFormField = (key: string, schema: any) => {
    const type = schema || 'string'
    const value = formParams[key] || ''

    if (type === 'date' || type === 'datetime') {
      return (
        <div className="mb-4">
          <Label htmlFor={key}>
            {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </Label>
          <Input
            id={key}
            type="datetime-local"
            value={value}
            onChange={(e) => setFormParams({ ...formParams, [key]: e.target.value })}
            required
          />
        </div>
      )
    }

    if (type === 'float' || type === 'number') {
      return (
        <div className="mb-4">
          <Label htmlFor={key}>
            {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </Label>
          <Input
            id={key}
            type="number"
            step="0.01"
            value={value}
            onChange={(e) => setFormParams({ ...formParams, [key]: e.target.value })}
            required
          />
        </div>
      )
    }

    // Default: string
    return (
      <div className="mb-4">
        <Label htmlFor={key}>
          {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </Label>
        <Input
          id={key}
          type="text"
          value={value}
          onChange={(e) => setFormParams({ ...formParams, [key]: e.target.value })}
          required
        />
      </div>
    )
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

  const isAdminOrTecnico = user?.role === 'administrador' || user?.role === 'tecnico'

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
                      <Button size="sm" onClick={() => handleRequestClick(process)}>
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
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(request.estado)}`}>
                        {request.estado}
                      </span>
                      {request.estado === 'completado' && (
                        <Button size="sm" onClick={() => handleViewResult(request)}>
                          Ver Resultado
                        </Button>
                      )}
                      {request.estado === 'pendiente' && isAdminOrTecnico && (
                        <Button size="sm" onClick={() => handleExecute(request)} disabled={submitting}>
                          Ejecutar
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>

            {/* Request Modal */}
      <Dialog
        open={requestModalOpen}
        onOpenChange={setRequestModalOpen}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedProcess?.nombre}</DialogTitle>
          </DialogHeader>
          <div>
            <p className="text-sm text-gray-600 mb-4">{selectedProcess?.descripcion}</p>
            <p className="text-sm font-medium mb-4">
              Costo: {selectedProcess && formatCurrency(selectedProcess.costo)} 
            </p>

            {selectedProcess?.parametros_schema && (
              <div className="space-y-2">
                {Object.entries(selectedProcess.parametros_schema).map(([key, schema]: [string, any]) => (
                  <div key={key}>
                    {renderFormField(key, schema)}
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end gap-3 mt-6">
              <Button variant="outline" onClick={() => setRequestModalOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleSubmitRequest} disabled={submitting}>        
                {submitting ? 'Enviando...' : 'Solicitar'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Result Modal */}
      <Dialog 
        open={resultModalOpen} 
        onOpenChange={setResultModalOpen}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resultado de Ejecución</DialogTitle>
          </DialogHeader>
          <div>
            {execution && (
              <>
                <div className="mb-4">
                  <p className="text-sm text-gray-600">
                    Estado: <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(execution.estado)}`}>
                      {execution.estado}
                    </span>
                  </p>
                  {execution.fecha_ejecucion && (
                    <p className="text-sm text-gray-600 mt-2">
                      Fecha: {formatDate(execution.fecha_ejecucion)}
                    </p>
                  )}
                </div>
                
                {execution.error_message && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                    <p className="text-red-800 font-medium">Error:</p>
                    <p className="text-red-600 text-sm">{execution.error_message}</p>
                  </div>
                )}
                
                {execution.resultado && (
                  <div className="bg-gray-50 border rounded-lg p-4 mb-4">
                    <p className="text-sm font-medium mb-2">Resultado:</p>
                    <pre className="text-xs overflow-auto max-h-96 whitespace-pre-wrap">
                      {JSON.stringify(execution.resultado, null, 2)}
                    </pre>
                  </div>
                )}
              </>
            )}
            
            <div className="flex justify-end">
              <Button onClick={() => setResultModalOpen(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
