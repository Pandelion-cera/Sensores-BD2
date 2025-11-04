"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AlertRulesPage() {
  const router = useRouter();
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingRule, setEditingRule] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);

  const [formData, setFormData] = useState({
    nombre: "",
    descripcion: "",
    temp_min: "",
    temp_max: "",
    humidity_min: "",
    humidity_max: "",
    location_scope: "ciudad",
    ciudad: "",
    region: "",
    pais: "",
    fecha_inicio: "",
    fecha_fin: "",
    prioridad: "3",
    estado: "activa",
  });

  useEffect(() => {
    checkAdminAccess();
    loadRules();
    loadSummary();
  }, []);

  const checkAdminAccess = () => {
    const userData = localStorage.getItem("user");
    if (userData) {
      const user = JSON.parse(userData);
      if (user.role !== "administrador") {
        alert(
          "Acceso denegado. Solo administradores pueden acceder a esta página."
        );
        router.push("/alerts");
      }
    }
  };

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await api.getAlertRules();
      setRules(data);
    } catch (error) {
      console.error("Error loading rules:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const data = await api.getAlertRulesSummary();
      setSummary(data);
    } catch (error) {
      console.error("Error loading summary:", error);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Convertir strings vacíos a null
      const payload: any = {
        nombre: formData.nombre,
        descripcion: formData.descripcion,
        temp_min: formData.temp_min ? parseFloat(formData.temp_min) : null,
        temp_max: formData.temp_max ? parseFloat(formData.temp_max) : null,
        humidity_min: formData.humidity_min
          ? parseFloat(formData.humidity_min)
          : null,
        humidity_max: formData.humidity_max
          ? parseFloat(formData.humidity_max)
          : null,
        location_scope: formData.location_scope,
        ciudad: formData.ciudad || null,
        region: formData.region || null,
        pais: formData.pais,
        fecha_inicio: formData.fecha_inicio
          ? new Date(formData.fecha_inicio).toISOString()
          : null,
        fecha_fin: formData.fecha_fin
          ? new Date(formData.fecha_fin).toISOString()
          : null,
        prioridad: parseInt(formData.prioridad),
        estado: formData.estado,
      };

      if (editingRule) {
        await api.updateAlertRule(editingRule._id || editingRule.id, payload);
      } else {
        await api.createAlertRule(payload);
      }

      setShowDialog(false);
      resetForm();
      loadRules();
      loadSummary();
    } catch (error: any) {
      console.error("Error saving rule:", error);
      alert(error.response?.data?.detail || "Error al guardar la regla");
    }
  };

  const resetForm = () => {
    setFormData({
      nombre: "",
      descripcion: "",
      temp_min: "",
      temp_max: "",
      humidity_min: "",
      humidity_max: "",
      location_scope: "ciudad",
      ciudad: "",
      region: "",
      pais: "",
      fecha_inicio: "",
      fecha_fin: "",
      prioridad: "3",
      estado: "activa",
    });
    setEditingRule(null);
  };

  const handleEdit = (rule: any) => {
    setEditingRule(rule);
    setFormData({
      nombre: rule.nombre || "",
      descripcion: rule.descripcion || "",
      temp_min: rule.temp_min?.toString() || "",
      temp_max: rule.temp_max?.toString() || "",
      humidity_min: rule.humidity_min?.toString() || "",
      humidity_max: rule.humidity_max?.toString() || "",
      location_scope: rule.location_scope || "ciudad",
      ciudad: rule.ciudad || "",
      region: rule.region || "",
      pais: rule.pais || "",
      fecha_inicio: rule.fecha_inicio
        ? new Date(rule.fecha_inicio).toISOString().split("T")[0]
        : "",
      fecha_fin: rule.fecha_fin
        ? new Date(rule.fecha_fin).toISOString().split("T")[0]
        : "",
      prioridad: rule.prioridad?.toString() || "3",
      estado: rule.estado || "activa",
    });
    setShowDialog(true);
  };

  const handleToggleStatus = async (rule: any) => {
    try {
      if (rule.estado === "activa") {
        await api.deactivateAlertRule(rule._id || rule.id);
      } else {
        await api.activateAlertRule(rule._id || rule.id);
      }
      loadRules();
      loadSummary();
    } catch (error) {
      console.error("Error toggling status:", error);
    }
  };

  const handleDelete = async (rule: any) => {
    if (!confirm(`¿Está seguro de eliminar la regla "${rule.nombre}"?`)) return;

    try {
      await api.deleteAlertRule(rule._id || rule.id);
      loadRules();
      loadSummary();
    } catch (error) {
      console.error("Error deleting rule:", error);
    }
  };

  const getPriorityColor = (prioridad: number) => {
    if (prioridad >= 4) return "bg-red-100 text-red-800";
    if (prioridad === 3) return "bg-orange-100 text-orange-800";
    if (prioridad === 2) return "bg-yellow-100 text-yellow-800";
    return "bg-gray-100 text-gray-800";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Gestión de Reglas de Alertas
          </h1>
          <Button onClick={() => router.push("/alerts")} variant="outline">
            Volver a Alertas
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Resumen */}
        {summary && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Resumen de Reglas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-2xl font-bold">{summary.total}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Activas</p>
                  <p className="text-2xl font-bold text-green-600">
                    {summary.activas}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Inactivas</p>
                  <p className="text-2xl font-bold text-gray-600">
                    {summary.inactivas}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Botón crear */}
        <div className="mb-6">
          <Button
            onClick={() => {
              resetForm();
              setShowDialog(true);
            }}
          >
            + Nueva Regla de Alerta
          </Button>
        </div>

        {/* Lista de reglas */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Cargando reglas...</p>
          </div>
        ) : rules.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No hay reglas configuradas</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {rules.map((rule) => (
              <Card key={rule._id || rule.id}>
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold">{rule.nombre}</h3>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            rule.estado === "activa"
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {rule.estado}
                        </span>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${getPriorityColor(
                            rule.prioridad
                          )}`}
                        >
                          Prioridad: {rule.prioridad}/5
                        </span>
                      </div>

                      <p className="text-gray-600 mb-3">{rule.descripcion}</p>

                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Ubicación:</span>{" "}
                          {rule.location_scope === "ciudad" &&
                            rule.ciudad &&
                            `${rule.ciudad}, ${rule.pais}`}
                          {rule.location_scope === "region" &&
                            rule.region &&
                            `${rule.region}, ${rule.pais}`}
                          {rule.location_scope === "pais" && rule.pais}
                        </div>
                        <div>
                          <span className="font-medium">Condiciones:</span>{" "}
                          {rule.temp_min && `Temp ≥ ${rule.temp_min}°C`}
                          {rule.temp_max && `Temp ≤ ${rule.temp_max}°C`}
                          {rule.humidity_min && `Hum ≥ ${rule.humidity_min}%`}
                          {rule.humidity_max && `Hum ≤ ${rule.humidity_max}%`}
                        </div>
                        {(rule.fecha_inicio || rule.fecha_fin) && (
                          <div>
                            <span className="font-medium">Vigencia:</span>{" "}
                            {rule.fecha_inicio &&
                              `Desde ${new Date(
                                rule.fecha_inicio
                              ).toLocaleDateString()}`}
                            {rule.fecha_fin &&
                              ` hasta ${new Date(
                                rule.fecha_fin
                              ).toLocaleDateString()}`}
                          </div>
                        )}
                        <div>
                          <span className="font-medium">Creada por:</span>{" "}
                          {rule.creado_por}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2 ml-4">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleEdit(rule)}
                      >
                        Editar
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleToggleStatus(rule)}
                      >
                        {rule.estado === "activa" ? "Desactivar" : "Activar"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDelete(rule)}
                      >
                        Eliminar
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Dialog para crear/editar */}
        <Dialog open={showDialog} onOpenChange={setShowDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingRule ? "Editar Regla" : "Nueva Regla de Alerta"}
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="nombre">Nombre *</Label>
                <Input
                  id="nombre"
                  required
                  value={formData.nombre}
                  onChange={(e) => handleInputChange("nombre", e.target.value)}
                  placeholder="Ej: Ola de calor Buenos Aires"
                />
              </div>

              <div>
                <Label htmlFor="descripcion">Descripción *</Label>
                <textarea
                  id="descripcion"
                  required
                  className="w-full p-2 border rounded"
                  rows={3}
                  value={formData.descripcion}
                  onChange={(e) =>
                    handleInputChange("descripcion", e.target.value)
                  }
                  placeholder="Descripción detallada de qué detecta esta regla"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="temp_min">Temperatura Mínima (°C)</Label>
                  <Input
                    id="temp_min"
                    type="number"
                    step="0.1"
                    value={formData.temp_min}
                    onChange={(e) =>
                      handleInputChange("temp_min", e.target.value)
                    }
                    placeholder="-10.0"
                  />
                </div>
                <div>
                  <Label htmlFor="temp_max">Temperatura Máxima (°C)</Label>
                  <Input
                    id="temp_max"
                    type="number"
                    step="0.1"
                    value={formData.temp_max}
                    onChange={(e) =>
                      handleInputChange("temp_max", e.target.value)
                    }
                    placeholder="45.0"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="humidity_min">Humedad Mínima (%)</Label>
                  <Input
                    id="humidity_min"
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={formData.humidity_min}
                    onChange={(e) =>
                      handleInputChange("humidity_min", e.target.value)
                    }
                    placeholder="0"
                  />
                </div>
                <div>
                  <Label htmlFor="humidity_max">Humedad Máxima (%)</Label>
                  <Input
                    id="humidity_max"
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={formData.humidity_max}
                    onChange={(e) =>
                      handleInputChange("humidity_max", e.target.value)
                    }
                    placeholder="100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="location_scope">Alcance *</Label>
                  <select
                    id="location_scope"
                    required
                    className="w-full p-2 border rounded"
                    value={formData.location_scope}
                    onChange={(e) =>
                      handleInputChange("location_scope", e.target.value)
                    }
                  >
                    <option value="ciudad">Ciudad</option>
                    <option value="region">Región</option>
                    <option value="pais">País</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="pais">País *</Label>
                  <Input
                    id="pais"
                    required
                    value={formData.pais}
                    onChange={(e) => handleInputChange("pais", e.target.value)}
                    placeholder="Argentina"
                  />
                </div>
                {formData.location_scope === "ciudad" && (
                  <div>
                    <Label htmlFor="ciudad">Ciudad *</Label>
                    <Input
                      id="ciudad"
                      required
                      value={formData.ciudad}
                      onChange={(e) =>
                        handleInputChange("ciudad", e.target.value)
                      }
                      placeholder="Buenos Aires"
                    />
                  </div>
                )}
                {formData.location_scope === "region" && (
                  <div>
                    <Label htmlFor="region">Región *</Label>
                    <Input
                      id="region"
                      required
                      value={formData.region}
                      onChange={(e) =>
                        handleInputChange("region", e.target.value)
                      }
                      placeholder="Patagonia"
                    />
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="fecha_inicio">Fecha Inicio</Label>
                  <Input
                    id="fecha_inicio"
                    type="date"
                    value={formData.fecha_inicio}
                    onChange={(e) =>
                      handleInputChange("fecha_inicio", e.target.value)
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="fecha_fin">Fecha Fin</Label>
                  <Input
                    id="fecha_fin"
                    type="date"
                    value={formData.fecha_fin}
                    onChange={(e) =>
                      handleInputChange("fecha_fin", e.target.value)
                    }
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="prioridad">Prioridad *</Label>
                  <select
                    id="prioridad"
                    required
                    className="w-full p-2 border rounded"
                    value={formData.prioridad}
                    onChange={(e) =>
                      handleInputChange("prioridad", e.target.value)
                    }
                  >
                    <option value="1">1 - Muy baja</option>
                    <option value="2">2 - Baja</option>
                    <option value="3">3 - Media</option>
                    <option value="4">4 - Alta</option>
                    <option value="5">5 - Crítica</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="estado">Estado *</Label>
                  <select
                    id="estado"
                    required
                    className="w-full p-2 border rounded"
                    value={formData.estado}
                    onChange={(e) =>
                      handleInputChange("estado", e.target.value)
                    }
                  >
                    <option value="activa">Activa</option>
                    <option value="inactiva">Inactiva</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowDialog(false);
                    resetForm();
                  }}
                >
                  Cancelar
                </Button>
                <Button type="submit">
                  {editingRule ? "Actualizar" : "Crear"} Regla
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}
