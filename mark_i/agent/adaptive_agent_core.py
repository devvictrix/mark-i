"""
Adaptive Agent Core for MARK-I hierarchical AI architecture.

This module integrates uncertainty handling and error recovery with the Enhanced Agent Core
to provide robust, adaptive execution capabilities with comprehensive error management.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from mark_i.core.interfaces import (
    IAgentCore, Context, Goal, Action, Observation, ExecutionResult
)
from mark_i.core.architecture_config import AgentCoreConfig
from mark_i.agent.enhanced_agent_core import EnhancedAgentCore
from mark_i.agent.uncertainty_handler import UncertaintyHandler, ClarificationRequest, ClarificationResponse
from mark_i.agent.error_recovery import ErrorRecoverySystem, ErrorEvent, RecoveryAttempt

logger = logging.getLogger("mark_i.agent.adaptive_agent_core")


class AdaptiveAgentCore(EnhancedAgentCore):
    """
    Adaptive Agent Core with integrated uncertainty handling and error recovery.
    
    Extends the Enhanced Agent Core with robust uncertainty management,
    user clarification mechanisms, and adaptive error recovery strategies.
    """
    
    def __init__(self, 
                 action_executor,
                 toolbelt,
                 world_model,
                 config: Optional[AgentCoreConfig] = None):
        """Initialize the Adaptive Agent Core."""
        super().__init__(action_executor, toolbelt, world_model, config)
        
        # Initialize uncertainty handler and error recovery
        self.uncertainty_handler = UncertaintyHandler(config)
        self.error_recovery = ErrorRecoverySystem(config)
        
        # Integration state
        self.active_clarifications: Dict[str, ClarificationRequest] = {}
        self.recovery_in_progress = False
        
        # User interaction callbacks
        self.user_clarification_callbacks: List[Callable[[ClarificationRequest], Optional[ClarificationResponse]]] = []
        
    def _initialize_component(self) -> bool:
        """Initialize the Adaptive Agent Core component."""
        try:
            # Initialize parent component
            if not super()._initialize_component():
                return False
            
            # Initialize uncertainty handler
            if not self.uncertainty_handler.initialize():
                self.logger.error("Failed to initialize uncertainty handler")
                return False
            
            # Initialize error recovery system
            if not self.error_recovery.initialize():
                self.logger.error("Failed to initialize error recovery system")
                return False
            
            # Set up integration callbacks
            self._setup_integration_callbacks()
            
            self.logger.info("Adaptive Agent Core initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Adaptive Agent Core: {e}")
            return False
    
    def execute_command(self, command: str, context: Optional[Context] = None) -> ExecutionResult:
        """Execute a command with uncertainty handling and error recovery."""
        try:
            # Assess uncertainty before execution
            situation_data = {
                'command': command,
                'available_options': self.toolbelt.get_available_tools(),
                'required_resources': [],
                'available_resources': []
            }
            
            uncertainty_assessment = self.uncertainty_handler.assess_uncertainty(
                context or self._build_current_context(), 
                situation_data
            )
            
            # Handle high uncertainty before proceeding
            if uncertainty_assessment.level.value in ['high', 'critical']:
                clarification_result = self._handle_pre_execution_uncertainty(uncertainty_assessment)
                if not clarification_result.get('proceed', True):
                    return ExecutionResult(
                        success=False,
                        message=f"Execution cancelled due to uncertainty: {clarification_result.get('reason', 'Unknown')}"
                    )
            
            # Execute command with error recovery
            return self._execute_with_recovery(lambda: super().execute_command(command, context))
            
        except Exception as e:
            error_msg = f"Failed to execute adaptive command: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def execute_goal(self, goal: Goal) -> ExecutionResult:
        """Execute a goal with uncertainty handling and error recovery."""
        try:
            # Assess goal complexity and uncertainty
            goal_assessment = self._assess_goal_uncertainty(goal)
            
            # Handle uncertainty if needed
            if goal_assessment['uncertainty_level'] in ['high', 'critical']:
                clarification_result = self._handle_goal_uncertainty(goal, goal_assessment)
                if not clarification_result.get('proceed', True):
                    return ExecutionResult(
                        success=False,
                        message=f"Goal execution cancelled: {clarification_result.get('reason', 'Unknown')}"
                    )
            
            # Execute goal with adaptive recovery
            return self._execute_with_recovery(lambda: super().execute_goal(goal))
            
        except Exception as e:
            error_msg = f"Failed to execute adaptive goal: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def handle_uncertainty(self, uncertainty: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced uncertainty handling with user interaction."""
        try:
            # Use the uncertainty handler for comprehensive processing
            uncertainty_assessment = self.uncertainty_handler.assess_uncertainty(
                self.current_context or self._build_current_context(),
                uncertainty
            )
            
            # Request clarification if needed
            if uncertainty_assessment.level.value in ['medium', 'high', 'critical']:
                clarification_request = self.uncertainty_handler.request_clarification(uncertainty_assessment)
                
                # Try to get user clarification
                clarification_response = self._get_user_clarification(clarification_request)
                
                if clarification_response:
                    # Process the clarification response
                    resolution = self.uncertainty_handler.handle_clarification_response(clarification_response)
                    return resolution
            
            # Fallback to automatic resolution
            return self.uncertainty_handler.resolve_uncertainty(uncertainty_assessment)
            
        except Exception as e:
            self.logger.error(f"Failed to handle uncertainty: {e}")
            return super().handle_uncertainty(uncertainty)
    
    def add_user_clarification_callback(self, callback: Callable[[ClarificationRequest], Optional[ClarificationResponse]]) -> None:
        """Add a callback for user clarification requests."""
        if callback not in self.user_clarification_callbacks:
            self.user_clarification_callbacks.append(callback)
            self.uncertainty_handler.add_user_interaction_callback(callback)
    
    def remove_user_clarification_callback(self, callback: Callable[[ClarificationRequest], Optional[ClarificationResponse]]) -> None:
        """Remove a user clarification callback."""
        if callback in self.user_clarification_callbacks:
            self.user_clarification_callbacks.remove(callback)
            self.uncertainty_handler.remove_user_interaction_callback(callback)
    
    def get_adaptation_metrics(self) -> Dict[str, Any]:
        """Get metrics about adaptation performance."""
        try:
            uncertainty_stats = {
                'total_uncertainties': len(self.uncertainty_handler.uncertainty_assessments),
                'resolved_uncertainties': len(self.uncertainty_handler.clarification_responses),
                'pending_clarifications': len(self.active_clarifications)
            }
            
            recovery_stats = self.error_recovery.get_recovery_statistics()
            
            return {
                'uncertainty_handling': uncertainty_stats,
                'error_recovery': recovery_stats,
                'adaptation_effectiveness': self._calculate_adaptation_effectiveness(uncertainty_stats, recovery_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get adaptation metrics: {e}")
            return {}
    
    # Private helper methods
    
    def _setup_integration_callbacks(self) -> None:
        """Set up callbacks for integration between components."""
        try:
            # Add recovery callback to learn from recovery attempts
            self.error_recovery.add_recovery_callback(self._on_recovery_completed)
            
        except Exception as e:
            self.logger.error(f"Failed to setup integration callbacks: {e}")
    
    def _handle_pre_execution_uncertainty(self, uncertainty_assessment) -> Dict[str, Any]:
        """Handle uncertainty before command execution."""
        try:
            # Request clarification for high uncertainty
            clarification_request = self.uncertainty_handler.request_clarification(uncertainty_assessment)
            
            # Try to get clarification
            clarification_response = self._get_user_clarification(clarification_request)
            
            if clarification_response and clarification_response.response_type == 'answer':
                # Process the response
                resolution = self.uncertainty_handler.handle_clarification_response(clarification_response)
                return {'proceed': resolution.get('status') == 'resolved', 'resolution': resolution}
            
            # If no clarification available, decide based on uncertainty level
            if uncertainty_assessment.level.value == 'critical':
                return {'proceed': False, 'reason': 'Critical uncertainty without clarification'}
            
            return {'proceed': True, 'reason': 'Proceeding with caution'}
            
        except Exception as e:
            self.logger.error(f"Failed to handle pre-execution uncertainty: {e}")
            return {'proceed': False, 'reason': f'Uncertainty handling failed: {e}'}
    
    def _assess_goal_uncertainty(self, goal: Goal) -> Dict[str, Any]:
        """Assess uncertainty specific to goal execution."""
        try:
            # Analyze goal complexity
            complexity_factors = []
            
            if len(goal.success_criteria) > 5:
                complexity_factors.append('many_success_criteria')
            
            if goal.description and len(goal.description.split()) > 20:
                complexity_factors.append('complex_description')
            
            if goal.context and goal.context.system_state:
                if goal.context.system_state.get('high_complexity', False):
                    complexity_factors.append('complex_context')
            
            # Determine uncertainty level
            if len(complexity_factors) >= 3:
                uncertainty_level = 'critical'
            elif len(complexity_factors) >= 2:
                uncertainty_level = 'high'
            elif len(complexity_factors) >= 1:
                uncertainty_level = 'medium'
            else:
                uncertainty_level = 'low'
            
            return {
                'uncertainty_level': uncertainty_level,
                'complexity_factors': complexity_factors,
                'assessment_confidence': 0.8
            }
            
        except Exception as e:
            self.logger.error(f"Failed to assess goal uncertainty: {e}")
            return {'uncertainty_level': 'medium', 'complexity_factors': [], 'assessment_confidence': 0.5}
    
    def _handle_goal_uncertainty(self, goal: Goal, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Handle uncertainty specific to goal execution."""
        try:
            # Create uncertainty data for the handler
            uncertainty_data = {
                'type': 'goal_complexity',
                'description': f"Goal has {assessment['uncertainty_level']} complexity",
                'context': {'goal': goal.description, 'factors': assessment['complexity_factors']},
                'possible_resolutions': [
                    'Break down into smaller goals',
                    'Request more specific instructions',
                    'Proceed with current understanding'
                ]
            }
            
            # Use uncertainty handler
            uncertainty_assessment = self.uncertainty_handler.assess_uncertainty(
                goal.context or self._build_current_context(),
                uncertainty_data
            )
            
            # Request clarification
            clarification_request = self.uncertainty_handler.request_clarification(uncertainty_assessment)
            clarification_response = self._get_user_clarification(clarification_request)
            
            if clarification_response:
                resolution = self.uncertainty_handler.handle_clarification_response(clarification_response)
                return {'proceed': resolution.get('status') == 'resolved', 'resolution': resolution}
            
            return {'proceed': True, 'reason': 'Proceeding with available information'}
            
        except Exception as e:
            self.logger.error(f"Failed to handle goal uncertainty: {e}")
            return {'proceed': False, 'reason': f'Goal uncertainty handling failed: {e}'}
    
    def _execute_with_recovery(self, execution_func: Callable[[], ExecutionResult]) -> ExecutionResult:
        """Execute a function with error recovery capabilities."""
        try:
            self.recovery_in_progress = False
            
            # Initial execution attempt
            result = execution_func()
            
            # If successful, return immediately
            if result.success:
                return result
            
            # Detect and handle error
            error_event = self.error_recovery.detect_error(result, context=self.current_context)
            
            if not error_event:
                return result  # No recoverable error detected
            
            # Plan recovery attempts
            recovery_attempts = self.error_recovery.plan_recovery(error_event)
            
            if not recovery_attempts:
                return result  # No recovery strategies available
            
            # Execute recovery attempts
            self.recovery_in_progress = True
            
            for attempt in recovery_attempts:
                try:
                    recovery_result = self.error_recovery.execute_recovery(
                        attempt, 
                        self._create_recovery_executor(execution_func)
                    )
                    
                    # Learn from the recovery attempt
                    self.error_recovery.learn_from_recovery(recovery_result)
                    
                    # If recovery was successful, return the result
                    if recovery_result.success and recovery_result.execution_result:
                        self.recovery_in_progress = False
                        return recovery_result.execution_result
                        
                except Exception as e:
                    self.logger.error(f"Recovery attempt failed: {e}")
                    continue
            
            # All recovery attempts failed
            self.recovery_in_progress = False
            return ExecutionResult(
                success=False,
                message=f"Execution failed and all recovery attempts exhausted. Original error: {result.message}"
            )
            
        except Exception as e:
            self.recovery_in_progress = False
            error_msg = f"Error during recovery execution: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def _get_user_clarification(self, clarification_request: ClarificationRequest) -> Optional[ClarificationResponse]:
        """Get clarification from user through callbacks."""
        try:
            # Store active clarification
            self.active_clarifications[clarification_request.request_id] = clarification_request
            
            # Try each callback until we get a response
            for callback in self.user_clarification_callbacks:
                try:
                    response = callback(clarification_request)
                    if response:
                        # Remove from active clarifications
                        self.active_clarifications.pop(clarification_request.request_id, None)
                        return response
                except Exception as e:
                    self.logger.error(f"User clarification callback failed: {e}")
                    continue
            
            # No response received
            self.active_clarifications.pop(clarification_request.request_id, None)
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get user clarification: {e}")
            return None
    
    def _create_recovery_executor(self, original_func: Callable[[], ExecutionResult]) -> Callable[[Action, Dict[str, Any]], ExecutionResult]:
        """Create an executor function for recovery attempts."""
        def recovery_executor(action: Action, parameters: Dict[str, Any]) -> ExecutionResult:
            try:
                # For recovery, we typically want to execute the modified action
                # This is a simplified implementation - in practice, this would
                # integrate more closely with the action execution system
                return original_func()
            except Exception as e:
                return ExecutionResult(success=False, message=str(e))
        
        return recovery_executor
    
    def _on_recovery_completed(self, attempt: RecoveryAttempt, result) -> None:
        """Callback for when a recovery attempt is completed."""
        try:
            # Log recovery completion
            self.logger.info(f"Recovery attempt completed: {attempt.strategy.value} -> {'success' if result.success else 'failure'}")
            
            # Notify observers
            self._notify_observers({
                'type': 'recovery_completed',
                'attempt': {
                    'strategy': attempt.strategy.value,
                    'error_id': attempt.error_id
                },
                'result': {
                    'success': result.success,
                    'lessons_learned': result.lessons_learned
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to handle recovery completion: {e}")
    
    def _calculate_adaptation_effectiveness(self, uncertainty_stats: Dict[str, Any], recovery_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall adaptation effectiveness metrics."""
        try:
            # Calculate uncertainty resolution rate
            total_uncertainties = uncertainty_stats.get('total_uncertainties', 0)
            resolved_uncertainties = uncertainty_stats.get('resolved_uncertainties', 0)
            uncertainty_resolution_rate = resolved_uncertainties / total_uncertainties if total_uncertainties > 0 else 0.0
            
            # Get error recovery rate
            error_recovery_rate = recovery_stats.get('overall_success_rate', 0.0)
            
            # Calculate combined effectiveness
            if uncertainty_resolution_rate > 0 and error_recovery_rate > 0:
                combined_effectiveness = (uncertainty_resolution_rate + error_recovery_rate) / 2
            elif uncertainty_resolution_rate > 0:
                combined_effectiveness = uncertainty_resolution_rate * 0.7  # Partial effectiveness
            elif error_recovery_rate > 0:
                combined_effectiveness = error_recovery_rate * 0.7  # Partial effectiveness
            else:
                combined_effectiveness = 0.0
            
            return {
                'uncertainty_resolution_rate': uncertainty_resolution_rate,
                'error_recovery_rate': error_recovery_rate,
                'combined_effectiveness': combined_effectiveness,
                'adaptation_quality': 'excellent' if combined_effectiveness > 0.8 else
                                    'good' if combined_effectiveness > 0.6 else
                                    'fair' if combined_effectiveness > 0.4 else 'poor'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate adaptation effectiveness: {e}")
            return {'combined_effectiveness': 0.0, 'adaptation_quality': 'unknown'}
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Adaptive Agent Core specific status."""
        base_status = super()._get_component_status()
        
        adaptive_status = {
            'uncertainty_handler_status': self.uncertainty_handler.get_status(),
            'error_recovery_status': self.error_recovery.get_status(),
            'active_clarifications': len(self.active_clarifications),
            'recovery_in_progress': self.recovery_in_progress,
            'user_clarification_callbacks': len(self.user_clarification_callbacks),
        }
        
        base_status.update(adaptive_status)
        return base_status