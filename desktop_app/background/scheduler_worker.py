import threading
import time
import logging
from datetime import datetime, timedelta

from desktop_app.services.factories import (
    get_process_scheduler_service,
)

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
            # Check and execute schedules
            scheduler_service = get_process_scheduler_service()
            executed_count = scheduler_service.check_and_execute_schedules()
            logger.info(f"Scheduler worker executed {executed_count} scheduled processes")
            
        except Exception as e:
            logger.error(f"Error executing scheduled processes: {e}", exc_info=True)

