"""
Alert Rules widget for viewing and managing alert rules
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QComboBox, QGroupBox, QHeaderView, QAbstractItemView,
    QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from typing import Optional

from desktop_app.core.database import db_manager
from desktop_app.repositories.alert_rule_repository import AlertRuleRepository
from desktop_app.repositories.alert_repository import AlertRepository
from desktop_app.services.alert_rule_service import AlertRuleService
from desktop_app.models.alert_rule_models import (
    AlertRule, AlertRuleCreate, AlertRuleUpdate, AlertRuleStatus, LocationScope
)
from desktop_app.utils.session_manager import SessionManager


class AlertRuleDialog(QDialog):
    """Dialog for creating/editing alert rules"""
    
    def __init__(self, parent=None, rule: Optional[AlertRule] = None):
        super().__init__(parent)
        self.rule = rule
        self.setWindowTitle("Editar Regla de Alerta" if rule else "Crear Regla de Alerta")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self.init_ui()
        
        if rule:
            self.load_rule_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Name
        layout.addWidget(QLabel("Nombre:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Description
        layout.addWidget(QLabel("Descripción:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        layout.addWidget(self.desc_edit)
        
        # Temperature conditions
        temp_group = QGroupBox("Condiciones de Temperatura")
        temp_layout = QVBoxLayout()
        
        temp_row1 = QHBoxLayout()
        temp_row1.addWidget(QLabel("Temperatura Mínima:"))
        self.temp_min_spin = QDoubleSpinBox()
        self.temp_min_spin.setRange(-100, 100)
        self.temp_min_spin.setSpecialValueText("No establecido")
        self.temp_min_spin.setValue(-1000)  # Special value for "not set"
        temp_row1.addWidget(self.temp_min_spin)
        temp_row1.addWidget(QLabel("Temperatura Máxima:"))
        self.temp_max_spin = QDoubleSpinBox()
        self.temp_max_spin.setRange(-100, 100)
        self.temp_max_spin.setSpecialValueText("No establecido")
        self.temp_max_spin.setValue(-1000)
        temp_row1.addWidget(self.temp_max_spin)
        temp_layout.addLayout(temp_row1)
        
        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)
        
        # Humidity conditions
        hum_group = QGroupBox("Condiciones de Humedad")
        hum_layout = QVBoxLayout()
        
        hum_row1 = QHBoxLayout()
        hum_row1.addWidget(QLabel("Humedad Mínima:"))
        self.hum_min_spin = QDoubleSpinBox()
        self.hum_min_spin.setRange(0, 100)
        self.hum_min_spin.setSpecialValueText("No establecido")
        self.hum_min_spin.setValue(-1)  # Special value for "not set"
        hum_row1.addWidget(self.hum_min_spin)
        hum_row1.addWidget(QLabel("Humedad Máxima:"))
        self.hum_max_spin = QDoubleSpinBox()
        self.hum_max_spin.setRange(0, 100)
        self.hum_max_spin.setSpecialValueText("No establecido")
        self.hum_max_spin.setValue(-1)
        hum_row1.addWidget(self.hum_max_spin)
        hum_layout.addLayout(hum_row1)
        
        hum_group.setLayout(hum_layout)
        layout.addWidget(hum_group)
        
        # Location
        location_group = QGroupBox("Ubicación")
        location_layout = QVBoxLayout()
        
        location_layout.addWidget(QLabel("Ámbito:"))
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["ciudad", "region", "pais"])
        self.scope_combo.currentTextChanged.connect(self.on_scope_changed)
        location_layout.addWidget(self.scope_combo)
        
        location_layout.addWidget(QLabel("País:"))
        self.country_edit = QLineEdit()
        location_layout.addWidget(self.country_edit)
        
        self.city_label = QLabel("Ciudad:")
        self.city_edit = QLineEdit()
        location_layout.addWidget(self.city_label)
        location_layout.addWidget(self.city_edit)
        
        self.region_label = QLabel("Región:")
        self.region_edit = QLineEdit()
        location_layout.addWidget(self.region_label)
        location_layout.addWidget(self.region_edit)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # Date range
        date_group = QGroupBox("Rango de Tiempo")
        date_layout = QVBoxLayout()
        
        date_row1 = QHBoxLayout()
        date_row1.addWidget(QLabel("Fecha Inicio (Opcional):"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        date_row1.addWidget(self.start_date)
        
        date_row1.addWidget(QLabel("Fecha Fin (Opcional):"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_row1.addWidget(self.end_date)
        date_layout.addLayout(date_row1)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # Status and Priority
        meta_group = QGroupBox("Prioridad")
        meta_layout = QVBoxLayout()
        
        meta_row1 = QHBoxLayout()
        meta_row1.addWidget(QLabel("Estado:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["activa", "inactiva"])
        meta_row1.addWidget(self.status_combo)
        
        meta_row1.addWidget(QLabel("Prioridad (1-5):"))
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 5)
        self.priority_spin.setValue(1)
        meta_row1.addWidget(self.priority_spin)
        
        meta_layout.addLayout(meta_row1)
        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)
        
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
        self.on_scope_changed()
    
    def on_scope_changed(self):
        scope = self.scope_combo.currentText()
        if scope == "ciudad":
            self.city_label.setVisible(True)
            self.city_edit.setVisible(True)
            self.region_label.setVisible(False)
            self.region_edit.setVisible(False)
        elif scope == "region":
            self.city_label.setVisible(False)
            self.city_edit.setVisible(False)
            self.region_label.setVisible(True)
            self.region_edit.setVisible(True)
        else:  # pais
            self.city_label.setVisible(False)
            self.city_edit.setVisible(False)
            self.region_label.setVisible(False)
            self.region_edit.setVisible(False)
    
    def load_rule_data(self):
        if self.rule:
            self.name_edit.setText(self.rule.nombre)
            self.desc_edit.setPlainText(self.rule.descripcion)
            
            if self.rule.temp_min is not None:
                self.temp_min_spin.setValue(self.rule.temp_min)
            if self.rule.temp_max is not None:
                self.temp_max_spin.setValue(self.rule.temp_max)
            
            if self.rule.humidity_min is not None:
                self.hum_min_spin.setValue(self.rule.humidity_min)
            if self.rule.humidity_max is not None:
                self.hum_max_spin.setValue(self.rule.humidity_max)
            
            index = self.scope_combo.findText(self.rule.location_scope.value)
            if index >= 0:
                self.scope_combo.setCurrentIndex(index)
            
            self.country_edit.setText(self.rule.pais)
            if self.rule.ciudad:
                self.city_edit.setText(self.rule.ciudad)
            if self.rule.region:
                self.region_edit.setText(self.rule.region)
            
            if self.rule.fecha_inicio:
                qdate = QDate.fromString(self.rule.fecha_inicio.strftime("%Y-%m-%d"), "yyyy-MM-dd")
                self.start_date.setDate(qdate)
            if self.rule.fecha_fin:
                qdate = QDate.fromString(self.rule.fecha_fin.strftime("%Y-%m-%d"), "yyyy-MM-dd")
                self.end_date.setDate(qdate)
            
            index = self.status_combo.findText(self.rule.estado.value)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
            
            self.priority_spin.setValue(self.rule.prioridad)
    
    def get_data(self) -> dict:
        data = {
            "nombre": self.name_edit.text().strip(),
            "descripcion": self.desc_edit.toPlainText().strip(),
            "location_scope": LocationScope(self.scope_combo.currentText()),
            "pais": self.country_edit.text().strip(),
            "estado": AlertRuleStatus(self.status_combo.currentText()),
            "prioridad": self.priority_spin.value()
        }
        
        # Temperature
        temp_min_val = self.temp_min_spin.value()
        if temp_min_val > -1000:
            data["temp_min"] = temp_min_val
        else:
            data["temp_min"] = None
        
        temp_max_val = self.temp_max_spin.value()
        if temp_max_val > -1000:
            data["temp_max"] = temp_max_val
        else:
            data["temp_max"] = None
        
        # Humidity
        hum_min_val = self.hum_min_spin.value()
        if hum_min_val >= 0:
            data["humidity_min"] = hum_min_val
        else:
            data["humidity_min"] = None
        
        hum_max_val = self.hum_max_spin.value()
        if hum_max_val >= 0:
            data["humidity_max"] = hum_max_val
        else:
            data["humidity_max"] = None
        
        # Location based on scope
        scope = self.scope_combo.currentText()
        if scope == "ciudad":
            data["ciudad"] = self.city_edit.text().strip() or None
            data["region"] = None
        elif scope == "region":
            data["region"] = self.region_edit.text().strip() or None
            data["ciudad"] = None
        else:
            data["ciudad"] = None
            data["region"] = None
        
        # Dates - use None if not set
        start_date = self.start_date.date()
        if start_date.isValid():
            data["fecha_inicio"] = datetime(start_date.year(), start_date.month(), start_date.day())
        else:
            data["fecha_inicio"] = None
        
        end_date = self.end_date.date()
        if end_date.isValid():
            data["fecha_fin"] = datetime(end_date.year(), end_date.month(), end_date.day(), 23, 59, 59)
        else:
            data["fecha_fin"] = None
        
        return data


class AlertRulesWidget(QWidget):
    """Widget for managing alert rules"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.init_ui()
        self.load_rules()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title and actions
        header_layout = QHBoxLayout()
        title = QLabel("Reglas de Alerta")
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
        self.status_filter.addItems(["", "activa", "inactiva"])
        filter_layout.addWidget(self.status_filter)
        
        filter_btn = QPushButton("Filtrar")
        filter_btn.clicked.connect(self.load_rules)
        filter_layout.addWidget(filter_btn)
        
        clear_btn = QPushButton("Limpiar")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_rules)
        btn_layout.addWidget(refresh_btn)
        
        user_role = self.session_manager.get_user_role()
        if user_role in ["administrador", "tecnico"]:
            create_btn = QPushButton("Crear Regla")
            create_btn.clicked.connect(self.create_rule)
            btn_layout.addWidget(create_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Descripción", "Rango Temp", "Rango Humedad", 
            "Ubicación", "Estado", "Prioridad", "Creado", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def clear_filters(self):
        self.country_filter.clear()
        self.city_filter.clear()
        self.status_filter.setCurrentIndex(0)
        self.load_rules()
    
    def load_rules(self):
        try:
            mongo_db = db_manager.get_mongo_db()
            redis_client = db_manager.get_redis_client()
            
            rule_repo = AlertRuleRepository(mongo_db)
            alert_repo = AlertRepository(mongo_db, redis_client)
            rule_service = AlertRuleService(rule_repo, alert_repo)
            
            # Get filters
            country = self.country_filter.text().strip() or None
            city = self.city_filter.text().strip() or None
            status_str = self.status_filter.currentText()
            status = AlertRuleStatus(status_str) if status_str else None
            
            rules = rule_service.get_all_rules(
                skip=0,
                limit=1000,
                estado=status,
                pais=country,
                ciudad=city
            )
            
            self.table.setRowCount(len(rules))
            
            for row, rule in enumerate(rules):
                self.table.setItem(row, 0, QTableWidgetItem(str(rule.id)))
                self.table.setItem(row, 1, QTableWidgetItem(rule.nombre))
                self.table.setItem(row, 2, QTableWidgetItem(rule.descripcion[:100] + "..." if len(rule.descripcion) > 100 else rule.descripcion))
                
                temp_range = ""
                if rule.temp_min is not None or rule.temp_max is not None:
                    temp_range = f"{rule.temp_min or 'min'} - {rule.temp_max or 'max'} °C"
                self.table.setItem(row, 3, QTableWidgetItem(temp_range))
                
                hum_range = ""
                if rule.humidity_min is not None or rule.humidity_max is not None:
                    hum_range = f"{rule.humidity_min or 'min'} - {rule.humidity_max or 'max'} %"
                self.table.setItem(row, 4, QTableWidgetItem(hum_range))
                
                location_str = ""
                if rule.location_scope == LocationScope.CITY:
                    location_str = f"{rule.ciudad}, {rule.pais}"
                elif rule.location_scope == LocationScope.REGION:
                    location_str = f"{rule.region}, {rule.pais}"
                else:
                    location_str = rule.pais
                self.table.setItem(row, 5, QTableWidgetItem(location_str))
                
                self.table.setItem(row, 6, QTableWidgetItem(rule.estado.value))
                self.table.setItem(row, 7, QTableWidgetItem(str(rule.prioridad)))
                
                fecha_str = rule.fecha_creacion.strftime("%Y-%m-%d") if rule.fecha_creacion else ""
                self.table.setItem(row, 8, QTableWidgetItem(fecha_str))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(2, 2, 2, 2)
                
                user_role = self.session_manager.get_user_role()
                if user_role in ["administrador", "tecnico"]:
                    edit_btn = QPushButton("Editar")
                    edit_btn.clicked.connect(lambda checked, r=rule: self.edit_rule(r))
                    actions_layout.addWidget(edit_btn)
                    
                    delete_btn = QPushButton("Eliminar")
                    delete_btn.clicked.connect(lambda checked, r=rule: self.delete_rule(r))
                    actions_layout.addWidget(delete_btn)
                    
                    if rule.estado == AlertRuleStatus.ACTIVE:
                        deactivate_btn = QPushButton("Desactivar")
                        deactivate_btn.clicked.connect(lambda checked, r=rule: self.deactivate_rule(r))
                        actions_layout.addWidget(deactivate_btn)
                    else:
                        activate_btn = QPushButton("Activar")
                        activate_btn.clicked.connect(lambda checked, r=rule: self.activate_rule(r))
                        actions_layout.addWidget(activate_btn)
                
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 9, actions_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar reglas de alerta: {str(e)}")
    
    def create_rule(self):
        dialog = AlertRuleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                rule_data = AlertRuleCreate(**data)
                
                mongo_db = db_manager.get_mongo_db()
                redis_client = db_manager.get_redis_client()
                
                rule_repo = AlertRuleRepository(mongo_db)
                alert_repo = AlertRepository(mongo_db, redis_client)
                rule_service = AlertRuleService(rule_repo, alert_repo)
                
                user = self.session_manager.get_user()
                user_email = user.get("email", "") if user else ""
                # Fallback to user ID if email not available
                if not user_email:
                    user_id = self.session_manager.get_user_id()
                    user_email = f"user_{user_id}" if user_id else "unknown"
                rule_service.create_rule(rule_data, user_email)
                QMessageBox.information(self, "Éxito", "Regla de alerta creada exitosamente")
                self.load_rules()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al crear regla de alerta: {str(e)}")
    
    def edit_rule(self, rule: AlertRule):
        dialog = AlertRuleDialog(self, rule)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_data()
                rule_update = AlertRuleUpdate(**data)
                
                mongo_db = db_manager.get_mongo_db()
                redis_client = db_manager.get_redis_client()
                
                rule_repo = AlertRuleRepository(mongo_db)
                alert_repo = AlertRepository(mongo_db, redis_client)
                rule_service = AlertRuleService(rule_repo, alert_repo)
                
                rule_service.update_rule(rule.id, rule_update)
                QMessageBox.information(self, "Éxito", "Regla de alerta actualizada exitosamente")
                self.load_rules()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al actualizar regla de alerta: {str(e)}")
    
    def delete_rule(self, rule: AlertRule):
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar la regla de alerta '{rule.nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                mongo_db = db_manager.get_mongo_db()
                redis_client = db_manager.get_redis_client()
                
                rule_repo = AlertRuleRepository(mongo_db)
                alert_repo = AlertRepository(mongo_db, redis_client)
                rule_service = AlertRuleService(rule_repo, alert_repo)
                
                rule_service.delete_rule(rule.id)
                QMessageBox.information(self, "Éxito", "Regla de alerta eliminada exitosamente")
                self.load_rules()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar regla de alerta: {str(e)}")
    
    def activate_rule(self, rule: AlertRule):
        try:
            mongo_db = db_manager.get_mongo_db()
            redis_client = db_manager.get_redis_client()
            
            rule_repo = AlertRuleRepository(mongo_db)
            alert_repo = AlertRepository(mongo_db, redis_client)
            rule_service = AlertRuleService(rule_repo, alert_repo)
            
            rule_service.activate_rule(rule.id)
            QMessageBox.information(self, "Éxito", "Regla de alerta activada exitosamente")
            self.load_rules()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al activar regla de alerta: {str(e)}")
    
    def deactivate_rule(self, rule: AlertRule):
        try:
            mongo_db = db_manager.get_mongo_db()
            redis_client = db_manager.get_redis_client()
            
            rule_repo = AlertRuleRepository(mongo_db)
            alert_repo = AlertRepository(mongo_db, redis_client)
            rule_service = AlertRuleService(rule_repo, alert_repo)
            
            rule_service.deactivate_rule(rule.id)
            QMessageBox.information(self, "Éxito", "Regla de alerta desactivada exitosamente")
            self.load_rules()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al desactivar regla de alerta: {str(e)}")
