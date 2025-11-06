"""
Measurements widget for viewing sensor measurements
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QLineEdit, QDateEdit, QHeaderView, QAbstractItemView,
    QDialog, QComboBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, timedelta
from typing import Optional, Tuple

from desktop_app.core.database import db_manager
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.repositories.alert_rule_repository import AlertRuleRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.sensor_service import SensorService
from desktop_app.services.alert_service import AlertService
from desktop_app.services.alert_rule_service import AlertRuleService
from desktop_app.models.measurement_models import MeasurementCreate
from desktop_app.models.sensor_models import SensorStatus
from desktop_app.core.config import settings


class MeasurementDialog(QDialog):
    """Dialog for creating a new measurement"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Medición")
        self.setMinimumWidth(400)
        self.init_ui()
        self.load_sensors()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Sensor selection
        layout.addWidget(QLabel("Sensor:"))
        self.sensor_combo = QComboBox()
        self.sensor_combo.setEditable(False)
        layout.addWidget(self.sensor_combo)
        
        # Temperature - use wider range to allow sentinel value
        layout.addWidget(QLabel("Temperatura (°C):"))
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(-999, 100)  # Extended range to allow -999 as sentinel
        self.temp_spin.setDecimals(2)
        self.temp_spin.setSuffix(" °C")
        self.temp_spin.setSpecialValueText("No establecido")
        self.temp_spin.setValue(-999)  # Special sentinel value for "not set"
        layout.addWidget(self.temp_spin)
        
        # Humidity - allow negative values for sentinel
        layout.addWidget(QLabel("Humedad (%):"))
        self.humidity_spin = QDoubleSpinBox()
        self.humidity_spin.setRange(-1, 100)  # Allow -1 as sentinel
        self.humidity_spin.setDecimals(2)
        self.humidity_spin.setSuffix(" %")
        self.humidity_spin.setSpecialValueText("No establecido")
        self.humidity_spin.setValue(-1)  # Special sentinel value for "not set"
        layout.addWidget(self.humidity_spin)
        
        # Info label
        info_label = QLabel("Nota: Debe proporcionar al menos temperatura o humedad")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info_label)
        
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
    
    def load_sensors(self):
        """Load active sensors into the combo box"""
        try:
            mongo_db = db_manager.get_mongo_db()
            sensor_repo = SensorRepository(mongo_db)
            sensors = sensor_repo.get_all(skip=0, limit=1000, estado=SensorStatus.ACTIVE)
            
            self.sensor_combo.clear()
            for sensor in sensors:
                display_text = f"{sensor.nombre} ({sensor.ciudad}, {sensor.pais})"
                self.sensor_combo.addItem(display_text, sensor.id)
        except Exception as e:
            QMessageBox.warning(self, "Advertencia", f"Error al cargar sensores: {str(e)}")
    
    def get_data(self) -> Tuple[str, MeasurementCreate]:
        """Get the sensor ID and measurement data"""
        sensor_id = self.sensor_combo.currentData()
        
        temp_val = self.temp_spin.value()
        humidity_val = self.humidity_spin.value()
        
        # Convert special sentinel values to None
        # Temperature: -999 is the sentinel for "not set"
        # Humidity: -1 is the sentinel for "not set"
        temperature = None if temp_val == -999 else temp_val
        humidity = None if humidity_val == -1 else humidity_val
        
        measurement_data = MeasurementCreate(
            temperature=temperature,
            humidity=humidity
        )
        
        return sensor_id, measurement_data
    
    def accept(self):
        """Validate and accept the dialog"""
        # Get sensor ID
        sensor_id = self.sensor_combo.currentData()
        if not sensor_id:
            QMessageBox.warning(self, "Error de Validación", "Por favor seleccione un sensor")
            return
        
        # Check that at least one value is provided
        temp_val = self.temp_spin.value()
        humidity_val = self.humidity_spin.value()
        temperature = None if temp_val == -999 else temp_val
        humidity = None if humidity_val == -1 else humidity_val
        
        if temperature is None and humidity is None:
            QMessageBox.warning(
                self, 
                "Error de Validación", 
                "Debe proporcionar al menos temperatura o humedad"
            )
            return
        
        super().accept()


class MeasurementsWidget(QWidget):
    """Widget for viewing measurements"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title and actions
        header_layout = QHBoxLayout()
        title = QLabel("Mediciones")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Add measurement button
        add_btn = QPushButton("Agregar Medición")
        add_btn.clicked.connect(self.add_measurement)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # Filters
        filter_group = QGroupBox("Filtros de Búsqueda")
        filter_layout = QVBoxLayout()
        
        # Location filters
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("País:"))
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("ej., Argentina")
        location_layout.addWidget(self.country_edit)
        
        location_layout.addWidget(QLabel("Ciudad:"))
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("ej., Buenos Aires")
        location_layout.addWidget(self.city_edit)
        filter_layout.addLayout(location_layout)
        
        # Date filters
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Fecha Inicio:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("Fecha Fin:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)
        filter_layout.addLayout(date_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        search_btn = QPushButton("Buscar")
        search_btn.clicked.connect(self.search_measurements)
        btn_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("Limpiar")
        clear_btn.clicked.connect(self.clear_filters)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        filter_layout.addLayout(btn_layout)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Stats group
        self.stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("No hay datos cargados. Por favor busque mediciones.")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Fecha/Hora", "ID Sensor", "Temperatura (°C)", "Humedad (%)", "País", "Ciudad"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def add_measurement(self):
        """Open dialog to add a new measurement"""
        dialog = MeasurementDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                sensor_id, measurement_data = dialog.get_data()
                
                # Get services
                mongo_db = db_manager.get_mongo_db()
                cassandra_session = db_manager.get_cassandra_session()
                redis_client = db_manager.get_redis_client()
                
                sensor_repo = SensorRepository(mongo_db)
                measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
                alert_repo = AlertRepository(mongo_db, redis_client)
                alert_service = AlertService(alert_repo)
                
                # Initialize alert rule service if available
                rule_repo = AlertRuleRepository(mongo_db)
                alert_rule_service = AlertRuleService(rule_repo, alert_repo)
                
                user_repo = UserRepository(mongo_db, neo4j_driver)
                sensor_service = SensorService(
                    sensor_repo, 
                    measurement_repo, 
                    alert_service,
                    alert_rule_service,
                    user_repo=user_repo
                )
                
                # Register the measurement
                result = sensor_service.register_measurement(sensor_id, measurement_data)
                
                QMessageBox.information(
                    self, 
                    "Éxito", 
                    f"Medición agregada exitosamente!\n\n"
                    f"Temperatura: {measurement_data.temperature or 'N/A'}°C\n"
                    f"Humedad: {measurement_data.humidity or 'N/A'}%"
                )
                
                # Optionally refresh the search if filters are set
                if self.country_edit.text().strip() and self.city_edit.text().strip():
                    self.search_measurements()
                    
            except ValueError as e:
                QMessageBox.warning(self, "Error de Validación", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al agregar medición: {str(e)}")
    
    def clear_filters(self):
        self.country_edit.clear()
        self.city_edit.clear()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.end_date.setDate(QDate.currentDate())
        self.table.setRowCount(0)
        self.stats_label.setText("No hay datos cargados. Por favor busque mediciones.")
    
    def search_measurements(self):
        country = self.country_edit.text().strip()
        city = self.city_edit.text().strip()
        
        if not country or not city:
            QMessageBox.warning(self, "Error de Validación", "Por favor ingrese país y ciudad")
            return
        
        try:
            # Get dates
            start_qdate = self.start_date.date()
            end_qdate = self.end_date.date()
            start_date = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
            end_date = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
            
            # Get measurements
            mongo_db = db_manager.get_mongo_db()
            cassandra_session = db_manager.get_cassandra_session()
            redis_client = db_manager.get_redis_client()
            
            sensor_repo = SensorRepository(mongo_db)
            measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
            alert_repo = AlertRepository(mongo_db, redis_client)
            alert_service = AlertService(alert_repo)
            neo4j_driver = db_manager.get_neo4j_driver()
            user_repo = UserRepository(mongo_db, neo4j_driver)
            sensor_service = SensorService(sensor_repo, measurement_repo, alert_service, user_repo=user_repo)
            
            measurements = sensor_service.get_location_measurements(
                pais=country,
                ciudad=city,
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
                self.table.setItem(row, 1, QTableWidgetItem(str(measurement.get("sensor_id", ""))))
                
                # Use Spanish keys (temperatura, humedad) as returned by the service
                temp = measurement.get("temperatura")
                humidity = measurement.get("humedad")
                
                temp_str = f"{temp:.2f}" if temp is not None else "N/A"
                humidity_str = f"{humidity:.2f}" if humidity is not None else "N/A"
                
                self.table.setItem(row, 2, QTableWidgetItem(temp_str))
                self.table.setItem(row, 3, QTableWidgetItem(humidity_str))
                self.table.setItem(row, 4, QTableWidgetItem(str(measurement.get("pais", ""))))
                self.table.setItem(row, 5, QTableWidgetItem(str(measurement.get("ciudad", ""))))
            
            # Calculate and show stats
            if measurements:
                # Use Spanish keys (temperatura, humedad) as returned by the service
                temps = [m.get("temperatura") for m in measurements if m.get("temperatura") is not None]
                hums = [m.get("humedad") for m in measurements if m.get("humedad") is not None]
                
                if temps:
                    avg_temp = sum(temps) / len(temps)
                    min_temp = min(temps)
                    max_temp = max(temps)
                else:
                    avg_temp = min_temp = max_temp = 0
                
                if hums:
                    avg_hum = sum(hums) / len(hums)
                    min_hum = min(hums)
                    max_hum = max(hums)
                else:
                    avg_hum = min_hum = max_hum = 0
                
                stats_text = (
                    f"Total: {len(measurements)} mediciones | "
                    f"Temp: {min_temp:.1f}°C - {max_temp:.1f}°C (prom: {avg_temp:.1f}°C) | "
                    f"Humedad: {min_hum:.1f}% - {max_hum:.1f}% (prom: {avg_hum:.1f}%)"
                )
                self.stats_label.setText(stats_text)
            else:
                self.stats_label.setText("No se encontraron mediciones para los filtros especificados.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar mediciones: {str(e)}")
            self.table.setRowCount(0)
