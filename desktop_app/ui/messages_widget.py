"""
Messages widget for viewing messages
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from datetime import datetime

from desktop_app.core.database import db_manager
from desktop_app.repositories.message_repository import MessageRepository
from desktop_app.repositories.group_repository import GroupRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.services.message_service import MessageService
from desktop_app.utils.session_manager import SessionManager


class MessagesWidget(QWidget):
    """Widget for viewing messages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.init_ui()
        self.load_messages()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Mensajes")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Tabs for private and group messages
        self.tabs = QTabWidget()
        
        # Private messages tab
        private_container = QWidget()
        private_layout = QVBoxLayout()
        self.private_table = QTableWidget()
        self.private_table.setColumnCount(5)
        self.private_table.setHorizontalHeaderLabels([
            "De", "Tipo", "Contenido", "Fecha", "ID"
        ])
        self.private_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.private_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.private_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        private_layout.addWidget(self.private_table)
        private_container.setLayout(private_layout)
        self.tabs.addTab(private_container, "Mensajes Privados")
        
        # Group messages tab
        group_container = QWidget()
        group_layout = QVBoxLayout()
        self.group_table = QTableWidget()
        self.group_table.setColumnCount(5)
        self.group_table.setHorizontalHeaderLabels([
            "De", "Tipo", "Contenido", "Fecha", "ID"
        ])
        self.group_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.group_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.group_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        group_layout.addWidget(self.group_table)
        group_container.setLayout(group_layout)
        self.tabs.addTab(group_container, "Mensajes Grupales")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_messages)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_messages(self):
        try:
            user_id = self.session_manager.get_user_id()
            if not user_id:
                QMessageBox.warning(self, "Error", "Usuario no conectado")
                return
            
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            
            message_repo = MessageRepository(mongo_db)
            group_repo = GroupRepository(mongo_db, neo4j_driver)
            user_repo = UserRepository(mongo_db, neo4j_driver)
            message_service = MessageService(message_repo, group_repo, user_repo)
            
            # Get all messages
            all_messages = message_service.get_all_user_messages(user_id, skip=0, limit=200)
            
            # Load private messages
            private_msgs = all_messages.get("private", [])
            self.private_table.setRowCount(len(private_msgs))
            for row, msg in enumerate(private_msgs):
                self.private_table.setItem(row, 0, QTableWidgetItem(msg.sender_name or "Desconocido"))
                self.private_table.setItem(row, 1, QTableWidgetItem("Privado"))
                self.private_table.setItem(row, 2, QTableWidgetItem(msg.content))
                fecha_str = ""
                if msg.timestamp:
                    if isinstance(msg.timestamp, datetime):
                        fecha_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        fecha_str = str(msg.timestamp)
                self.private_table.setItem(row, 3, QTableWidgetItem(fecha_str))
                self.private_table.setItem(row, 4, QTableWidgetItem(str(msg.id)))
            
            # Load group messages
            group_msgs = all_messages.get("group", [])
            self.group_table.setRowCount(len(group_msgs))
            for row, msg in enumerate(group_msgs):
                self.group_table.setItem(row, 0, QTableWidgetItem(msg.sender_name or "Desconocido"))
                self.group_table.setItem(row, 1, QTableWidgetItem("Grupal"))
                self.group_table.setItem(row, 2, QTableWidgetItem(msg.content))
                fecha_str = ""
                if msg.timestamp:
                    if isinstance(msg.timestamp, datetime):
                        fecha_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        fecha_str = str(msg.timestamp)
                self.group_table.setItem(row, 3, QTableWidgetItem(fecha_str))
                self.group_table.setItem(row, 4, QTableWidgetItem(str(msg.id)))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar mensajes: {str(e)}")
