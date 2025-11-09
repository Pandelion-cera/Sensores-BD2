"""
Alerts widget for viewing and managing alerts
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QLineEdit, QComboBox, QDateEdit, QHeaderView, QAbstractItemView,
    QDialog, QDialogButtonBox, QTextEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from datetime import datetime
from typing import Optional

from desktop_app.controllers import get_alert_controller
from desktop_app.models.alert_models import Alert, AlertStatus, AlertType
from desktop_app.utils.session_manager import SessionManager


class AlertsWidget(QWidget):
    """Widget for viewing and managing alerts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.alert_controller = get_alert_controller()
        self.init_ui()
        self.load_alerts()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Alertas")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Filters
        filter_group = QGroupBox("Filtros")
        filter_layout = QVBoxLayout()
        
        # First row
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Estado:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["", "activa", "finalizada"])
        row1.addWidget(self.status_filter)
        
        row1.addWidget(QLabel("Tipo:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["", "sensor", "climatica", "umbral", "proceso_ejecutado"])
        row1.addWidget(self.type_filter)
        
        row1.addWidget(QLabel("ID Sensor:"))
        self.sensor_id_filter = QLineEdit()
        self.sensor_id_filter.setPlaceholderText("Filtrar por ID de sensor")
        row1.addWidget(self.sensor_id_filter)
        filter_layout.addLayout(row1)
        
        # Second row - dates
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Fecha Inicio:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        row2.addWidget(self.start_date)
        
        row2.addWidget(QLabel("Fecha Fin:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        row2.addWidget(self.end_date)
        filter_layout.addLayout(row2)
        
        # Buttons
        btn_layout = QHBoxLayout()
        filter_btn = QPushButton("Aplicar Filtros")
        filter_btn.clicked.connect(self.load_alerts)
        btn_layout.addWidget(filter_btn)
        
        clear_btn = QPushButton("Limpiar Filtros")
        clear_btn.clicked.connect(self.clear_filters)
        btn_layout.addWidget(clear_btn)
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_alerts)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        filter_layout.addLayout(btn_layout)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Stats
        self.stats_label = QLabel("Cargando alertas...")
        layout.addWidget(self.stats_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tipo", "ID Sensor", "Descripción", "Valor", "Umbral", "Estado", "Fecha"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # Connect double-click to show details
        self.table.itemDoubleClicked.connect(self.show_alert_details)
        layout.addWidget(self.table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        details_btn = QPushButton("Ver Detalles")
        details_btn.clicked.connect(self.show_selected_alert_details)
        action_layout.addWidget(details_btn)
        resolve_btn = QPushButton("Marcar como Resuelta")
        resolve_btn.clicked.connect(self.resolve_selected_alert)
        action_layout.addWidget(resolve_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
    
    def clear_filters(self):
        self.status_filter.setCurrentIndex(0)
        self.type_filter.setCurrentIndex(0)
        self.sensor_id_filter.clear()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date.setDate(QDate.currentDate())
        self.load_alerts()
    
    def load_alerts(self):
        try:
            # Get filters
            status_str = self.status_filter.currentText()
            status = AlertStatus(status_str) if status_str else None
            
            type_str = self.type_filter.currentText()
            # Convert to string for repository (it expects string, not enum)
            tipo_str = type_str if type_str else None
            
            sensor_id = self.sensor_id_filter.text().strip() or None
            
            start_qdate = self.start_date.date()
            end_qdate = self.end_date.date()
            start_date = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
            end_date = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
            
            # Filter by user_id unless user is admin
            user_id = None
            user_role = self.session_manager.get_user_role()
            if user_role != "administrador":
                user_id = self.session_manager.get_user_id()
            
            alerts = self.alert_controller.list_alerts(
                skip=0,
                limit=1000,
                estado=status,
                tipo=tipo_str,
                sensor_id=sensor_id,
                user_id=user_id,
                fecha_desde=start_date,
                fecha_hasta=end_date
            )
            
            # Update stats
            active_count = len([a for a in alerts if a.estado == AlertStatus.ACTIVE])
            total_count = len(alerts)
            self.stats_label.setText(f"Total: {total_count} alertas ({active_count} activas)")
            
            # Store alerts for detail view
            self.alerts = alerts
            
            # Update table
            self.table.setRowCount(len(alerts))
            for row, alert in enumerate(alerts):
                self.table.setItem(row, 0, QTableWidgetItem(str(alert.id)))
                self.table.setItem(row, 1, QTableWidgetItem(alert.tipo.value if alert.tipo else ""))
                # Show sensor_id or process_id depending on alert type
                sensor_or_process = str(alert.sensor_id) if alert.sensor_id else (str(alert.process_id) if hasattr(alert, 'process_id') and alert.process_id else "N/A")
                self.table.setItem(row, 2, QTableWidgetItem(sensor_or_process))
                self.table.setItem(row, 3, QTableWidgetItem(alert.descripcion or ""))
                self.table.setItem(row, 4, QTableWidgetItem(str(alert.valor) if alert.valor else ""))
                self.table.setItem(row, 5, QTableWidgetItem(str(alert.umbral) if alert.umbral else ""))
                self.table.setItem(row, 6, QTableWidgetItem(alert.estado.value if alert.estado else ""))
                
                fecha_str = ""
                if alert.fecha_hora:
                    if isinstance(alert.fecha_hora, datetime):
                        fecha_str = alert.fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        fecha_str = str(alert.fecha_hora)
                self.table.setItem(row, 7, QTableWidgetItem(fecha_str))
                
                # Color code by status
                if alert.estado == AlertStatus.ACTIVE:
                    for col in range(8):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(QColor(Qt.GlobalColor.red).lighter(180))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar alertas: {str(e)}")
            self.table.setRowCount(0)
    
    def resolve_selected_alert(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error de Selección", "Por favor seleccione una alerta para resolver")
            return
        
        alert_id = self.table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Marcar alerta {alert_id} como resuelta?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                alert = self.alert_controller.get_alert(alert_id)
                if alert:
                    self.alert_controller.resolve_alert(alert_id)
                    QMessageBox.information(self, "Éxito", "Alerta marcada como resuelta")
                    self.load_alerts()
                else:
                    QMessageBox.warning(self, "Error", "Alerta no encontrada")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al resolver alerta: {str(e)}")
    
    def show_alert_details(self, item: QTableWidgetItem):
        """Show alert details dialog (called on double-click)"""
        row = item.row()
        if row < 0 or row >= len(self.alerts):
            return
        
        alert = self.alerts[row]
        dialog = AlertDetailDialog(alert, self, controller=self.alert_controller)
        dialog.exec()
    
    def show_selected_alert_details(self):
        """Show alert details dialog for selected row (called from button)"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error de Selección", "Por favor seleccione una alerta para ver sus detalles")
            return
        
        if current_row >= len(self.alerts):
            return
        
        alert = self.alerts[current_row]
        dialog = AlertDetailDialog(alert, self, controller=self.alert_controller)
        dialog.exec()


class AlertDetailDialog(QDialog):
    """Dialog for showing alert details"""
    
    def __init__(self, alert: Alert, parent=None, controller=None):
        super().__init__(parent)
        self.alert = alert
        self.alert_controller = controller or get_alert_controller()
        self.setWindowTitle(f"Detalles de Alerta #{alert.id}")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Basic info
        basic_group = QGroupBox("Información Básica")
        basic_layout = QFormLayout()
        
        basic_layout.addRow("ID:", QLabel(str(self.alert.id)))
        basic_layout.addRow("Tipo:", QLabel(self.alert.tipo.value if self.alert.tipo else "N/A"))
        basic_layout.addRow("Estado:", QLabel(self.alert.estado.value if self.alert.estado else "N/A"))
        
        fecha_str = ""
        if self.alert.fecha_hora:
            if isinstance(self.alert.fecha_hora, datetime):
                fecha_str = self.alert.fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fecha_str = str(self.alert.fecha_hora)
        basic_layout.addRow("Fecha y Hora:", QLabel(fecha_str))
        
        if self.alert.prioridad:
            prioridad_label = QLabel(str(self.alert.prioridad))
            # Color code by priority
            if self.alert.prioridad >= 4:
                prioridad_label.setStyleSheet("color: #e74c3c; font-weight: bold;")  # Red for high priority
            elif self.alert.prioridad == 3:
                prioridad_label.setStyleSheet("color: #f39c12; font-weight: bold;")  # Orange for medium-high
            else:
                prioridad_label.setStyleSheet("color: #27ae60;")  # Green for low-medium
            basic_layout.addRow("Prioridad:", prioridad_label)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Description
        desc_group = QGroupBox("Descripción")
        desc_layout = QVBoxLayout()
        desc_label = QLabel(self.alert.descripcion or "Sin descripción")
        desc_label.setWordWrap(True)
        desc_layout.addWidget(desc_label)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # Sensor/Process info
        if self.alert.sensor_id:
            sensor_group = QGroupBox("Información del Sensor")
            sensor_layout = QFormLayout()
            sensor_layout.addRow("ID Sensor:", QLabel(str(self.alert.sensor_id)))
            
            # Try to get sensor details
            sensor = self.alert_controller.get_sensor(self.alert.sensor_id)
            if sensor:
                sensor_layout.addRow("Nombre:", QLabel(sensor.nombre))
                sensor_layout.addRow("Ubicación:", QLabel(f"{sensor.ciudad}, {sensor.pais}"))
                sensor_layout.addRow("Estado:", QLabel(sensor.estado.value if sensor.estado else "N/A"))
            
            sensor_group.setLayout(sensor_layout)
            layout.addWidget(sensor_group)
        
        if hasattr(self.alert, 'process_id') and self.alert.process_id:
            process_group = QGroupBox("Información del Proceso")
            process_layout = QFormLayout()
            process_layout.addRow("ID Proceso:", QLabel(str(self.alert.process_id)))
            
            if hasattr(self.alert, 'execution_id') and self.alert.execution_id:
                process_layout.addRow("ID Ejecución:", QLabel(str(self.alert.execution_id)))
            
            # Try to get process details
            process = self.alert_controller.get_process(self.alert.process_id)
            if process:
                process_layout.addRow("Nombre:", QLabel(process.nombre))
                process_layout.addRow("Tipo:", QLabel(process.tipo.value if process.tipo else "N/A"))
                process_layout.addRow("Costo:", QLabel(f"${process.costo:.2f}"))
            
            process_group.setLayout(process_layout)
            layout.addWidget(process_group)
        
        # Measurement values (for threshold alerts)
        if self.alert.valor is not None or self.alert.umbral is not None:
            values_group = QGroupBox("Valores de Medición")
            values_layout = QFormLayout()
            
            if self.alert.valor is not None:
                values_layout.addRow("Valor Detectado:", QLabel(f"{self.alert.valor:.2f}"))
            
            if self.alert.umbral is not None:
                values_layout.addRow("Umbral:", QLabel(f"{self.alert.umbral:.2f}"))
            
            values_group.setLayout(values_layout)
            layout.addWidget(values_group)
        
        # Rule info (if applicable)
        if hasattr(self.alert, 'rule_name') and self.alert.rule_name:
            rule_group = QGroupBox("Información de la Regla")
            rule_layout = QFormLayout()
            rule_layout.addRow("Nombre de Regla:", QLabel(self.alert.rule_name))
            
            if hasattr(self.alert, 'rule_id') and self.alert.rule_id:
                rule_layout.addRow("ID Regla:", QLabel(str(self.alert.rule_id)))
            
            rule_group.setLayout(rule_layout)
            layout.addWidget(rule_group)
        
        # User info (if applicable)
        if hasattr(self.alert, 'user_id') and self.alert.user_id:
            user_group = QGroupBox("Usuario")
            user_layout = QFormLayout()
            
            # Try to get user details
            user = self.alert_controller.get_user(self.alert.user_id)
            if user:
                user_layout.addRow("Nombre:", QLabel(user.nombre_completo))
                user_layout.addRow("Email:", QLabel(user.email))
            else:
                user_layout.addRow("ID Usuario:", QLabel(str(self.alert.user_id)))
            
            user_group.setLayout(user_layout)
            layout.addWidget(user_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
