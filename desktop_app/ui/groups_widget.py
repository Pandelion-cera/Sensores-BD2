"""
Groups management widget for administrators
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QListWidget, QListWidgetItem, QComboBox,
    QHeaderView, QAbstractItemView, QGroupBox
)
from PyQt6.QtCore import Qt
from datetime import datetime

from desktop_app.core.database import db_manager
from desktop_app.repositories.group_repository import GroupRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.repositories.invoice_repository import InvoiceRepository
from desktop_app.services.user_service import UserService
from desktop_app.models.group_models import Group, GroupCreate
from desktop_app.utils.session_manager import SessionManager


class GroupsWidget(QWidget):
    """Widget for managing groups (admin only)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.init_ui()
        self.load_groups()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Gestión de Grupos")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Crear Grupo")
        create_btn.clicked.connect(self.show_create_dialog)
        btn_layout.addWidget(create_btn)
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_groups)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Groups table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Nombre", "Miembros", "Fecha de Creación", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_groups(self):
        """Load all groups"""
        try:
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            group_repo = GroupRepository(mongo_db, neo4j_driver)
            user_repo = UserRepository(mongo_db, neo4j_driver)
            
            groups = group_repo.get_all(skip=0, limit=100)
            
            self.table.setRowCount(len(groups))
            for row, group in enumerate(groups):
                # Group name
                self.table.setItem(row, 0, QTableWidgetItem(group.nombre))
                
                # Members count and names
                members_text = f"{len(group.miembros)} miembros"
                if group.miembros:
                    # Get member names
                    member_names = []
                    for user_id in group.miembros[:5]:  # Show first 5
                        user = user_repo.get_by_id(user_id)
                        if user:
                            member_names.append(user.nombre_completo)
                    if member_names:
                        members_text = f"{len(group.miembros)} miembros: {', '.join(member_names)}"
                        if len(group.miembros) > 5:
                            members_text += "..."
                
                self.table.setItem(row, 1, QTableWidgetItem(members_text))
                
                # Creation date
                fecha_str = ""
                if group.fecha_creacion:
                    if isinstance(group.fecha_creacion, datetime):
                        fecha_str = group.fecha_creacion.strftime("%Y-%m-%d")
                    else:
                        fecha_str = str(group.fecha_creacion)
                self.table.setItem(row, 2, QTableWidgetItem(fecha_str))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                manage_btn = QPushButton("Gestionar")
                manage_btn.clicked.connect(lambda checked, g=group: self.show_manage_dialog(g))
                actions_layout.addWidget(manage_btn)
                
                delete_btn = QPushButton("Eliminar")
                delete_btn.setStyleSheet("background-color: #dc3545; color: white;")
                delete_btn.clicked.connect(lambda checked, g=group: self.delete_group(g))
                actions_layout.addWidget(delete_btn)
                
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 3, actions_widget)
                
                # Store group ID in hidden column data
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, group.id)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar grupos: {str(e)}")
            self.table.setRowCount(0)
    
    def show_create_dialog(self):
        """Show dialog to create a new group"""
        dialog = CreateGroupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_groups()
    
    def show_manage_dialog(self, group: Group):
        """Show dialog to manage group members"""
        dialog = ManageGroupDialog(group, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_groups()
    
    def delete_group(self, group: Group):
        """Delete a group"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el grupo '{group.nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                mongo_db = db_manager.get_mongo_db()
                neo4j_driver = db_manager.get_neo4j_driver()
                
                group_repo = GroupRepository(mongo_db, neo4j_driver)
                success = group_repo.delete(group.id)
                
                if success:
                    QMessageBox.information(self, "Éxito", "Grupo eliminado correctamente")
                    self.load_groups()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo eliminar el grupo")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar grupo: {str(e)}")


class CreateGroupDialog(QDialog):
    """Dialog for creating a new group"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Grupo")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Group name
        name_label = QLabel("Nombre del Grupo:")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Equipo Técnico")
        layout.addWidget(self.name_input)
        
        # Available users
        users_label = QLabel("Usuarios Disponibles:")
        layout.addWidget(users_label)
        
        self.users_list = QListWidget()
        self.users_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.users_list.setMinimumHeight(200)
        layout.addWidget(self.users_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        create_btn = QPushButton("Crear")
        create_btn.clicked.connect(self.create_group)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_users(self):
        """Load all users"""
        try:
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            user_repo = UserRepository(mongo_db, neo4j_driver)
            invoice_repo = InvoiceRepository(mongo_db)
            user_service = UserService(user_repo, invoice_repo)
            
            users = user_service.get_all_users(skip=0, limit=200)
            
            self.users_list.clear()
            for user in users:
                item = QListWidgetItem(f"{user.nombre_completo} ({user.email})")
                item.setData(Qt.ItemDataRole.UserRole, user.id)
                self.users_list.addItem(item)
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar usuarios: {str(e)}")
    
    def create_group(self):
        """Create the group"""
        try:
            # Validate name
            name = self.name_input.text().strip()
            if not name or len(name) < 3:
                QMessageBox.warning(self, "Error", "El nombre del grupo debe tener al menos 3 caracteres")
                return
            
            if len(name) > 100:
                QMessageBox.warning(self, "Error", "El nombre del grupo no puede exceder 100 caracteres")
                return
            
            # Get selected users
            selected_items = self.users_list.selectedItems()
            member_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
            
            # Create group
            group_data = GroupCreate(
                nombre=name,
                miembros=member_ids
            )
            
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            group_repo = GroupRepository(mongo_db, neo4j_driver)
            group_repo.create(group_data)
            
            QMessageBox.information(self, "Éxito", "Grupo creado correctamente")
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear grupo: {str(e)}")


class ManageGroupDialog(QDialog):
    """Dialog for managing group members"""
    
    def __init__(self, group: Group, parent=None):
        super().__init__(parent)
        self.group = group
        self.setWindowTitle(f"Gestionar Grupo: {group.nombre}")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.init_ui()
        self.load_members()
        self.load_available_users()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Group info
        info_label = QLabel(f"Grupo: {self.group.nombre}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(info_label)
        
        # Two column layout
        columns_layout = QHBoxLayout()
        
        # Current members
        members_group = QGroupBox("Miembros Actuales")
        members_layout = QVBoxLayout()
        
        self.members_list = QListWidget()
        self.members_list.setMinimumHeight(300)
        members_layout.addWidget(self.members_list)
        
        remove_btn = QPushButton("Remover Seleccionados")
        remove_btn.setStyleSheet("background-color: #dc3545; color: white;")
        remove_btn.clicked.connect(self.remove_members)
        members_layout.addWidget(remove_btn)
        
        members_group.setLayout(members_layout)
        columns_layout.addWidget(members_group)
        
        # Available users
        users_group = QGroupBox("Usuarios Disponibles")
        users_layout = QVBoxLayout()
        
        self.available_users_list = QListWidget()
        self.available_users_list.setMinimumHeight(300)
        users_layout.addWidget(self.available_users_list)
        
        add_btn = QPushButton("Agregar Seleccionados")
        add_btn.setStyleSheet("background-color: #28a745; color: white;")
        add_btn.clicked.connect(self.add_members)
        users_layout.addWidget(add_btn)
        
        users_group.setLayout(users_layout)
        columns_layout.addWidget(users_group)
        
        layout.addLayout(columns_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_members(self):
        """Load current group members"""
        try:
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            user_repo = UserRepository(mongo_db, neo4j_driver)
            group_repo = GroupRepository(mongo_db, neo4j_driver)
            
            # Refresh group data
            group = group_repo.get_by_id(self.group.id)
            if not group:
                QMessageBox.warning(self, "Error", "Grupo no encontrado")
                self.reject()
                return
            
            self.group = group
            self.members_list.clear()
            
            for user_id in group.miembros:
                user = user_repo.get_by_id(user_id)
                if user:
                    item = QListWidgetItem(f"{user.nombre_completo} ({user.email})")
                    item.setData(Qt.ItemDataRole.UserRole, user_id)
                    self.members_list.addItem(item)
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar miembros: {str(e)}")
    
    def load_available_users(self):
        """Load users not in the group"""
        try:
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            user_repo = UserRepository(mongo_db, neo4j_driver)
            invoice_repo = InvoiceRepository(mongo_db)
            user_service = UserService(user_repo, invoice_repo)
            
            users = user_service.get_all_users(skip=0, limit=200)
            
            self.available_users_list.clear()
            current_member_ids = set(self.group.miembros)
            
            for user in users:
                if user.id not in current_member_ids:
                    item = QListWidgetItem(f"{user.nombre_completo} ({user.email})")
                    item.setData(Qt.ItemDataRole.UserRole, user.id)
                    self.available_users_list.addItem(item)
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar usuarios: {str(e)}")
    
    def add_members(self):
        """Add selected users to the group"""
        try:
            selected_items = self.available_users_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Advertencia", "Seleccione al menos un usuario para agregar")
                return
            
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            group_repo = GroupRepository(mongo_db, neo4j_driver)
            
            added_count = 0
            for item in selected_items:
                user_id = item.data(Qt.ItemDataRole.UserRole)
                if group_repo.add_member(self.group.id, user_id):
                    added_count += 1
            
            if added_count > 0:
                QMessageBox.information(self, "Éxito", f"{added_count} usuario(s) agregado(s) correctamente")
                self.load_members()
                self.load_available_users()
            else:
                QMessageBox.warning(self, "Advertencia", "No se pudieron agregar los usuarios")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al agregar miembros: {str(e)}")
    
    def remove_members(self):
        """Remove selected users from the group"""
        try:
            selected_items = self.members_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Advertencia", "Seleccione al menos un miembro para remover")
                return
            
            reply = QMessageBox.question(
                self,
                "Confirmar",
                f"¿Está seguro de que desea remover {len(selected_items)} miembro(s) del grupo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            group_repo = GroupRepository(mongo_db, neo4j_driver)
            
            removed_count = 0
            for item in selected_items:
                user_id = item.data(Qt.ItemDataRole.UserRole)
                if group_repo.remove_member(self.group.id, user_id):
                    removed_count += 1
            
            if removed_count > 0:
                QMessageBox.information(self, "Éxito", f"{removed_count} miembro(s) removido(s) correctamente")
                self.load_members()
                self.load_available_users()
            else:
                QMessageBox.warning(self, "Advertencia", "No se pudieron remover los miembros")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al remover miembros: {str(e)}")

