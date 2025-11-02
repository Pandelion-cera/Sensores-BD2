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

export default function AdminGroupsPage() {
  const router = useRouter()
  const [groups, setGroups] = useState<any[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)
  
  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [addMemberModalOpen, setAddMemberModalOpen] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState<any>(null)
  const [selectedUserId, setSelectedUserId] = useState<string>('')
  const [formData, setFormData] = useState({
    nombre: '',
    miembros: [] as string[]
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadData()
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const userData = JSON.parse(userStr)
      setUser(userData)
      if (userData.role !== 'administrador') {
        router.push('/dashboard')
      }
    } else {
      router.push('/login')
    }
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [groupsData, usersData] = await Promise.all([
        api.getAllGroups(),
        api.getAllUsers()
      ])
      setGroups(groupsData)
      setUsers(usersData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateClick = () => {
    setFormData({ nombre: '', miembros: [] })
    setSelectedUserId('')
    setCreateModalOpen(true)
  }

  const handleAddMemberClick = (group: any) => {
    setSelectedGroup(group)
    setSelectedUserId('')
    setAddMemberModalOpen(true)
  }

  const handleRemoveMember = async (group: any, userId: string) => {
    const userToRemove = users.find(u => u.id === userId)
    if (!confirm(`¿Estás seguro de remover a "${userToRemove?.nombre_completo}" del grupo "${group.nombre}"?`)) {
      return
    }

    try {
      setSubmitting(true)
      await api.removeGroupMember(group.id, userId)
      alert('Miembro removido exitosamente')
      loadData()
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail || 'Error al remover miembro'
      alert(errorDetail)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteGroup = async (group: any) => {
    if (!confirm(`¿Estás seguro de eliminar el grupo "${group.nombre}"? Esta acción no se puede deshacer.`)) {
      return
    }

    try {
      setSubmitting(true)
      await api.deleteGroup(group.id)
      alert('Grupo eliminado exitosamente')
      loadData()
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail || 'Error al eliminar grupo'
      alert(errorDetail)
    } finally {
      setSubmitting(false)
    }
  }

  const handleCreateGroup = async () => {
    if (!formData.nombre.trim()) {
      alert('Por favor ingresa un nombre para el grupo')
      return
    }

    try {
      setSubmitting(true)
      await api.createGroup(formData)
      alert('Grupo creado exitosamente')
      setCreateModalOpen(false)
      setFormData({ nombre: '', miembros: [] })
      loadData()
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail || 'Error al crear grupo'
      alert(errorDetail)
    } finally {
      setSubmitting(false)
    }
  }

  const handleAddMember = async () => {
    if (!selectedUserId) {
      alert('Por favor selecciona un usuario')
      return
    }

    try {
      setSubmitting(true)
      await api.addGroupMember(selectedGroup.id, selectedUserId)
      alert('Miembro agregado exitosamente')
      setAddMemberModalOpen(false)
      setSelectedUserId('')
      loadData()
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail || 'Error al agregar miembro'
      alert(errorDetail)
    } finally {
      setSubmitting(false)
    }
  }

  const toggleMemberSelection = (userId: string) => {
    setFormData(prev => {
      const isSelected = prev.miembros.includes(userId)
      return {
        ...prev,
        miembros: isSelected
          ? prev.miembros.filter(id => id !== userId)
          : [...prev.miembros, userId]
      }
    })
  }

  const getUserName = (userId: string) => {
    const user = users.find(u => u.id === userId)
    return user ? user.nombre_completo : 'Usuario desconocido'
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
            Administración de Grupos
          </h1>
          <Button onClick={() => router.push('/dashboard')} variant="outline">
            Volver al Dashboard
          </Button>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Grupos</h2>
            <p className="mt-1 text-sm text-gray-600">
              Gestiona grupos y sus miembros
            </p>
          </div>
          <Button onClick={handleCreateClick}>
            Crear Grupo
          </Button>
        </div>

        {groups.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No hay grupos creados</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {groups.map((group) => (
              <Card key={group.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>{group.nombre}</CardTitle>
                      <CardDescription>
                        Creado: {formatDate(group.fecha_creacion)}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleAddMemberClick(group)}
                      >
                        Agregar Miembro
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteGroup(group)}
                        disabled={submitting}
                      >
                        Eliminar
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">
                      Miembros ({group.miembros.length})
                    </h4>
                    {group.miembros.length === 0 ? (
                      <p className="text-sm text-gray-500">No hay miembros</p>
                    ) : (
                      <div className="space-y-2">
                        {group.miembros.map((userId: string) => (
                          <div
                            key={userId}
                            className="flex items-center justify-between p-2 bg-gray-50 rounded"
                          >
                            <span className="text-sm text-gray-700">
                              {getUserName(userId)}
                            </span>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleRemoveMember(group, userId)}
                              disabled={submitting}
                            >
                              Remover
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Create Group Modal */}
      <Dialog
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        title="Crear Grupo"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="nombre">Nombre del Grupo</Label>
            <Input
              id="nombre"
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
              placeholder="Equipo de Trabajo"
            />
          </div>

          <div>
            <Label>Miembros</Label>
            <div className="mt-2 border rounded-lg max-h-64 overflow-y-auto">
              {users.length === 0 ? (
                <p className="p-4 text-sm text-gray-500 text-center">No hay usuarios disponibles</p>
              ) : (
                users.map((user) => (
                  <div key={user.id} className="p-2 hover:bg-gray-50">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.miembros.includes(user.id)}
                        onChange={() => toggleMemberSelection(user.id)}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-700">{user.nombre_completo}</span>
                    </label>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setCreateModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleCreateGroup} disabled={submitting}>
              {submitting ? 'Creando...' : 'Crear Grupo'}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Add Member Modal */}
      <Dialog
        open={addMemberModalOpen}
        onOpenChange={setAddMemberModalOpen}
        title={`Agregar Miembro a ${selectedGroup?.nombre}`}
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="user_select">Seleccionar Usuario</Label>
            <Select
              id="user_select"
              options={users
                .filter(u => !selectedGroup?.miembros.includes(u.id))
                .map(u => ({ value: u.id, label: u.nombre_completo }))}
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              placeholder="Selecciona un usuario"
            />
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setAddMemberModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleAddMember} disabled={submitting}>
              {submitting ? 'Agregando...' : 'Agregar'}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}

