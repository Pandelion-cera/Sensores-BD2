"""
Messages widget for viewing messages
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QTabWidget,
    QHeaderView, QAbstractItemView, QDialog, QComboBox,
    QTextEdit, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt6.QtCore import Qt
from datetime import datetime

from desktop_app.core.database import db_manager
from desktop_app.repositories.message_repository import MessageRepository
from desktop_app.repositories.group_repository import GroupRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.repositories.invoice_repository import InvoiceRepository
from desktop_app.services.message_service import MessageService
from desktop_app.services.user_service import UserService
from desktop_app.models.message_models import MessageCreate, MessageType
from desktop_app.utils.session_manager import SessionManager


class MessagesWidget(QWidget):
    """Widget for viewing messages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        # Store messages for detail view
        self.private_messages = {}  # row -> MessageResponse
        self.group_messages = {}  # table -> {row -> MessageResponse}
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
        self.private_table.itemDoubleClicked.connect(self.show_message_detail)
        private_layout.addWidget(self.private_table)
        private_container.setLayout(private_layout)
        self.tabs.addTab(private_container, "Mensajes Privados")
        
        # Group messages tab - will be populated with group-specific tabs
        self.group_tabs = QTabWidget()
        
        # Create a container for the group messages tabs
        group_container = QWidget()
        group_layout = QVBoxLayout()
        group_layout.addWidget(self.group_tabs)
        group_container.setLayout(group_layout)
        self.tabs.addTab(group_container, "Mensajes Grupales")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        send_btn = QPushButton("Enviar Mensaje")
        send_btn.clicked.connect(self.show_send_dialog)
        btn_layout.addWidget(send_btn)
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
            self.private_messages = {}  # Clear previous messages
            self.private_table.setRowCount(len(private_msgs))
            for row, msg in enumerate(private_msgs):
                self.private_messages[row] = msg  # Store message for detail view
                self.private_table.setItem(row, 0, QTableWidgetItem(msg.sender_name or "Desconocido"))
                self.private_table.setItem(row, 1, QTableWidgetItem("Privado"))
                # Truncate content for display
                display_content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                self.private_table.setItem(row, 2, QTableWidgetItem(display_content))
                fecha_str = ""
                if msg.timestamp:
                    if isinstance(msg.timestamp, datetime):
                        fecha_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        fecha_str = str(msg.timestamp)
                self.private_table.setItem(row, 3, QTableWidgetItem(fecha_str))
                self.private_table.setItem(row, 4, QTableWidgetItem(str(msg.id)))
            
            # Load group messages - organize by group
            group_msgs = all_messages.get("group", [])
            
            # Clear existing group tabs
            self.group_tabs.clear()
            
            # Group messages by recipient_id (group_id)
            messages_by_group = {}
            for msg in group_msgs:
                group_id = msg.recipient_id
                group_name = msg.recipient_name or f"Grupo {group_id[:8]}"
                if group_id not in messages_by_group:
                    messages_by_group[group_id] = {
                        "name": group_name,
                        "messages": []
                    }
                messages_by_group[group_id]["messages"].append(msg)
            
            # Create a table for each group
            self.group_messages = {}  # Clear previous messages
            for group_id, group_data in messages_by_group.items():
                group_table = QTableWidget()
                group_table.setColumnCount(4)
                group_table.setHorizontalHeaderLabels([
                    "De", "Contenido", "Fecha", "ID"
                ])
                group_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                group_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
                group_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
                group_table.itemDoubleClicked.connect(self.show_message_detail)
                
                # Populate table with messages for this group
                messages = group_data["messages"]
                group_table.setRowCount(len(messages))
                group_messages_dict = {}  # Store messages for this group table
                for row, msg in enumerate(messages):
                    group_messages_dict[row] = msg  # Store message for detail view
                    group_table.setItem(row, 0, QTableWidgetItem(msg.sender_name or "Desconocido"))
                    # Truncate content for display
                    display_content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    group_table.setItem(row, 1, QTableWidgetItem(display_content))
                    fecha_str = ""
                    if msg.timestamp:
                        if isinstance(msg.timestamp, datetime):
                            fecha_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            fecha_str = str(msg.timestamp)
                    group_table.setItem(row, 2, QTableWidgetItem(fecha_str))
                    group_table.setItem(row, 3, QTableWidgetItem(str(msg.id)))
                
                self.group_messages[group_table] = group_messages_dict  # Store messages for this table
                
                # Add tab for this group
                group_widget = QWidget()
                group_widget_layout = QVBoxLayout()
                group_widget_layout.addWidget(group_table)
                group_widget.setLayout(group_widget_layout)
                self.group_tabs.addTab(group_widget, group_data["name"])
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar mensajes: {str(e)}")
    
    def show_send_dialog(self):
        """Show dialog to send a new message"""
        dialog = SendMessageDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_messages()  # Refresh messages after sending
    
    def show_message_detail(self, item):
        """Show detailed view of a message"""
        table = item.tableWidget()
        row = item.row()
        
        # Get the message based on which table was clicked
        if table == self.private_table:
            if row in self.private_messages:
                msg = self.private_messages[row]
                dialog = MessageDetailDialog(msg, self)
                dialog.exec()
        else:
            # Check if this is a group table
            if table in self.group_messages:
                if row in self.group_messages[table]:
                    msg = self.group_messages[table][row]
                    dialog = MessageDetailDialog(msg, self)
                    dialog.exec()


class SendMessageDialog(QDialog):
    """Dialog for sending a new message"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.setWindowTitle("Enviar Mensaje")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()
        self.load_recipients()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Message type selection
        type_group = QGroupBox("Tipo de Mensaje")
        type_layout = QVBoxLayout()
        self.type_button_group = QButtonGroup()
        
        self.private_radio = QRadioButton("Privado")
        self.private_radio.setChecked(True)
        self.private_radio.toggled.connect(self.on_type_changed)
        self.type_button_group.addButton(self.private_radio, 0)
        type_layout.addWidget(self.private_radio)
        
        self.group_radio = QRadioButton("Grupal")
        self.group_radio.toggled.connect(self.on_type_changed)
        self.type_button_group.addButton(self.group_radio, 1)
        type_layout.addWidget(self.group_radio)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Recipient selection
        recipient_label = QLabel("Destinatario:")
        layout.addWidget(recipient_label)
        
        self.recipient_combo = QComboBox()
        self.recipient_combo.setEditable(True)  # Allow typing email/ID for private messages
        layout.addWidget(self.recipient_combo)
        
        # Message content
        content_label = QLabel("Mensaje:")
        layout.addWidget(content_label)
        
        self.content_text = QTextEdit()
        self.content_text.setMinimumHeight(150)
        self.content_text.setPlaceholderText("Escribe tu mensaje aquí...")
        layout.addWidget(self.content_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        send_btn = QPushButton("Enviar")
        send_btn.clicked.connect(self.send_message)
        btn_layout.addWidget(send_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def on_type_changed(self):
        """Update recipient list when message type changes"""
        self.load_recipients()
    
    def load_recipients(self):
        """Load available recipients based on message type"""
        self.recipient_combo.clear()
        
        try:
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            user_id = self.session_manager.get_user_id()
            
            if self.private_radio.isChecked():
                # Load all users for private messages
                user_repo = UserRepository(mongo_db, neo4j_driver)
                invoice_repo = InvoiceRepository(mongo_db)
                user_service = UserService(user_repo, invoice_repo)
                users = user_service.get_all_users(skip=0, limit=200)
                
                for user in users:
                    if user.id != user_id:  # Don't show current user
                        display_text = f"{user.nombre_completo} ({user.email})"
                        self.recipient_combo.addItem(display_text, user.email)
            else:
                # Load user's groups for group messages
                group_repo = GroupRepository(mongo_db, neo4j_driver)
                groups = group_repo.get_user_groups(user_id)
                
                for group in groups:
                    self.recipient_combo.addItem(group.nombre, group.id)
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar destinatarios: {str(e)}")
    
    def send_message(self):
        """Send the message"""
        try:
            # Validate content
            content = self.content_text.toPlainText().strip()
            if not content:
                QMessageBox.warning(self, "Error", "El mensaje no puede estar vacío")
                return
            
            if len(content) > 1000:
                QMessageBox.warning(self, "Error", "El mensaje no puede exceder 1000 caracteres")
                return
            
            # Get recipient
            recipient_data = self.recipient_combo.currentData()
            recipient_text = self.recipient_combo.currentText()
            
            if not recipient_data and not recipient_text:
                QMessageBox.warning(self, "Error", "Debe seleccionar un destinatario")
                return
            
            # Use data if available, otherwise use text (for manually entered emails/IDs)
            recipient_id = recipient_data if recipient_data else recipient_text.strip()
            
            # Determine message type
            message_type = MessageType.PRIVATE if self.private_radio.isChecked() else MessageType.GROUP
            
            # Create message
            message_data = MessageCreate(
                recipient_type=message_type,
                recipient_id=recipient_id,
                content=content
            )
            
            # Send message
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
            
            message_service.send_message(user_id, message_data)
            
            QMessageBox.information(self, "Éxito", "Mensaje enviado correctamente")
            self.accept()
        
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al enviar mensaje: {str(e)}")


class MessageDetailDialog(QDialog):
    """Dialog for viewing full message details"""
    
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.message = message
        self.setWindowTitle("Detalle del Mensaje")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Message type
        type_label = QLabel(f"Tipo: {self.message.recipient_type.value.capitalize()}")
        type_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(type_label)
        
        # Sender
        sender_label = QLabel(f"De: {self.message.sender_name or 'Desconocido'}")
        sender_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(sender_label)
        
        # Recipient (for group messages)
        if self.message.recipient_type == MessageType.GROUP and self.message.recipient_name:
            recipient_label = QLabel(f"Grupo: {self.message.recipient_name}")
            recipient_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(recipient_label)
        
        # Timestamp
        fecha_str = ""
        if self.message.timestamp:
            if isinstance(self.message.timestamp, datetime):
                fecha_str = self.message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fecha_str = str(self.message.timestamp)
        date_label = QLabel(f"Fecha: {fecha_str}")
        date_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(date_label)
        
        # Separator
        separator = QLabel("─" * 50)
        layout.addWidget(separator)
        
        # Message content
        content_label = QLabel("Mensaje:")
        content_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(content_label)
        
        content_text = QTextEdit()
        content_text.setReadOnly(True)
        content_text.setPlainText(self.message.content)
        content_text.setMinimumHeight(200)
        layout.addWidget(content_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
