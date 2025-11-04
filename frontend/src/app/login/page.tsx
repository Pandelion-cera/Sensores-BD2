'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@apollo/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { LOGIN, REGISTER } from '@/graphql/mutations'

export default function LoginPage() {
  const router = useRouter()
  const [isLogin, setIsLogin] = useState(true)
  const [error, setError] = useState('')

  const [loginMutation, { loading: loginLoading }] = useMutation(LOGIN)
  const [registerMutation, { loading: registerLoading }] = useMutation(REGISTER)

  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
  })

  const [registerData, setRegisterData] = useState({
    nombre_completo: '',
    email: '',
    password: '',
  })

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      const { data } = await loginMutation({
        variables: {
          input: {
            email: loginData.email,
            password: loginData.password,
          },
        },
      })
      
      if (data?.login) {
        // Store token and user data
        localStorage.setItem('token', data.login.accessToken)
        localStorage.setItem('user', JSON.stringify(data.login.user))
        localStorage.setItem('session_id', data.login.sessionId)
        
        // Redirect to dashboard
        router.push('/dashboard')
      }
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión')
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      await registerMutation({
        variables: {
          input: {
            nombreCompleto: registerData.nombre_completo,
            email: registerData.email,
            password: registerData.password,
          },
        },
      })
      
      // After successful registration, switch to login
      setIsLogin(true)
      setLoginData({ email: registerData.email, password: registerData.password })
      setError('') // Clear any previous errors
      alert('Registro exitoso! Ahora puedes iniciar sesión.')
    } catch (err: any) {
      setError(err.message || 'Error al registrarse')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">
            {isLogin ? 'Iniciar Sesión' : 'Registrarse'}
          </CardTitle>
          <CardDescription className="text-center">
            Sistema de Gestión de Sensores Climáticos
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLogin ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="correo@ejemplo.com"
                  value={loginData.email}
                  onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  value={loginData.password}
                  onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                  required
                />
              </div>
              {error && (
                <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
                  {error}
                </div>
              )}
              <Button type="submit" className="w-full" disabled={loginLoading}>
                {loginLoading ? 'Cargando...' : 'Iniciar Sesión'}
              </Button>
              <div className="text-center text-sm">
                <span className="text-muted-foreground">¿No tienes cuenta? </span>
                <button
                  type="button"
                  onClick={() => setIsLogin(false)}
                  className="text-primary hover:underline"
                >
                  Regístrate
                </button>
              </div>
              <div className="mt-4 p-3 bg-blue-50 rounded text-sm">
                <p className="font-semibold mb-1">Cuentas de prueba:</p>
                <p className="text-xs">admin@test.com / admin123</p>
                <p className="text-xs">user@test.com / user123</p>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre Completo</Label>
                <Input
                  id="nombre"
                  type="text"
                  placeholder="Juan Pérez"
                  value={registerData.nombre_completo}
                  onChange={(e) => setRegisterData({ ...registerData, nombre_completo: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reg-email">Email</Label>
                <Input
                  id="reg-email"
                  type="email"
                  placeholder="correo@ejemplo.com"
                  value={registerData.email}
                  onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reg-password">Contraseña</Label>
                <Input
                  id="reg-password"
                  type="password"
                  value={registerData.password}
                  onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                  required
                  minLength={6}
                />
              </div>
              {error && (
                <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
                  {error}
                </div>
              )}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Cargando...' : 'Registrarse'}
              </Button>
              <div className="text-center text-sm">
                <span className="text-muted-foreground">¿Ya tienes cuenta? </span>
                <button
                  type="button"
                  onClick={() => setIsLogin(true)}
                  className="text-primary hover:underline"
                >
                  Inicia sesión
                </button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

