"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AlertsPage() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [user, setUser] = useState<any>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Filtros
  const [filters, setFilters] = useState({
    pais: "",
    ciudad: "",
    estado: "",
    tipo: "",
    fecha_desde: "",
    fecha_hasta: "",
  });

  useEffect(() => {
    // Cargar usuario desde localStorage
    const userData = localStorage.getItem("user");
    if (userData) {
      setUser(JSON.parse(userData));
    }
    loadAlerts();
    loadSummary();
  }, []);

  const loadAlerts = async (customFilters?: any) => {
    try {
      setLoading(true);
      const filterParams = customFilters || filters;

      // Usar endpoint con ubicación si hay filtros de ubicación
      if (filterParams.pais || filterParams.ciudad) {
        const data = await api.getAlertsByLocation(filterParams);
        setAlerts(data);
      } else {
        const data = await api.getAlerts(filterParams);
        setAlerts(data);
      }
    } catch (error) {
      console.error("Error loading alerts:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const data = await api.getAlertsSummary(filters);
      setSummary(data);
    } catch (error) {
      console.error("Error loading summary:", error);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    loadAlerts(filters);
    loadSummary();
  };

  const clearFilters = () => {
    const emptyFilters = {
      pais: "",
      ciudad: "",
      estado: "",
      tipo: "",
      fecha_desde: "",
      fecha_hasta: "",
    };
    setFilters(emptyFilters);
    loadAlerts(emptyFilters);
    loadSummary();
  };

  const getTypeColor = (tipo: string) => {
    switch (tipo) {
      case "sensor":
        return "bg-red-100 text-red-800";
      case "climatica":
        return "bg-orange-100 text-orange-800";
      case "umbral":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusColor = (estado: string) => {
    switch (estado) {
      case "activa":
        return "bg-red-500";
      case "finalizada":
        return "bg-gray-500";
      default:
        return "bg-gray-500";
    }
  };

  const getPriorityColor = (prioridad: number) => {
    if (prioridad >= 4) return "text-red-600 font-bold";
    if (prioridad === 3) return "text-orange-600 font-semibold";
    if (prioridad === 2) return "text-yellow-600";
    return "text-gray-600";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Sistema de Gestión de Sensores
          </h1>
          <div className="flex gap-2">
            {user?.role === "administrador" && (
              <Button
                onClick={() => router.push("/alerts/rules")}
                variant="outline"
              >
                Gestionar Reglas
              </Button>
            )}
            <Button onClick={() => router.push("/dashboard")} variant="outline">
              Volver al Dashboard
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">
              Alertas del Sistema
            </h2>
            <p className="mt-1 text-sm text-gray-600">
              Monitoreo de alertas climáticas y de funcionamiento de sensores
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setShowFilters(!showFilters)}
              variant="outline"
            >
              {showFilters ? "Ocultar Filtros" : "Mostrar Filtros"}
            </Button>
            <Button
              onClick={() => {
                loadAlerts();
                loadSummary();
              }}
              variant="outline"
            >
              Actualizar
            </Button>
          </div>
        </div>

        {/* Resumen de estadísticas */}
        {summary && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Resumen de Alertas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-2xl font-bold">{summary.total}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Activas</p>
                  <p className="text-2xl font-bold text-red-600">
                    {summary.por_estado?.activa || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Finalizadas</p>
                  <p className="text-2xl font-bold text-gray-600">
                    {summary.por_estado?.finalizada || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Panel de filtros */}
        {showFilters && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Filtros de Búsqueda</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="pais">País</Label>
                  <Input
                    id="pais"
                    placeholder="Ej: Argentina"
                    value={filters.pais}
                    onChange={(e) => handleFilterChange("pais", e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="ciudad">Ciudad</Label>
                  <Input
                    id="ciudad"
                    placeholder="Ej: Buenos Aires"
                    value={filters.ciudad}
                    onChange={(e) =>
                      handleFilterChange("ciudad", e.target.value)
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="estado">Estado</Label>
                  <select
                    id="estado"
                    className="w-full p-2 border rounded"
                    value={filters.estado}
                    onChange={(e) =>
                      handleFilterChange("estado", e.target.value)
                    }
                  >
                    <option value="">Todos</option>
                    <option value="activa">Activa</option>
                    <option value="finalizada">Finalizada</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="tipo">Tipo</Label>
                  <select
                    id="tipo"
                    className="w-full p-2 border rounded"
                    value={filters.tipo}
                    onChange={(e) => handleFilterChange("tipo", e.target.value)}
                  >
                    <option value="">Todos</option>
                    <option value="umbral">Umbral</option>
                    <option value="sensor">Sensor</option>
                    <option value="climatica">Climática</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="fecha_desde">Fecha Desde</Label>
                  <Input
                    id="fecha_desde"
                    type="date"
                    value={filters.fecha_desde}
                    onChange={(e) =>
                      handleFilterChange("fecha_desde", e.target.value)
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="fecha_hasta">Fecha Hasta</Label>
                  <Input
                    id="fecha_hasta"
                    type="date"
                    value={filters.fecha_hasta}
                    onChange={(e) =>
                      handleFilterChange("fecha_hasta", e.target.value)
                    }
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <Button onClick={applyFilters}>Aplicar Filtros</Button>
                <Button onClick={clearFilters} variant="outline">
                  Limpiar Filtros
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Lista de alertas */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Cargando alertas...</p>
          </div>
        ) : alerts.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No hay alertas registradas</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <Card key={alert._id || alert.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <div
                          className={`w-3 h-3 rounded-full ${getStatusColor(
                            alert.estado
                          )}`}
                        />
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${getTypeColor(
                            alert.tipo
                          )}`}
                        >
                          {alert.tipo}
                        </span>
                        {alert.prioridad && (
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-semibold ${getPriorityColor(
                              alert.prioridad
                            )}`}
                          >
                            Prioridad: {alert.prioridad}/5
                          </span>
                        )}
                        {alert.sensor_id && (
                          <span className="text-xs text-gray-500">
                            Sensor: {alert.sensor_id.slice(0, 8)}...
                          </span>
                        )}
                      </div>

                      {alert.rule_name && (
                        <div className="mb-2">
                          <span className="text-sm font-semibold text-blue-600">
                            📋 {alert.rule_name}
                          </span>
                        </div>
                      )}

                      <p className="text-base mb-3">{alert.descripcion}</p>

                      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">Fecha:</span>{" "}
                          {formatDate(alert.fecha_hora)}
                        </div>
                        {alert.valor !== null && alert.valor !== undefined && (
                          <div>
                            <span className="font-medium">Valor:</span>{" "}
                            {alert.valor.toFixed(1)}
                            {alert.tipo === "umbral" && "°C"}
                          </div>
                        )}
                        {alert.umbral !== null &&
                          alert.umbral !== undefined && (
                            <div>
                              <span className="font-medium">Umbral:</span>{" "}
                              {alert.umbral}°C
                            </div>
                          )}
                        <div>
                          <span className="font-medium">Estado:</span>{" "}
                          <span
                            className={
                              alert.estado === "activa"
                                ? "text-red-600 font-semibold"
                                : alert.estado === "reconocida"
                                ? "text-yellow-600"
                                : "text-green-600"
                            }
                          >
                            {alert.estado}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
