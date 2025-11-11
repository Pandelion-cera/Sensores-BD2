"""
Processes widget for viewing and managing process requests
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget,
    QHeaderView, QAbstractItemView, QComboBox, QDialog,
    QLineEdit, QDateTimeEdit, QTextEdit, QGroupBox, QScrollArea,
    QTimeEdit, QSpinBox, QRadioButton, QButtonGroup, QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QDateTime, QTime
from datetime import datetime
from typing import Any, Dict, Optional
import logging
import json

from desktop_app.controllers import get_process_controller
from desktop_app.utils.session_manager import SessionManager
from desktop_app.models.process_models import ProcessRequestCreate, ProcessStatus, Process, Execution, ProcessType
from desktop_app.models.scheduled_process_models import (
    ScheduledProcessCreate, ScheduledProcessUpdate, ScheduleType, ScheduleStatus
)


class ProcessRequestDialog(QDialog):
    """Dialog for collecting process request parameters"""
    
    def __init__(self, process: Process, parent=None):
        super().__init__(parent)
        self.process = process
        self.setWindowTitle(f"Solicitar Proceso: {process.nombre}")
        self.setMinimumWidth(500)
        self.parametros: Dict[str, Any] = {}
        self.is_alert_config = process.tipo == ProcessType.ALERT_CONFIG
        self._temp_sentinel = -999.0
        self._hum_sentinel = -1.0
        self.city_required = process.tipo not in {
            ProcessType.TEMP_MAX_MIN_REPORT,
            ProcessType.TEMP_AVG_REPORT,
        }
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        desc_label = QLabel(self.process.descripcion or "")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(desc_label)
        
        if self.is_alert_config:
            self._init_alert_config_ui(layout)
        else:
            self._init_default_ui(layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Solicitar")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def _init_default_ui(self, layout: QVBoxLayout):
        layout.addWidget(QLabel("País *:"))
        self.pais_edit = QLineEdit()
        self.pais_edit.setPlaceholderText("Ej: Argentina")
        layout.addWidget(self.pais_edit)
        
        ciudad_label_text = "Ciudad *:" if self.city_required else "Ciudad (Opcional):"
        self.ciudad_label = QLabel(ciudad_label_text)
        layout.addWidget(self.ciudad_label)
        self.ciudad_edit = QLineEdit()
        placeholder = "Ej: Buenos Aires"
        if not self.city_required:
            placeholder = "Ej: Buenos Aires (opcional)"
        self.ciudad_edit.setPlaceholderText(placeholder)
        layout.addWidget(self.ciudad_edit)
        
        layout.addWidget(QLabel("Fecha Inicio *:"))
        self.fecha_inicio_edit = QDateTimeEdit()
        self.fecha_inicio_edit.setCalendarPopup(True)
        self.fecha_inicio_edit.setDateTime(QDateTime.currentDateTime().addDays(-30))
        self.fecha_inicio_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        layout.addWidget(self.fecha_inicio_edit)
        
        layout.addWidget(QLabel("Fecha Fin *:"))
        self.fecha_fin_edit = QDateTimeEdit()
        self.fecha_fin_edit.setCalendarPopup(True)
        self.fecha_fin_edit.setDateTime(QDateTime.currentDateTime())
        self.fecha_fin_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        layout.addWidget(self.fecha_fin_edit)
        
        info_label = QLabel("* Campos requeridos")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_label)
    
    def _init_alert_config_ui(self, layout: QVBoxLayout):
        layout.addWidget(QLabel("Nombre de la Regla *:"))
        self.rule_name_edit = QLineEdit()
        self.rule_name_edit.setPlaceholderText("Ej: Alerta altas temperaturas matutinas")
        layout.addWidget(self.rule_name_edit)
        
        layout.addWidget(QLabel("Descripción *:"))
        self.rule_desc_edit = QTextEdit()
        self.rule_desc_edit.setMaximumHeight(90)
        layout.addWidget(self.rule_desc_edit)
        
        thresholds_group = QGroupBox("Condiciones (al menos una)")
        thresholds_layout = QVBoxLayout()
        
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperatura mínima:"))
        self.temp_min_spin = QDoubleSpinBox()
        self.temp_min_spin.setRange(self._temp_sentinel, 100.0)
        self.temp_min_spin.setDecimals(2)
        self.temp_min_spin.setSpecialValueText("No establecido")
        self.temp_min_spin.setValue(self._temp_sentinel)
        temp_layout.addWidget(self.temp_min_spin)
        
        temp_layout.addWidget(QLabel("Temperatura máxima:"))
        self.temp_max_spin = QDoubleSpinBox()
        self.temp_max_spin.setRange(self._temp_sentinel, 100.0)
        self.temp_max_spin.setDecimals(2)
        self.temp_max_spin.setSpecialValueText("No establecido")
        self.temp_max_spin.setValue(self._temp_sentinel)
        temp_layout.addWidget(self.temp_max_spin)
        thresholds_layout.addLayout(temp_layout)
        
        hum_layout = QHBoxLayout()
        hum_layout.addWidget(QLabel("Humedad mínima:"))
        self.hum_min_spin = QDoubleSpinBox()
        self.hum_min_spin.setRange(self._hum_sentinel, 100.0)
        self.hum_min_spin.setDecimals(2)
        self.hum_min_spin.setSpecialValueText("No establecido")
        self.hum_min_spin.setValue(self._hum_sentinel)
        hum_layout.addWidget(self.hum_min_spin)
        
        hum_layout.addWidget(QLabel("Humedad máxima:"))
        self.hum_max_spin = QDoubleSpinBox()
        self.hum_max_spin.setRange(self._hum_sentinel, 100.0)
        self.hum_max_spin.setDecimals(2)
        self.hum_max_spin.setSpecialValueText("No establecido")
        self.hum_max_spin.setValue(self._hum_sentinel)
        hum_layout.addWidget(self.hum_max_spin)
        thresholds_layout.addLayout(hum_layout)
        
        thresholds_group.setLayout(thresholds_layout)
        layout.addWidget(thresholds_group)
        
        location_group = QGroupBox("Ámbito de Aplicación *")
        location_layout = QVBoxLayout()
        
        scope_row = QHBoxLayout()
        scope_row.addWidget(QLabel("Ámbito:"))
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["ciudad", "region", "pais"])
        self.scope_combo.currentTextChanged.connect(self._update_scope_visibility)
        scope_row.addWidget(self.scope_combo)
        scope_row.addStretch()
        location_layout.addLayout(scope_row)
        
        location_layout.addWidget(QLabel("País:"))
        self.rule_country_edit = QLineEdit()
        self.rule_country_edit.setPlaceholderText("Ej: Argentina")
        location_layout.addWidget(self.rule_country_edit)
        
        self.city_label = QLabel("Ciudad:")
        self.rule_city_edit = QLineEdit()
        self.rule_city_edit.setPlaceholderText("Ej: Buenos Aires")
        location_layout.addWidget(self.city_label)
        location_layout.addWidget(self.rule_city_edit)
        
        self.region_label = QLabel("Región:")
        self.rule_region_edit = QLineEdit()
        self.rule_region_edit.setPlaceholderText("Ej: Patagonia Sur")
        location_layout.addWidget(self.region_label)
        location_layout.addWidget(self.rule_region_edit)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        dates_group = QGroupBox("Rango de Vigencia (Opcional)")
        dates_layout = QVBoxLayout()
        
        start_row = QHBoxLayout()
        self.use_start_date_checkbox = QCheckBox("Definir fecha de inicio")
        self.alert_start_dt = QDateTimeEdit()
        self.alert_start_dt.setCalendarPopup(True)
        self.alert_start_dt.setDateTime(QDateTime.currentDateTime())
        self.alert_start_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.alert_start_dt.setEnabled(False)
        self.use_start_date_checkbox.toggled.connect(self.alert_start_dt.setEnabled)
        start_row.addWidget(self.use_start_date_checkbox)
        start_row.addWidget(self.alert_start_dt)
        dates_layout.addLayout(start_row)
        
        end_row = QHBoxLayout()
        self.use_end_date_checkbox = QCheckBox("Definir fecha de fin")
        self.alert_end_dt = QDateTimeEdit()
        self.alert_end_dt.setCalendarPopup(True)
        self.alert_end_dt.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.alert_end_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.alert_end_dt.setEnabled(False)
        self.use_end_date_checkbox.toggled.connect(self.alert_end_dt.setEnabled)
        end_row.addWidget(self.use_end_date_checkbox)
        end_row.addWidget(self.alert_end_dt)
        dates_layout.addLayout(end_row)
        
        dates_group.setLayout(dates_layout)
        layout.addWidget(dates_group)
        
        priority_row = QHBoxLayout()
        priority_row.addWidget(QLabel("Prioridad (1-5):"))
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 5)
        self.priority_spin.setValue(3)
        priority_row.addWidget(self.priority_spin)
        priority_row.addStretch()
        layout.addLayout(priority_row)
        
        info_label = QLabel("Las reglas creadas se asignarán a tu usuario y se aplicarán automáticamente a nuevas mediciones.")
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info_label)
        
        self._update_scope_visibility(self.scope_combo.currentText())
    
    def _update_scope_visibility(self, scope: str):
        is_city = scope == "ciudad"
        is_region = scope == "region"
        
        self.city_label.setVisible(is_city)
        self.rule_city_edit.setVisible(is_city)
        self.rule_city_edit.setEnabled(is_city)
        
        self.region_label.setVisible(is_region)
        self.rule_region_edit.setVisible(is_region)
        self.rule_region_edit.setEnabled(is_region)
    
    def accept(self):
        try:
            if self.is_alert_config:
                self._validate_alert_request()
            else:
                self._validate_default_request()
        except ValueError as exc:
            QMessageBox.warning(self, "Error de Validación", str(exc))
            return
        
        super().accept()
    
    def _validate_default_request(self) -> None:
        pais = self.pais_edit.text().strip()
        ciudad = self.ciudad_edit.text().strip()
        if not pais:
            raise ValueError("Por favor ingrese el país")
        if self.city_required and not ciudad:
            raise ValueError("Por favor ingrese la ciudad")
        
        fecha_inicio = self.fecha_inicio_edit.dateTime().toPyDateTime()
        fecha_fin = self.fecha_fin_edit.dateTime().toPyDateTime()
        if fecha_inicio >= fecha_fin:
            raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        self.parametros = {
            "pais": pais,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat()
        }
        if ciudad:
            self.parametros["ciudad"] = ciudad
    
    def _validate_alert_request(self) -> None:
        nombre = self.rule_name_edit.text().strip()
        descripcion = self.rule_desc_edit.toPlainText().strip()
        if len(nombre) < 3:
            raise ValueError("El nombre de la regla debe tener al menos 3 caracteres")
        if len(descripcion) < 10:
            raise ValueError("La descripción debe tener al menos 10 caracteres")
        
        def _get_value(spin: QDoubleSpinBox, sentinel: float) -> Optional[float]:
            value = round(spin.value(), 2)
            return None if abs(value - sentinel) < 1e-6 else value
        
        temp_min = _get_value(self.temp_min_spin, self._temp_sentinel)
        temp_max = _get_value(self.temp_max_spin, self._temp_sentinel)
        hum_min = _get_value(self.hum_min_spin, self._hum_sentinel)
        hum_max = _get_value(self.hum_max_spin, self._hum_sentinel)
        
        if all(value is None for value in (temp_min, temp_max, hum_min, hum_max)):
            raise ValueError("Debe definir al menos una condición de temperatura u humedad")
        if temp_min is not None and temp_max is not None and temp_min > temp_max:
            raise ValueError("La temperatura mínima no puede ser mayor que la máxima")
        if hum_min is not None and hum_max is not None and hum_min > hum_max:
            raise ValueError("La humedad mínima no puede ser mayor que la máxima")
        
        scope = self.scope_combo.currentText()
        pais = self.rule_country_edit.text().strip()
        ciudad = self.rule_city_edit.text().strip()
        region = self.rule_region_edit.text().strip()
        
        if not pais:
            raise ValueError("Debe indicar el país donde aplica la regla")
        if scope == "ciudad" and not ciudad:
            raise ValueError("Debe indicar la ciudad para el ámbito 'ciudad'")
        if scope == "region" and not region:
            raise ValueError("Debe indicar la región para el ámbito 'region'")
        
        fecha_inicio = self.alert_start_dt.dateTime().toPyDateTime() if self.use_start_date_checkbox.isChecked() else None
        fecha_fin = self.alert_end_dt.dateTime().toPyDateTime() if self.use_end_date_checkbox.isChecked() else None
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin")
        
        self.parametros = {
            "nombre": nombre,
            "descripcion": descripcion,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "humidity_min": hum_min,
            "humidity_max": hum_max,
            "location_scope": scope,
            "pais": pais,
            "ciudad": ciudad if scope == "ciudad" else "",
            "region": region if scope == "region" else "",
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
            "prioridad": self.priority_spin.value()
        }
    
    def get_parametros(self) -> dict:
        return self.parametros


class ProcessResultsDialog(QDialog):
    """Dialog for displaying process execution results"""
    
    def __init__(self, execution: Execution, process_name: str = "", parent=None):
        super().__init__(parent)
        self.execution = execution
        self.process_name = process_name
        self.setWindowTitle(f"Resultados de Ejecución: {process_name}")
        self.setMinimumSize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Execution info
        info_group = QGroupBox("Información de Ejecución")
        info_layout = QVBoxLayout()
        
        estado_label = QLabel(f"Estado: {self.execution.estado.value if self.execution.estado else 'N/A'}")
        estado_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        info_layout.addWidget(estado_label)
        
        if self.execution.fecha_ejecucion:
            fecha_str = ""
            if isinstance(self.execution.fecha_ejecucion, datetime):
                fecha_str = self.execution.fecha_ejecucion.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fecha_str = str(self.execution.fecha_ejecucion)
            fecha_label = QLabel(f"Fecha de Ejecución: {fecha_str}")
            info_layout.addWidget(fecha_label)
        
        if self.execution.id:
            id_label = QLabel(f"ID de Ejecución: {self.execution.id}")
            info_layout.addWidget(id_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Error message (if failed)
        if self.execution.estado and self.execution.estado.value == "fallido":
            error_group = QGroupBox("Error")
            error_layout = QVBoxLayout()
            error_text = QTextEdit()
            error_text.setReadOnly(True)
            error_text.setMaximumHeight(150)
            error_text.setStyleSheet("background-color: #ffebee; color: #c62828;")
            error_msg = self.execution.error_message or "Error desconocido"
            error_text.setPlainText(error_msg)
            error_layout.addWidget(error_text)
            error_group.setLayout(error_layout)
            layout.addWidget(error_group)
        
        # Results (if completed)
        if self.execution.estado and self.execution.estado.value == "completado":
            if self.execution.resultado:
                results_group = QGroupBox("Resultados")
                results_layout = QVBoxLayout()
                
                # Create scrollable area for results
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll_content = QWidget()
                scroll_layout = QVBoxLayout()
                
                resultado = self.execution.resultado
                
                # Format results based on type
                if isinstance(resultado, dict):
                    tipo = resultado.get("tipo", "")
                    
                    if tipo in ["reporte_max_min", "informe_promedio"]:
                        # Report results
                        self._format_report_results(resultado, scroll_layout)
                    elif tipo == "consulta_online":
                        # Online query results
                        self._format_query_results(resultado, scroll_layout)
                    else:
                        # Generic JSON display
                        self._format_generic_results(resultado, scroll_layout)
                else:
                    # Generic display
                    result_text = QTextEdit()
                    result_text.setReadOnly(True)
                    result_text.setPlainText(str(resultado))
                    scroll_layout.addWidget(result_text)
                
                scroll_content.setLayout(scroll_layout)
                scroll.setWidget(scroll_content)
                results_layout.addWidget(scroll)
                results_group.setLayout(results_layout)
                layout.addWidget(results_group)
            else:
                # No results available
                no_results_group = QGroupBox("Resultados")
                no_results_layout = QVBoxLayout()
                no_results_label = QLabel("No hay resultados disponibles para esta ejecución.")
                no_results_label.setStyleSheet("color: gray; padding: 10px;")
                no_results_layout.addWidget(no_results_label)
                no_results_group.setLayout(no_results_layout)
                layout.addWidget(no_results_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def _format_report_results(self, resultado: dict, layout: QVBoxLayout):
        """Format report results (max/min or average)"""
        # Location info
        pais = resultado.get("pais")
        ciudad = resultado.get("ciudad")
        tipo = resultado.get("tipo")

        if pais or ciudad:
            if pais and ciudad:
                location_text = f"Ubicación: {ciudad}, {pais}"
            elif pais:
                location_text = f"Ubicación: {pais}"
            else:
                location_text = f"Ubicación: {ciudad}"
            location_label = QLabel(location_text)
            location_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(location_label)
        
        # Period info
        if "periodo" in resultado:
            periodo = resultado["periodo"]
            periodo_label = QLabel(
                f"Período: {periodo.get('inicio', 'N/A')} - {periodo.get('fin', 'N/A')}"
            )
            layout.addWidget(periodo_label)
        
        # Results table
        if "resultados" in resultado:
            resultados = resultado["resultados"]
            if isinstance(resultados, dict) and resultados:
                # Create table for statistics
                table = QTableWidget()
                table.setColumnCount(4)
                table.setHorizontalHeaderLabels(["Métrica", "Temperatura", "Humedad", "Unidad"])
                
                row = 0
                # Check if resultados has temperatura and humedad as direct keys (new format)
                if "temperatura" in resultados and "humedad" in resultados:
                    temp_stats = resultados.get("temperatura", {})
                    hum_stats = resultados.get("humedad", {})
                    stat_labels = {
                        "max": "Máximo",
                        "min": "Mínimo",
                        "avg": "Promedio",
                    }
                    if tipo == "reporte_max_min":
                        relevant_stats = ["max", "min"]
                    elif tipo in ["informe_promedio", "reporte_promedio"]:
                        relevant_stats = ["avg"]
                    else:
                        relevant_stats = ["max", "min", "avg"]

                    for stat_name in relevant_stats:
                        temp_val = temp_stats.get(stat_name) if isinstance(temp_stats, dict) else None
                        hum_val = hum_stats.get(stat_name) if isinstance(hum_stats, dict) else None
                        if temp_val is None and hum_val is None:
                            continue

                        table.insertRow(row)
                        table.setItem(row, 0, QTableWidgetItem(stat_labels.get(stat_name, stat_name.title())))
                        table.setItem(row, 1, QTableWidgetItem(f"{temp_val:.2f}" if temp_val is not None else "N/A"))
                        table.setItem(row, 2, QTableWidgetItem(f"{hum_val:.2f}" if hum_val is not None else "N/A"))
                        table.setItem(row, 3, QTableWidgetItem("°C / %"))
                        row += 1

                    # Add count if available and greater than zero
                    count_value = resultados.get("count")
                    if isinstance(count_value, int) and count_value > 0:
                        table.insertRow(row)
                        table.setItem(row, 0, QTableWidgetItem("Cantidad de Mediciones"))
                        table.setItem(row, 1, QTableWidgetItem(str(count_value)))
                        table.setItem(row, 2, QTableWidgetItem(""))
                        table.setItem(row, 3, QTableWidgetItem(""))
                        row += 1
                else:
                    # Old format - iterate through keys
                    for key, value in resultados.items():
                        if isinstance(value, dict):
                            temp = value.get("temperatura")
                            hum = value.get("humedad")
                            if temp is None and hum is None:
                                continue
                            table.insertRow(row)
                            table.setItem(row, 0, QTableWidgetItem(key.replace("_", " ").title()))
                            
                            table.setItem(row, 1, QTableWidgetItem(f"{temp:.2f}" if temp is not None and isinstance(temp, (int, float)) else "N/A"))
                            table.setItem(row, 2, QTableWidgetItem(f"{hum:.2f}" if hum is not None and isinstance(hum, (int, float)) else "N/A"))
                            table.setItem(row, 3, QTableWidgetItem("°C / %"))
                            row += 1
                
                if row > 0:
                    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                    table.setMaximumHeight(300)
                    layout.addWidget(table)
                else:
                    # No data to display
                    no_data_label = QLabel("No hay datos estadísticos disponibles")
                    no_data_label.setStyleSheet("color: gray; padding: 10px;")
                    layout.addWidget(no_data_label)
            else:
                # Display as JSON if not a dict
                result_text = QTextEdit()
                result_text.setReadOnly(True)
                result_text.setPlainText(json.dumps(resultados, indent=2, ensure_ascii=False, default=str))
                layout.addWidget(result_text)
    
    def _format_query_results(self, resultado: dict, layout: QVBoxLayout):
        """Format online query results with pagination"""
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton
        
        # Location info
        if "pais" in resultado or "ciudad" in resultado:
            location_label = QLabel(f"Ubicación: {resultado.get('ciudad', 'N/A')}, {resultado.get('pais', 'N/A')}")
            location_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(location_label)
        
        # Period info
        if "periodo" in resultado:
            periodo = resultado["periodo"]
            periodo_label = QLabel(
                f"Período: {periodo.get('inicio', 'N/A')} - {periodo.get('fin', 'N/A')}"
            )
            layout.addWidget(periodo_label)
        
        # Count
        cantidad = resultado.get("cantidad_mediciones", 0)
        count_label = QLabel(f"Total de Mediciones: {cantidad}")
        count_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(count_label)
        
        # Measurements table with pagination
        if "mediciones" in resultado:
            mediciones = resultado["mediciones"]
            if mediciones and isinstance(mediciones, list):
                # Pagination settings
                items_per_page = 100
                total_pages = (len(mediciones) + items_per_page - 1) // items_per_page if mediciones else 1
                current_page = [1]  # Use list to allow modification in nested function
                
                # Create table
                table = QTableWidget()
                table.setColumnCount(5)
                table.setHorizontalHeaderLabels(["Sensor ID", "Fecha", "Temperatura", "Humedad", "Unidad"])
                
                # Page info label
                page_info_label = QLabel()
                page_info_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
                
                # Create buttons first so they're accessible in update_table
                prev_btn = QPushButton("← Anterior")
                next_btn = QPushButton("Siguiente →")
                
                def update_table(page: int):
                    """Update table with measurements for the given page"""
                    table.setRowCount(0)  # Clear table
                    start_idx = (page - 1) * items_per_page
                    end_idx = min(start_idx + items_per_page, len(mediciones))
                    
                    for idx, medida in enumerate(mediciones[start_idx:end_idx]):
                        table_row = idx
                        table.insertRow(table_row)
                        table.setItem(table_row, 0, QTableWidgetItem(str(medida.get("sensor_id", "N/A"))))
                        
                        fecha = medida.get("timestamp") or medida.get("fecha")
                        if fecha:
                            if isinstance(fecha, datetime):
                                fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                fecha_str = str(fecha)
                        else:
                            fecha_str = "N/A"
                        table.setItem(table_row, 1, QTableWidgetItem(fecha_str))
                        
                        temp = medida.get("temperature") or medida.get("temperatura")
                        hum = medida.get("humidity") or medida.get("humedad")
                        
                        table.setItem(table_row, 2, QTableWidgetItem(f"{temp:.2f}" if temp is not None else "N/A"))
                        table.setItem(table_row, 3, QTableWidgetItem(f"{hum:.2f}" if hum is not None else "N/A"))
                        table.setItem(table_row, 4, QTableWidgetItem("°C / %"))
                    
                    # Update page info
                    page_info_label.setText(f"Página {page} de {total_pages} (Mostrando {start_idx + 1}-{end_idx} de {len(mediciones)})")
                    
                    # Update button states
                    prev_btn.setEnabled(page > 1)
                    next_btn.setEnabled(page < total_pages)
                
                # Initial table load
                update_table(1)
                
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table.setMaximumHeight(400)
                layout.addWidget(table)
                
                # Pagination controls (only show if more than 1 page)
                if total_pages > 1:
                    layout.addWidget(page_info_label)
                    
                    pagination_layout = QHBoxLayout()
                    pagination_layout.addStretch()
                    
                    def go_to_prev_page():
                        if current_page[0] > 1:
                            current_page[0] -= 1
                            update_table(current_page[0])
                    
                    def go_to_next_page():
                        if current_page[0] < total_pages:
                            current_page[0] += 1
                            update_table(current_page[0])
                    
                    prev_btn.clicked.connect(go_to_prev_page)
                    prev_btn.setEnabled(False)
                    pagination_layout.addWidget(prev_btn)
                    
                    next_btn.clicked.connect(go_to_next_page)
                    pagination_layout.addWidget(next_btn)
                    
                    pagination_layout.addStretch()
                    
                    pagination_widget = QWidget()
                    pagination_widget.setLayout(pagination_layout)
                    layout.addWidget(pagination_widget)
                else:
                    # Single page, just show info
                    page_info_label.setText(f"Mostrando todas las {len(mediciones)} mediciones")
                    layout.addWidget(page_info_label)
    
    def _format_generic_results(self, resultado: dict, layout: QVBoxLayout):
        """Format generic results as JSON"""
        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_text.setPlainText(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
        layout.addWidget(result_text)


class ProcessesWidget(QWidget):
    """Widget for viewing and managing processes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.process_controller = get_process_controller()
        self.init_ui()
        self.load_processes()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Procesos")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Available processes tab
        processes_container = QWidget()
        processes_layout = QVBoxLayout()
        self.processes_table = QTableWidget()
        self.processes_table.setColumnCount(5)
        self.processes_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Tipo", "Descripción", "Costo"
        ])
        self.processes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.processes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.processes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        processes_layout.addWidget(self.processes_table)
        processes_container.setLayout(processes_layout)
        self.tabs.addTab(processes_container, "Procesos Disponibles")
        
        # My requests tab
        requests_container = QWidget()
        requests_layout = QVBoxLayout()
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(5)
        self.requests_table.setHorizontalHeaderLabels([
            "ID", "ID Proceso", "Estado", "Fecha de Solicitud", "Parámetros"
        ])
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.requests_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.requests_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        requests_layout.addWidget(self.requests_table)
        requests_container.setLayout(requests_layout)
        self.tabs.addTab(requests_container, "Mis Solicitudes")
        
        # Scheduled processes tab
        scheduled_container = QWidget()
        scheduled_layout = QVBoxLayout()
        
        # Buttons for scheduled processes
        scheduled_btn_layout = QHBoxLayout()
        schedule_btn = QPushButton("Programar Proceso")
        schedule_btn.clicked.connect(self.show_schedule_dialog)
        scheduled_btn_layout.addWidget(schedule_btn)
        scheduled_btn_layout.addStretch()
        scheduled_layout.addLayout(scheduled_btn_layout)
        
        self.scheduled_table = QTableWidget()
        self.scheduled_table.setColumnCount(7)
        self.scheduled_table.setHorizontalHeaderLabels([
            "Proceso", "Tipo", "Próxima Ejecución", "Última Ejecución", "Estado", "Acciones", "ID"
        ])
        self.scheduled_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.scheduled_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.scheduled_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        scheduled_layout.addWidget(self.scheduled_table)
        scheduled_container.setLayout(scheduled_layout)
        self.tabs.addTab(scheduled_container, "Procesos Programados")
        
        # All requests tab (for técnicos/admins)
        user_role = self.session_manager.get_user_role()
        if user_role in ["administrador", "tecnico"]:
            all_requests_container = QWidget()
            all_requests_layout = QVBoxLayout()
            
            # Status filter
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel("Filtrar por estado:"))
            self.status_filter = QComboBox()
            self.status_filter.addItems(["Todos", "Pendiente", "En Progreso", "Completado", "Fallido"])
            self.status_filter.setCurrentText("Pendiente")
            self.status_filter.currentTextChanged.connect(self.load_all_requests)
            filter_layout.addWidget(self.status_filter)
            filter_layout.addStretch()
            all_requests_layout.addLayout(filter_layout)
            
            self.all_requests_table = QTableWidget()
            self.all_requests_table.setColumnCount(7)
            self.all_requests_table.setHorizontalHeaderLabels([
                "ID", "Usuario", "Email", "Proceso", "Estado", "Fecha de Solicitud", "Parámetros"
            ])
            self.all_requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.all_requests_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.all_requests_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            all_requests_layout.addWidget(self.all_requests_table)
            all_requests_container.setLayout(all_requests_layout)
            self.tabs.addTab(all_requests_container, "Todas las Solicitudes")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        request_btn = QPushButton("Solicitar Proceso Seleccionado")
        request_btn.clicked.connect(self.request_process)
        btn_layout.addWidget(request_btn)
        
        if user_role in ["administrador", "tecnico"]:
            execute_btn = QPushButton("Ejecutar Solicitud Seleccionada")
            execute_btn.clicked.connect(self.execute_selected_request)
            btn_layout.addWidget(execute_btn)
        
        view_result_btn = QPushButton("Ver Resultado")
        view_result_btn.clicked.connect(self.view_request_result)
        btn_layout.addWidget(view_result_btn)
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_processes)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_processes(self):
        try:
            processes = self.process_controller.list_processes(skip=0, limit=100)
            self.processes_table.setRowCount(len(processes))
            for row, process in enumerate(processes):
                self.processes_table.setItem(row, 0, QTableWidgetItem(str(process.id)))
                self.processes_table.setItem(row, 1, QTableWidgetItem(process.nombre))
                self.processes_table.setItem(row, 2, QTableWidgetItem(process.tipo.value if process.tipo else ""))
                self.processes_table.setItem(row, 3, QTableWidgetItem(process.descripcion or ""))
                self.processes_table.setItem(row, 4, QTableWidgetItem(f"${process.costo:.2f}"))

            self.load_scheduled_processes()

            user_id = self.session_manager.get_user_id()
            if user_id:
                requests = self.process_controller.get_user_requests(user_id, skip=0, limit=100)
                self.requests_table.setRowCount(len(requests))
                for row, request in enumerate(requests):
                    request_id = request.id
                    if not request_id:
                        import logging
                        logging.getLogger(__name__).warning("Process request without id: %s", request)
                        continue

                    self.requests_table.setItem(row, 0, QTableWidgetItem(str(request_id)))
                    self.requests_table.setItem(row, 1, QTableWidgetItem(str(request.process_id)))
                    self.requests_table.setItem(row, 2, QTableWidgetItem(request.estado.value if request.estado else ""))

                    fecha_str = ""
                    if request.estado and request.estado.value == "completado":
                        execution = self.process_controller.get_execution(request_id)
                        if execution and execution.fecha_ejecucion:
                            fecha_val = execution.fecha_ejecucion
                            if isinstance(fecha_val, datetime):
                                fecha_str = fecha_val.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                fecha_str = str(fecha_val)
                        if not fecha_str and request.fecha_solicitud:
                            fecha_val = request.fecha_solicitud
                            fecha_str = fecha_val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(fecha_val, datetime) else str(fecha_val)
                    elif request.fecha_solicitud:
                        fecha_val = request.fecha_solicitud
                        fecha_str = fecha_val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(fecha_val, datetime) else str(fecha_val)

                    self.requests_table.setItem(row, 3, QTableWidgetItem(fecha_str))
                    params_text = str(request.parametros) if request.parametros else ""
                    self.requests_table.setItem(row, 4, QTableWidgetItem(params_text))
            else:
                self.requests_table.setRowCount(0)

            if self.session_manager.get_user_role() in ["administrador", "tecnico"]:
                self.load_all_requests()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar procesos: {str(e)}")
    
    def load_all_requests(self):
        """Load all requests for técnicos/admins"""
        try:
            # Get status filter
            status_filter = None
            filter_text = self.status_filter.currentText()
            if filter_text == "Pendiente":
                status_filter = ProcessStatus.PENDING
            elif filter_text == "En Progreso":
                status_filter = ProcessStatus.IN_PROGRESS
            elif filter_text == "Completado":
                status_filter = ProcessStatus.COMPLETED
            elif filter_text == "Fallido":
                status_filter = ProcessStatus.FAILED
            
            # Load all requests
            all_requests = self.process_controller.list_all_requests(status=status_filter, skip=0, limit=100)
            self.all_requests_table.setRowCount(len(all_requests))
            
            for row, request in enumerate(all_requests):
                # Ensure request has a valid id
                request_id = request.get("id") or request.get("_id")
                if not request_id:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Request at row {row} has no ID: {request}")
                    continue
                
                request_id_str = str(request_id)
                if request_id_str.lower() in ['none', 'false', '', 'null']:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Request at row {row} has invalid ID: '{request_id_str}'")
                    continue
                
                self.all_requests_table.setItem(row, 0, QTableWidgetItem(request_id_str))
                
                user_info = request.get("user", {})
                self.all_requests_table.setItem(row, 1, QTableWidgetItem(user_info.get("nombre_completo", request.get("user_id", ""))))
                self.all_requests_table.setItem(row, 2, QTableWidgetItem(user_info.get("email", "N/A")))
                
                process_info = request.get("process", {})
                self.all_requests_table.setItem(row, 3, QTableWidgetItem(process_info.get("nombre", request.get("process_id", ""))))
                
                estado = request.get("estado")
                if isinstance(estado, ProcessStatus):
                    estado_str = estado.value
                else:
                    estado_str = str(estado) if estado else ""
                self.all_requests_table.setItem(row, 4, QTableWidgetItem(estado_str))
                
                fecha_solicitud = request.get("fecha_solicitud")
                fecha_str = ""
                if fecha_solicitud:
                    if isinstance(fecha_solicitud, datetime):
                        fecha_str = fecha_solicitud.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        fecha_str = str(fecha_solicitud)
                self.all_requests_table.setItem(row, 5, QTableWidgetItem(fecha_str))
                
                params = request.get("parametros", {})
                params_text = str(params) if params else ""
                self.all_requests_table.setItem(row, 6, QTableWidgetItem(params_text))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar todas las solicitudes: {str(e)}")
    
    def request_process(self):
        current_row = self.processes_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error de Selección", "Por favor seleccione un proceso para solicitar")
            return
        
        process_id = self.processes_table.item(current_row, 0).text()
        
        try:
            user_id = self.session_manager.get_user_id()
            if not user_id:
                QMessageBox.warning(self, "Error", "Usuario no conectado")
                return
            
            # Get process details
            process = self.process_controller.get_process(process_id)
            
            if not process:
                QMessageBox.warning(self, "Error", "Proceso no encontrado")
                return
            
            # Show dialog to collect parameters
            dialog = ProcessRequestDialog(process, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            # Get parameters from dialog
            parametros = dialog.get_parametros()
            
            # Create the request
            request_data = ProcessRequestCreate(
                process_id=process_id,
                parametros=parametros
            )
            self.process_controller.request_process(user_id, request_data)
            QMessageBox.information(self, "Éxito", "Solicitud de proceso enviada exitosamente")
            self.load_processes()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al solicitar proceso: {str(e)}")
    
    def execute_selected_request(self):
        """Execute a selected process request (admin/tecnico only)"""
        # Check which table is active
        current_tab = self.tabs.currentIndex()
        current_tab_text = self.tabs.tabText(current_tab) if current_tab >= 0 else ""
        
        # Check if we're in "Todas las Solicitudes" tab (index 3 after adding scheduled processes tab)
        if current_tab_text == "Todas las Solicitudes" and hasattr(self, 'all_requests_table'):
            # All requests tab (for técnicos)
            current_row = self.all_requests_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Error de Selección", "Por favor seleccione una solicitud de proceso para ejecutar")
                return
            request_id = self.all_requests_table.item(current_row, 0).text()
        else:
            # My requests tab - técnicos should not execute from here
            QMessageBox.warning(self, "Error", "Para ejecutar solicitudes, use la pestaña 'Todas las Solicitudes'")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Ejecución",
            f"¿Ejecutar solicitud de proceso {request_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                execution = self.process_controller.execute_request(request_id)
                
                # Get process name for display
                request_obj = self.process_controller.get_request(request_id)
                process_name = ""
                if request_obj:
                    process = self.process_controller.get_process(request_obj.process_id)
                    if process:
                        process_name = process.nombre
                
                # Show results dialog
                results_dialog = ProcessResultsDialog(execution, process_name, self)
                results_dialog.exec()
                
                self.load_processes()
                self.load_all_requests()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al ejecutar proceso: {str(e)}")
    
    def view_request_result(self, request_id: str = None):
        """View results for a completed request"""
        import logging
        logger = logging.getLogger(__name__)
        
        # PyQt button clicked signal passes False, so treat False as None
        if request_id is False or request_id is None:
            request_id = None
        
        # Get request_id from parameter or from selected row
        if request_id is None:
            # Try to get from current selection
            current_tab = self.tabs.currentIndex()
            current_tab_text = self.tabs.tabText(current_tab) if current_tab >= 0 else ""
            
            if current_tab_text == "Mis Solicitudes":
                current_row = self.requests_table.currentRow()
                if current_row < 0:
                    QMessageBox.warning(self, "Error de Selección", "Por favor seleccione una solicitud para ver sus resultados")
                    return
                table_item = self.requests_table.item(current_row, 0)
                if not table_item:
                    QMessageBox.warning(self, "Error", "No se pudo obtener el ID de la solicitud desde la tabla")
                    logger.error(f"Table item is None at row {current_row}, column 0")
                    return
                request_id = table_item.text()
                logger.debug(f"Retrieved request_id from table: '{request_id}' (type: {type(request_id)})")
            elif current_tab_text == "Todas las Solicitudes" and hasattr(self, 'all_requests_table'):
                current_row = self.all_requests_table.currentRow()
                if current_row < 0:
                    QMessageBox.warning(self, "Error de Selección", "Por favor seleccione una solicitud para ver sus resultados")
                    return
                table_item = self.all_requests_table.item(current_row, 0)
                if not table_item:
                    QMessageBox.warning(self, "Error", "No se pudo obtener el ID de la solicitud desde la tabla")
                    logger.error(f"Table item is None at row {current_row}, column 0")
                    return
                request_id = table_item.text()
                logger.debug(f"Retrieved request_id from all_requests table: '{request_id}' (type: {type(request_id)})")
            else:
                QMessageBox.warning(self, "Error", "Por favor seleccione una solicitud completada")
                return
        
        # Validate request_id before using it
        if not request_id:
            logger.error(f"Invalid request_id: {request_id} (type: {type(request_id)})")
            QMessageBox.warning(self, "Error", f"ID de solicitud inválido: {request_id}")
            return
        
        # Ensure it's a string and clean it
        request_id = str(request_id).strip()
        
        # Check for invalid values
        if request_id.lower() in ['none', 'false', '', 'null']:
            logger.error(f"Invalid request_id after cleaning: '{request_id}'")
            QMessageBox.warning(self, "Error", f"ID de solicitud inválido: '{request_id}'")
            return
        
        logger.info(f"Viewing results for request_id: {request_id}")
        
        try:
            # Get execution
            execution = self.process_controller.get_execution(request_id)
            if not execution:
                QMessageBox.warning(self, "Error", "No se encontraron resultados de ejecución para esta solicitud")
                return
            
            # Check if resultado exists
            if execution.resultado is None:
                QMessageBox.information(
                    self, 
                    "Información", 
                    f"La ejecución se completó pero no hay resultados almacenados.\n"
                    f"Estado: {execution.estado.value if execution.estado else 'N/A'}\n"
                    f"ID Ejecución: {execution.id}\n\n"
                    f"Esto puede ocurrir si no hay datos de mediciones para los parámetros especificados."
                )
                return
            
            # Get process name
            request_obj = self.process_controller.get_request(request_id)
            process_name = ""
            if request_obj:
                process = self.process_controller.get_process(request_obj.process_id)
                if process:
                    process_name = process.nombre
            
            # Show results dialog
            results_dialog = ProcessResultsDialog(execution, process_name, self)
            results_dialog.exec()
        
        except Exception as e:
            logger.error(f"Error viewing request result: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al cargar resultados: {str(e)}")
    
    def load_scheduled_processes(self):
        """Load scheduled processes for the current user"""
        try:
            user_id = self.session_manager.get_user_id()
            if not user_id:
                self.scheduled_table.setRowCount(0)
                return
            
            schedules = self.process_controller.list_schedules(user_id, skip=0, limit=100)
            
            self.scheduled_table.setRowCount(len(schedules))
            for row, schedule in enumerate(schedules):
                # Get process name
                process = self.process_controller.get_process(schedule.process_id)
                process_name = process.nombre if process else f"Proceso {schedule.process_id[:8]}"
                
                # Schedule type
                type_map = {
                    ScheduleType.DAILY: "Diario",
                    ScheduleType.WEEKLY: "Semanal",
                    ScheduleType.MONTHLY: "Mensual",
                    ScheduleType.ANNUAL: "Anual"
                }
                type_str = type_map.get(schedule.schedule_type, schedule.schedule_type.value)
                
                self.scheduled_table.setItem(row, 0, QTableWidgetItem(process_name))
                self.scheduled_table.setItem(row, 1, QTableWidgetItem(type_str))
                
                # Next execution
                next_exec_str = ""
                if schedule.next_execution:
                    if isinstance(schedule.next_execution, datetime):
                        next_exec_str = schedule.next_execution.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        next_exec_str = str(schedule.next_execution)
                self.scheduled_table.setItem(row, 2, QTableWidgetItem(next_exec_str))
                
                # Last execution
                last_exec_str = "Nunca"
                if schedule.last_execution:
                    if isinstance(schedule.last_execution, datetime):
                        last_exec_str = schedule.last_execution.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        last_exec_str = str(schedule.last_execution)
                self.scheduled_table.setItem(row, 3, QTableWidgetItem(last_exec_str))
                
                # Status
                status_str = "Activo" if schedule.status == ScheduleStatus.ACTIVE else "Pausado"
                self.scheduled_table.setItem(row, 4, QTableWidgetItem(status_str))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("Editar")
                edit_btn.clicked.connect(lambda checked, s=schedule: self.edit_schedule(s))
                actions_layout.addWidget(edit_btn)
                
                pause_resume_text = "Pausar" if schedule.status == ScheduleStatus.ACTIVE else "Reanudar"
                pause_resume_btn = QPushButton(pause_resume_text)
                pause_resume_btn.clicked.connect(lambda checked, s=schedule: self.pause_resume_schedule(s))
                actions_layout.addWidget(pause_resume_btn)
                
                delete_btn = QPushButton("Eliminar")
                delete_btn.setStyleSheet("background-color: #dc3545; color: white;")
                delete_btn.clicked.connect(lambda checked, s=schedule: self.delete_schedule(s))
                actions_layout.addWidget(delete_btn)
                
                actions_widget.setLayout(actions_layout)
                self.scheduled_table.setCellWidget(row, 5, actions_widget)
                
                # Store schedule ID
                self.scheduled_table.setItem(row, 6, QTableWidgetItem(str(schedule.id)))
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar procesos programados: {str(e)}")
            self.scheduled_table.setRowCount(0)
    
    def show_schedule_dialog(self):
        """Show dialog to create a new scheduled process"""
        dialog = ScheduleProcessDialog(self, controller=self.process_controller)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_scheduled_processes()
    
    def edit_schedule(self, schedule):
        """Edit an existing scheduled process"""
        dialog = EditScheduleDialog(schedule, self, controller=self.process_controller)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_scheduled_processes()
    
    def pause_resume_schedule(self, schedule):
        """Pause or resume a scheduled process"""
        try:
            if schedule.status == ScheduleStatus.ACTIVE:
                self.process_controller.pause_schedule(schedule.id)
                QMessageBox.information(self, "Éxito", "Proceso programado pausado")
            else:
                self.process_controller.resume_schedule(schedule.id)
                QMessageBox.information(self, "Éxito", "Proceso programado reanudado")
            
            self.load_scheduled_processes()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cambiar estado: {str(e)}")
    
    def delete_schedule(self, schedule):
        """Delete a scheduled process"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el proceso programado '{schedule.id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.process_controller.delete_schedule(schedule.id)
                QMessageBox.information(self, "Éxito", "Proceso programado eliminado")
                self.load_scheduled_processes()
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")


class ScheduleProcessDialog(QDialog):
    """Dialog for creating a new scheduled process"""
    
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.process_controller = controller or get_process_controller()
        self.setWindowTitle("Programar Proceso")
        self.setMinimumWidth(500)
        self.schedule_data = None
        self.process_lookup: Dict[str, Process] = {}
        self.city_required = True
        self.init_ui()
        self.load_processes()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Process selection
        layout.addWidget(QLabel("Proceso:"))
        self.process_combo = QComboBox()
        self.process_combo.currentIndexChanged.connect(self._on_process_changed)
        layout.addWidget(self.process_combo)
        
        # Parameters (same as ProcessRequestDialog)
        params_group = QGroupBox("Parámetros")
        params_layout = QVBoxLayout()
        
        params_layout.addWidget(QLabel("País *:"))
        self.pais_edit = QLineEdit()
        self.pais_edit.setPlaceholderText("Ej: Argentina")
        params_layout.addWidget(self.pais_edit)
        
        self.ciudad_label = QLabel("Ciudad *:")
        params_layout.addWidget(self.ciudad_label)
        self.ciudad_edit = QLineEdit()
        self.ciudad_edit.setPlaceholderText("Ej: Buenos Aires")
        params_layout.addWidget(self.ciudad_edit)
        
        params_layout.addWidget(QLabel("Fecha Inicio *:"))
        self.fecha_inicio_edit = QDateTimeEdit()
        self.fecha_inicio_edit.setCalendarPopup(True)
        self.fecha_inicio_edit.setDateTime(QDateTime.currentDateTime().addDays(-30))
        self.fecha_inicio_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        params_layout.addWidget(self.fecha_inicio_edit)
        
        params_layout.addWidget(QLabel("Fecha Fin *:"))
        self.fecha_fin_edit = QDateTimeEdit()
        self.fecha_fin_edit.setCalendarPopup(True)
        self.fecha_fin_edit.setDateTime(QDateTime.currentDateTime())
        self.fecha_fin_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        params_layout.addWidget(self.fecha_fin_edit)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Schedule type
        schedule_group = QGroupBox("Tipo de Programación")
        schedule_layout = QVBoxLayout()
        
        self.schedule_type_group = QButtonGroup()
        self.daily_radio = QRadioButton("Diario")
        self.daily_radio.setChecked(True)
        self.daily_radio.toggled.connect(self.on_schedule_type_changed)
        self.schedule_type_group.addButton(self.daily_radio, 0)
        schedule_layout.addWidget(self.daily_radio)
        
        self.weekly_radio = QRadioButton("Semanal")
        self.weekly_radio.toggled.connect(self.on_schedule_type_changed)
        self.schedule_type_group.addButton(self.weekly_radio, 1)
        schedule_layout.addWidget(self.weekly_radio)
        
        self.monthly_radio = QRadioButton("Mensual")
        self.monthly_radio.toggled.connect(self.on_schedule_type_changed)
        self.schedule_type_group.addButton(self.monthly_radio, 2)
        schedule_layout.addWidget(self.monthly_radio)
        
        self.annual_radio = QRadioButton("Anual")
        self.annual_radio.toggled.connect(self.on_schedule_type_changed)
        self.schedule_type_group.addButton(self.annual_radio, 3)
        schedule_layout.addWidget(self.annual_radio)
        
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)
        
        # Schedule configuration
        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout()
        self.config_widget.setLayout(self.config_layout)
        layout.addWidget(self.config_widget)
        
        # Time selection (common to all types)
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Hora:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setDisplayFormat("HH:mm")
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        self.config_layout.addLayout(time_layout)
        
        # Update config widget for daily (default)
        self.on_schedule_type_changed()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        create_btn = QPushButton("Programar")
        create_btn.clicked.connect(self.create_schedule)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_processes(self):
        """Load available processes"""
        try:
            processes = self.process_controller.list_processes(skip=0, limit=100)
            
            self.process_combo.clear()
            self.process_lookup.clear()
            for process in processes:
                self.process_combo.addItem(process.nombre, process.id)
                self.process_lookup[process.id] = process
            
            current_id = self.process_combo.currentData()
            self._update_city_requirement_by_process(current_id)
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar procesos: {str(e)}")
    
    def _on_process_changed(self, index: int):
        process_id = self.process_combo.itemData(index)
        self._update_city_requirement_by_process(process_id)

    def _update_city_requirement_by_process(self, process_id: Optional[str]):
        process = self.process_lookup.get(process_id)
        if not process and process_id:
            try:
                process = self.process_controller.get_process(process_id)
            except Exception:
                process = None
        self.city_required = True
        if process and process.tipo in {
            ProcessType.TEMP_MAX_MIN_REPORT,
            ProcessType.TEMP_AVG_REPORT,
        }:
            self.city_required = False
        label_text = "Ciudad *:" if self.city_required else "Ciudad (Opcional):"
        self.ciudad_label.setText(label_text)
        placeholder = "Ej: Buenos Aires" if self.city_required else "Ej: Buenos Aires (opcional)"
        self.ciudad_edit.setPlaceholderText(placeholder)
        if not self.city_required and not self.ciudad_edit.text().strip():
            self.ciudad_edit.clear()

    def on_schedule_type_changed(self):
        """Update configuration widget based on schedule type"""
        # Clear existing config widgets (except time)
        while self.config_layout.count() > 1:  # Keep time layout
            item = self.config_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        if self.weekly_radio.isChecked():
            # Weekly: day of week
            day_layout = QHBoxLayout()
            day_layout.addWidget(QLabel("Día de la semana:"))
            self.day_combo = QComboBox()
            self.day_combo.addItems(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
            day_layout.addWidget(self.day_combo)
            day_layout.addStretch()
            self.config_layout.addLayout(day_layout)
        
        elif self.monthly_radio.isChecked():
            # Monthly: day of month
            day_layout = QHBoxLayout()
            day_layout.addWidget(QLabel("Día del mes (1-31):"))
            self.day_spin = QSpinBox()
            self.day_spin.setRange(1, 31)
            self.day_spin.setValue(1)
            day_layout.addWidget(self.day_spin)
            day_layout.addStretch()
            self.config_layout.addLayout(day_layout)
        
        elif self.annual_radio.isChecked():
            # Annual: month and day
            month_layout = QHBoxLayout()
            month_layout.addWidget(QLabel("Mes:"))
            self.month_combo = QComboBox()
            self.month_combo.addItems([
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ])
            month_layout.addWidget(self.month_combo)
            month_layout.addStretch()
            self.config_layout.addLayout(month_layout)
            
            day_layout = QHBoxLayout()
            day_layout.addWidget(QLabel("Día del mes (1-31):"))
            self.annual_day_spin = QSpinBox()
            self.annual_day_spin.setRange(1, 31)
            self.annual_day_spin.setValue(1)
            day_layout.addWidget(self.annual_day_spin)
            day_layout.addStretch()
            self.config_layout.addLayout(day_layout)
    
    def create_schedule(self):
        """Create the scheduled process"""
        try:
            # Validate process selection
            process_id = self.process_combo.currentData()
            if not process_id:
                QMessageBox.warning(self, "Error", "Por favor seleccione un proceso")
                return
            
            # Validate parameters
            self._update_city_requirement_by_process(process_id)
            pais = self.pais_edit.text().strip()
            ciudad = self.ciudad_edit.text().strip()
            
            if not pais:
                QMessageBox.warning(self, "Error", "Por favor complete todos los campos requeridos")
                return
            if self.city_required and not ciudad:
                QMessageBox.warning(self, "Error", "Por favor ingrese la ciudad")
                return
            
            fecha_inicio = self.fecha_inicio_edit.dateTime().toPyDateTime()
            fecha_fin = self.fecha_fin_edit.dateTime().toPyDateTime()
            
            if fecha_inicio >= fecha_fin:
                QMessageBox.warning(self, "Error", "La fecha de inicio debe ser anterior a la fecha de fin")
                return
            
            # Build parameters
            parametros = {
                "pais": pais,
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            }
            if ciudad:
                parametros["ciudad"] = ciudad
            
            # Determine schedule type
            if self.daily_radio.isChecked():
                schedule_type = ScheduleType.DAILY
                schedule_config = {}
            elif self.weekly_radio.isChecked():
                schedule_type = ScheduleType.WEEKLY
                day_of_week = self.day_combo.currentIndex()  # 0=Monday, 6=Sunday
                schedule_config = {"day_of_week": day_of_week}
            elif self.monthly_radio.isChecked():
                schedule_type = ScheduleType.MONTHLY
                day_of_month = self.day_spin.value()
                schedule_config = {"day_of_month": day_of_month}
            else:  # annual
                schedule_type = ScheduleType.ANNUAL
                month = self.month_combo.currentIndex() + 1  # 1-12
                day_of_month = self.annual_day_spin.value()
                schedule_config = {"month": month, "day_of_month": day_of_month}
            
            # Get time
            time = self.time_edit.time()
            schedule_config["hour"] = time.hour()
            schedule_config["minute"] = time.minute()
            
            # Create schedule
            schedule_data = ScheduledProcessCreate(
                process_id=process_id,
                parametros=parametros,
                schedule_type=schedule_type,
                schedule_config=schedule_config
            )
            
            # Save to database
            user_id = SessionManager.get_instance().get_user_id()
            if not user_id:
                QMessageBox.warning(self, "Error", "Usuario no conectado")
                return
            
            self.process_controller.create_schedule(user_id, schedule_data)
            
            QMessageBox.information(self, "Éxito", "Proceso programado correctamente")
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al programar proceso: {str(e)}")


class EditScheduleDialog(ScheduleProcessDialog):
    """Dialog for editing an existing scheduled process"""
    
    def __init__(self, schedule, parent=None, controller=None):
        self.schedule = schedule
        super().__init__(parent, controller=controller)
        self.setWindowTitle("Editar Proceso Programado")
        self.load_schedule_data()
    
    def load_schedule_data(self):
        """Load existing schedule data into the form"""
        # Load process
        process = self.process_controller.get_process(self.schedule.process_id)
        
        if process:
            index = self.process_combo.findData(process.id)
            if index >= 0:
                self.process_combo.setCurrentIndex(index)
                self._update_city_requirement_by_process(process.id)
        
        # Load parameters
        if "pais" in self.schedule.parametros:
            self.pais_edit.setText(str(self.schedule.parametros["pais"]))
        if "ciudad" in self.schedule.parametros:
            self.ciudad_edit.setText(str(self.schedule.parametros["ciudad"]))
        if "fecha_inicio" in self.schedule.parametros:
            try:
                fecha_inicio = datetime.fromisoformat(self.schedule.parametros["fecha_inicio"].replace("Z", "+00:00"))
                self.fecha_inicio_edit.setDateTime(QDateTime.fromPyDateTime(fecha_inicio))
            except:
                pass
        if "fecha_fin" in self.schedule.parametros:
            try:
                fecha_fin = datetime.fromisoformat(self.schedule.parametros["fecha_fin"].replace("Z", "+00:00"))
                self.fecha_fin_edit.setDateTime(QDateTime.fromPyDateTime(fecha_fin))
            except:
                pass
        
        # Load schedule type and config
        if self.schedule.schedule_type == ScheduleType.DAILY:
            self.daily_radio.setChecked(True)
        elif self.schedule.schedule_type == ScheduleType.WEEKLY:
            self.weekly_radio.setChecked(True)
            self.on_schedule_type_changed()
            if "day_of_week" in self.schedule.schedule_config:
                self.day_combo.setCurrentIndex(self.schedule.schedule_config["day_of_week"])
        elif self.schedule.schedule_type == ScheduleType.MONTHLY:
            self.monthly_radio.setChecked(True)
            self.on_schedule_type_changed()
            if "day_of_month" in self.schedule.schedule_config:
                self.day_spin.setValue(self.schedule.schedule_config["day_of_month"])
        elif self.schedule.schedule_type == ScheduleType.ANNUAL:
            self.annual_radio.setChecked(True)
            self.on_schedule_type_changed()
            if "month" in self.schedule.schedule_config:
                self.month_combo.setCurrentIndex(self.schedule.schedule_config["month"] - 1)
            if "day_of_month" in self.schedule.schedule_config:
                self.annual_day_spin.setValue(self.schedule.schedule_config["day_of_month"])
        
        # Load time
        hour = self.schedule.schedule_config.get("hour", 9)
        minute = self.schedule.schedule_config.get("minute", 0)
        self.time_edit.setTime(QTime(hour, minute))
    
    def create_schedule(self):
        """Update the scheduled process"""
        try:
            # Validate process selection
            process_id = self.process_combo.currentData()
            if not process_id:
                QMessageBox.warning(self, "Error", "Por favor seleccione un proceso")
                return
            
            self._update_city_requirement_by_process(process_id)
            # Validate parameters
            pais = self.pais_edit.text().strip()
            ciudad = self.ciudad_edit.text().strip()
            
            if not pais:
                QMessageBox.warning(self, "Error", "Por favor complete todos los campos requeridos")
                return
            if self.city_required and not ciudad:
                QMessageBox.warning(self, "Error", "Por favor ingrese la ciudad")
                return
            
            fecha_inicio = self.fecha_inicio_edit.dateTime().toPyDateTime()
            fecha_fin = self.fecha_fin_edit.dateTime().toPyDateTime()
            
            if fecha_inicio >= fecha_fin:
                QMessageBox.warning(self, "Error", "La fecha de inicio debe ser anterior a la fecha de fin")
                return
            
            # Build parameters
            parametros = {
                "pais": pais,
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            }
            if ciudad:
                parametros["ciudad"] = ciudad
            
            # Determine schedule type
            if self.daily_radio.isChecked():
                schedule_type = ScheduleType.DAILY
                schedule_config = {}
            elif self.weekly_radio.isChecked():
                schedule_type = ScheduleType.WEEKLY
                day_of_week = self.day_combo.currentIndex()
                schedule_config = {"day_of_week": day_of_week}
            elif self.monthly_radio.isChecked():
                schedule_type = ScheduleType.MONTHLY
                day_of_month = self.day_spin.value()
                schedule_config = {"day_of_month": day_of_month}
            else:  # annual
                schedule_type = ScheduleType.ANNUAL
                month = self.month_combo.currentIndex() + 1
                day_of_month = self.annual_day_spin.value()
                schedule_config = {"month": month, "day_of_month": day_of_month}
            
            # Get time
            time = self.time_edit.time()
            schedule_config["hour"] = time.hour()
            schedule_config["minute"] = time.minute()
            
            # Update schedule
            update_data = ScheduledProcessUpdate(
                parametros=parametros,
                schedule_type=schedule_type,
                schedule_config=schedule_config
            )
            
            self.process_controller.update_schedule(self.schedule.id, update_data)
            
            QMessageBox.information(self, "Éxito", "Proceso programado actualizado correctamente")
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar proceso programado: {str(e)}")
    