"""
Sensors widget for viewing and managing sensors
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QComboBox, QGroupBox, QHeaderView, QAbstractItemView,
    QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from typing import Optional, List
from datetime import datetime, timedelta

from desktop_app.core.database import db_manager
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.repositories.user_repository import UserRepository
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
        self.setWindowTitle("Editar Sensor" if sensor else "Crear Sensor")
        self.setMinimumWidth(400)
        self.init_ui()
        
        if sensor:
            self.load_sensor_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Name
        layout.addWidget(QLabel("Nombre:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Type
        layout.addWidget(QLabel("Tipo:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["temperatura", "humedad", "temperatura_humedad"])
        layout.addWidget(self.type_combo)
        
        # Location
        layout.addWidget(QLabel("País:"))
        self.country_edit = QLineEdit()
        layout.addWidget(self.country_edit)
        
        layout.addWidget(QLabel("Ciudad:"))
        self.city_edit = QLineEdit()
        layout.addWidget(self.city_edit)
        
        # Coordinates
        layout.addWidget(QLabel("Latitud:"))
        self.lat_edit = QLineEdit()
        layout.addWidget(self.lat_edit)
        
        layout.addWidget(QLabel("Longitud:"))
        self.lon_edit = QLineEdit()
        layout.addWidget(self.lon_edit)
        
        # Status
        layout.addWidget(QLabel("Estado:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["activo", "inactivo", "falla"])
        layout.addWidget(self.status_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancelar")
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


class SensorMeasurementsDialog(QDialog):
    """Dialog for viewing sensor measurements"""
    
    def __init__(self, parent=None, sensor: Optional[Sensor] = None):
        super().__init__(parent)
        self.sensor = sensor
        self.setWindowTitle(f"Mediciones - {sensor.nombre if sensor else 'Sensor'}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.init_ui()
        
        if sensor:
            self.load_measurements()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Sensor info
        info_label = QLabel(f"<b>Sensor:</b> {self.sensor.nombre if self.sensor else 'N/A'}<br>"
                           f"<b>Ubicación:</b> {self.sensor.ciudad}, {self.sensor.pais if self.sensor else 'N/A'}")
        layout.addWidget(info_label)
        
        # Date range filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Rango de Tiempo:"))
        
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["Últimas 24 horas", "Últimos 7 días", "Últimos 30 días", "Personalizado"])
        self.time_range_combo.currentTextChanged.connect(self.on_time_range_changed)
        filter_layout.addWidget(self.time_range_combo)
        
        filter_layout.addWidget(QLabel("Fecha Inicio:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-1))
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("Fecha Fin:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date)
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_measurements)
        filter_layout.addWidget(refresh_btn)
        layout.addLayout(filter_layout)
        
        # Statistics
        self.stats_label = QLabel("Cargando...")
        layout.addWidget(self.stats_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Fecha/Hora", "Temperatura (°C)", "Humedad (%)", "Estado"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Set default time range
        self.on_time_range_changed()
    
    def on_time_range_changed(self):
        """Update date range based on selected time range"""
        range_text = self.time_range_combo.currentText()
        end_date = QDate.currentDate()
        self.end_date.setDate(end_date)
        
        if range_text == "Últimas 24 horas":
            self.start_date.setDate(end_date.addDays(-1))
        elif range_text == "Últimos 7 días":
            self.start_date.setDate(end_date.addDays(-7))
        elif range_text == "Últimos 30 días":
            self.start_date.setDate(end_date.addDays(-30))
        # For "Personalizado", user can manually set dates
    
    def load_measurements(self):
        """Load measurements for the sensor"""
        if not self.sensor:
            return
        
        try:
            # Get date range
            start_qdate = self.start_date.date()
            end_qdate = self.end_date.date()
            start_date = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
            end_date = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
            
            # Get services
            mongo_db = db_manager.get_mongo_db()
            cassandra_session = db_manager.get_cassandra_session()
            redis_client = db_manager.get_redis_client()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            sensor_repo = SensorRepository(mongo_db)
            measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
            alert_repo = AlertRepository(mongo_db, redis_client)
            alert_service = AlertService(alert_repo)
            user_repo = UserRepository(mongo_db, neo4j_driver)
            sensor_service = SensorService(sensor_repo, measurement_repo, alert_service, user_repo=user_repo)
            
            # Get measurements - try by MongoDB _id first
            measurements = sensor_service.get_sensor_measurements(
                sensor_id=self.sensor.id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Update table
            self.table.setRowCount(len(measurements))
            for row, measurement in enumerate(measurements):
                timestamp = measurement.get("timestamp", "")
                if isinstance(timestamp, datetime):
                    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    timestamp_str = str(timestamp)
                
                self.table.setItem(row, 0, QTableWidgetItem(timestamp_str))
                
                # Use Spanish keys that match get_sensor_measurements return value
                temp = measurement.get("temperatura") or measurement.get("temperature")
                temp_str = f"{temp:.2f}" if temp is not None else "N/A"
                self.table.setItem(row, 1, QTableWidgetItem(temp_str))
                
                humidity = measurement.get("humedad") or measurement.get("humidity")
                hum_str = f"{humidity:.2f}" if humidity is not None else "N/A"
                self.table.setItem(row, 2, QTableWidgetItem(hum_str))
                
                # Status indicator
                status_item = QTableWidgetItem("OK")
                if temp is not None and (temp < -10 or temp > 50):
                    status_item.setText("⚠ Alerta")
                    status_item.setForeground(Qt.GlobalColor.red)
                elif humidity is not None and (humidity < 0 or humidity > 100):
                    status_item.setText("⚠ Alerta")
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 3, status_item)
            
            # Calculate statistics
            if measurements:
                # Use Spanish keys that match get_sensor_measurements return value
                temps = []
                hums = []
                for m in measurements:
                    temp = m.get("temperatura") or m.get("temperature")
                    if temp is not None:
                        temps.append(temp)
                    hum = m.get("humedad") or m.get("humidity")
                    if hum is not None:
                        hums.append(hum)
                
                stats_text = f"<b>Estadísticas:</b> Total: {len(measurements)} mediciones"
                if temps:
                    avg_temp = sum(temps) / len(temps)
                    min_temp = min(temps)
                    max_temp = max(temps)
                    stats_text += f" | Temp: {min_temp:.1f}°C - {max_temp:.1f}°C (prom: {avg_temp:.1f}°C)"
                if hums:
                    avg_hum = sum(hums) / len(hums)
                    min_hum = min(hums)
                    max_hum = max(hums)
                    stats_text += f" | Humedad: {min_hum:.1f}% - {max_hum:.1f}% (prom: {avg_hum:.1f}%)"
                self.stats_label.setText(stats_text)
            else:
                self.stats_label.setText("No se encontraron mediciones para el rango de tiempo seleccionado.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar mediciones: {str(e)}")
            self.table.setRowCount(0)
            self.stats_label.setText(f"Error: {str(e)}")


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
        title = QLabel("Sensores")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Filters
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("País:"))
        self.country_filter = QLineEdit()
        self.country_filter.setPlaceholderText("Filtrar por país")
        filter_layout.addWidget(self.country_filter)
        
        filter_layout.addWidget(QLabel("Ciudad:"))
        self.city_filter = QLineEdit()
        self.city_filter.setPlaceholderText("Filtrar por ciudad")
        filter_layout.addWidget(self.city_filter)
        
        filter_layout.addWidget(QLabel("Estado:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["", "activo", "inactivo", "falla"])
        filter_layout.addWidget(self.status_filter)
        
        filter_btn = QPushButton("Filtrar")
        filter_btn.clicked.connect(self.load_sensors)
        filter_layout.addWidget(filter_btn)
        
        clear_btn = QPushButton("Limpiar")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_sensors)
        btn_layout.addWidget(refresh_btn)
        
        user_role = self.session_manager.get_user_role()
        if user_role in ["administrador", "tecnico"]:
            create_btn = QPushButton("Crear Sensor")
            create_btn.clicked.connect(self.create_sensor)
            btn_layout.addWidget(create_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Tipo", "País", "Ciudad", "Coordenadas", "Estado", "Acciones"
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
                    edit_btn = QPushButton("Editar")
                    edit_btn.clicked.connect(lambda checked, s=sensor: self.edit_sensor(s))
                    actions_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("Eliminar")
                    delete_btn.clicked.connect(lambda checked, s=sensor: self.delete_sensor(s))
                    actions_layout.addWidget(delete_btn)
                
                view_measurements_btn = QPushButton("Ver Mediciones")
                view_measurements_btn.clicked.connect(lambda checked, s=sensor: self.view_sensor_measurements(s))
                actions_layout.addWidget(view_measurements_btn)
                
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 7, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar sensores: {str(e)}")
    
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
                user_repo = UserRepository(mongo_db, neo4j_driver)
                sensor_service = SensorService(sensor_repo, measurement_repo, alert_service, user_repo=user_repo)
                
                sensor_service.create_sensor(sensor_data)
                QMessageBox.information(self, "Éxito", "Sensor creado exitosamente")
                self.load_sensors()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al crear sensor: {str(e)}")
    
    def edit_sensor(self, sensor: Sensor):
        dialog = SensorDialog(self, sensor)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                sensor_update = SensorUpdate(**data)
                
                mongo_db = db_manager.get_mongo_db()
                neo4j_driver = db_manager.get_neo4j_driver()
                redis_client = db_manager.get_redis_client()
                cassandra_session = db_manager.get_cassandra_session()
                
                sensor_repo = SensorRepository(mongo_db)
                measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
                alert_repo = AlertRepository(mongo_db, redis_client)
                alert_service = AlertService(alert_repo)
                user_repo = UserRepository(mongo_db, neo4j_driver)
                sensor_service = SensorService(sensor_repo, measurement_repo, alert_service, user_repo=user_repo)
                
                sensor_service.update_sensor(sensor.id, sensor_update)
                QMessageBox.information(self, "Éxito", "Sensor actualizado exitosamente")
                self.load_sensors()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al actualizar sensor: {str(e)}")
    
    def delete_sensor(self, sensor: Sensor):
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el sensor '{sensor.nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                mongo_db = db_manager.get_mongo_db()
                sensor_repo = SensorRepository(mongo_db)
                sensor_repo.delete(sensor.id)
                QMessageBox.information(self, "Éxito", "Sensor eliminado exitosamente")
                self.load_sensors()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar sensor: {str(e)}")
    
    def view_sensor_measurements(self, sensor: Sensor):
        """Open dialog to view measurements for a sensor"""
        dialog = SensorMeasurementsDialog(self, sensor)
        dialog.exec()
