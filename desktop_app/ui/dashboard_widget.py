"""
Dashboard widget showing overview and statistics
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QGroupBox
)
from PyQt6.QtCore import Qt

from desktop_app.core.database import db_manager
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.utils.session_manager import SessionManager


class DashboardWidget(QWidget):
    """Dashboard widget showing statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
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
        
        # Refresh button
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh dashboard data"""
        try:
            mongo_db = db_manager.get_mongo_db()
            redis_client = db_manager.get_redis_client()
            
            sensor_repo = SensorRepository(mongo_db)
            alert_repo = AlertRepository(mongo_db, redis_client)
            
            # Get sensor stats
            all_sensors = sensor_repo.get_all(limit=1000)
            active_sensors = [s for s in all_sensors if s.estado == "activo"]
            
            self.total_sensors_label.setText(f"Sensores Totales: {len(all_sensors)}")
            self.active_sensors_label.setText(f"Sensores Activos: {len(active_sensors)}")
            
            # Get alert stats
            active_alerts = alert_repo.get_active_alerts(limit=1000)
            self.active_alerts_label.setText(f"Alertas Activas: {len(active_alerts)}")
            
        except Exception as e:
            self.total_sensors_label.setText(f"Error: {str(e)}")
            self.active_sensors_label.setText("")
            self.active_alerts_label.setText("")

