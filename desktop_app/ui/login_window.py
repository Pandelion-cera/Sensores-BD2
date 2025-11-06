"""
Login window for desktop application
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any

from desktop_app.core.database import db_manager
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.repositories.session_repository import SessionRepository
from desktop_app.services.auth_service import AuthService
from desktop_app.models.user_models import UserCreate, UserLogin
from desktop_app.utils.session_manager import SessionManager


class LoginWindow(QDialog):
    """Login and registration dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Sensores - Inicio de Sesión")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)
        
        self.session_manager = SessionManager.get_instance()
        
        # Initialize services
        mongo_db = db_manager.get_mongo_db()
        redis_client = db_manager.get_redis_client()
        neo4j_driver = db_manager.get_neo4j_driver()
        
        user_repo = UserRepository(mongo_db, neo4j_driver)
        session_repo = SessionRepository(redis_client, mongo_db)
        self.auth_service = AuthService(user_repo, session_repo)
        
        self.result_data: Optional[Dict[str, Any]] = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Sistema de Gestión de Sensores")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Login tab
        login_tab = self.create_login_tab()
        self.tabs.addTab(login_tab, "Iniciar Sesión")
        
        # Register tab
        register_tab = self.create_register_tab()
        self.tabs.addTab(register_tab, "Registrarse")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def create_login_tab(self) -> QWidget:
        """Create login tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Email
        email_label = QLabel("Email:")
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("admin@test.com")
        layout.addWidget(email_label)
        layout.addWidget(self.login_email)
        
        # Password
        password_label = QLabel("Contraseña:")
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("Ingrese su contraseña")
        layout.addWidget(password_label)
        layout.addWidget(self.login_password)
        
        # Login button
        login_btn = QPushButton("Iniciar Sesión")
        login_btn.setStyleSheet("background-color: #007bff; color: white; padding: 8px;")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_register_tab(self) -> QWidget:
        """Create register tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Full name
        name_label = QLabel("Nombre Completo:")
        self.register_name = QLineEdit()
        self.register_name.setPlaceholderText("Juan Pérez")
        layout.addWidget(name_label)
        layout.addWidget(self.register_name)
        
        # Email
        email_label = QLabel("Email:")
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("usuario@ejemplo.com")
        layout.addWidget(email_label)
        layout.addWidget(self.register_email)
        
        # Password
        password_label = QLabel("Contraseña:")
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setPlaceholderText("Mínimo 6 caracteres")
        layout.addWidget(password_label)
        layout.addWidget(self.register_password)
        
        # Register button
        register_btn = QPushButton("Registrarse")
        register_btn.setStyleSheet("background-color: #28a745; color: white; padding: 8px;")
        register_btn.clicked.connect(self.handle_register)
        layout.addWidget(register_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def handle_login(self):
        """Handle login button click"""
        email = self.login_email.text().strip()
        password = self.login_password.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error de Validación", "Por favor complete todos los campos")
            return
        
        try:
            login_data = UserLogin(email=email, password=password)
            result = self.auth_service.login(login_data)
            
            # Store in session manager
            self.session_manager.set_session(
                token=result["access_token"],
                session_id=result["session_id"],
                user=result["user"]
            )
            
            self.result_data = result
            self.accept()
            
        except ValueError as e:
            QMessageBox.critical(self, "Error de Inicio de Sesión", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")
    
    def handle_register(self):
        """Handle register button click"""
        name = self.register_name.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        
        if not name or not email or not password:
            QMessageBox.warning(self, "Error de Validación", "Por favor complete todos los campos")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Error de Validación", "La contraseña debe tener al menos 6 caracteres")
            return
        
        try:
            user_data = UserCreate(
                nombre_completo=name,
                email=email,
                password=password
            )
            result = self.auth_service.register(user_data)
            QMessageBox.information(
                self,
                "Registro Exitoso",
                f"Usuario {result['email']} registrado exitosamente!\nPor favor inicie sesión con sus credenciales."
            )
            # Switch to login tab
            self.tabs.setCurrentIndex(0)
            self.login_email.setText(email)
            
        except ValueError as e:
            QMessageBox.critical(self, "Error de Registro", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")

