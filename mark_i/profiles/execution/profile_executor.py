"""
Profile Executor

Main execution engine that integrates with MARK-I's Eye-Brain-Hand architecture
for intelligent profile execution with screen capture, decision making, and actions.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from ..models.profile import AutomationProfile
from ..models.rule import Rule, Condition, Action, ConditionType, ActionType
from ..models.region import Region
from ..testing.execution_logger import ExecutionLogger
from .integration_bridge import IntegrationBridge
from .context_manager import ProfileContextManager


class ExecutionResult(Enum):
    """Execution result types"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ProfileExecutor:
    """Main profile execution engine with MARK-I integration"""
    
    def __init__(self):
        self.logger = logging.getLogger("mark_i.profiles.execution.executor")
        
        # Integration components
        self.integration_bridge = IntegrationBridge()
        self.context_manager = ProfileContextManager()
        self.execution_logger = ExecutionLogger()
        
        # Execution state
        self.is_executing = False
        self.current_profile: Optional[AutomationProfile] = None
        self.execution_context: Dict[str, Any] = {}
        self.user_variables: Dict[str, Any] = {}
        
        # Callbacks for UI integration
        self.on_execution_start: Optional[Callable[[AutomationProfile], None]] = None
        self.on_execution_complete: Optional[Callable[[ExecutionResult, Dict[str, Any]], None]] = None
        self.on_rule_start: Optional[Callable[[Rule], None]] = None
        self.on_rule_complete: Optional[Callable[[Rule, bool], None]] = None
        self.on_step_start: Optional[Callable[[str, str], None]] = None
        self.on_step_complete: Optional[Callable[[str, bool, Any], None]] = None
        self.on_error: Optional[Callable[[str, Exception], None]] = None
        
        self.logger.info("ProfileExecutor initialized")
    
    def execute_profile(self, profile: AutomationProfile, 
                       user_variables: Dict[str, Any] = None,
                       execution_mode: str = "normal") -> ExecutionResult:
        """
        Execute an automation profile
        
        Args:
            profile: Profile to execute
            user_variables: User-provided variables for execution
            execution_mode: Execution mode ('normal', 'debug', 'simulation')
            
        Returns:
            ExecutionResult indicating success/failure
        """
        if self.is_executing:
            raise RuntimeError("Another profile is already executing")
        
        self.logger.info(f"Starting execution of profile: {profile.name}")
        
        try:
            # Initialize execution
            self.is_executing = True
            self.current_profile = profile
            self.user_variables = user_variables or {}
            
            # Start execution logging
            execution_id = self.execution_logger.start_execution_log(profile.name)
            
            # Initialize context
            self.context_manager.initialize_context(profile, self.user_variables)
            
            # Callback
            if self.on_execution_start:
                self.on_execution_start(profile)
            
            # Execute profile
            result = self._execute_profile_internal(profile, execution_mode)
            
            # Complete execution logging
            success = result == ExecutionResult.SUCCESS
            summary = self._get_execution_summary()
            self.execution_logger.end_execution_log(success, summary)
            
            # Callback
            if self.on_execution_complete:
                self.on_execution_complete(result, summary)
            
            self.logger.info(f"Profile execution completed: {result.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Profile execution failed: {e}")
            
            # Log error
            self.execution_logger.log_critical(
                'profile', f"Execution failed with exception: {str(e)}"
            )
            
            # End logging
            self.execution_logger.end_execution_log(False, {'error': str(e)})
            
            # Callback
            if self.on_error:
                self.on_error("Profile execution failed", e)
            
            return ExecutionResult.FAILURE
            
        finally:
            # Cleanup
            self.is_executing = False
            self.current_profile = None
            self.execution_context = {}
            self.context_manager.cleanup_context()
    
    def _execute_profile_internal(self, profile: AutomationProfile, 
                                execution_mode: str) -> ExecutionResult:
        """Internal profile execution logic"""
        
        # Validate profile before execution
        if not self._validate_execution_environment(profile):
            return ExecutionResult.FAILURE
        
        # Sort rules by priority
        enabled_rules = [rule for rule in profile.rules if rule.enabled]
        enabled_rules.sort(key=lambda r: r.priority)
        
        self.execution_logger.log_info(
            'profile', f"Executing {len(enabled_rules)} enabled rules"
        )
        
        executed_rules = 0
        successful_rules = 0
        
        # Execute each rule
        for rule in enabled_rules:
            if not self.is_executing:  # Check for cancellation
                return ExecutionResult.CANCELLED
            
            try:
                rule_result = self._execute_rule(rule, execution_mode)
                executed_rules += 1
                
                if rule_result:
                    successful_rules += 1
                    
            except Exception as e:
                self.logger.error(f"Rule execution failed: {rule.name} - {e}")
                self.execution_logger.log_error(
                    'rule', f"Rule execution failed: {str(e)}", 
                    rule_name=rule.name
                )
                
                # Continue with next rule unless it's a critical failure
                if not self._is_recoverable_error(e):
                    return ExecutionResult.FAILURE
        
        # Determine overall result
        if successful_rules == 0:
            return ExecutionResult.FAILURE
        elif successful_rules == executed_rules:
            return ExecutionResult.SUCCESS
        else:
            return ExecutionResult.PARTIAL
    
    def _execute_rule(self, rule: Rule, execution_mode: str) -> bool:
        """Execute a single rule"""
        self.logger.debug(f"Executing rule: {rule.name}")
        
        start_time = time.time()
        
        # Callback
        if self.on_rule_start:
            self.on_rule_start(rule)
        
        # Log rule start
        self.execution_logger.log_rule_start(
            rule.name, rule.priority, 
            {'logical_operator': rule.logical_operator}
        )
        
        try:
            # Evaluate conditions
            conditions_result = self._evaluate_rule_conditions(rule, execution_mode)
            
            if not conditions_result:
                self.logger.debug(f"Rule conditions not met: {rule.name}")
                self.execution_logger.log_info(
                    'rule', f"Rule conditions not met: {rule.name}",
                    rule_name=rule.name
                )
                
                # Callback
                if self.on_rule_complete:
                    self.on_rule_complete(rule, False)
                
                return False
            
            # Execute actions
            actions_result = self._execute_rule_actions(rule, execution_mode)
            
            duration = time.time() - start_time
            
            # Log rule completion
            self.execution_logger.log_rule_end(
                rule.name, actions_result, duration,
                {'conditions_met': conditions_result}
            )
            
            # Callback
            if self.on_rule_complete:
                self.on_rule_complete(rule, actions_result)
            
            return actions_result
            
        except Exception as e:
            duration = time.time() - start_time
            self.execution_logger.log_rule_end(
                rule.name, False, duration, {'error': str(e)}
            )
            raise
    
    def _evaluate_rule_conditions(self, rule: Rule, execution_mode: str) -> bool:
        """Evaluate all conditions for a rule"""
        if not rule.conditions:
            return True  # No conditions means always execute
        
        condition_results = []
        
        for i, condition in enumerate(rule.conditions):
            try:
                result = self._evaluate_condition(condition, execution_mode, i)
                condition_results.append(result)
                
            except Exception as e:
                self.logger.error(f"Condition evaluation failed: {e}")
                self.execution_logger.log_error(
                    'condition', f"Condition evaluation failed: {str(e)}",
                    rule_name=rule.name, step_index=i
                )
                condition_results.append(False)
        
        # Apply logical operator
        if rule.logical_operator == "OR":
            return any(condition_results)
        else:  # Default to AND
            return all(condition_results)
    
    def _evaluate_condition(self, condition: Condition, execution_mode: str, 
                          condition_index: int) -> bool:
        """Evaluate a single condition"""
        start_time = time.time()
        
        # Callback
        if self.on_step_start:
            self.on_step_start("condition", f"Evaluating {condition.condition_type.value}")
        
        try:
            result = False
            
            if condition.condition_type == ConditionType.VISUAL_MATCH:
                result = self._evaluate_visual_match_condition(condition)
            elif condition.condition_type == ConditionType.OCR_CONTAINS:
                result = self._evaluate_ocr_condition(condition)
            elif condition.condition_type == ConditionType.TEMPLATE_MATCH:
                result = self._evaluate_template_match_condition(condition)
            elif condition.condition_type == ConditionType.SYSTEM_STATE:
                result = self._evaluate_system_state_condition(condition)
            elif condition.condition_type == ConditionType.TIME_BASED:
                result = self._evaluate_time_condition(condition)
            else:
                self.logger.warning(f"Unknown condition type: {condition.condition_type}")
                result = False
            
            duration = time.time() - start_time
            
            # Log condition evaluation
            self.execution_logger.log_condition_evaluation(
                self.current_profile.name if self.current_profile else "unknown",
                condition_index,
                condition.condition_type.value,
                result,
                duration,
                {'region': condition.region_name, 'parameters': condition.parameters}
            )
            
            # Callback
            if self.on_step_complete:
                self.on_step_complete("condition", result, condition.condition_type.value)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.execution_logger.log_condition_evaluation(
                self.current_profile.name if self.current_profile else "unknown",
                condition_index,
                condition.condition_type.value,
                False,
                duration,
                {'error': str(e)}
            )
            raise
    
    def _evaluate_visual_match_condition(self, condition: Condition) -> bool:
        """Evaluate visual match condition using MARK-I's vision system"""
        try:
            # Get region for analysis
            region = self._get_region_by_name(condition.region_name)
            if not region:
                raise ValueError(f"Region not found: {condition.region_name}")
            
            # Capture region using integration bridge
            screenshot = self.integration_bridge.capture_region(region)
            if screenshot is None:
                return False
            
            # Use MARK-I's vision analysis
            template_path = condition.parameters.get('template_path')
            threshold = condition.parameters.get('threshold', 0.8)
            
            match_result = self.integration_bridge.analyze_visual_match(
                screenshot, template_path, threshold
            )
            
            return match_result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"Visual match condition failed: {e}")
            return False
    
    def _evaluate_ocr_condition(self, condition: Condition) -> bool:
        """Evaluate OCR condition using MARK-I's text recognition"""
        try:
            # Get region for analysis
            region = self._get_region_by_name(condition.region_name)
            if not region:
                raise ValueError(f"Region not found: {condition.region_name}")
            
            # Capture region
            screenshot = self.integration_bridge.capture_region(region)
            if screenshot is None:
                return False
            
            # Use MARK-I's OCR capabilities
            ocr_result = self.integration_bridge.perform_ocr(screenshot)
            if not ocr_result:
                return False
            
            # Check if text contains target
            search_text = condition.parameters.get('text', '')
            case_sensitive = condition.parameters.get('case_sensitive', False)
            
            ocr_text = ocr_result.get('text', '')
            
            if not case_sensitive:
                ocr_text = ocr_text.lower()
                search_text = search_text.lower()
            
            return search_text in ocr_text
            
        except Exception as e:
            self.logger.error(f"OCR condition failed: {e}")
            return False
    
    def _evaluate_template_match_condition(self, condition: Condition) -> bool:
        """Evaluate template match condition"""
        try:
            # Get region for analysis
            region = self._get_region_by_name(condition.region_name)
            if not region:
                raise ValueError(f"Region not found: {condition.region_name}")
            
            # Capture region
            screenshot = self.integration_bridge.capture_region(region)
            if screenshot is None:
                return False
            
            # Use template matching
            template_file = condition.parameters.get('template_file')
            confidence = condition.parameters.get('confidence', 0.8)
            
            match_result = self.integration_bridge.match_template(
                screenshot, template_file, confidence
            )
            
            return match_result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"Template match condition failed: {e}")
            return False
    
    def _evaluate_system_state_condition(self, condition: Condition) -> bool:
        """Evaluate system state condition"""
        try:
            state_type = condition.parameters.get('state_type')
            state_value = condition.parameters.get('state_value')
            
            return self.integration_bridge.check_system_state(state_type, state_value)
            
        except Exception as e:
            self.logger.error(f"System state condition failed: {e}")
            return False
    
    def _evaluate_time_condition(self, condition: Condition) -> bool:
        """Evaluate time-based condition"""
        try:
            time_condition = condition.parameters.get('time_condition')
            time_value = condition.parameters.get('time_value')
            
            return self.integration_bridge.check_time_condition(time_condition, time_value)
            
        except Exception as e:
            self.logger.error(f"Time condition failed: {e}")
            return False
    
    def _execute_rule_actions(self, rule: Rule, execution_mode: str) -> bool:
        """Execute all actions for a rule"""
        if not rule.actions:
            return True  # No actions is considered success
        
        successful_actions = 0
        
        for i, action in enumerate(rule.actions):
            try:
                action_result = self._execute_action(action, execution_mode, i)
                if action_result:
                    successful_actions += 1
                    
            except Exception as e:
                self.logger.error(f"Action execution failed: {e}")
                self.execution_logger.log_error(
                    'action', f"Action execution failed: {str(e)}",
                    rule_name=rule.name, step_index=i
                )
                
                # Continue with next action unless it's critical
                if not self._is_recoverable_error(e):
                    return False
        
        # Consider rule successful if at least one action succeeded
        return successful_actions > 0
    
    def _execute_action(self, action: Action, execution_mode: str, 
                       action_index: int) -> bool:
        """Execute a single action"""
        start_time = time.time()
        
        # Callback
        if self.on_step_start:
            self.on_step_start("action", f"Executing {action.action_type.value}")
        
        try:
            result = False
            
            if action.action_type == ActionType.CLICK:
                result = self._execute_click_action(action)
            elif action.action_type == ActionType.TYPE_TEXT:
                result = self._execute_type_text_action(action)
            elif action.action_type == ActionType.WAIT:
                result = self._execute_wait_action(action)
            elif action.action_type == ActionType.ASK_USER:
                result = self._execute_ask_user_action(action)
            elif action.action_type == ActionType.RUN_COMMAND:
                result = self._execute_run_command_action(action)
            else:
                self.logger.warning(f"Unknown action type: {action.action_type}")
                result = False
            
            duration = time.time() - start_time
            
            # Log action execution
            self.execution_logger.log_action_execution(
                self.current_profile.name if self.current_profile else "unknown",
                action_index,
                action.action_type.value,
                result,
                duration,
                {'target': action.target_region, 'parameters': action.parameters}
            )
            
            # Callback
            if self.on_step_complete:
                self.on_step_complete("action", result, action.action_type.value)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.execution_logger.log_action_execution(
                self.current_profile.name if self.current_profile else "unknown",
                action_index,
                action.action_type.value,
                False,
                duration,
                {'error': str(e)}
            )
            raise
    
    def _execute_click_action(self, action: Action) -> bool:
        """Execute click action using MARK-I's action system"""
        try:
            # Get target region
            region = self._get_region_by_name(action.target_region)
            if not region:
                raise ValueError(f"Target region not found: {action.target_region}")
            
            # Get click parameters
            click_type = action.parameters.get('click_type', 'left')
            offset_x = action.parameters.get('offset_x', 0)
            offset_y = action.parameters.get('offset_y', 0)
            
            # Calculate click position
            click_x = region.x + (region.width // 2) + offset_x
            click_y = region.y + (region.height // 2) + offset_y
            
            # Execute click using integration bridge
            return self.integration_bridge.execute_click(click_x, click_y, click_type)
            
        except Exception as e:
            self.logger.error(f"Click action failed: {e}")
            return False
    
    def _execute_type_text_action(self, action: Action) -> bool:
        """Execute type text action"""
        try:
            text = action.parameters.get('text', '')
            clear_first = action.parameters.get('clear_first', False)
            
            # Process text variables
            processed_text = self._process_text_variables(text)
            
            # Execute typing using integration bridge
            return self.integration_bridge.execute_type_text(processed_text, clear_first)
            
        except Exception as e:
            self.logger.error(f"Type text action failed: {e}")
            return False
    
    def _execute_wait_action(self, action: Action) -> bool:
        """Execute wait action"""
        try:
            duration = action.parameters.get('duration', 1.0)
            wait_type = action.parameters.get('wait_type', 'fixed')
            
            if wait_type == 'random':
                import random
                duration = random.uniform(duration * 0.5, duration * 1.5)
            
            time.sleep(duration)
            return True
            
        except Exception as e:
            self.logger.error(f"Wait action failed: {e}")
            return False
    
    def _execute_ask_user_action(self, action: Action) -> bool:
        """Execute ask user action"""
        try:
            prompt = action.parameters.get('prompt', 'Please provide input:')
            input_type = action.parameters.get('input_type', 'text')
            
            # Use integration bridge to show user dialog
            user_response = self.integration_bridge.ask_user(prompt, input_type)
            
            if user_response is not None:
                # Store user response for later use
                self.user_variables['last_user_input'] = user_response
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ask user action failed: {e}")
            return False
    
    def _execute_run_command_action(self, action: Action) -> bool:
        """Execute run command action"""
        try:
            command = action.parameters.get('command', '')
            wait_for_completion = action.parameters.get('wait_for_completion', True)
            
            # Process command variables
            processed_command = self._process_text_variables(command)
            
            # Execute command using integration bridge
            return self.integration_bridge.execute_command(processed_command, wait_for_completion)
            
        except Exception as e:
            self.logger.error(f"Run command action failed: {e}")
            return False
    
    def _get_region_by_name(self, region_name: str) -> Optional[Region]:
        """Get region by name from current profile"""
        if not self.current_profile:
            return None
        
        for region in self.current_profile.regions:
            if region.name == region_name:
                return region
        
        return None
    
    def _process_text_variables(self, text: str) -> str:
        """Process variables in text"""
        processed_text = text
        
        # Replace user variables
        for var_name, var_value in self.user_variables.items():
            placeholder = f"{{{var_name}}}"
            processed_text = processed_text.replace(placeholder, str(var_value))
        
        # Replace system variables
        system_vars = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S')
        }
        
        for var_name, var_value in system_vars.items():
            placeholder = f"{{{var_name}}}"
            processed_text = processed_text.replace(placeholder, var_value)
        
        return processed_text
    
    def _validate_execution_environment(self, profile: AutomationProfile) -> bool:
        """Validate that the execution environment is ready"""
        try:
            # Check if integration bridge is available
            if not self.integration_bridge.is_available():
                self.logger.error("Integration bridge not available")
                return False
            
            # Check if target application is running (if specified)
            if profile.target_application:
                if not self.integration_bridge.is_application_running(profile.target_application):
                    self.logger.warning(f"Target application not running: {profile.target_application}")
                    # Don't fail execution, just warn
            
            return True
            
        except Exception as e:
            self.logger.error(f"Environment validation failed: {e}")
            return False
    
    def _is_recoverable_error(self, error: Exception) -> bool:
        """Check if an error is recoverable"""
        # Define recoverable error types
        recoverable_types = (
            TimeoutError,
            ConnectionError,
            # Add more recoverable error types as needed
        )
        
        return isinstance(error, recoverable_types)
    
    def _get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        return {
            'profile_name': self.current_profile.name if self.current_profile else None,
            'execution_time': datetime.now().isoformat(),
            'user_variables': self.user_variables.copy(),
            'context': self.execution_context.copy()
        }
    
    def cancel_execution(self):
        """Cancel current execution"""
        if self.is_executing:
            self.logger.info("Execution cancelled by user")
            self.is_executing = False
            
            self.execution_logger.log_info(
                'profile', "Execution cancelled by user"
            )
    
    def is_execution_active(self) -> bool:
        """Check if execution is currently active"""
        return self.is_executing
    
    def get_current_profile(self) -> Optional[AutomationProfile]:
        """Get currently executing profile"""
        return self.current_profile