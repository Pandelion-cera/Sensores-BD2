from typing import Optional, List
from datetime import datetime, timedelta
import logging

from desktop_app.repositories.scheduled_process_repository import ScheduledProcessRepository
from desktop_app.models.scheduled_process_models import (
    ScheduledProcess, ScheduledProcessCreate, ScheduledProcessUpdate,
    ScheduleType, ScheduleStatus
)

logger = logging.getLogger(__name__)


class ScheduledProcessService:
    def __init__(self, schedule_repo: ScheduledProcessRepository):
        self.schedule_repo = schedule_repo
    
    def create_schedule(self, user_id: str, schedule_data: ScheduledProcessCreate) -> ScheduledProcess:
        """Create a new scheduled process"""
        # Calculate next execution time
        next_execution = self.calculate_next_execution(
            schedule_data.schedule_type,
            schedule_data.schedule_config
        )
        
        # Create the schedule
        schedule = self.schedule_repo.create(user_id, schedule_data, next_execution)
        logger.info(f"Created scheduled process {schedule.id} for user {user_id}, next execution: {next_execution}")
        
        return schedule
    
    def get_user_schedules(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ScheduledProcess]:
        """Get all scheduled processes for a user"""
        return self.schedule_repo.get_by_user(user_id, skip, limit)
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduledProcess]:
        """Get a scheduled process by ID"""
        return self.schedule_repo.get_by_id(schedule_id)
    
    def update_schedule(self, schedule_id: str, update_data: ScheduledProcessUpdate) -> Optional[ScheduledProcess]:
        """Update a scheduled process"""
        # If schedule type or config changed, recalculate next execution
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        
        # Recalculate next execution if schedule type or config changed
        if update_data.schedule_type is not None or update_data.schedule_config is not None:
            schedule_type = update_data.schedule_type or schedule.schedule_type
            schedule_config = update_data.schedule_config or schedule.schedule_config
            next_execution = self.calculate_next_execution(schedule_type, schedule_config)
            # Update next_execution separately
            self.schedule_repo.update_next_execution(schedule_id, next_execution)
        
        # Update other fields
        updated = self.schedule_repo.update(schedule_id, update_data)
        logger.info(f"Updated scheduled process {schedule_id}")
        
        return updated
    
    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a scheduled process"""
        result = self.schedule_repo.update_status(schedule_id, ScheduleStatus.PAUSED)
        if result:
            logger.info(f"Paused scheduled process {schedule_id}")
        return result
    
    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused scheduled process"""
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            return False
        
        # Recalculate next execution when resuming
        next_execution = self.calculate_next_execution(
            schedule.schedule_type,
            schedule.schedule_config
        )
        self.schedule_repo.update_next_execution(schedule_id, next_execution)
        
        result = self.schedule_repo.update_status(schedule_id, ScheduleStatus.ACTIVE)
        if result:
            logger.info(f"Resumed scheduled process {schedule_id}, next execution: {next_execution}")
        return result
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a scheduled process"""
        result = self.schedule_repo.delete(schedule_id)
        if result:
            logger.info(f"Deleted scheduled process {schedule_id}")
        return result
    
    def calculate_next_execution(self, schedule_type: ScheduleType, schedule_config: dict) -> datetime:
        """Calculate the next execution time based on schedule type and config"""
        now = datetime.utcnow()
        hour = schedule_config.get("hour", 0)
        minute = schedule_config.get("minute", 0)
        
        if schedule_type == ScheduleType.DAILY:
            # Daily: same time tomorrow (or today if time hasn't passed)
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_exec <= now:
                next_exec += timedelta(days=1)
            return next_exec
        
        elif schedule_type == ScheduleType.WEEKLY:
            # Weekly: same day of week and time
            day_of_week = schedule_config.get("day_of_week", 0)  # 0=Monday, 6=Sunday
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Calculate days until next occurrence of that day
            days_ahead = day_of_week - next_exec.weekday()
            if days_ahead < 0 or (days_ahead == 0 and next_exec <= now):
                days_ahead += 7
            
            next_exec += timedelta(days=days_ahead)
            return next_exec
        
        elif schedule_type == ScheduleType.MONTHLY:
            # Monthly: same day of month and time
            day_of_month = schedule_config.get("day_of_month", 1)
            next_exec = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            
            # If day has passed this month, move to next month
            if next_exec <= now:
                # Move to next month
                if next_exec.month == 12:
                    next_exec = next_exec.replace(year=next_exec.year + 1, month=1)
                else:
                    next_exec = next_exec.replace(month=next_exec.month + 1)
            
            # Handle months with fewer days (e.g., day 31 in February)
            # Adjust to last day of month if needed
            while True:
                try:
                    # Try to create the date, if it fails, the day doesn't exist in that month
                    test_date = next_exec.replace(day=day_of_month)
                    next_exec = test_date
                    break
                except ValueError:
                    # Day doesn't exist in this month, use last day of month
                    if next_exec.month == 12:
                        next_exec = next_exec.replace(year=next_exec.year + 1, month=1, day=1)
                    else:
                        next_exec = next_exec.replace(month=next_exec.month + 1, day=1)
                    # Get last day of the month
                    if next_exec.month == 12:
                        last_day = (next_exec.replace(year=next_exec.year + 1, month=1, day=1) - timedelta(days=1)).day
                    else:
                        last_day = (next_exec.replace(month=next_exec.month + 1, day=1) - timedelta(days=1)).day
                    next_exec = next_exec.replace(day=min(day_of_month, last_day))
                    break
            
            return next_exec
        
        elif schedule_type == ScheduleType.ANNUAL:
            # Annual: same month, day, and time
            month = schedule_config.get("month", 1)  # 1-12
            day_of_month = schedule_config.get("day_of_month", 1)
            next_exec = now.replace(month=month, day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            
            # If date has passed this year, move to next year
            if next_exec <= now:
                next_exec = next_exec.replace(year=next_exec.year + 1)
            
            # Handle leap years and invalid dates (e.g., Feb 30)
            while True:
                try:
                    test_date = next_exec.replace(month=month, day=day_of_month)
                    next_exec = test_date
                    break
                except ValueError:
                    # Invalid date (e.g., Feb 30), use last day of month
                    if month == 12:
                        last_day = (next_exec.replace(year=next_exec.year + 1, month=1, day=1) - timedelta(days=1)).day
                    else:
                        last_day = (next_exec.replace(month=month + 1, day=1) - timedelta(days=1)).day
                    next_exec = next_exec.replace(day=min(day_of_month, last_day))
                    break
            
            return next_exec
        
        else:
            # Default: tomorrow at specified time
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_exec <= now:
                next_exec += timedelta(days=1)
            return next_exec
    
    def calculate_next_execution_after_current(self, schedule: ScheduledProcess) -> datetime:
        """Calculate next execution time after the current execution"""
        now = datetime.utcnow()
        hour = schedule.schedule_config.get("hour", 0)
        minute = schedule.schedule_config.get("minute", 0)
        
        if schedule.schedule_type == ScheduleType.DAILY:
            # Next day at same time
            return (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        elif schedule.schedule_type == ScheduleType.WEEKLY:
            # Next week same day
            day_of_week = schedule.schedule_config.get("day_of_week", 0)
            next_exec = (now + timedelta(days=7)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Adjust to correct day of week
            days_ahead = day_of_week - next_exec.weekday()
            if days_ahead < 0:
                days_ahead += 7
            
            next_exec += timedelta(days=days_ahead)
            return next_exec
        
        elif schedule.schedule_type == ScheduleType.MONTHLY:
            # Next month same day
            day_of_month = schedule.schedule_config.get("day_of_month", 1)
            if now.month == 12:
                next_exec = now.replace(year=now.year + 1, month=1, day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_exec = now.replace(month=now.month + 1, day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            
            # Handle invalid days
            while True:
                try:
                    test_date = next_exec.replace(day=day_of_month)
                    return test_date
                except ValueError:
                    # Use last day of month
                    if next_exec.month == 12:
                        last_day = (next_exec.replace(year=next_exec.year + 1, month=1, day=1) - timedelta(days=1)).day
                    else:
                        last_day = (next_exec.replace(month=next_exec.month + 1, day=1) - timedelta(days=1)).day
                    return next_exec.replace(day=min(day_of_month, last_day))
        
        elif schedule.schedule_type == ScheduleType.ANNUAL:
            # Next year same month/day
            month = schedule.schedule_config.get("month", 1)
            day_of_month = schedule.schedule_config.get("day_of_month", 1)
            next_exec = now.replace(year=now.year + 1, month=month, day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            
            # Handle invalid dates
            while True:
                try:
                    test_date = next_exec.replace(day=day_of_month)
                    return test_date
                except ValueError:
                    # Use last day of month
                    if month == 12:
                        last_day = (next_exec.replace(year=next_exec.year + 1, month=1, day=1) - timedelta(days=1)).day
                    else:
                        last_day = (next_exec.replace(month=month + 1, day=1) - timedelta(days=1)).day
                    return next_exec.replace(day=min(day_of_month, last_day))
        
        else:
            # Default: next day
            return (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)

