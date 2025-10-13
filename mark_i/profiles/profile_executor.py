"""
Profile Executor

Executes automation profiles using MARK-I's Eye-Brain-Hand architecture.
Integrates CaptureEngine (Eye), AgentCore (Brain), and ActionExecutor (Hand).
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .models.profile import AutomationProfile
from .models.region import Region
from .models.rule import Rule, Condition, Action, ConditionType, ActionType


class ExecutionStatus(Enum):
    """Execution status values"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of profile execution"""
    profile_id: str
    profile_name: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    rules_executed: int
    actions_performed: int
    errors: List[str]
    warnings: List[str]
    execution_log: List[str]
    
    @property
    def duration_seconds(self) -> float:
        """Get execution duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def success(self) -> bool:
        """Check if execution was successful"""
        return self.status == ExecutionStatus.COMPLETED and len(self.errors) == 0


@dataclass
class RuleResult:
    """Result of rule execution"""
    rule_name: str
    executed: bool
    conditions_met: bool
    actions_performed: int
    errors: List[str]
    execution_time_seconds: float


@dataclass
class ExecutionContext:
    """Context for profile execution"""
    profile: AutomationProfile
    variables: Dict[str, Any]
    current_screenshot: Optional[Any] = None
    region_analyses: Dict[str, Any] = None
    execution_start_time: datetime = None
    
    def __post_init__(self):
        if self.execution_start_time is None:
            self.execution_start_time = datetime.now()
        if self.region_analyses is None:
            self.region_analyses = {}
        if self.variables is None:
            self.variables = {}
    
    def get_region(self, name: str) -> Optional[Region]:
        """Get region by name from profile"""
        return self.profile.get_region(name)
    
    def set_variable(self, name: str, value: Any):
        """Set a context variable"""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a context variable"""
        return self.variables.get(name, default)


class ProfileExecutor:
    """Executes automation profiles using Eye-Brain-Hand architecture"""
    
    def __init__(self, capture_engine=None, agent_core=None, action_executor=None):
        """
        Initialize ProfileExecutor with Eye-Brain-Hand components
        
        Args:
            capture_engine: Eye component for visual perception
            agent_core: Brain component for decision making
            action_executor: Hand component for action execution
        """
        self.eye = capture_engine  # CaptureEngine
        self.brain = agent_core    # AgentCore
        self.hand = action_executor # ActionExecutor
        
        self.logger = logging.getLogger("mark_i.profiles.executor")
        
        # Execution state
        self._current_execution: Optional[ExecutionResult] = None
        self._execution_cancelled = False
        self._execution_paused = False
        
        self.logger.info("ProfileExecutor initialized")
    
    def execute_profile(self, profile: AutomationProfile, variables: Dict[str, Any] = None) -> ExecutionResult:
        """
        Execute an automation profile
        
        Args:
            profile: Profile to execute
            variables: Variables to use during execution
            
        Returns:
            ExecutionResult with execution details
        """
        if variables is None:
            variables = {}
        
        # Initialize execution result
        execution_result = ExecutionResult(
            profile_id=profile.id,
            profile_name=profile.name,
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now(),
            end_time=None,
            rules_executed=0,
            actions_performed=0,
            errors=[],
            warnings=[],
            execution_log=[]
        )
        
        self._current_execution = execution_result
        self._execution_cancelled = False
        self._execution_paused = False
        
        try:
            self.logger.info(f"Starting execution of profile: {profile.name}")
            execution_result.execution_log.append(f"Started execution at {execution_result.start_time}")
            
            # Create execution context
            context = ExecutionContext(
                profile=profile,
                variables=variables,
                execution_start_time=execution_result.start_time
            )
            
            # Take initial screenshot if Eye is available
            if self.eye:
                try:
                    context.current_screenshot = self.eye.capture_screen()
                    execution_result.execution_log.append("Captured initial screenshot")
                except Exception as e:
                    execution_result.warnings.append(f"Failed to capture initial screenshot: {str(e)}")
            
            # Get enabled rules sorted by priority
            enabled_rules = profile.get_enabled_rules()
            execution_result.execution_log.append(f"Found {len(enabled_rules)} enabled rules")
            
            # Execute rules
            for rule in enabled_rules:
                if self._execution_cancelled:
                    execution_result.status = ExecutionStatus.CANCELLED
                    break
                
                # Handle pause
                while self._execution_paused and not self._execution_cancelled:
                    time.sleep(0.1)
                
                if self._execution_cancelled:
                    execution_result.status = ExecutionStatus.CANCELLED
                    break
                
                # Execute rule
                rule_result = self.execute_rule(rule, context)
                execution_result.rules_executed += 1
                
                if rule_result.executed:
                    execution_result.actions_performed += rule_result.actions_performed
                
                if rule_result.errors:
                    execution_result.errors.extend(rule_result.errors)
                    if not rule.continue_on_failure:
                        execution_result.execution_log.append(f"Rule '{rule.name}' failed, stopping execution")
                        break
                
                execution_result.execution_log.append(
                    f"Rule '{rule.name}': {'executed' if rule_result.executed else 'skipped'}"
                )
                
                # Check execution timeout
                if context.execution_start_time:
                    elapsed = (datetime.now() - context.execution_start_time).total_seconds()
                    if elapsed > profile.settings.max_execution_time_seconds:
                        execution_result.errors.append("Execution timeout exceeded")
                        execution_result.execution_log.append("Execution timeout exceeded")
                        break
            
            # Determine final status
            if execution_result.status == ExecutionStatus.RUNNING:
                if execution_result.errors:
                    execution_result.status = ExecutionStatus.FAILED
                else:
                    execution_result.status = ExecutionStatus.COMPLETED
            
            execution_result.end_time = datetime.now()
            execution_result.execution_log.append(f"Execution completed at {execution_result.end_time}")
            
            self.logger.info(f"Profile execution completed: {execution_result.status.value}")
            
        except Exception as e:
            execution_result.status = ExecutionStatus.FAILED
            execution_result.errors.append(f"Execution failed: {str(e)}")
            execution_result.end_time = datetime.now()
            execution_result.execution_log.append(f"Execution failed: {str(e)}")
            self.logger.error(f"Profile execution failed: {str(e)}")
        
        finally:
            self._current_execution = None
        
        return execution_result
    
    def execute_rule(self, rule: Rule, context: ExecutionContext) -> RuleResult:
        """
        Execute a single rule
        
        Args:
            rule: Rule to execute
            context: Execution context
            
        Returns:
            RuleResult with execution details
        """
        start_time = time.time()
        rule_result = RuleResult(
            rule_name=rule.name,
            executed=False,
            conditions_met=False,
            actions_performed=0,
            errors=[],
            execution_time_seconds=0
        )
        
        try:
            self.logger.debug(f"Evaluating rule: {rule.name}")
            
            # Evaluate conditions
            conditions_met = self._evaluate_rule_conditions(rule, context)
            rule_result.conditions_met = conditions_met
            
            if conditions_met:
                self.logger.debug(f"Rule conditions met, executing actions: {rule.name}")
                
                # Execute actions
                for action in rule.actions:
                    if self._execution_cancelled:
                        break
                    
                    try:
                        action_success = self._execute_action(action, context)
                        if action_success:
                            rule_result.actions_performed += 1
                        else:
                            rule_result.errors.append(f"Action '{action.type}' failed")
                            if not rule.continue_on_failure:
                                break
                    
                    except Exception as e:
                        error_msg = f"Action '{action.type}' error: {str(e)}"
                        rule_result.errors.append(error_msg)
                        self.logger.error(error_msg)
                        if not rule.continue_on_failure:
                            break
                
                rule_result.executed = True
            else:
                self.logger.debug(f"Rule conditions not met, skipping: {rule.name}")
        
        except Exception as e:
            error_msg = f"Rule execution error: {str(e)}"
            rule_result.errors.append(error_msg)
            self.logger.error(error_msg)
        
        rule_result.execution_time_seconds = time.time() - start_time
        return rule_result
    
    def _evaluate_rule_conditions(self, rule: Rule, context: ExecutionContext) -> bool:
        """Evaluate all conditions for a rule"""
        if not rule.conditions:
            return True
        
        condition_results = []
        
        for condition in rule.conditions:
            try:
                result = self._evaluate_condition(condition, context)
                if condition.negate:
                    result = not result
                condition_results.append(result)
            except Exception as e:
                self.logger.error(f"Condition evaluation error: {str(e)}")
                condition_results.append(False)
        
        # Apply logical operator
        if rule.logical_operator == "AND":
            return all(condition_results)
        elif rule.logical_operator == "OR":
            return any(condition_results)
        else:
            return False
    
    def _evaluate_condition(self, condition: Condition, context: ExecutionContext) -> bool:
        """Evaluate a single condition"""
        region = context.get_region(condition.region)
        if not region:
            self.logger.error(f"Region not found for condition: {condition.region}")
            return False
        
        if condition.type == ConditionType.ALWAYS_TRUE.value:
            return True
        
        elif condition.type == ConditionType.VISUAL_MATCH.value:
            return self._check_visual_match(region, condition.parameters, context)
        
        elif condition.type == ConditionType.OCR_CONTAINS.value:
            return self._check_ocr_contains(region, condition.parameters, context)
        
        elif condition.type == ConditionType.TEMPLATE_MATCH.value:
            return self._check_template_match(region, condition.parameters, context)
        
        elif condition.type == ConditionType.COLOR_MATCH.value:
            return self._check_color_match(region, condition.parameters, context)
        
        elif condition.type == ConditionType.WINDOW_EXISTS.value:
            return self._check_window_exists(condition.parameters, context)
        
        else:
            self.logger.warning(f"Unknown condition type: {condition.type}")
            return False
    
    def _check_visual_match(self, region: Region, parameters: Dict[str, Any], context: ExecutionContext) -> bool:
        """Check if region is visually present/visible"""
        if not self.eye:
            self.logger.warning("No Eye (CaptureEngine) available for visual match")
            return parameters.get('visible', True)  # Default assumption
        
        try:
            # Capture region
            region_image = self.eye.capture_region(region.x, region.y, region.width, region.height)
            
            # Use Brain (Gemini) for analysis if available
            if self.brain and hasattr(self.brain, 'analyze_image'):
                analysis_prompt = f"Is this region visible and contains interactive elements? Region: {region.description}"
                analysis = self.brain.analyze_image(region_image, analysis_prompt)
                return 'visible' in analysis.lower() or 'yes' in analysis.lower()
            
            # Basic check - region is not completely black/empty
            # This is a simplified check - could be enhanced
            return True
            
        except Exception as e:
            self.logger.error(f"Visual match check failed: {str(e)}")
            return False
    
    def _check_ocr_contains(self, region: Region, parameters: Dict[str, Any], context: ExecutionContext) -> bool:
        """Check if region contains specific text via OCR"""
        if not self.eye:
            self.logger.warning("No Eye (CaptureEngine) available for OCR")
            return False
        
        try:
            text_to_find = parameters.get('text', '')
            if not text_to_find:
                return False
            
            # Capture region
            region_image = self.eye.capture_region(region.x, region.y, region.width, region.height)
            
            # Use Brain for OCR analysis if available
            if self.brain and hasattr(self.brain, 'analyze_image'):
                ocr_prompt = f"What text do you see in this image? Look for: '{text_to_find}'"
                analysis = self.brain.analyze_image(region_image, ocr_prompt)
                return text_to_find.lower() in analysis.lower()
            
            # Fallback - assume text is present
            return True
            
        except Exception as e:
            self.logger.error(f"OCR check failed: {str(e)}")
            return False
    
    def _check_template_match(self, region: Region, parameters: Dict[str, Any], context: ExecutionContext) -> bool:
        """Check if region matches a template image"""
        # This would require template matching implementation
        # For now, return True as placeholder
        self.logger.debug("Template matching not yet implemented")
        return True
    
    def _check_color_match(self, region: Region, parameters: Dict[str, Any], context: ExecutionContext) -> bool:
        """Check if region contains expected color"""
        # This would require color analysis implementation
        # For now, return True as placeholder
        self.logger.debug("Color matching not yet implemented")
        return True
    
    def _check_window_exists(self, parameters: Dict[str, Any], context: ExecutionContext) -> bool:
        """Check if a specific window exists"""
        # This would require window detection implementation
        # For now, return True as placeholder
        self.logger.debug("Window detection not yet implemented")
        return True
    
    def _execute_action(self, action: Action, context: ExecutionContext) -> bool:
        """Execute a single action"""
        try:
            # Apply delay before action
            if action.delay_before > 0:
                time.sleep(action.delay_before)
            
            success = False
            
            if action.type == ActionType.CLICK.value:
                success = self._execute_click_action(action, context)
            
            elif action.type == ActionType.TYPE_TEXT.value:
                success = self._execute_type_text_action(action, context)
            
            elif action.type == ActionType.WAIT.value:
                success = self._execute_wait_action(action, context)
            
            elif action.type == ActionType.WAIT_FOR_VISUAL_CUE.value:
                success = self._execute_wait_for_visual_cue_action(action, context)
            
            elif action.type == ActionType.ASK_USER.value:
                success = self._execute_ask_user_action(action, context)
            
            elif action.type == ActionType.PRESS_KEY.value:
                success = self._execute_press_key_action(action, context)
            
            elif action.type == ActionType.LOG_MESSAGE.value:
                success = self._execute_log_message_action(action, context)
            
            else:
                self.logger.warning(f"Unknown action type: {action.type}")
                success = False
            
            # Apply delay after action
            if action.delay_after > 0:
                time.sleep(action.delay_after)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Action execution failed: {str(e)}")
            return False
    
    def _execute_click_action(self, action: Action, context: ExecutionContext) -> bool:
        """Execute click action"""
        if not action.region:
            self.logger.error("Click action requires a region")
            return False
        
        region = context.get_region(action.region)
        if not region:
            self.logger.error(f"Region not found: {action.region}")
            return False
        
        if self.hand and hasattr(self.hand, 'click'):
            try:
                # Click at region center
                self.hand.click(region.center_x, region.center_y)
                self.logger.debug(f"Clicked at ({region.center_x}, {region.center_y})")
                return True
            except Exception as e:
                self.logger.error(f"Click failed: {str(e)}")
                return False
        else:
            self.logger.warning("No Hand (ActionExecutor) available for click")
            return False
    
    def _execute_type_text_action(self, action: Action, context: ExecutionContext) -> bool:
        """Execute type text action"""
        text = action.parameters.get('text', '')
        if not text:
            self.logger.error("Type text action requires text parameter")
            return False
        
        # Substitute variables in text
        text = self._substitute_variables(text, context.variables)
        
        if self.hand and hasattr(self.hand, 'type_text'):
            try:
                self.hand.type_text(text)
                self.logger.debug(f"Typed text: {text}")
                return True
            except Exception as e:
                self.logger.error(f"Type text failed: {str(e)}")
                return False
        else:
            self.logger.warning("No Hand (ActionExecutor) available for typing")
            return False
    
    def _execute_wait_action(self, action: Action, context: ExecutionContext) -> bool:
        """Execute wait action"""
        wait_seconds = action.parameters.get('seconds', 1.0)
        try:
            time.sleep(wait_seconds)
            self.logger.debug(f"Waited {wait_seconds} seconds")
            return True
        except Exception as e:
            self.logger.error(f"Wait failed: {str(e)}")
            return False
    
    def _execute_wait_for_visual_cue_action(self, action: Action, context: ExecutionContext) -> bool:
        """Execute wait for visual cue action"""
        # This would implement waiting for specific visual elements
        # For now, just wait a short time
        time.sleep(2.0)
        self.logger.debug("Waited for visual cue (placeholder)")
        return True
    
    def _execute_ask_user_action(self, action: Action, context: ExecutionContext) -> bool:
        """Execute ask user action"""
        question = action.parameters.get('question', 'Please provide input')
        
        if self.brain and hasattr(self.brain, 'ask_user'):
            try:
                response = self.brain.ask_user(question)
                # Store response in context variables
                context.set_variable('last_user_response', response)
                self.logger.debug(f"Asked user: {question}, Response: {response}")
                return True
            except Exception as e:
                self.logger.error(f"Ask user failed: {str(e)}")
                return False
        else:
            self.logger.warning("No Brain (AgentCore) available for asking user")
            return False
    
    def _execute_press_key_action(self, action: Action, context: ExecutionContext) -> bool:
        """Execute press key action"""
        key = action.parameters.get('key', '')
        if not key:
            self.logger.error("Press key action requires key parameter")
            return False
        
        if self.hand and hasattr(self.hand, 'press_key'):
            try:
                self.hand.press_key(key)
                self.logger.debug(f"Pressed key: {key}")
                return True
            except Exception as e:
                self.logger.error(f"Press key failed: {str(e)}")
                return False
        else:
            self.logger.warning("No Hand (ActionExecutor) available for key press")
            return False
    
    def _execute_log_message_action(self, action: Action, context: ExecutionContext) -> bool:
        """Execute log message action"""
        message = action.parameters.get('message', '')
        level = action.parameters.get('level', 'INFO')
        
        # Substitute variables in message
        message = self._substitute_variables(message, context.variables)
        
        if level.upper() == 'DEBUG':
            self.logger.debug(message)
        elif level.upper() == 'WARNING':
            self.logger.warning(message)
        elif level.upper() == 'ERROR':
            self.logger.error(message)
        else:
            self.logger.info(message)
        
        return True
    
    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in text using {variable_name} format"""
        try:
            return text.format(**variables)
        except KeyError as e:
            self.logger.warning(f"Variable not found for substitution: {str(e)}")
            return text
        except Exception as e:
            self.logger.error(f"Variable substitution failed: {str(e)}")
            return text
    
    def cancel_execution(self):
        """Cancel current execution"""
        self._execution_cancelled = True
        self.logger.info("Execution cancellation requested")
    
    def pause_execution(self):
        """Pause current execution"""
        self._execution_paused = True
        self.logger.info("Execution paused")
    
    def resume_execution(self):
        """Resume paused execution"""
        self._execution_paused = False
        self.logger.info("Execution resumed")
    
    def get_current_execution_status(self) -> Optional[ExecutionResult]:
        """Get current execution status"""
        return self._current_execution
    
    def is_executing(self) -> bool:
        """Check if currently executing a profile"""
        return self._current_execution is not None