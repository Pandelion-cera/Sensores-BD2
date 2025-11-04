"""
Measurements widget for viewing sensor measurements
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QLineEdit, QDateEdit, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, timedelta
from typing import Optional

from desktop_app.core.database import db_manager
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.services.sensor_service import SensorService
from desktop_app.services.alert_service import AlertService
from desktop_app.core.config import settings


class MeasurementsWidget(QWidget):
    """Widget for viewing measurements"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Measurements")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Filters
        filter_group = QGroupBox("Search Filters")
        filter_layout = QVBoxLayout()
        
        # Location filters
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Country:"))
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("e.g., Argentina")
        location_layout.addWidget(self.country_edit)
        
        location_layout.addWidget(QLabel("City:"))
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("e.g., Buenos Aires")
        location_layout.addWidget(self.city_edit)
        filter_layout.addLayout(location_layout)
        
        # Date filters
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Start Date:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("End Date:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)
        filter_layout.addLayout(date_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_measurements)
        btn_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_filters)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        filter_layout.addLayout(btn_layout)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Stats group
        self.stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("No data loaded. Please search for measurements.")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Sensor ID", "Temperature (°C)", "Humidity (%)", "Country", "City"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def clear_filters(self):
        self.country_edit.clear()
        self.city_edit.clear()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.end_date.setDate(QDate.currentDate())
        self.table.setRowCount(0)
        self.stats_label.setText("No data loaded. Please search for measurements.")
    
    def search_measurements(self):
        country = self.country_edit.text().strip()
        city = self.city_edit.text().strip()
        
        if not country or not city:
            QMessageBox.warning(self, "Validation Error", "Please enter both country and city")
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
            sensor_service = SensorService(sensor_repo, measurement_repo, alert_service)
            
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
                self.table.setItem(row, 2, QTableWidgetItem(f"{measurement.get('temperature', 0):.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{measurement.get('humidity', 0):.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(str(measurement.get("pais", ""))))
                self.table.setItem(row, 5, QTableWidgetItem(str(measurement.get("ciudad", ""))))
            
            # Calculate and show stats
            if measurements:
                temps = [m.get("temperature", 0) for m in measurements if m.get("temperature") is not None]
                hums = [m.get("humidity", 0) for m in measurements if m.get("humidity") is not None]
                
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
                    f"Total: {len(measurements)} measurements | "
                    f"Temp: {min_temp:.1f}°C - {max_temp:.1f}°C (avg: {avg_temp:.1f}°C) | "
                    f"Humidity: {min_hum:.1f}% - {max_hum:.1f}% (avg: {avg_hum:.1f}%)"
                )
                self.stats_label.setText(stats_text)
            else:
                self.stats_label.setText("No measurements found for the specified filters.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load measurements: {str(e)}")
            self.table.setRowCount(0)
