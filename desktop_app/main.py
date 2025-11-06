"""
Main entry point for desktop application
"""
import sys
import logging
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from desktop_app.core.database import db_manager
from desktop_app.ui.login_window import LoginWindow
from desktop_app.ui.main_window import MainWindow
from desktop_app.background.scheduler_worker import SchedulerWorker

# Configure logging to both file and console
def setup_logging():
    """Configure logging to write to both file and console"""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Log file with timestamp
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    root_logger.handlers = []
    
    # File handler - detailed logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler - important messages only
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    return str(log_file)

# Setup logging
log_file_path = setup_logging()
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
    
    # Start scheduler worker for scheduled processes
    scheduler_worker = SchedulerWorker()
    scheduler_worker.start()
    logger.info("Scheduler worker started")
    
    # Main application loop - allows returning to login after logout
    logout_requested = False
    
    while True:
        # Show login window
        login_window = LoginWindow()
        
        if login_window.exec() != login_window.DialogCode.Accepted:
            # Login cancelled or failed, exit application
            break
        
        # Login successful, show main window
        main_window = MainWindow()
        main_window.show()
        
        # Reset logout flag
        logout_requested = False
        
        # Handle logout - when logout signal is emitted, set flag and quit event loop
        def handle_logout():
            nonlocal logout_requested
            logout_requested = True
            app.quit()  # Exit the event loop to return to login
        
        main_window.logout_requested.connect(handle_logout)
        
        # Run the main window event loop
        app.exec()
        
        # If logout was requested, continue the loop to show login again
        # Otherwise, the window was closed normally, so exit the application
        if not logout_requested:
            break
    
    # Stop scheduler worker before exiting
    scheduler_worker.stop()
    logger.info("Scheduler worker stopped")
    
    sys.exit(0)


if __name__ == "__main__":
    main()

