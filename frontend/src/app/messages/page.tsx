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
import { formatDate } from '@/lib/utils'

export default function MessagesPage() {
  const router = useRouter()
  const [messages, setMessages] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [sendModalOpen, setSendModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    recipient_type: 'privado',
    recipient_id: '',
    content: ''
  })
  const [submitting, setSubmitting] = useState(false)

  const recipientTypeOptions: SelectOption[] = [
    { value: 'privado', label: 'Privado' },
    { value: 'grupal', label: 'Grupal' }
  ]

  useEffect(() => {
    loadMessages()
  }, [])

  const loadMessages = async () => {
    try {
      const data = await api.getMyMessages()
      setMessages(data)
    } catch (error) {
      console.error('Error loading messages:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!formData.recipient_id || !formData.content) {
      alert('Por favor completa todos los campos')
      return
    }

    try {
      setSubmitting(true)
      await api.sendMessage(formData)
      alert('Mensaje enviado exitosamente')
      setSendModalOpen(false)
      setFormData({
        recipient_type: 'privado',
        recipient_id: '',
        content: ''
      })
      loadMessages()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al enviar mensaje')
    } finally {
      setSubmitting(false)
    }
  }

  const getTypeLabel = (type: string) => {
    return type === 'privado' ? 'Privado' : 'Grupal'
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
            <h2 className="text-3xl font-bold text-gray-900">Mensajería</h2>
            <p className="mt-1 text-sm text-gray-600">
              Gestiona tus mensajes privados y grupales
            </p>
          </div>
          <Button onClick={() => setSendModalOpen(true)}>
            Enviar Mensaje
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Cargando mensajes...</p>
          </div>
        ) : messages.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No tienes mensajes</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <Card key={message.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                          {getTypeLabel(message.recipient_type)}
                        </span>
                        <span className="text-sm font-medium text-gray-900">
                          De: {message.sender_name || 'Desconocido'}
                        </span>
                      </div>
                      <p className="text-gray-700 mb-3">{message.content}</p>
                      <div className="text-xs text-gray-500">
                        {formatDate(message.timestamp)}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Send Message Modal */}
      <Dialog 
        open={sendModalOpen} 
        onOpenChange={setSendModalOpen}
        title="Enviar Mensaje"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="recipient_type">Tipo</Label>
            <Select
              id="recipient_type"
              options={recipientTypeOptions}
              value={formData.recipient_type}
              onChange={(e) => setFormData({ ...formData, recipient_type: e.target.value })}
            />
          </div>

          <div>
            <Label htmlFor="recipient_id">
              {formData.recipient_type === 'privado' ? 'ID de Usuario' : 'ID de Grupo'}
            </Label>
            <Input
              id="recipient_id"
              value={formData.recipient_id}
              onChange={(e) => setFormData({ ...formData, recipient_id: e.target.value })}
              placeholder={formData.recipient_type === 'privado' ? 'user123' : 'group456'}
            />
            <p className="text-xs text-gray-500 mt-1">
              Ingresa el ID del destinatario
            </p>
          </div>

          <div>
            <Label htmlFor="content">Mensaje</Label>
            <textarea
              id="content"
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              placeholder="Escribe tu mensaje aquí..."
            />
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setSendModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSendMessage} disabled={submitting}>
              {submitting ? 'Enviando...' : 'Enviar'}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}


