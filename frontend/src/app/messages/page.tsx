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
  const [myGroups, setMyGroups] = useState<any[]>([])
  const [privateMessages, setPrivateMessages] = useState<any[]>([])
  const [groupMessages, setGroupMessages] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState<'privado' | 'grupal'>('privado')
  const [loading, setLoading] = useState(true)
  const [sendModalOpen, setSendModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    recipient_type: 'privado',
    recipient_id: '',
    content: ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [currentUser, setCurrentUser] = useState<any>(null)

  const recipientTypeOptions: SelectOption[] = [
    { value: 'privado', label: 'Privado' },
    { value: 'grupal', label: 'Grupal' }
  ]

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const user = JSON.parse(userStr)
      setCurrentUser(user)
      console.log('[FRONTEND DEBUG] Current user:', user)
    }
    loadData()
  }, [])


  const loadData = async () => {
    try {
      setLoading(true)
      
      // Load user's groups
      const groups = await api.getMyGroups()
      setMyGroups(groups)
      
      // Load messages (now returns {private: [...], group: [...]})
      const messagesData = await api.getMyMessages()
      console.log('[FRONTEND DEBUG] Messages data:', messagesData)
      
      // Separate private and group messages
      if (messagesData && typeof messagesData === 'object') {
        setPrivateMessages(messagesData.private || [])
        setGroupMessages(messagesData.group || [])
        // Keep old messages array for backward compatibility if needed
        setMessages([...(messagesData.private || []), ...(messagesData.group || [])])
      } else {
        // Fallback for old format (list of messages)
        setMessages(messagesData || [])
        setPrivateMessages(messagesData || [])
        setGroupMessages([])
      }
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async () => {
    console.log('[FRONTEND DEBUG] Form data before validation:', formData)
    // Check if recipient_id is valid (not empty and not just whitespace)
    const recipientIdValid = formData.recipient_id && formData.recipient_id.trim().length > 0
    if (!recipientIdValid || !formData.content || formData.content.trim().length === 0) {
      alert('Por favor completa todos los campos')
      return
    }

    try {
      setSubmitting(true)
      const userStr = localStorage.getItem('user')
      const currentUser = userStr ? JSON.parse(userStr) : null
      console.log('[FRONTEND DEBUG] Sending message:', {
        currentUserId: currentUser?.id, // Solo para referencia/debugging
        note: 'sender_id viene del JWT en el backend, no se envía desde aquí',
        recipient_type: formData.recipient_type,
        recipient_id: formData.recipient_id,
        content: formData.content
      })
      await api.sendMessage(formData)
      alert('Mensaje enviado exitosamente')
      setSendModalOpen(false)
      setFormData({
        recipient_type: 'privado',
        recipient_id: '',
        content: ''
      })
      loadData()
    } catch (error: any) {
      console.error('[FRONTEND DEBUG] Error sending message:', error)
      const errorDetail = error.response?.data?.detail || 'Error al enviar mensaje'
      console.error('[FRONTEND DEBUG] Error detail:', errorDetail)
      alert(errorDetail)
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
            {currentUser && (
              <>
                <p className="mt-1 text-xs text-gray-500">
                  Tu ID: {currentUser.id} - Email: {currentUser.email}
                </p>
              </>
            )}
          </div>
          <Button onClick={() => setSendModalOpen(true)}>
            Enviar Mensaje
          </Button>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('privado')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'privado'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Mensajes Privados
              {privateMessages.length > 0 && (
                <span className="ml-2 bg-blue-100 text-blue-800 py-0.5 px-2 rounded-full text-xs font-semibold">
                  {privateMessages.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('grupal')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'grupal'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Mensajes Grupales
              {groupMessages.length > 0 && (
                <span className="ml-2 bg-green-100 text-green-800 py-0.5 px-2 rounded-full text-xs font-semibold">
                  {groupMessages.length}
                </span>
              )}
            </button>
          </nav>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Cargando mensajes...</p>
          </div>
        ) : activeTab === 'privado' ? (
          privateMessages.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-gray-500">No tienes mensajes privados</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {privateMessages.map((message) => (
                <Card key={message.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                            Privado
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
          )
        ) : (
          groupMessages.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-gray-500">No tienes mensajes grupales</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-8">
              {(() => {
                // Group messages by recipient_name
                const groupedByGroup = groupMessages.reduce((acc, message) => {
                  const groupName = message.recipient_name || 'Grupo Desconocido'
                  if (!acc[groupName]) {
                    acc[groupName] = []
                  }
                  acc[groupName].push(message)
                  return acc
                }, {} as Record<string, any[]>)
                
                return Object.entries(groupedByGroup).map(([groupName, messages]) => (
                  <div key={groupName}>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">{groupName}</h3>
                    <div className="space-y-4">
                      {messages.map((message) => (
                        <Card key={message.id}>
                          <CardContent className="p-6">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                  <span className="px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                                    Grupal
                                  </span>
                                  <span className="text-sm text-gray-600">
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
                  </div>
                ))
              })()}
            </div>
          )
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
              onChange={(e) => {
                const newType = e.target.value
                const newRecipientId = newType === 'grupal' && myGroups.length > 0 ? myGroups[0].id : ''
                setFormData({ recipient_type: newType, recipient_id: newRecipientId, content: formData.content })
              }}
            />
          </div>

          <div>
            <Label htmlFor="recipient_id">
              {formData.recipient_type === 'privado' ? 'Email del Usuario' : 'Grupo'}
            </Label>
            {formData.recipient_type === 'privado' ? (
              <Input
                id="recipient_id"
                type="email"
                value={formData.recipient_id}
                onChange={(e) => setFormData({ ...formData, recipient_id: e.target.value })}
                placeholder="usuario@ejemplo.com"
              />
            ) : myGroups.length > 0 ? (
              <Select
                id="recipient_id"
                options={myGroups.map(g => ({ value: g.id, label: g.nombre }))}
                value={formData.recipient_id}
                onChange={(e) => setFormData({ ...formData, recipient_id: e.target.value })}
              />
            ) : (
              <Input
                id="recipient_id"
                type="text"
                value=""
                disabled
                placeholder="No hay grupos disponibles"
              />
            )}
            <p className="text-xs text-gray-500 mt-1">
              {formData.recipient_type === 'privado' 
                ? 'Ingresa el email del destinatario' 
                : myGroups.length === 0 
                  ? 'No perteneces a ningún grupo' 
                  : 'Selecciona un grupo'}
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


