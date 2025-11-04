"""
Sensors widget for viewing and managing sensors
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QComboBox, QGroupBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from typing import Optional, List
from datetime import datetime

from desktop_app.core.database import db_manager
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.services.sensor_service import SensorService
from desktop_app.services.alert_service import AlertService
from desktop_app.models.sensor_models import Sensor, SensorCreate, SensorUpdate, SensorStatus
from desktop_app.utils.session_manager import SessionManager
from desktop_app.core.config import settings


class SensorDialog(QDialog):
    """Dialog for creating/editing sensors"""
    
    def __init__(self, parent=None, sensor: Optional[Sensor] = None):
        super().__init__(parent)
        self.sensor = sensor
        self.setWindowTitle("Edit Sensor" if sensor else "Create Sensor")
        self.setMinimumWidth(400)
        self.init_ui()
        
        if sensor:
            self.load_sensor_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Type
        layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["temperatura", "humedad", "temperatura_humedad"])
        layout.addWidget(self.type_combo)
        
        # Location
        layout.addWidget(QLabel("Country:"))
        self.country_edit = QLineEdit()
        layout.addWidget(self.country_edit)
        
        layout.addWidget(QLabel("City:"))
        self.city_edit = QLineEdit()
        layout.addWidget(self.city_edit)
        
        # Coordinates
        layout.addWidget(QLabel("Latitude:"))
        self.lat_edit = QLineEdit()
        layout.addWidget(self.lat_edit)
        
        layout.addWidget(QLabel("Longitude:"))
        self.lon_edit = QLineEdit()
        layout.addWidget(self.lon_edit)
        
        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["activo", "inactivo", "falla"])
        layout.addWidget(self.status_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_sensor_data(self):
        if self.sensor:
            self.name_edit.setText(self.sensor.nombre)
            index = self.type_combo.findText(self.sensor.tipo)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
            self.country_edit.setText(self.sensor.pais)
            self.city_edit.setText(self.sensor.ciudad)
            self.lat_edit.setText(str(self.sensor.latitud))
            self.lon_edit.setText(str(self.sensor.longitud))
            index = self.status_combo.findText(self.sensor.estado)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
    
    def get_data(self) -> dict:
        return {
            "nombre": self.name_edit.text().strip(),
            "tipo": self.type_combo.currentText(),
            "pais": self.country_edit.text().strip(),
            "ciudad": self.city_edit.text().strip(),
            "latitud": float(self.lat_edit.text()) if self.lat_edit.text() else 0.0,
            "longitud": float(self.lon_edit.text()) if self.lon_edit.text() else 0.0,
            "estado": self.status_combo.currentText()
        }


class SensorsWidget(QWidget):
    """Widget for managing sensors"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.init_ui()
        self.load_sensors()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title and actions
        header_layout = QHBoxLayout()
        title = QLabel("Sensors")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Filters
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Country:"))
        self.country_filter = QLineEdit()
        self.country_filter.setPlaceholderText("Filter by country")
        filter_layout.addWidget(self.country_filter)
        
        filter_layout.addWidget(QLabel("City:"))
        self.city_filter = QLineEdit()
        self.city_filter.setPlaceholderText("Filter by city")
        filter_layout.addWidget(self.city_filter)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["", "activo", "inactivo", "falla"])
        filter_layout.addWidget(self.status_filter)
        
        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self.load_sensors)
        filter_layout.addWidget(filter_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_sensors)
        btn_layout.addWidget(refresh_btn)
        
        user_role = self.session_manager.get_user_role()
        if user_role in ["administrador", "tecnico"]:
            create_btn = QPushButton("Create Sensor")
            create_btn.clicked.connect(self.create_sensor)
            btn_layout.addWidget(create_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Type", "Country", "City", "Coordinates", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def clear_filters(self):
        self.country_filter.clear()
        self.city_filter.clear()
        self.status_filter.setCurrentIndex(0)
        self.load_sensors()
    
    def load_sensors(self):
        try:
            mongo_db = db_manager.get_mongo_db()
            sensor_repo = SensorRepository(mongo_db)
            
            # Get filters
            country = self.country_filter.text().strip() or None
            city = self.city_filter.text().strip() or None
            status_str = self.status_filter.currentText()
            status = SensorStatus(status_str) if status_str else None
            
            sensors = sensor_repo.get_all(
                skip=0,
                limit=1000,
                pais=country,
                ciudad=city,
                estado=status
            )
            
            self.table.setRowCount(len(sensors))
            
            for row, sensor in enumerate(sensors):
                self.table.setItem(row, 0, QTableWidgetItem(str(sensor.id)))
                self.table.setItem(row, 1, QTableWidgetItem(sensor.nombre))
                self.table.setItem(row, 2, QTableWidgetItem(sensor.tipo))
                self.table.setItem(row, 3, QTableWidgetItem(sensor.pais))
                self.table.setItem(row, 4, QTableWidgetItem(sensor.ciudad))
                coord_text = f"{sensor.latitud:.4f}, {sensor.longitud:.4f}"
                self.table.setItem(row, 5, QTableWidgetItem(coord_text))
                self.table.setItem(row, 6, QTableWidgetItem(sensor.estado))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(2, 2, 2, 2)
                
                user_role = self.session_manager.get_user_role()
                if user_role in ["administrador", "tecnico"]:
                    edit_btn = QPushButton("Edit")
                    edit_btn.clicked.connect(lambda checked, s=sensor: self.edit_sensor(s))
                    actions_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("Delete")
                    delete_btn.clicked.connect(lambda checked, s=sensor: self.delete_sensor(s))
                    actions_layout.addWidget(delete_btn)
                
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 7, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sensors: {str(e)}")
    
    def create_sensor(self):
        dialog = SensorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                sensor_data = SensorCreate(**data)
                
                mongo_db = db_manager.get_mongo_db()
                cassandra_session = db_manager.get_cassandra_session()
                redis_client = db_manager.get_redis_client()
                
                sensor_repo = SensorRepository(mongo_db)
                measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
                alert_repo = AlertRepository(mongo_db, redis_client)
                alert_service = AlertService(alert_repo)
                sensor_service = SensorService(sensor_repo, measurement_repo, alert_service)
                
                sensor_service.create_sensor(sensor_data)
                QMessageBox.information(self, "Success", "Sensor created successfully")
                self.load_sensors()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create sensor: {str(e)}")
    
    def edit_sensor(self, sensor: Sensor):
        dialog = SensorDialog(self, sensor)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                sensor_update = SensorUpdate(**data)
                
                mongo_db = db_manager.get_mongo_db()
                sensor_repo = SensorRepository(mongo_db)
                
                sensor_repo.update(sensor.id, sensor_update)
                QMessageBox.information(self, "Success", "Sensor updated successfully")
                self.load_sensors()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update sensor: {str(e)}")
    
    def delete_sensor(self, sensor: Sensor):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete sensor '{sensor.nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                mongo_db = db_manager.get_mongo_db()
                sensor_repo = SensorRepository(mongo_db)
                sensor_repo.delete(sensor.id)
                QMessageBox.information(self, "Success", "Sensor deleted successfully")
                self.load_sensors()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete sensor: {str(e)}")
