"""
Refresh Scheduler

Handles automatic context updates based on data type refresh intervals.
"""

import logging
import threading
import time
from typing import Dict, Callable, Optional
from datetime import datetime, timedelta


class RefreshScheduler:
    """Manages scheduled refresh of context data"""

    def __init__(self):
        """Initialize the refresh scheduler"""
        self.logger = logging.getLogger("mark_i.context.scheduler")
        
        # Scheduled tasks: {task_id: task_info}
        self._tasks: Dict[str, Dict] = {}
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        self.logger.info("RefreshScheduler initialized")

    def schedule_task(self, 
                     task_id: str, 
                     callback: Callable, 
                     interval_seconds: int,
                     run_immediately: bool = False):
        """
        Schedule a recurring task

        Args:
            task_id: Unique identifier for the task
            callback: Function to call on each interval
            interval_seconds: Interval between executions in seconds
            run_immediately: If True, run the task immediately
        """
        with self._lock:
            next_run = datetime.now()
            if not run_immediately:
                next_run += timedelta(seconds=interval_seconds)

            self._tasks[task_id] = {
                'callback': callback,
                'interval_seconds': interval_seconds,
                'next_run': next_run,
                'last_run': None,
                'run_count': 0,
                'error_count': 0
            }

            self.logger.info(f"Scheduled task: {task_id} (interval: {interval_seconds}s)")

            # Start scheduler if not running
            if not self._scheduler_thread or not self._scheduler_thread.is_alive():
                self._start_scheduler()

    def unschedule_task(self, task_id: str):
        """
        Remove a scheduled task

        Args:
            task_id: Task identifier to remove
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                self.logger.info(f"Unscheduled task: {task_id}")

    def get_scheduled_tasks(self) -> Dict[str, Dict]:
        """
        Get information about scheduled tasks

        Returns:
            Dictionary of task information
        """
        with self._lock:
            return {
                task_id: {
                    'interval_seconds': task_info['interval_seconds'],
                    'next_run': task_info['next_run'].isoformat(),
                    'last_run': task_info['last_run'].isoformat() if task_info['last_run'] else None,
                    'run_count': task_info['run_count'],
                    'error_count': task_info['error_count']
                }
                for task_id, task_info in self._tasks.items()
            }

    def update_task_interval(self, task_id: str, new_interval_seconds: int):
        """
        Update the interval for an existing task

        Args:
            task_id: Task identifier
            new_interval_seconds: New interval in seconds
        """
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]['interval_seconds'] = new_interval_seconds
                # Update next run time
                self._tasks[task_id]['next_run'] = datetime.now() + timedelta(seconds=new_interval_seconds)
                self.logger.info(f"Updated task interval: {task_id} -> {new_interval_seconds}s")

    def pause_task(self, task_id: str):
        """
        Pause a scheduled task

        Args:
            task_id: Task identifier to pause
        """
        with self._lock:
            if task_id in self._tasks:
                # Set next run to far future to effectively pause
                self._tasks[task_id]['next_run'] = datetime.now() + timedelta(days=365)
                self.logger.info(f"Paused task: {task_id}")

    def resume_task(self, task_id: str):
        """
        Resume a paused task

        Args:
            task_id: Task identifier to resume
        """
        with self._lock:
            if task_id in self._tasks:
                interval = self._tasks[task_id]['interval_seconds']
                self._tasks[task_id]['next_run'] = datetime.now() + timedelta(seconds=interval)
                self.logger.info(f"Resumed task: {task_id}")

    def stop_scheduler(self):
        """Stop the scheduler and all tasks"""
        self._stop_event.set()
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5)
        
        with self._lock:
            self._tasks.clear()
        
        self.logger.info("Scheduler stopped")

    def _start_scheduler(self):
        """Start the scheduler thread"""
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self._scheduler_thread.start()
        self.logger.info("Scheduler thread started")

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while not self._stop_event.is_set():
            try:
                current_time = datetime.now()
                tasks_to_run = []

                # Find tasks that need to run
                with self._lock:
                    for task_id, task_info in self._tasks.items():
                        if current_time >= task_info['next_run']:
                            tasks_to_run.append((task_id, task_info))

                # Execute tasks (outside of lock to avoid blocking)
                for task_id, task_info in tasks_to_run:
                    try:
                        self.logger.debug(f"Executing scheduled task: {task_id}")
                        task_info['callback']()
                        
                        # Update task info
                        with self._lock:
                            if task_id in self._tasks:  # Task might have been removed
                                self._tasks[task_id]['last_run'] = current_time
                                self._tasks[task_id]['run_count'] += 1
                                self._tasks[task_id]['next_run'] = current_time + timedelta(
                                    seconds=self._tasks[task_id]['interval_seconds']
                                )

                    except Exception as e:
                        self.logger.error(f"Task {task_id} failed: {str(e)}")
                        
                        # Update error count
                        with self._lock:
                            if task_id in self._tasks:
                                self._tasks[task_id]['error_count'] += 1

                # Sleep for a short interval before checking again
                self._stop_event.wait(1)  # Check every second

            except Exception as e:
                self.logger.error(f"Scheduler loop error: {str(e)}")
                time.sleep(5)  # Wait before retrying

    def get_scheduler_stats(self) -> Dict[str, any]:
        """
        Get scheduler statistics

        Returns:
            Dictionary containing scheduler statistics
        """
        with self._lock:
            total_runs = sum(task['run_count'] for task in self._tasks.values())
            total_errors = sum(task['error_count'] for task in self._tasks.values())
            
            return {
                'active_tasks': len(self._tasks),
                'scheduler_running': self._scheduler_thread and self._scheduler_thread.is_alive(),
                'total_runs': total_runs,
                'total_errors': total_errors,
                'tasks': list(self._tasks.keys())
            }

    def __del__(self):
        """Cleanup when scheduler is destroyed"""
        self.stop_scheduler()