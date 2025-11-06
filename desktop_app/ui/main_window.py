"""
Main window for desktop application
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QMenuBar, QStatusBar, QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from desktop_app.utils.session_manager import SessionManager
from desktop_app.ui.dashboard_widget import DashboardWidget
from desktop_app.ui.sensors_widget import SensorsWidget
from desktop_app.ui.measurements_widget import MeasurementsWidget
from desktop_app.ui.alerts_widget import AlertsWidget
from desktop_app.ui.alert_rules_widget import AlertRulesWidget
from desktop_app.ui.messages_widget import MessagesWidget
from desktop_app.ui.invoices_widget import InvoicesWidget
from desktop_app.ui.processes_widget import ProcessesWidget
from desktop_app.ui.groups_widget import GroupsWidget
from pathlib import Path
import logging
import subprocess
import platform


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signal emitted when user logs out
    logout_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Sensores")
        self.setMinimumSize(1000, 700)
        
        self.session_manager = SessionManager.get_instance()
        
        self.init_ui()
        self.update_status()
    
    def init_ui(self):
        """Initialize UI components"""
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Dashboard tab
        self.dashboard_widget = DashboardWidget()
        self.tabs.addTab(self.dashboard_widget, "Tablero")
        
        # Sensors tab
        self.sensors_widget = SensorsWidget()
        self.tabs.addTab(self.sensors_widget, "Sensores")
        
        # Measurements tab
        self.measurements_widget = MeasurementsWidget()
        self.tabs.addTab(self.measurements_widget, "Mediciones")
        
        # Alerts tab
        self.alerts_widget = AlertsWidget()
        self.tabs.addTab(self.alerts_widget, "Alertas")
        
        # Alert Rules tab
        user_role = self.session_manager.get_user_role()
        if user_role in ["administrador", "tecnico"]:
            self.alert_rules_widget = AlertRulesWidget()
            self.tabs.addTab(self.alert_rules_widget, "Reglas de Alerta")
        
        # Messages tab
        self.messages_widget = MessagesWidget()
        self.tabs.addTab(self.messages_widget, "Mensajes")
        
        # Invoices tab
        self.invoices_widget = InvoicesWidget()
        self.tabs.addTab(self.invoices_widget, "Facturas")
        
        # Processes tab
        self.processes_widget = ProcessesWidget()
        self.tabs.addTab(self.processes_widget, "Procesos")
        
        # Groups management tab (admin only)
        if user_role == "administrador":
            self.groups_widget = GroupsWidget()
            self.tabs.addTab(self.groups_widget, "Grupos")
        
        layout.addWidget(self.tabs)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # User info label
        user = self.session_manager.get_user()
        if user:
            user_info = f"Conectado como: {user.get('nombre_completo', '')} ({user.get('role', '')})"
            self.status_bar.addWidget(QLabel(user_info))
        
        self.status_bar.addPermanentWidget(QLabel("Listo"))
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Archivo")
        
        logout_action = QAction("Cerrar Sesión", self)
        logout_action.triggered.connect(self.handle_logout)
        file_menu.addAction(logout_action)
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("Ver")
        refresh_action = QAction("Actualizar", self)
        refresh_action.triggered.connect(self.refresh_current_tab)
        view_menu.addAction(refresh_action)
        
        view_logs_action = QAction("Ver Logs", self)
        view_logs_action.triggered.connect(self.open_logs_folder)
        view_menu.addAction(view_logs_action)
        
        # Help menu
        help_menu = menubar.addMenu("Ayuda")
        about_action = QAction("Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def update_status(self):
        """Update status bar"""
        # Check database connections
        from desktop_app.core.database import db_manager
        try:
            db_manager.get_mongo_client()
            db_manager.get_neo4j_driver()
            db_manager.get_cassandra_session()
            db_manager.get_redis_client()
            self.status_bar.showMessage("Todas las bases de datos conectadas", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Error de conexión a base de datos: {str(e)}", 0)
    
    def refresh_current_tab(self):
        """Refresh current tab"""
        current_widget = self.tabs.currentWidget()
        
        if current_widget == self.dashboard_widget:
            self.dashboard_widget.refresh()
        elif current_widget == self.sensors_widget:
            self.sensors_widget.load_sensors()
        elif current_widget == self.measurements_widget:
            # Measurements require search filters, so just refresh if they've already searched
            pass
        elif current_widget == self.alerts_widget:
            self.alerts_widget.load_alerts()
        elif hasattr(self, 'alert_rules_widget') and current_widget == self.alert_rules_widget:
            self.alert_rules_widget.load_rules()
        elif current_widget == self.messages_widget:
            self.messages_widget.load_messages()
        elif current_widget == self.invoices_widget:
            self.invoices_widget.load_invoices()
        elif current_widget == self.processes_widget:
            self.processes_widget.load_processes()
        elif hasattr(self, 'groups_widget') and current_widget == self.groups_widget:
            self.groups_widget.load_groups()
        self.status_bar.showMessage("Actualizado", 2000)
    
    def handle_logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self,
            "Confirmar Cierre de Sesión",
            "¿Está seguro que desea cerrar sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from desktop_app.services.auth_service import AuthService
            from desktop_app.core.database import db_manager
            from desktop_app.repositories.user_repository import UserRepository
            from desktop_app.repositories.session_repository import SessionRepository
            
            session_id = self.session_manager.session_id
            if session_id:
                try:
                    mongo_db = db_manager.get_mongo_db()
                    redis_client = db_manager.get_redis_client()
                    neo4j_driver = db_manager.get_neo4j_driver()
                    
                    user_repo = UserRepository(mongo_db, neo4j_driver)
                    session_repo = SessionRepository(redis_client)
                    auth_service = AuthService(user_repo, session_repo)
                    auth_service.logout(session_id)
                except:
                    pass
            
            self.session_manager.clear_session()
            # Emit signal to notify main that logout was requested
            self.logout_requested.emit()
            self.close()
    
    def open_logs_folder(self):
        """Open the logs folder in file explorer"""
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Opening logs folder: {log_dir}")
        
        try:
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer "{log_dir}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", str(log_dir)])
            else:  # Linux
                subprocess.Popen(["xdg-open", str(log_dir)])
            
            QMessageBox.information(
                self,
                "Carpeta de Logs",
                f"La carpeta de logs se ha abierto en:\n{log_dir}\n\n"
                f"Los archivos de log se guardan con el formato:\napp_YYYYMMDD.log"
            )
        except Exception as e:
            logger.error(f"Error opening logs folder: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo abrir la carpeta de logs.\n\n"
                f"Ruta: {log_dir}\n"
                f"Error: {str(e)}"
            )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "Acerca de",
            "Sistema de Gestión de Sensores\n\n"
            "Aplicación de Escritorio\n"
            "Versión 1.0.0\n\n"
            "Una aplicación de escritorio para gestionar sensores climáticos."
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup can be done here if needed
        event.accept()

