'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function InvoicesPage() {
  const router = useRouter()
  const [invoices, setInvoices] = useState<any[]>([])
  const [account, setAccount] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      // Load invoices
      const invoicesData = await api.getMyInvoices()
      setInvoices(invoicesData)

      // Load account
      const accountData = await api.getMyAccount()
      setAccount(accountData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePay = async (invoiceId: string, amount: number) => {
    try {
      await api.payInvoice(invoiceId, {
        monto: amount,
        metodo: 'tarjeta_credito'
      })
      alert('Pago registrado exitosamente')
      loadData() // Reload data
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al procesar el pago')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pagada':
        return 'bg-green-100 text-green-800'
      case 'pendiente':
        return 'bg-yellow-100 text-yellow-800'
      case 'vencida':
        return 'bg-red-100 text-red-800'
      case 'cancelada':
        return 'bg-gray-100 text-gray-800'
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
          <h2 className="text-3xl font-bold text-gray-900">Facturas y Pagos</h2>
          <p className="mt-1 text-sm text-gray-600">
            Gestiona tus facturas y cuenta corriente
          </p>
        </div>

        {/* Account Summary */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Cuenta Corriente</CardTitle>
            <CardDescription>Estado de tu cuenta</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-gray-500">Cargando...</p>
            ) : account ? (
              <div>
                <div className="text-3xl font-bold mb-4">
                  Saldo: <span className={account.saldo < 0 ? 'text-red-600' : 'text-green-600'}>
                    {formatCurrency(account.saldo)}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  {account.movimientos.length} movimientos registrados
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No se pudo cargar la cuenta</p>
            )}
          </CardContent>
        </Card>

        {/* Invoices List */}
        <Card>
          <CardHeader>
            <CardTitle>Mis Facturas</CardTitle>
            <CardDescription>Listado de facturas emitidas</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-gray-500">Cargando facturas...</p>
            ) : invoices.length === 0 ? (
              <p className="text-gray-500">No tienes facturas aún</p>
            ) : (
              <div className="space-y-4">
                {invoices.map((invoice) => (
                  <div key={invoice.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="font-semibold">Factura #{invoice.id.slice(-8)}</div>
                        <div className="text-sm text-gray-500">
                          Emitida: {formatDate(invoice.fecha_emision)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold">{formatCurrency(invoice.total)}</div>
                        <span className={`inline-block mt-1 px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(invoice.estado)}`}>
                          {invoice.estado}
                        </span>
                      </div>
                    </div>
                    
                    <div className="text-sm space-y-1 mb-3">
                      <div className="font-medium">Ítems:</div>
                      {invoice.items.map((item: any, idx: number) => (
                        <div key={idx} className="text-gray-600 pl-4">
                          - {item.process_name}: {formatCurrency(item.subtotal)}
                        </div>
                      ))}
                    </div>

                    {invoice.estado === 'pendiente' && (
                      <Button
                        onClick={() => handlePay(invoice.id, invoice.total)}
                        className="w-full"
                      >
                        Pagar Factura
                      </Button>
                    )}
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

