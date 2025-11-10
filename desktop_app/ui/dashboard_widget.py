"""
Dashboard widget showing overview and statistics
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, timedelta
from desktop_app.controllers import get_dashboard_controller
from desktop_app.utils.session_manager import SessionManager


class DashboardWidget(QWidget):
    """Dashboard widget showing statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.dashboard_controller = get_dashboard_controller()
        self.init_ui()
        self.refresh()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Welcome label
        user = self.session_manager.get_user()
        welcome_text = "¡Bienvenido/a!"
        if user:
            welcome_text = f"¡Bienvenido/a, {user.get('nombre_completo', 'Usuario')}!"
        
        welcome = QLabel(welcome_text)
        welcome.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(welcome)
        
        # Stats group
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout()
        
        self.total_sensors_label = QLabel("Sensores Totales: -")
        self.active_sensors_label = QLabel("Sensores Activos: -")
        self.active_alerts_label = QLabel("Alertas Activas: -")
        
        stats_layout.addWidget(self.total_sensors_label)
        stats_layout.addWidget(self.active_sensors_label)
        stats_layout.addWidget(self.active_alerts_label)
        stats_layout.addStretch()
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Measurements group
        measurements_group = QGroupBox("Mediciones")
        measurements_layout = QHBoxLayout()
        measurements_layout.addWidget(QLabel("Fecha Inicio:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        measurements_layout.addWidget(self.start_date)
        
        measurements_layout.addWidget(QLabel("Fecha Fin:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        measurements_layout.addWidget(self.end_date)

        search_btn = QPushButton("Buscar")
        search_btn.clicked.connect(self.refresh)
        measurements_layout.addWidget(search_btn)

        self.total_measurements_label = QLabel("Mediciones Totales: -")
        self.measurements_by_date_label = QLabel("Mediciones por Fecha: -")
        measurements_layout.addWidget(self.total_measurements_label)
        measurements_layout.addWidget(self.measurements_by_date_label)
        measurements_group.setLayout(measurements_layout)
        layout.addWidget(measurements_group)
        
        # Refresh button
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh dashboard data"""
        try:
            overview = self.dashboard_controller.get_overview()
            self.total_sensors_label.setText(f"Sensores Totales: {overview['total_sensors']}")
            self.active_sensors_label.setText(f"Sensores Activos: {overview['active_sensors']}")
            self.active_alerts_label.setText(f"Alertas Activas: {overview['active_alerts']}")

            start_qdate = self.start_date.date()
            end_qdate = self.end_date.date()
            start_date = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
            end_date = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
            measurements = self.dashboard_controller.get_amount_of_measurements_by_date(start_date, end_date)
            self.total_measurements_label.setText(f"Mediciones Totales: {measurements}")
            self.measurements_by_date_label.setText(f"Mediciones por Fecha: {measurements}")
            
        except Exception as e:
            self.total_sensors_label.setText(f"Error: {str(e)}")
            self.active_sensors_label.setText("")
            self.active_alerts_label.setText("")

