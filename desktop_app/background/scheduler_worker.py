import threading
import time
import logging
from datetime import datetime, timedelta

from desktop_app.core.database import db_manager
from desktop_app.repositories.scheduled_process_repository import ScheduledProcessRepository
from desktop_app.services.scheduled_process_service import ScheduledProcessService
from desktop_app.services.process_scheduler_service import ProcessSchedulerService
from desktop_app.services.process_service import ProcessService
from desktop_app.repositories.process_repository import ProcessRepository
from desktop_app.repositories.measurement_repository import MeasurementRepository
from desktop_app.repositories.sensor_repository import SensorRepository
from desktop_app.repositories.user_repository import UserRepository
from desktop_app.repositories.invoice_repository import InvoiceRepository
from desktop_app.repositories.account_repository import AccountRepository
from desktop_app.services.account_service import AccountService
from desktop_app.core.config import settings

logger = logging.getLogger(__name__)


class SchedulerWorker:
    """Background worker that runs once per day to execute scheduled processes"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_run_date = None
    
    def start(self):
        """Start the scheduler worker"""
        if self.running:
            logger.warning("Scheduler worker is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Scheduler worker started")
    
    def stop(self):
        """Stop the scheduler worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler worker stopped")
    
    def _run(self):
        """Main worker loop"""
        while self.running:
            try:
                now = datetime.utcnow()
                today = now.date()
                
                # Check if we need to run today
                if self.last_run_date != today:
                    logger.info(f"Running scheduled processes check for {today}")
                    self._execute_scheduled_processes()
                    self.last_run_date = today
                    logger.info(f"Completed scheduled processes check for {today}")
                
                # Sleep until next day (check every hour to be responsive)
                # Calculate seconds until next midnight
                next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                sleep_seconds = (next_midnight - now).total_seconds()
                
                # Sleep in 1-hour chunks to be responsive to shutdown
                hours_to_sleep = int(sleep_seconds / 3600)
                remaining_seconds = sleep_seconds % 3600
                
                for _ in range(hours_to_sleep):
                    if not self.running:
                        break
                    time.sleep(3600)  # Sleep 1 hour
                
                if self.running:
                    time.sleep(remaining_seconds)  # Sleep remaining time
                
            except Exception as e:
                logger.error(f"Error in scheduler worker: {e}", exc_info=True)
                # Sleep for 1 hour before retrying
                time.sleep(3600)
    
    def _execute_scheduled_processes(self):
        """Execute scheduled processes that are due"""
        try:
            # Initialize database connections
            mongo_db = db_manager.get_mongo_db()
            neo4j_driver = db_manager.get_neo4j_driver()
            cassandra_session = db_manager.get_cassandra_session()
            
            # Initialize repositories
            schedule_repo = ScheduledProcessRepository(mongo_db)
            process_repo = ProcessRepository(mongo_db, neo4j_driver)
            measurement_repo = MeasurementRepository(cassandra_session, settings.CASSANDRA_KEYSPACE)
            sensor_repo = SensorRepository(mongo_db)
            user_repo = UserRepository(mongo_db, neo4j_driver)
            invoice_repo = InvoiceRepository(mongo_db)
            account_repo = AccountRepository(mongo_db)
            account_service = AccountService(account_repo)
            
            # Initialize services
            schedule_service = ScheduledProcessService(schedule_repo)
            redis_client = db_manager.get_redis_client()
            from desktop_app.repositories.alert_repository import AlertRepository
            from desktop_app.services.alert_service import AlertService
            alert_repo = AlertRepository(mongo_db, redis_client)
            alert_service = AlertService(alert_repo)
            process_service = ProcessService(
                process_repo,
                measurement_repo,
                sensor_repo,
                user_repo,
                invoice_repo,
                account_service,
                alert_service
            )
            scheduler_service = ProcessSchedulerService(
                schedule_repo,
                schedule_service,
                process_service
            )
            
            # Check and execute schedules
            executed_count = scheduler_service.check_and_execute_schedules()
            logger.info(f"Scheduler worker executed {executed_count} scheduled processes")
            
        except Exception as e:
            logger.error(f"Error executing scheduled processes: {e}", exc_info=True)

