"""
Alerts widget for viewing and managing alerts
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QLineEdit, QComboBox, QDateEdit, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Optional

from desktop_app.core.database import db_manager
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.services.alert_service import AlertService
from desktop_app.models.alert_models import AlertStatus, AlertType
from desktop_app.utils.session_manager import SessionManager


class AlertsWidget(QWidget):
    """Widget for viewing and managing alerts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
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
        self.status_filter.addItems(["", "activa", "resuelta", "reconocida"])
        row1.addWidget(self.status_filter)
        
        row1.addWidget(QLabel("Tipo:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["", "sensor", "climatica", "umbral"])
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
        layout.addWidget(self.table)
        
        # Action buttons
        action_layout = QHBoxLayout()
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
            mongo_db = db_manager.get_mongo_db()
            redis_client = db_manager.get_redis_client()
            alert_repo = AlertRepository(mongo_db, redis_client)
            alert_service = AlertService(alert_repo)
            
            # Get filters
            status_str = self.status_filter.currentText()
            status = AlertStatus(status_str) if status_str else None
            
            type_str = self.type_filter.currentText()
            alert_type = AlertType(type_str) if type_str else None
            
            sensor_id = self.sensor_id_filter.text().strip() or None
            
            start_qdate = self.start_date.date()
            end_qdate = self.end_date.date()
            start_date = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
            end_date = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
            
            alerts = alert_service.get_all_alerts(
                skip=0,
                limit=1000,
                estado=status,
                tipo=alert_type,
                sensor_id=sensor_id,
                fecha_desde=start_date,
                fecha_hasta=end_date
            )
            
            # Update stats
            active_count = len([a for a in alerts if a.estado == AlertStatus.ACTIVE])
            total_count = len(alerts)
            self.stats_label.setText(f"Total: {total_count} alertas ({active_count} activas)")
            
            # Update table
            self.table.setRowCount(len(alerts))
            for row, alert in enumerate(alerts):
                self.table.setItem(row, 0, QTableWidgetItem(str(alert.id)))
                self.table.setItem(row, 1, QTableWidgetItem(alert.tipo.value if alert.tipo else ""))
                self.table.setItem(row, 2, QTableWidgetItem(str(alert.sensor_id)))
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
                            item.setBackground(Qt.GlobalColor.red.lighter(180))
                
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
                mongo_db = db_manager.get_mongo_db()
                redis_client = db_manager.get_redis_client()
                alert_repo = AlertRepository(mongo_db, redis_client)
                alert_service = AlertService(alert_repo)
                
                alert = alert_service.get_alert(alert_id)
                if alert:
                    from desktop_app.models.alert_models import AlertUpdate
                    update = AlertUpdate(estado=AlertStatus.RESOLVED)
                    alert_repo.update(alert_id, update)
                    QMessageBox.information(self, "Éxito", "Alerta marcada como resuelta")
                    self.load_alerts()
                else:
                    QMessageBox.warning(self, "Error", "Alerta no encontrada")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al resolver alerta: {str(e)}")
