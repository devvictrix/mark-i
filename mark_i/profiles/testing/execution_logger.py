"""
Execution Logger

Comprehensive logging and reporting system for profile execution,
debugging, and troubleshooting failed automations.
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional, TextIO
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum


class LogLevel(Enum):
    """Log levels for execution logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Individual log entry"""
    timestamp: datetime
    level: LogLevel
    category: str  # 'profile', 'rule', 'condition', 'action', 'system'
    message: str
    context: Dict[str, Any]
    execution_id: str
    rule_name: Optional[str] = None
    step_index: Optional[int] = None
    duration: Optional[float] = None
    screenshot_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['level'] = LogLevel(data['level'])
        return cls(**data)


class ExecutionLogger:
    """Comprehensive execution logging system"""
    
    def __init__(self, log_dir: str = None, max_log_files: int = 100):
        self.logger = logging.getLogger("mark_i.profiles.testing.execution_logger")
        
        # Setup log directory
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "logs" / "profile_execution"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_log_files = max_log_files
        
        # Current execution context
        self.current_execution_id: Optional[str] = None
        self.current_profile_name: Optional[str] = None
        self.execution_start_time: Optional[datetime] = None
        
        # Log entries for current execution
        self.current_log_entries: List[LogEntry] = []
        
        # File handles
        self.current_log_file: Optional[TextIO] = None
        
        # Configuration
        self.auto_flush = True
        self.include_screenshots = True
        self.max_entries_in_memory = 1000
        
        self.logger.info("ExecutionLogger initialized")
    
    def start_execution_log(self, profile_name: str, execution_id: str = None) -> str:
        """Start logging for a new execution"""
        if execution_id is None:
            execution_id = f"{profile_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_execution_id = execution_id
        self.current_profile_name = profile_name
        self.execution_start_time = datetime.now()
        self.current_log_entries = []
        
        # Create log file
        log_filename = f"{execution_id}.json"
        log_filepath = self.log_dir / log_filename
        
        try:
            self.current_log_file = open(log_filepath, 'w', encoding='utf-8')
            
            # Write execution header
            header = {
                'execution_id': execution_id,
                'profile_name': profile_name,
                'start_time': self.execution_start_time.isoformat(),
                'log_entries': []
            }
            
            json.dump(header, self.current_log_file, indent=2)
            self.current_log_file.write('\n')
            
            if self.auto_flush:
                self.current_log_file.flush()
            
        except Exception as e:
            self.logger.error(f"Failed to create log file: {e}")
            self.current_log_file = None
        
        self.log_info('profile', f"Started execution logging for profile: {profile_name}")
        
        return execution_id
    
    def end_execution_log(self, success: bool = True, summary: Dict[str, Any] = None):
        """End current execution logging"""
        if not self.current_execution_id:
            return
        
        end_time = datetime.now()
        duration = (end_time - self.execution_start_time).total_seconds() if self.execution_start_time else 0
        
        # Log execution end
        self.log_info('profile', f"Execution completed: {'SUCCESS' if success else 'FAILED'}", 
                     context={'duration': duration, 'summary': summary or {}})
        
        # Write final log file
        if self.current_log_file:
            try:
                # Write all log entries
                for entry in self.current_log_entries:
                    json.dump(entry.to_dict(), self.current_log_file)
                    self.current_log_file.write('\n')
                
                # Write execution footer
                footer = {
                    'execution_end': {
                        'end_time': end_time.isoformat(),
                        'duration': duration,
                        'success': success,
                        'total_entries': len(self.current_log_entries),
                        'summary': summary or {}
                    }
                }
                
                json.dump(footer, self.current_log_file)
                self.current_log_file.close()
                
            except Exception as e:
                self.logger.error(f"Failed to finalize log file: {e}")
            finally:
                self.current_log_file = None
        
        # Cleanup old log files
        self._cleanup_old_logs()
        
        # Reset state
        self.current_execution_id = None
        self.current_profile_name = None
        self.execution_start_time = None
        self.current_log_entries = []
        
        self.logger.info("Execution logging ended")
    
    def log_debug(self, category: str, message: str, context: Dict[str, Any] = None, 
                  rule_name: str = None, step_index: int = None, duration: float = None):
        """Log debug message"""
        self._log_entry(LogLevel.DEBUG, category, message, context, rule_name, step_index, duration)
    
    def log_info(self, category: str, message: str, context: Dict[str, Any] = None,
                 rule_name: str = None, step_index: int = None, duration: float = None):
        """Log info message"""
        self._log_entry(LogLevel.INFO, category, message, context, rule_name, step_index, duration)
    
    def log_warning(self, category: str, message: str, context: Dict[str, Any] = None,
                    rule_name: str = None, step_index: int = None, duration: float = None):
        """Log warning message"""
        self._log_entry(LogLevel.WARNING, category, message, context, rule_name, step_index, duration)
    
    def log_error(self, category: str, message: str, context: Dict[str, Any] = None,
                  rule_name: str = None, step_index: int = None, duration: float = None,
                  screenshot_path: str = None):
        """Log error message"""
        self._log_entry(LogLevel.ERROR, category, message, context, rule_name, step_index, duration, screenshot_path)
    
    def log_critical(self, category: str, message: str, context: Dict[str, Any] = None,
                     rule_name: str = None, step_index: int = None, duration: float = None,
                     screenshot_path: str = None):
        """Log critical message"""
        self._log_entry(LogLevel.CRITICAL, category, message, context, rule_name, step_index, duration, screenshot_path)
    
    def _log_entry(self, level: LogLevel, category: str, message: str, 
                   context: Dict[str, Any] = None, rule_name: str = None, 
                   step_index: int = None, duration: float = None, screenshot_path: str = None):
        """Internal method to create and store log entry"""
        if not self.current_execution_id:
            # If no execution is active, just log to standard logger
            getattr(self.logger, level.value.lower())(f"{category}: {message}")
            return
        
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            context=context or {},
            execution_id=self.current_execution_id,
            rule_name=rule_name,
            step_index=step_index,
            duration=duration,
            screenshot_path=screenshot_path
        )
        
        # Add to current entries
        self.current_log_entries.append(entry)
        
        # Also log to standard logger
        log_msg = f"[{self.current_execution_id}] {category}: {message}"
        if rule_name:
            log_msg += f" (Rule: {rule_name})"
        if step_index is not None:
            log_msg += f" (Step: {step_index})"
        
        getattr(self.logger, level.value.lower())(log_msg)
        
        # Manage memory usage
        if len(self.current_log_entries) > self.max_entries_in_memory:
            self._flush_entries_to_file()
    
    def _flush_entries_to_file(self):
        """Flush log entries to file to manage memory"""
        if not self.current_log_file or not self.current_log_entries:
            return
        
        try:
            # Write entries to file
            for entry in self.current_log_entries[:-100]:  # Keep last 100 in memory
                json.dump(entry.to_dict(), self.current_log_file)
                self.current_log_file.write('\n')
            
            if self.auto_flush:
                self.current_log_file.flush()
            
            # Keep only recent entries in memory
            self.current_log_entries = self.current_log_entries[-100:]
            
        except Exception as e:
            self.logger.error(f"Failed to flush log entries: {e}")
    
    def log_rule_start(self, rule_name: str, rule_priority: int, context: Dict[str, Any] = None):
        """Log rule execution start"""
        self.log_info('rule', f"Starting rule execution: {rule_name}", 
                     context={'priority': rule_priority, **(context or {})}, 
                     rule_name=rule_name)
    
    def log_rule_end(self, rule_name: str, success: bool, duration: float, context: Dict[str, Any] = None):
        """Log rule execution end"""
        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Rule execution {'completed' if success else 'failed'}: {rule_name}"
        
        self._log_entry(level, 'rule', message, 
                       context={'success': success, 'duration': duration, **(context or {})},
                       rule_name=rule_name, duration=duration)
    
    def log_condition_evaluation(self, rule_name: str, condition_index: int, condition_type: str,
                                success: bool, duration: float, result: Any = None, 
                                context: Dict[str, Any] = None):
        """Log condition evaluation"""
        level = LogLevel.DEBUG if success else LogLevel.INFO
        message = f"Condition {condition_index + 1} ({condition_type}): {'PASS' if success else 'FAIL'}"
        
        self._log_entry(level, 'condition', message,
                       context={'condition_type': condition_type, 'result': result, 
                               'success': success, **(context or {})},
                       rule_name=rule_name, step_index=condition_index, duration=duration)
    
    def log_action_execution(self, rule_name: str, action_index: int, action_type: str,
                           success: bool, duration: float, result: Any = None,
                           context: Dict[str, Any] = None, screenshot_path: str = None):
        """Log action execution"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Action {action_index + 1} ({action_type}): {'SUCCESS' if success else 'FAILED'}"
        
        self._log_entry(level, 'action', message,
                       context={'action_type': action_type, 'result': result,
                               'success': success, **(context or {})},
                       rule_name=rule_name, step_index=action_index, duration=duration,
                       screenshot_path=screenshot_path)
    
    def log_system_event(self, event_type: str, message: str, context: Dict[str, Any] = None):
        """Log system-level events"""
        self.log_info('system', f"{event_type}: {message}", context)
    
    def log_performance_metric(self, metric_name: str, value: float, context: Dict[str, Any] = None):
        """Log performance metrics"""
        self.log_debug('performance', f"{metric_name}: {value}", 
                      context={'metric': metric_name, 'value': value, **(context or {})})
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of current execution"""
        if not self.current_execution_id:
            return {}
        
        # Count entries by level and category
        level_counts = {}
        category_counts = {}
        
        for entry in self.current_log_entries:
            level_counts[entry.level.value] = level_counts.get(entry.level.value, 0) + 1
            category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
        
        duration = (datetime.now() - self.execution_start_time).total_seconds() if self.execution_start_time else 0
        
        return {
            'execution_id': self.current_execution_id,
            'profile_name': self.current_profile_name,
            'start_time': self.execution_start_time.isoformat() if self.execution_start_time else None,
            'duration': duration,
            'total_entries': len(self.current_log_entries),
            'level_counts': level_counts,
            'category_counts': category_counts,
            'has_errors': any(entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] for entry in self.current_log_entries),
            'has_warnings': any(entry.level == LogLevel.WARNING for entry in self.current_log_entries)
        }
    
    def get_recent_entries(self, count: int = 50, level: LogLevel = None) -> List[LogEntry]:
        """Get recent log entries"""
        entries = self.current_log_entries[-count:] if self.current_log_entries else []
        
        if level:
            entries = [entry for entry in entries if entry.level == level]
        
        return entries
    
    def search_logs(self, query: str, category: str = None, level: LogLevel = None) -> List[LogEntry]:
        """Search log entries"""
        results = []
        
        for entry in self.current_log_entries:
            # Filter by category
            if category and entry.category != category:
                continue
            
            # Filter by level
            if level and entry.level != level:
                continue
            
            # Search in message and context
            if (query.lower() in entry.message.lower() or 
                query.lower() in str(entry.context).lower()):
                results.append(entry)
        
        return results
    
    def export_execution_log(self, execution_id: str, output_path: str) -> bool:
        """Export execution log to file"""
        try:
            log_file = self.log_dir / f"{execution_id}.json"
            
            if not log_file.exists():
                self.logger.error(f"Log file not found: {log_file}")
                return False
            
            # Copy log file to output path
            import shutil
            shutil.copy2(log_file, output_path)
            
            self.logger.info(f"Exported execution log to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export execution log: {e}")
            return False
    
    def generate_execution_report(self, execution_id: str = None) -> str:
        """Generate detailed execution report"""
        if execution_id:
            # Load specific execution log
            entries = self._load_execution_log(execution_id)
            if not entries:
                return f"No log found for execution: {execution_id}"
        else:
            # Use current execution
            entries = self.current_log_entries
            execution_id = self.current_execution_id or "current"
        
        if not entries:
            return "No log entries found"
        
        # Generate report
        report = []
        report.append(f"Execution Report: {execution_id}")
        report.append("=" * 50)
        
        # Summary statistics
        level_counts = {}
        category_counts = {}
        rule_stats = {}
        
        for entry in entries:
            level_counts[entry.level.value] = level_counts.get(entry.level.value, 0) + 1
            category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
            
            if entry.rule_name:
                if entry.rule_name not in rule_stats:
                    rule_stats[entry.rule_name] = {'total': 0, 'errors': 0, 'warnings': 0}
                rule_stats[entry.rule_name]['total'] += 1
                if entry.level == LogLevel.ERROR:
                    rule_stats[entry.rule_name]['errors'] += 1
                elif entry.level == LogLevel.WARNING:
                    rule_stats[entry.rule_name]['warnings'] += 1
        
        report.append("Summary:")
        report.append(f"  Total Entries: {len(entries)}")
        report.append(f"  Errors: {level_counts.get('ERROR', 0)}")
        report.append(f"  Warnings: {level_counts.get('WARNING', 0)}")
        report.append(f"  Info: {level_counts.get('INFO', 0)}")
        report.append(f"  Debug: {level_counts.get('DEBUG', 0)}")
        report.append("")
        
        # Rule statistics
        if rule_stats:
            report.append("Rule Statistics:")
            for rule_name, stats in rule_stats.items():
                report.append(f"  {rule_name}: {stats['total']} entries, {stats['errors']} errors, {stats['warnings']} warnings")
            report.append("")
        
        # Recent errors
        errors = [entry for entry in entries if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        if errors:
            report.append("Recent Errors:")
            for error in errors[-10:]:  # Last 10 errors
                report.append(f"  [{error.timestamp.strftime('%H:%M:%S')}] {error.category}: {error.message}")
                if error.rule_name:
                    report.append(f"    Rule: {error.rule_name}")
                if error.context:
                    report.append(f"    Context: {error.context}")
            report.append("")
        
        # Performance metrics
        perf_entries = [entry for entry in entries if entry.category == 'performance']
        if perf_entries:
            report.append("Performance Metrics:")
            for entry in perf_entries[-20:]:  # Last 20 metrics
                report.append(f"  {entry.message}")
            report.append("")
        
        return "\n".join(report)
    
    def _load_execution_log(self, execution_id: str) -> List[LogEntry]:
        """Load execution log from file"""
        try:
            log_file = self.log_dir / f"{execution_id}.json"
            
            if not log_file.exists():
                return []
            
            entries = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if 'level' in data and 'category' in data:  # It's a log entry
                            entries.append(LogEntry.from_dict(data))
                    except json.JSONDecodeError:
                        continue  # Skip invalid lines
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Failed to load execution log: {e}")
            return []
    
    def _cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            log_files = list(self.log_dir.glob("*.json"))
            
            if len(log_files) <= self.max_log_files:
                return
            
            # Sort by modification time and remove oldest
            log_files.sort(key=lambda f: f.stat().st_mtime)
            files_to_remove = log_files[:-self.max_log_files]
            
            for file_path in files_to_remove:
                file_path.unlink()
                self.logger.debug(f"Removed old log file: {file_path}")
            
            self.logger.info(f"Cleaned up {len(files_to_remove)} old log files")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
    
    def list_execution_logs(self) -> List[Dict[str, Any]]:
        """List available execution logs"""
        try:
            log_files = list(self.log_dir.glob("*.json"))
            
            logs = []
            for log_file in log_files:
                try:
                    stat = log_file.stat()
                    execution_id = log_file.stem
                    
                    logs.append({
                        'execution_id': execution_id,
                        'file_path': str(log_file),
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
                except Exception:
                    continue
            
            # Sort by creation time (newest first)
            logs.sort(key=lambda x: x['created'], reverse=True)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to list execution logs: {e}")
            return []