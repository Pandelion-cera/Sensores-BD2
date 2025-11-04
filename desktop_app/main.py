"""
Main entry point for desktop application
"""
import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from desktop_app.core.database import db_manager
from desktop_app.ui.login_window import LoginWindow
from desktop_app.ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_databases():
    """Initialize database connections"""
    try:
        logger.info("Initializing database connections...")
        db_manager.get_mongo_client()
        db_manager.get_cassandra_session()
        db_manager.get_neo4j_driver()
        db_manager.get_redis_client()
        logger.info("All database connections established")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize databases: {e}")
        return False


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Sensor Management System")
    
    # Initialize databases
    if not initialize_databases():
        QMessageBox.critical(
            None,
            "Database Connection Error",
            "Failed to connect to databases.\n\n"
            "Please ensure that:\n"
            "1. Docker containers are running (docker-compose up -d)\n"
            "2. Databases are initialized (run init_databases.py)\n"
            "3. Check database connection settings in config.py"
        )
        sys.exit(1)
    
    # Show login window
    login_window = LoginWindow()
    
    if login_window.exec() == login_window.DialogCode.Accepted:
        # Login successful, show main window
        main_window = MainWindow()
        main_window.show()
        
        sys.exit(app.exec())
    else:
        # Login cancelled or failed
        sys.exit(0)


if __name__ == "__main__":
    main()

