"""
Main window for desktop application
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QMenuBar, QStatusBar, QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from desktop_app.utils.session_manager import SessionManager
from desktop_app.ui.dashboard_widget import DashboardWidget
from desktop_app.ui.sensors_widget import SensorsWidget
from desktop_app.ui.measurements_widget import MeasurementsWidget
from desktop_app.ui.alerts_widget import AlertsWidget
from desktop_app.ui.messages_widget import MessagesWidget
from desktop_app.ui.invoices_widget import InvoicesWidget
from desktop_app.ui.processes_widget import ProcessesWidget


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor Management System")
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
        self.tabs.addTab(self.dashboard_widget, "Dashboard")
        
        # Sensors tab
        self.sensors_widget = SensorsWidget()
        self.tabs.addTab(self.sensors_widget, "Sensors")
        
        # Measurements tab
        self.measurements_widget = MeasurementsWidget()
        self.tabs.addTab(self.measurements_widget, "Measurements")
        
        # Alerts tab
        self.alerts_widget = AlertsWidget()
        self.tabs.addTab(self.alerts_widget, "Alerts")
        
        # Messages tab
        self.messages_widget = MessagesWidget()
        self.tabs.addTab(self.messages_widget, "Messages")
        
        # Invoices tab
        self.invoices_widget = InvoicesWidget()
        self.tabs.addTab(self.invoices_widget, "Invoices")
        
        # Processes tab
        self.processes_widget = ProcessesWidget()
        self.tabs.addTab(self.processes_widget, "Processes")
        
        layout.addWidget(self.tabs)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # User info label
        user = self.session_manager.get_user()
        if user:
            user_info = f"Logged in as: {user.get('nombre_completo', '')} ({user.get('role', '')})"
            self.status_bar.addWidget(QLabel(user_info))
        
        self.status_bar.addPermanentWidget(QLabel("Ready"))
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.handle_logout)
        file_menu.addAction(logout_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_current_tab)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
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
            self.status_bar.showMessage("All databases connected", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Database connection error: {str(e)}", 0)
    
    def refresh_current_tab(self):
        """Refresh current tab"""
        current_index = self.tabs.currentIndex()
        if current_index == 0:  # Dashboard
            self.dashboard_widget.refresh()
        elif current_index == 1:  # Sensors
            self.sensors_widget.load_sensors()
        elif current_index == 2:  # Measurements
            # Measurements require search filters, so just refresh if they've already searched
            pass
        elif current_index == 3:  # Alerts
            self.alerts_widget.load_alerts()
        elif current_index == 4:  # Messages
            self.messages_widget.load_messages()
        elif current_index == 5:  # Invoices
            self.invoices_widget.load_invoices()
        elif current_index == 6:  # Processes
            self.processes_widget.load_processes()
        self.status_bar.showMessage("Refreshed", 2000)
    
    def handle_logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
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
            self.close()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About",
            "Sensor Management System\n\n"
            "Desktop Application\n"
            "Version 1.0.0\n\n"
            "A desktop application for managing climate sensors."
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup can be done here if needed
        event.accept()

