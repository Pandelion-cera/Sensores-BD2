"""
Maintenance widget for managing sensor maintenance records
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QComboBox, QTextEdit, QDateEdit, QDateTimeEdit, QFormLayout,
    QDialogButtonBox, QHeaderView, QAbstractItemView, QGroupBox
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor
from datetime import datetime
from typing import Optional

from desktop_app.core.database import db_manager
from desktop_app.repositories.maintenance_repository import MaintenanceRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.maintenance_service import MaintenanceService
from desktop_app.utils.session_manager import SessionManager
from desktop_app.models.maintenance_models import (
    MaintenanceRecord, MaintenanceRecordCreate, MaintenanceStatus
)


class MaintenanceRecordDialog(QDialog):
    """Dialog for creating/editing maintenance records"""
    
    def __init__(self, parent=None, sensor_id: Optional[str] = None, record: Optional[MaintenanceRecord] = None):
        super().__init__(parent)
        self.record = record
        self.sensor_id = sensor_id or (record.sensor_id if record else None)
        self.setWindowTitle("Editar Registro" if record else "Nuevo Registro de Control")
        self.setMinimumWidth(500)
        self.init_ui()
        
        if record:
            self.load_record_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Sensor selection (only if creating new record)
        if not self.record:
            mongo_db = db_manager.get_mongo_db()
            sensor_repo = SensorRepository(mongo_db)
            sensors = sensor_repo.get_all()
            
            self.sensor_combo = QComboBox()
            for sensor in sensors:
                self.sensor_combo.addItem(f"{sensor.nombre} ({sensor.id})", sensor.id)
            form_layout.addRow("Sensor:", self.sensor_combo)
            
            if self.sensor_id:
                # Find and select the sensor
                for i in range(self.sensor_combo.count()):
                    if self.sensor_combo.itemData(i) == self.sensor_id:
                        self.sensor_combo.setCurrentIndex(i)
                        break
        
        # Revision date
        self.revision_date = QDateTimeEdit()
        self.revision_date.setDateTime(QDateTime.currentDateTime())
        self.revision_date.setCalendarPopup(True)
        form_layout.addRow("Fecha de Revisión:", self.revision_date)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("OK", MaintenanceStatus.OK)
        self.status_combo.addItem("Reparación Necesaria", MaintenanceStatus.REPAIR_NEEDED)
        self.status_combo.addItem("Reemplazo Necesario", MaintenanceStatus.REPLACEMENT_NEEDED)
        self.status_combo.addItem("Fuera de Servicio", MaintenanceStatus.OUT_OF_SERVICE)
        form_layout.addRow("Estado:", self.status_combo)
        
        # Observations
        self.observations_edit = QTextEdit()
        self.observations_edit.setMaximumHeight(100)
        form_layout.addRow("Observaciones:", self.observations_edit)
        
        # Actions taken
        self.actions_edit = QTextEdit()
        self.actions_edit.setMaximumHeight(100)
        form_layout.addRow("Acciones Realizadas:", self.actions_edit)
        
        # Next revision date
        self.next_revision_date = QDateTimeEdit()
        self.next_revision_date.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.next_revision_date.setCalendarPopup(True)
        form_layout.addRow("Próxima Revisión:", self.next_revision_date)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_record_data(self):
        """Load existing record data into form"""
        if not self.record:
            return
        
        self.revision_date.setDateTime(QDateTime.fromString(
            self.record.fecha_revision.isoformat(), Qt.DateFormat.ISODate
        ))
        
        # Find and select status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.record.estado:
                self.status_combo.setCurrentIndex(i)
                break
        
        self.observations_edit.setPlainText(self.record.observaciones or "")
        self.actions_edit.setPlainText(self.record.acciones_realizadas or "")
        
        if self.record.proxima_revision:
            self.next_revision_date.setDateTime(QDateTime.fromString(
                self.record.proxima_revision.isoformat(), Qt.DateFormat.ISODate
            ))
    
    def get_record_data(self) -> MaintenanceRecordCreate:
        """Get record data from form"""
        session_manager = SessionManager.get_instance()
        tecnico_id = session_manager.get_user_id()
        
        sensor_id = self.sensor_id
        if not sensor_id and hasattr(self, 'sensor_combo'):
            sensor_id = self.sensor_combo.currentData()
        
        return MaintenanceRecordCreate(
            sensor_id=sensor_id,
            tecnico_id=tecnico_id,
            fecha_revision=self.revision_date.dateTime().toPyDateTime(),
            estado=self.status_combo.currentData(),
            observaciones=self.observations_edit.toPlainText() or None,
            acciones_realizadas=self.actions_edit.toPlainText() or None,
            proxima_revision=self.next_revision_date.dateTime().toPyDateTime()
        )


class MaintenanceWidget(QWidget):
    """Widget for managing maintenance records"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.init_ui()
        self.load_records()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Control de Funcionamiento")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Nuevo Registro")
        create_btn.clicked.connect(self.create_record)
        btn_layout.addWidget(create_btn)
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_records)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Sensor", "Técnico", "Fecha Revisión", "Estado", "Próxima Revisión", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_records(self):
        """Load maintenance records"""
        try:
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            maintenance_repo = MaintenanceRepository(mongo_db)
            sensor_repo = SensorRepository(mongo_db)
            user_repo = UserRepository(mongo_db, neo4j_driver)
            
            maintenance_service = MaintenanceService(maintenance_repo, sensor_repo, user_repo)
            
            # Get user role to determine what records to show
            user_role = self.session_manager.get_user_role()
            user_id = self.session_manager.get_user_id()
            
            if user_role in ["administrador", "tecnico"]:
                # Admins and technicians see all records
                records = maintenance_service.get_all(skip=0, limit=100)
            else:
                # Regular users don't have access
                records = []
            
            # Get sensors and users for display
            sensors = {s.id: s for s in sensor_repo.get_all()}
            users = {u.id: u for u in user_repo.get_all(skip=0, limit=1000)}
            
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(str(record.id)))
                
                # Sensor name
                sensor = sensors.get(record.sensor_id)
                sensor_name = sensor.nombre if sensor else record.sensor_id
                self.table.setItem(row, 1, QTableWidgetItem(sensor_name))
                
                # Technician name
                tecnico = users.get(record.tecnico_id)
                tecnico_name = tecnico.nombre_completo if tecnico else record.tecnico_id
                self.table.setItem(row, 2, QTableWidgetItem(tecnico_name))
                
                # Revision date
                fecha_str = ""
                if record.fecha_revision:
                    if isinstance(record.fecha_revision, datetime):
                        fecha_str = record.fecha_revision.strftime("%Y-%m-%d %H:%M")
                    else:
                        fecha_str = str(record.fecha_revision)
                self.table.setItem(row, 3, QTableWidgetItem(fecha_str))
                
                # Status
                status_item = QTableWidgetItem(record.estado.value)
                # Color code by status
                if record.estado == MaintenanceStatus.OK:
                    status_item.setForeground(QColor("#27ae60"))  # Green
                elif record.estado == MaintenanceStatus.REPAIR_NEEDED:
                    status_item.setForeground(QColor("#f39c12"))  # Orange
                elif record.estado == MaintenanceStatus.REPLACEMENT_NEEDED:
                    status_item.setForeground(QColor("#e67e22"))  # Dark orange
                else:  # OUT_OF_SERVICE
                    status_item.setForeground(QColor("#e74c3c"))  # Red
                self.table.setItem(row, 4, status_item)
                
                # Next revision
                next_rev_str = ""
                if record.proxima_revision:
                    if isinstance(record.proxima_revision, datetime):
                        next_rev_str = record.proxima_revision.strftime("%Y-%m-%d")
                    else:
                        next_rev_str = str(record.proxima_revision)
                self.table.setItem(row, 5, QTableWidgetItem(next_rev_str))
                
                # Actions
                actions_layout = QHBoxLayout()
                view_btn = QPushButton("Ver")
                view_btn.clicked.connect(lambda checked, r=record: self.view_record(r))
                actions_layout.addWidget(view_btn)
                
                if user_role in ["administrador", "tecnico"]:
                    edit_btn = QPushButton("Editar")
                    edit_btn.clicked.connect(lambda checked, r=record: self.edit_record(r))
                    actions_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("Eliminar")
                    delete_btn.clicked.connect(lambda checked, r=record: self.delete_record(r))
                    actions_layout.addWidget(delete_btn)
                
                actions_widget = QWidget()
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 6, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar registros: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading maintenance records: {e}", exc_info=True)
    
    def create_record(self, sensor_id: Optional[str] = None):
        """Create a new maintenance record"""
        try:
            dialog = MaintenanceRecordDialog(self, sensor_id=sensor_id)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                record_data = dialog.get_record_data()
                
                mongo_db = db_manager.get_mongo_db()
                neo4j_driver = db_manager.get_neo4j_driver()
                
                maintenance_repo = MaintenanceRepository(mongo_db)
                sensor_repo = SensorRepository(mongo_db)
                user_repo = UserRepository(mongo_db, neo4j_driver)
                
                maintenance_service = MaintenanceService(maintenance_repo, sensor_repo, user_repo)
                
                maintenance_service.create_record(record_data)
                
                QMessageBox.information(self, "Éxito", "Registro de control creado exitosamente")
                self.load_records()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear registro: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating maintenance record: {e}", exc_info=True)
    
    def view_record(self, record: MaintenanceRecord):
        """View maintenance record details"""
        try:
            mongo_db = db_manager.get_mongo_db()
            sensor_repo = SensorRepository(mongo_db)
            user_repo = UserRepository(mongo_db, db_manager.get_neo4j_driver())
            
            sensor = sensor_repo.get_by_id(record.sensor_id)
            tecnico = user_repo.get_by_id(record.tecnico_id)
            
            details = f"""
            <b>ID:</b> {record.id}<br>
            <b>Sensor:</b> {sensor.nombre if sensor else record.sensor_id}<br>
            <b>Técnico:</b> {tecnico.nombre_completo if tecnico else record.tecnico_id}<br>
            <b>Fecha de Revisión:</b> {record.fecha_revision.strftime("%Y-%m-%d %H:%M") if isinstance(record.fecha_revision, datetime) else record.fecha_revision}<br>
            <b>Estado:</b> {record.estado.value}<br>
            <b>Observaciones:</b> {record.observaciones or "N/A"}<br>
            <b>Acciones Realizadas:</b> {record.acciones_realizadas or "N/A"}<br>
            <b>Próxima Revisión:</b> {record.proxima_revision.strftime("%Y-%m-%d") if record.proxima_revision and isinstance(record.proxima_revision, datetime) else "N/A"}
            """
            
            QMessageBox.information(self, "Detalles del Registro", details)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al ver registro: {str(e)}")
    
    def edit_record(self, record: MaintenanceRecord):
        """Edit maintenance record"""
        try:
            dialog = MaintenanceRecordDialog(self, record=record)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                record_data = dialog.get_record_data()
                
                mongo_db = db_manager.get_mongo_db()
                neo4j_driver = db_manager.get_neo4j_driver()
                
                maintenance_repo = MaintenanceRepository(mongo_db)
                sensor_repo = SensorRepository(mongo_db)
                user_repo = UserRepository(mongo_db, neo4j_driver)
                
                maintenance_service = MaintenanceService(maintenance_repo, sensor_repo, user_repo)
                
                from desktop_app.models.maintenance_models import MaintenanceRecordUpdate
                update_data = MaintenanceRecordUpdate(
                    estado=record_data.estado,
                    observaciones=record_data.observaciones,
                    acciones_realizadas=record_data.acciones_realizadas,
                    proxima_revision=record_data.proxima_revision
                )
                
                maintenance_service.update_record(record.id, update_data)
                
                QMessageBox.information(self, "Éxito", "Registro actualizado exitosamente")
                self.load_records()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al editar registro: {str(e)}")
    
    def delete_record(self, record: MaintenanceRecord):
        """Delete maintenance record"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el registro de control {record.id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                mongo_db = db_manager.get_mongo_db()
                neo4j_driver = db_manager.get_neo4j_driver()
                
                maintenance_repo = MaintenanceRepository(mongo_db)
                sensor_repo = SensorRepository(mongo_db)
                user_repo = UserRepository(mongo_db, neo4j_driver)
                
                maintenance_service = MaintenanceService(maintenance_repo, sensor_repo, user_repo)
                
                maintenance_service.delete_record(record.id)
                
                QMessageBox.information(self, "Éxito", "Registro eliminado exitosamente")
                self.load_records()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar registro: {str(e)}")

