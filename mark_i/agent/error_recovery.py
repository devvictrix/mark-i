"""
Error Recovery System for MARK-I Agent Core.

This module provides comprehensive error detection, analysis, and recovery capabilities
with adaptive retry logic and strategy modification.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from mark_i.core.base_component import BaseComponent
from mark_i.core.interfaces import ExecutionResult, Action, Context
from mark_i.core.architecture_config import ComponentConfig

logger = logging.getLogger("mark_i.agent.error_recovery")


class ErrorType(Enum):
    """Types of errors that can occur."""
    EXECUTION_FAILURE = "execution_failure"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    INVALID_INPUT = "invalid_input"
    NETWORK_ERROR = "network_error"
    SYSTEM_ERROR = "system_error"
    USER_INTERRUPTION = "user_interruption"
    UNEXPECTED_STATE = "unexpected_state"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY_SAME = "retry_same"
    RETRY_MODIFIED = "retry_modified"
    ALTERNATIVE_METHOD = "alternative_method"
    FALLBACK_ACTION = "fallback_action"
    USER_INTERVENTION = "user_intervention"
    ABORT_GRACEFULLY = "abort_gracefully"
    ESCALATE = "escalate"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """Represents an error event."""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    description: str
    context: Dict[str, Any]
    failed_action: Optional[Action]
    execution_result: Optional[ExecutionResult]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RecoveryAttempt:
    """Represents a recovery attempt."""
    attempt_id: str
    error_id: str
    strategy: RecoveryStrategy
    modified_action: Optional[Action]
    parameters: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    result_id: str
    attempt_id: str
    success: bool
    execution_result: Optional[ExecutionResult]
    lessons_learned: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ErrorRecoverySystem(BaseComponent):
    """
    Comprehensive error recovery system with adaptive strategies.
    
    Detects errors, analyzes their causes, and implements appropriate recovery
    strategies with learning capabilities for continuous improvement.
    """    
  
  def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize the Error Recovery System."""
        super().__init__("error_recovery_system", config)
        
        # Error tracking
        self.error_events: Dict[str, ErrorEvent] = {}
        self.recovery_attempts: Dict[str, RecoveryAttempt] = {}
        self.recovery_results: Dict[str, RecoveryResult] = {}
        
        # Counters
        self.error_counter = 0
        self.attempt_counter = 0
        self.result_counter = 0
        
        # Configuration
        self.max_retry_attempts = 3
        self.retry_delay_base = 1.0  # seconds
        self.retry_delay_multiplier = 2.0
        self.max_retry_delay = 30.0  # seconds
        
        # Recovery strategies mapping
        self.recovery_strategies: Dict[ErrorType, List[RecoveryStrategy]] = {
            ErrorType.EXECUTION_FAILURE: [
                RecoveryStrategy.RETRY_SAME,
                RecoveryStrategy.RETRY_MODIFIED,
                RecoveryStrategy.ALTERNATIVE_METHOD
            ],
            ErrorType.TIMEOUT: [
                RecoveryStrategy.RETRY_SAME,
                RecoveryStrategy.RETRY_MODIFIED,
                RecoveryStrategy.FALLBACK_ACTION
            ],
            ErrorType.PERMISSION_DENIED: [
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.ALTERNATIVE_METHOD,
                RecoveryStrategy.ESCALATE
            ],
            ErrorType.RESOURCE_UNAVAILABLE: [
                RecoveryStrategy.ALTERNATIVE_METHOD,
                RecoveryStrategy.FALLBACK_ACTION,
                RecoveryStrategy.USER_INTERVENTION
            ],
            ErrorType.INVALID_INPUT: [
                RecoveryStrategy.RETRY_MODIFIED,
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.ABORT_GRACEFULLY
            ],
            ErrorType.NETWORK_ERROR: [
                RecoveryStrategy.RETRY_SAME,
                RecoveryStrategy.RETRY_MODIFIED,
                RecoveryStrategy.FALLBACK_ACTION
            ],
            ErrorType.SYSTEM_ERROR: [
                RecoveryStrategy.RETRY_SAME,
                RecoveryStrategy.ESCALATE,
                RecoveryStrategy.ABORT_GRACEFULLY
            ],
            ErrorType.USER_INTERRUPTION: [
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.ABORT_GRACEFULLY
            ],
            ErrorType.UNEXPECTED_STATE: [
                RecoveryStrategy.ALTERNATIVE_METHOD,
                RecoveryStrategy.RETRY_MODIFIED,
                RecoveryStrategy.USER_INTERVENTION
            ]
        }
        
        # Learning data
        self.strategy_success_rates: Dict[Tuple[ErrorType, RecoveryStrategy], float] = {}
        self.error_patterns: List[Dict[str, Any]] = []
        
        # Callbacks
        self.recovery_callbacks: List[Callable[[RecoveryAttempt, RecoveryResult], None]] = []
    
    def _initialize_component(self) -> bool:
        """Initialize the Error Recovery System component."""
        try:
            # Initialize success rates with default values
            for error_type, strategies in self.recovery_strategies.items():
                for strategy in strategies:
                    self.strategy_success_rates[(error_type, strategy)] = 0.5
            
            self.logger.info("Error Recovery System initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Error Recovery System: {e}")
            return False
    
    def detect_error(self, execution_result: ExecutionResult, 
                    action: Optional[Action] = None, 
                    context: Optional[Context] = None) -> Optional[ErrorEvent]:
        """Detect and classify errors from execution results."""
        try:
            if execution_result.success:
                return None  # No error detected
            
            # Analyze the error
            error_type = self._classify_error(execution_result, action, context)
            severity = self._assess_error_severity(error_type, execution_result, context)
            
            # Create error event
            error_event = ErrorEvent(
                error_id=f"error_{self.error_counter}",
                error_type=error_type,
                severity=severity,
                description=execution_result.message,
                context=self._extract_error_context(execution_result, action, context),
                failed_action=action,
                execution_result=execution_result
            )
            
            self.error_counter += 1
            self.error_events[error_event.error_id] = error_event
            
            self.logger.warning(f"Error detected: {error_type.value} ({severity.value})")
            
            # Notify observers
            self._notify_observers({
                'type': 'error_detected',
                'error': asdict(error_event),
                'timestamp': datetime.now().isoformat()
            })
            
            return error_event
            
        except Exception as e:
            self.logger.error(f"Failed to detect error: {e}")
            return None
    
    def plan_recovery(self, error_event: ErrorEvent) -> List[RecoveryAttempt]:
        """Plan recovery attempts for an error event."""
        try:
            # Get available strategies for this error type
            available_strategies = self.recovery_strategies.get(error_event.error_type, [RecoveryStrategy.ABORT_GRACEFULLY])
            
            # Sort strategies by success rate
            sorted_strategies = self._sort_strategies_by_success_rate(error_event.error_type, available_strategies)
            
            # Create recovery attempts
            recovery_attempts = []
            for i, strategy in enumerate(sorted_strategies[:self.max_retry_attempts]):
                attempt = RecoveryAttempt(
                    attempt_id=f"attempt_{self.attempt_counter}",
                    error_id=error_event.error_id,
                    strategy=strategy,
                    modified_action=self._create_modified_action(error_event, strategy),
                    parameters=self._generate_recovery_parameters(error_event, strategy, i)
                )
                
                self.attempt_counter += 1
                self.recovery_attempts[attempt.attempt_id] = attempt
                recovery_attempts.append(attempt)
            
            self.logger.info(f"Planned {len(recovery_attempts)} recovery attempts for {error_event.error_id}")
            
            return recovery_attempts
            
        except Exception as e:
            self.logger.error(f"Failed to plan recovery: {e}")
            return []
    
    def execute_recovery(self, recovery_attempt: RecoveryAttempt, 
                        executor: Callable[[Action, Dict[str, Any]], ExecutionResult]) -> RecoveryResult:
        """Execute a recovery attempt."""
        try:
            self.logger.info(f"Executing recovery attempt: {recovery_attempt.strategy.value}")
            
            # Apply delay if this is a retry
            if recovery_attempt.strategy in [RecoveryStrategy.RETRY_SAME, RecoveryStrategy.RETRY_MODIFIED]:
                delay = self._calculate_retry_delay(recovery_attempt.parameters.get('attempt_number', 0))
                if delay > 0:
                    time.sleep(delay)
            
            # Execute the recovery strategy
            if recovery_attempt.strategy == RecoveryStrategy.RETRY_SAME:
                result = self._execute_retry_same(recovery_attempt, executor)
            elif recovery_attempt.strategy == RecoveryStrategy.RETRY_MODIFIED:
                result = self._execute_retry_modified(recovery_attempt, executor)
            elif recovery_attempt.strategy == RecoveryStrategy.ALTERNATIVE_METHOD:
                result = self._execute_alternative_method(recovery_attempt, executor)
            elif recovery_attempt.strategy == RecoveryStrategy.FALLBACK_ACTION:
                result = self._execute_fallback_action(recovery_attempt, executor)
            elif recovery_attempt.strategy == RecoveryStrategy.USER_INTERVENTION:
                result = self._execute_user_intervention(recovery_attempt)
            elif recovery_attempt.strategy == RecoveryStrategy.ABORT_GRACEFULLY:
                result = self._execute_graceful_abort(recovery_attempt)
            elif recovery_attempt.strategy == RecoveryStrategy.ESCALATE:
                result = self._execute_escalation(recovery_attempt)
            else:
                result = ExecutionResult(success=False, message="Unknown recovery strategy")
            
            # Create recovery result
            recovery_result = RecoveryResult(
                result_id=f"result_{self.result_counter}",
                attempt_id=recovery_attempt.attempt_id,
                success=result.success,
                execution_result=result,
                lessons_learned=self._extract_lessons_learned(recovery_attempt, result)
            )
            
            self.result_counter += 1
            self.recovery_results[recovery_result.result_id] = recovery_result
            
            # Update success rates
            self._update_strategy_success_rate(recovery_attempt, recovery_result)
            
            # Notify callbacks
            for callback in self.recovery_callbacks:
                try:
                    callback(recovery_attempt, recovery_result)
                except Exception as e:
                    self.logger.error(f"Recovery callback failed: {e}")
            
            self.logger.info(f"Recovery attempt completed: {'success' if result.success else 'failure'}")
            
            return recovery_result
            
        except Exception as e:
            self.logger.error(f"Failed to execute recovery: {e}")
            return RecoveryResult(
                result_id=f"error_result_{self.result_counter}",
                attempt_id=recovery_attempt.attempt_id,
                success=False,
                execution_result=ExecutionResult(success=False, message=str(e)),
                lessons_learned=[f"Recovery execution failed: {e}"]
            )
    
    def learn_from_recovery(self, recovery_result: RecoveryResult) -> None:
        """Learn from recovery results to improve future recovery strategies."""
        try:
            # Get the recovery attempt
            attempt = self.recovery_attempts.get(recovery_result.attempt_id)
            if not attempt:
                return
            
            # Get the original error
            error_event = self.error_events.get(attempt.error_id)
            if not error_event:
                return
            
            # Extract patterns for learning
            pattern = {
                'error_type': error_event.error_type.value,
                'error_context': error_event.context,
                'recovery_strategy': attempt.strategy.value,
                'success': recovery_result.success,
                'lessons': recovery_result.lessons_learned,
                'timestamp': recovery_result.timestamp.isoformat()
            }
            
            self.error_patterns.append(pattern)
            
            # Keep only recent patterns
            if len(self.error_patterns) > 1000:
                self.error_patterns = self.error_patterns[-1000:]
            
            # Update strategy preferences based on success
            if recovery_result.success:
                self._promote_successful_strategy(error_event.error_type, attempt.strategy)
            else:
                self._demote_failed_strategy(error_event.error_type, attempt.strategy)
            
            self.logger.debug(f"Learned from recovery: {attempt.strategy.value} -> {'success' if recovery_result.success else 'failure'}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn from recovery: {e}")
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get statistics about error recovery performance."""
        try:
            total_errors = len(self.error_events)
            total_attempts = len(self.recovery_attempts)
            total_results = len(self.recovery_results)
            
            successful_recoveries = len([r for r in self.recovery_results.values() if r.success])
            
            # Calculate success rate by error type
            error_type_stats = {}
            for error_type in ErrorType:
                type_errors = [e for e in self.error_events.values() if e.error_type == error_type]
                type_attempts = []
                for error in type_errors:
                    type_attempts.extend([a for a in self.recovery_attempts.values() if a.error_id == error.error_id])
                
                type_results = []
                for attempt in type_attempts:
                    type_results.extend([r for r in self.recovery_results.values() if r.attempt_id == attempt.attempt_id])
                
                successful_type_results = [r for r in type_results if r.success]
                
                error_type_stats[error_type.value] = {
                    'total_errors': len(type_errors),
                    'total_attempts': len(type_attempts),
                    'successful_recoveries': len(successful_type_results),
                    'success_rate': len(successful_type_results) / len(type_results) if type_results else 0.0
                }
            
            # Calculate success rate by strategy
            strategy_stats = {}
            for strategy in RecoveryStrategy:
                strategy_attempts = [a for a in self.recovery_attempts.values() if a.strategy == strategy]
                strategy_results = []
                for attempt in strategy_attempts:
                    strategy_results.extend([r for r in self.recovery_results.values() if r.attempt_id == attempt.attempt_id])
                
                successful_strategy_results = [r for r in strategy_results if r.success]
                
                strategy_stats[strategy.value] = {
                    'total_attempts': len(strategy_attempts),
                    'successful_recoveries': len(successful_strategy_results),
                    'success_rate': len(successful_strategy_results) / len(strategy_results) if strategy_results else 0.0
                }
            
            return {
                'total_errors': total_errors,
                'total_attempts': total_attempts,
                'total_results': total_results,
                'successful_recoveries': successful_recoveries,
                'overall_success_rate': successful_recoveries / total_results if total_results else 0.0,
                'error_type_statistics': error_type_stats,
                'strategy_statistics': strategy_stats,
                'learned_patterns': len(self.error_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get recovery statistics: {e}")
            return {}
    
    def add_recovery_callback(self, callback: Callable[[RecoveryAttempt, RecoveryResult], None]) -> None:
        """Add a callback for recovery events."""
        if callback not in self.recovery_callbacks:
            self.recovery_callbacks.append(callback)
    
    def remove_recovery_callback(self, callback: Callable[[RecoveryAttempt, RecoveryResult], None]) -> None:
        """Remove a recovery callback."""
        if callback in self.recovery_callbacks:
            self.recovery_callbacks.remove(callback)
    
    # Private helper methods
    
    def _classify_error(self, execution_result: ExecutionResult, 
                       action: Optional[Action], 
                       context: Optional[Context]) -> ErrorType:
        """Classify the type of error based on execution result and context."""
        try:
            message = execution_result.message.lower()
            
            # Check for specific error patterns
            if 'timeout' in message or 'timed out' in message:
                return ErrorType.TIMEOUT
            elif 'permission' in message or 'access denied' in message:
                return ErrorType.PERMISSION_DENIED
            elif 'not found' in message or 'unavailable' in message:
                return ErrorType.RESOURCE_UNAVAILABLE
            elif 'invalid' in message or 'bad input' in message:
                return ErrorType.INVALID_INPUT
            elif 'network' in message or 'connection' in message:
                return ErrorType.NETWORK_ERROR
            elif 'system error' in message or 'internal error' in message:
                return ErrorType.SYSTEM_ERROR
            elif 'interrupted' in message or 'cancelled' in message:
                return ErrorType.USER_INTERRUPTION
            elif 'unexpected' in message or 'unknown state' in message:
                return ErrorType.UNEXPECTED_STATE
            else:
                return ErrorType.EXECUTION_FAILURE
                
        except Exception as e:
            self.logger.error(f"Failed to classify error: {e}")
            return ErrorType.EXECUTION_FAILURE
    
    def _assess_error_severity(self, error_type: ErrorType, 
                              execution_result: ExecutionResult, 
                              context: Optional[Context]) -> ErrorSeverity:
        """Assess the severity of an error."""
        try:
            # Base severity by error type
            severity_mapping = {
                ErrorType.EXECUTION_FAILURE: ErrorSeverity.MEDIUM,
                ErrorType.TIMEOUT: ErrorSeverity.LOW,
                ErrorType.PERMISSION_DENIED: ErrorSeverity.HIGH,
                ErrorType.RESOURCE_UNAVAILABLE: ErrorSeverity.MEDIUM,
                ErrorType.INVALID_INPUT: ErrorSeverity.LOW,
                ErrorType.NETWORK_ERROR: ErrorSeverity.MEDIUM,
                ErrorType.SYSTEM_ERROR: ErrorSeverity.HIGH,
                ErrorType.USER_INTERRUPTION: ErrorSeverity.LOW,
                ErrorType.UNEXPECTED_STATE: ErrorSeverity.HIGH
            }
            
            base_severity = severity_mapping.get(error_type, ErrorSeverity.MEDIUM)
            
            # Adjust based on context
            if context and context.system_state:
                if context.system_state.get('critical_task', False):
                    # Upgrade severity for critical tasks
                    if base_severity == ErrorSeverity.LOW:
                        base_severity = ErrorSeverity.MEDIUM
                    elif base_severity == ErrorSeverity.MEDIUM:
                        base_severity = ErrorSeverity.HIGH
            
            return base_severity
            
        except Exception as e:
            self.logger.error(f"Failed to assess error severity: {e}")
            return ErrorSeverity.MEDIUM
    
    def _extract_error_context(self, execution_result: ExecutionResult, 
                              action: Optional[Action], 
                              context: Optional[Context]) -> Dict[str, Any]:
        """Extract relevant context information for error analysis."""
        try:
            error_context = {
                'execution_data': execution_result.data or {},
                'timestamp': execution_result.timestamp.isoformat()
            }
            
            if action:
                error_context['action'] = {
                    'name': action.name,
                    'parameters': action.parameters,
                    'confidence': action.confidence
                }
            
            if context:
                error_context['context'] = {
                    'active_applications': context.active_applications,
                    'user_activity': context.user_activity,
                    'system_state': context.system_state
                }
            
            return error_context
            
        except Exception as e:
            self.logger.error(f"Failed to extract error context: {e}")
            return {}
    
    def _sort_strategies_by_success_rate(self, error_type: ErrorType, 
                                        strategies: List[RecoveryStrategy]) -> List[RecoveryStrategy]:
        """Sort recovery strategies by their success rate for the given error type."""
        try:
            strategy_rates = []
            for strategy in strategies:
                rate = self.strategy_success_rates.get((error_type, strategy), 0.5)
                strategy_rates.append((strategy, rate))
            
            # Sort by success rate (descending)
            strategy_rates.sort(key=lambda x: x[1], reverse=True)
            
            return [strategy for strategy, rate in strategy_rates]
            
        except Exception as e:
            self.logger.error(f"Failed to sort strategies: {e}")
            return strategies
    
    def _create_modified_action(self, error_event: ErrorEvent, 
                               strategy: RecoveryStrategy) -> Optional[Action]:
        """Create a modified action for recovery strategies that need it."""
        try:
            if not error_event.failed_action:
                return None
            
            original_action = error_event.failed_action
            
            if strategy == RecoveryStrategy.RETRY_MODIFIED:
                # Modify parameters based on error type
                modified_params = original_action.parameters.copy()
                
                if error_event.error_type == ErrorType.TIMEOUT:
                    # Increase timeout if available
                    if 'timeout' in modified_params:
                        modified_params['timeout'] *= 2
                elif error_event.error_type == ErrorType.INVALID_INPUT:
                    # Try to fix common input issues
                    if 'text' in modified_params:
                        modified_params['text'] = modified_params['text'].strip()
                
                return Action(
                    name=original_action.name,
                    parameters=modified_params,
                    expected_outcome=original_action.expected_outcome,
                    confidence=original_action.confidence * 0.8  # Reduce confidence
                )
            
            elif strategy == RecoveryStrategy.ALTERNATIVE_METHOD:
                # Create alternative action
                alternative_actions = {
                    'click': 'key_press',
                    'key_press': 'click',
                    'type_text': 'key_press'
                }
                
                alt_name = alternative_actions.get(original_action.name, original_action.name)
                alt_params = self._generate_alternative_parameters(original_action)
                
                return Action(
                    name=alt_name,
                    parameters=alt_params,
                    expected_outcome=f"Alternative to {original_action.expected_outcome}",
                    confidence=0.6
                )
            
            return original_action
            
        except Exception as e:
            self.logger.error(f"Failed to create modified action: {e}")
            return error_event.failed_action
    
    def _generate_recovery_parameters(self, error_event: ErrorEvent, 
                                    strategy: RecoveryStrategy, 
                                    attempt_number: int) -> Dict[str, Any]:
        """Generate parameters for recovery attempt."""
        return {
            'attempt_number': attempt_number,
            'error_type': error_event.error_type.value,
            'strategy': strategy.value,
            'original_error': error_event.description
        }
    
    def _calculate_retry_delay(self, attempt_number: int) -> float:
        """Calculate delay before retry attempt."""
        delay = self.retry_delay_base * (self.retry_delay_multiplier ** attempt_number)
        return min(delay, self.max_retry_delay)
    
    def _execute_retry_same(self, attempt: RecoveryAttempt, 
                           executor: Callable[[Action, Dict[str, Any]], ExecutionResult]) -> ExecutionResult:
        """Execute retry with same action."""
        error_event = self.error_events[attempt.error_id]
        if error_event.failed_action:
            return executor(error_event.failed_action, attempt.parameters)
        return ExecutionResult(success=False, message="No action to retry")
    
    def _execute_retry_modified(self, attempt: RecoveryAttempt, 
                               executor: Callable[[Action, Dict[str, Any]], ExecutionResult]) -> ExecutionResult:
        """Execute retry with modified action."""
        if attempt.modified_action:
            return executor(attempt.modified_action, attempt.parameters)
        return ExecutionResult(success=False, message="No modified action available")
    
    def _execute_alternative_method(self, attempt: RecoveryAttempt, 
                                   executor: Callable[[Action, Dict[str, Any]], ExecutionResult]) -> ExecutionResult:
        """Execute alternative method."""
        if attempt.modified_action:
            return executor(attempt.modified_action, attempt.parameters)
        return ExecutionResult(success=False, message="No alternative method available")
    
    def _execute_fallback_action(self, attempt: RecoveryAttempt, 
                                executor: Callable[[Action, Dict[str, Any]], ExecutionResult]) -> ExecutionResult:
        """Execute fallback action."""
        # Create a safe fallback action
        fallback_action = Action(
            name="safe_fallback",
            parameters={'message': 'Executing safe fallback'},
            expected_outcome="Safe state maintained"
        )
        return executor(fallback_action, attempt.parameters)
    
    def _execute_user_intervention(self, attempt: RecoveryAttempt) -> ExecutionResult:
        """Request user intervention."""
        return ExecutionResult(
            success=False,
            message="User intervention required",
            data={'intervention_type': 'user_assistance_needed'}
        )
    
    def _execute_graceful_abort(self, attempt: RecoveryAttempt) -> ExecutionResult:
        """Execute graceful abort."""
        return ExecutionResult(
            success=False,
            message="Task aborted gracefully",
            data={'abort_reason': 'recovery_failed'}
        )
    
    def _execute_escalation(self, attempt: RecoveryAttempt) -> ExecutionResult:
        """Escalate the error to higher level."""
        return ExecutionResult(
            success=False,
            message="Error escalated to higher level",
            data={'escalation_level': 'supervisor'}
        )
    
    def _generate_alternative_parameters(self, original_action: Action) -> Dict[str, Any]:
        """Generate alternative parameters for an action."""
        # Simple parameter alternatives
        alt_params = original_action.parameters.copy()
        
        # Add some variation to coordinates if present
        if 'x' in alt_params and 'y' in alt_params:
            alt_params['x'] += 5  # Small offset
            alt_params['y'] += 5
        
        return alt_params
    
    def _extract_lessons_learned(self, attempt: RecoveryAttempt, result: ExecutionResult) -> List[str]:
        """Extract lessons learned from recovery attempt."""
        lessons = []
        
        if result.success:
            lessons.append(f"Strategy {attempt.strategy.value} was successful")
        else:
            lessons.append(f"Strategy {attempt.strategy.value} failed: {result.message}")
        
        # Add strategy-specific lessons
        if attempt.strategy == RecoveryStrategy.RETRY_SAME and not result.success:
            lessons.append("Same retry failed - consider modifying approach")
        elif attempt.strategy == RecoveryStrategy.ALTERNATIVE_METHOD and result.success:
            lessons.append("Alternative method was more effective than original")
        
        return lessons
    
    def _update_strategy_success_rate(self, attempt: RecoveryAttempt, result: RecoveryResult) -> None:
        """Update success rate for a strategy."""
        try:
            error_event = self.error_events[attempt.error_id]
            key = (error_event.error_type, attempt.strategy)
            
            current_rate = self.strategy_success_rates.get(key, 0.5)
            
            # Simple moving average update
            if result.success:
                new_rate = current_rate * 0.9 + 0.1  # Increase success rate
            else:
                new_rate = current_rate * 0.9  # Decrease success rate
            
            self.strategy_success_rates[key] = max(0.1, min(0.9, new_rate))
            
        except Exception as e:
            self.logger.error(f"Failed to update strategy success rate: {e}")
    
    def _promote_successful_strategy(self, error_type: ErrorType, strategy: RecoveryStrategy) -> None:
        """Promote a successful strategy in the strategy list."""
        try:
            strategies = self.recovery_strategies.get(error_type, [])
            if strategy in strategies:
                # Move successful strategy towards the front
                strategies.remove(strategy)
                strategies.insert(0, strategy)
                self.recovery_strategies[error_type] = strategies
                
        except Exception as e:
            self.logger.error(f"Failed to promote successful strategy: {e}")
    
    def _demote_failed_strategy(self, error_type: ErrorType, strategy: RecoveryStrategy) -> None:
        """Demote a failed strategy in the strategy list."""
        try:
            strategies = self.recovery_strategies.get(error_type, [])
            if strategy in strategies and len(strategies) > 1:
                # Move failed strategy towards the back
                strategies.remove(strategy)
                strategies.append(strategy)
                self.recovery_strategies[error_type] = strategies
                
        except Exception as e:
            self.logger.error(f"Failed to demote failed strategy: {e}")
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Error Recovery System specific status."""
        return {
            'total_errors': len(self.error_events),
            'total_recovery_attempts': len(self.recovery_attempts),
            'successful_recoveries': len([r for r in self.recovery_results.values() if r.success]),
            'max_retry_attempts': self.max_retry_attempts,
            'learned_patterns': len(self.error_patterns),
            'strategy_success_rates': len(self.strategy_success_rates),
        }