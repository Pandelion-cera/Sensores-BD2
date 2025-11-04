"""
Processes widget for viewing and managing process requests
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from datetime import datetime

from desktop_app.core.database import db_manager
from desktop_app.repositories.process_repository import ProcessRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.services.process_service import ProcessService
from desktop_app.utils.session_manager import SessionManager
from desktop_app.core.config import settings
from desktop_app.models.process_models import ProcessRequestCreate


class ProcessesWidget(QWidget):
    """Widget for viewing and managing processes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.init_ui()
        self.load_processes()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Processes")
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
            "ID", "Name", "Type", "Description", "Cost"
        ])
        self.processes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.processes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.processes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        processes_layout.addWidget(self.processes_table)
        processes_container.setLayout(processes_layout)
        self.tabs.addTab(processes_container, "Available Processes")
        
        # My requests tab
        requests_container = QWidget()
        requests_layout = QVBoxLayout()
        self.requests_table = QTableWidget()
        self.requests_table.setColumnCount(5)
        self.requests_table.setHorizontalHeaderLabels([
            "ID", "Process ID", "Status", "Request Date", "Parameters"
        ])
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.requests_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.requests_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        requests_layout.addWidget(self.requests_table)
        requests_container.setLayout(requests_layout)
        self.tabs.addTab(requests_container, "My Requests")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        request_btn = QPushButton("Request Selected Process")
        request_btn.clicked.connect(self.request_process)
        btn_layout.addWidget(request_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_processes)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_processes(self):
        try:
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            cassandra_session = db_manager.get_cassandra_session()
            
            process_repo = ProcessRepository(mongo_db, neo4j_driver)
            measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
            sensor_repo = SensorRepository(mongo_db)
            process_service = ProcessService(process_repo, measurement_repo, sensor_repo)
            
            # Load available processes
            processes = process_service.get_all_processes(skip=0, limit=100)
            self.processes_table.setRowCount(len(processes))
            for row, process in enumerate(processes):
                self.processes_table.setItem(row, 0, QTableWidgetItem(str(process.id)))
                self.processes_table.setItem(row, 1, QTableWidgetItem(process.nombre))
                self.processes_table.setItem(row, 2, QTableWidgetItem(process.tipo.value if process.tipo else ""))
                self.processes_table.setItem(row, 3, QTableWidgetItem(process.descripcion or ""))
                self.processes_table.setItem(row, 4, QTableWidgetItem(f"${process.costo:.2f}"))
            
            # Load user requests
            user_id = self.session_manager.get_user_id()
            if user_id:
                requests = process_service.get_user_requests(user_id, skip=0, limit=100)
                self.requests_table.setRowCount(len(requests))
                for row, request in enumerate(requests):
                    self.requests_table.setItem(row, 0, QTableWidgetItem(str(request.id)))
                    self.requests_table.setItem(row, 1, QTableWidgetItem(str(request.process_id)))
                    self.requests_table.setItem(row, 2, QTableWidgetItem(request.estado.value if request.estado else ""))
                    
                    fecha_str = ""
                    if request.fecha_solicitud:
                        if isinstance(request.fecha_solicitud, datetime):
                            fecha_str = request.fecha_solicitud.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            fecha_str = str(request.fecha_solicitud)
                    self.requests_table.setItem(row, 3, QTableWidgetItem(fecha_str))
                    
                    params_text = str(request.parametros) if request.parametros else ""
                    self.requests_table.setItem(row, 4, QTableWidgetItem(params_text))
            else:
                self.requests_table.setRowCount(0)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load processes: {str(e)}")
    
    def request_process(self):
        current_row = self.processes_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a process to request")
            return
        
        process_id = self.processes_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Request",
            f"Request execution of process: {self.processes_table.item(current_row, 1).text()}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                user_id = self.session_manager.get_user_id()
                if not user_id:
                    QMessageBox.warning(self, "Error", "User not logged in")
                    return
                
                mongo_db = db_manager.get_mongo_db()
                neo4j_driver = db_manager.get_neo4j_driver()
                cassandra_session = db_manager.get_cassandra_session()
                
                process_repo = ProcessRepository(mongo_db, neo4j_driver)
                measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
                sensor_repo = SensorRepository(mongo_db)
                process_service = ProcessService(process_repo, measurement_repo, sensor_repo)
                
                request_data = ProcessRequestCreate(
                    process_id=process_id,
                    parametros={}
                )
                process_service.request_process(user_id, request_data)
                QMessageBox.information(self, "Success", "Process request submitted successfully")
                self.load_processes()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to request process: {str(e)}")
