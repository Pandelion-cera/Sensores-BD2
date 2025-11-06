from typing import List
from datetime import datetime
import logging

from desktop_app.repositories.scheduled_process_repository import ScheduledProcessRepository
from desktop_app.services.scheduled_process_service import ScheduledProcessService
from desktop_app.services.process_service import ProcessService
from desktop_app.models.process_models import ProcessRequestCreate, ProcessStatus
from desktop_app.models.scheduled_process_models import ScheduleStatus

logger = logging.getLogger(__name__)


class ProcessSchedulerService:
    def __init__(
        self,
        schedule_repo: ScheduledProcessRepository,
        schedule_service: ScheduledProcessService,
        process_service: ProcessService
    ):
        self.schedule_repo = schedule_repo
        self.schedule_service = schedule_service
        self.process_service = process_service
    
    def check_and_execute_schedules(self) -> int:
        """Check for schedules that need to be executed and execute them"""
        # Get all active schedules that should execute today or earlier
        today = datetime.utcnow()
        schedules_to_execute = self.schedule_repo.get_active_schedules(before_date=today)
        
        logger.info(f"Found {len(schedules_to_execute)} scheduled processes to execute")
        
        executed_count = 0
        for schedule in schedules_to_execute:
            try:
                self.execute_scheduled_process(schedule)
                executed_count += 1
            except Exception as e:
                logger.error(f"Error executing scheduled process {schedule.id}: {e}", exc_info=True)
                # Continue with other schedules even if one fails
                # Update last_execution and next_execution even on failure
                # so the schedule doesn't get stuck
                try:
                    now = datetime.utcnow()
                    self.schedule_repo.update_last_execution(schedule.id, now)
                    next_exec = self.schedule_service.calculate_next_execution_after_current(schedule)
                    self.schedule_repo.update_next_execution(schedule.id, next_exec)
                except Exception as update_error:
                    logger.error(f"Error updating schedule {schedule.id} after failed execution: {update_error}")
        
        logger.info(f"Executed {executed_count} scheduled processes")
        return executed_count
    
    def execute_scheduled_process(self, schedule) -> None:
        """Execute a specific scheduled process"""
        logger.info(f"Executing scheduled process {schedule.id} for user {schedule.user_id}, process {schedule.process_id}")
        
        # Calculate dynamic parameters based on last_execution
        now = datetime.utcnow()
        parametros = schedule.parametros.copy()  # Copy to avoid modifying original
        
        if schedule.last_execution:
            # Subsequent execution: use last_execution as start, now as end
            parametros["fecha_inicio"] = schedule.last_execution.isoformat()
            parametros["fecha_fin"] = now.isoformat()
            logger.info(f"Subsequent execution: using fecha_inicio={schedule.last_execution}, fecha_fin={now}")
        else:
            # First execution: use original dates from schedule.parametros
            # fecha_inicio and fecha_fin should already be in parametros
            logger.info(f"First execution: using original dates from schedule.parametros")
        
        # Create a ProcessRequest automatically with calculated parameters
        request_data = ProcessRequestCreate(
            process_id=schedule.process_id,
            parametros=parametros
        )
        
        try:
            # Create the request
            request = self.process_service.request_process(schedule.user_id, request_data)
            logger.info(f"Created process request {request.id} for scheduled process {schedule.id}")
            
            # Execute the process immediately
            execution = self.process_service.execute_process(request.id)
            logger.info(f"Executed scheduled process {schedule.id}, execution ID: {execution.id}, status: {execution.estado}")
            
            # Update schedule: set last_execution and calculate next_execution
            now = datetime.utcnow()
            self.schedule_repo.update_last_execution(schedule.id, now)
            
            # Calculate next execution based on schedule type
            next_exec = self.schedule_service.calculate_next_execution_after_current(schedule)
            self.schedule_repo.update_next_execution(schedule.id, next_exec)
            
            logger.info(f"Updated schedule {schedule.id}: last_execution={now}, next_execution={next_exec}")
            
        except Exception as e:
            logger.error(f"Error executing scheduled process {schedule.id}: {e}", exc_info=True)
            # Update last_execution and next_execution even on failure
            # so the schedule doesn't get stuck retrying the same execution
            now = datetime.utcnow()
            self.schedule_repo.update_last_execution(schedule.id, now)
            next_exec = self.schedule_service.calculate_next_execution_after_current(schedule)
            self.schedule_repo.update_next_execution(schedule.id, next_exec)
            
            # Re-raise to let caller know it failed
            raise

