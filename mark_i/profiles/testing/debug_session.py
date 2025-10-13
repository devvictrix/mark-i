"""
Debug Session

Interactive debugging session for step-by-step profile execution with
breakpoints, variable inspection, and manual control.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..models.profile import AutomationProfile
from ..models.rule import Rule, Condition, Action


class DebugState(Enum):
    """Debug session states"""
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STEP_BY_STEP = "step_by_step"
    BREAKPOINT = "breakpoint"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class DebugBreakpoint:
    """Debug breakpoint definition"""
    id: str
    rule_name: str
    step_type: str  # 'condition', 'action', 'rule_start', 'rule_end'
    step_index: int = -1  # -1 for rule start/end
    enabled: bool = True
    condition: Optional[str] = None  # Optional condition for conditional breakpoints
    hit_count: int = 0
    
    def matches(self, rule_name: str, step_type: str, step_index: int = -1) -> bool:
        """Check if breakpoint matches current execution point"""
        return (self.enabled and 
                self.rule_name == rule_name and 
                self.step_type == step_type and 
                (self.step_index == -1 or self.step_index == step_index))


@dataclass
class DebugStep:
    """Debug execution step with context"""
    step_id: str
    rule_name: str
    step_type: str  # 'condition', 'action', 'rule_start', 'rule_end'
    step_index: int
    step_name: str
    timestamp: datetime
    status: str = "pending"  # 'pending', 'executing', 'completed', 'failed', 'skipped'
    result: Optional[Any] = None
    error: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    screenshot_path: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class DebugContext:
    """Debug execution context"""
    profile: AutomationProfile
    current_rule: Optional[Rule] = None
    current_step: Optional[DebugStep] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    call_stack: List[str] = field(default_factory=list)
    execution_history: List[DebugStep] = field(default_factory=list)


class DebugSession:
    """Interactive debugging session for profile execution"""
    
    def __init__(self, profile: AutomationProfile):
        self.profile = profile
        self.logger = logging.getLogger("mark_i.profiles.testing.debug")
        
        # Debug state
        self.state = DebugState.READY
        self.context = DebugContext(profile)
        self.breakpoints: Dict[str, DebugBreakpoint] = {}
        
        # Execution control
        self.step_mode = False
        self.continue_execution = False
        self.abort_execution = False
        
        # Callbacks for UI integration
        self.on_state_changed: Optional[Callable[[DebugState], None]] = None
        self.on_step_executed: Optional[Callable[[DebugStep], None]] = None
        self.on_breakpoint_hit: Optional[Callable[[DebugBreakpoint, DebugStep], None]] = None
        self.on_variable_changed: Optional[Callable[[str, Any], None]] = None
        
        self.logger.info(f"Debug session created for profile: {profile.name}")
    
    def add_breakpoint(self, rule_name: str, step_type: str, step_index: int = -1, 
                      condition: str = None) -> str:
        """Add a breakpoint"""
        breakpoint_id = f"{rule_name}_{step_type}_{step_index}_{len(self.breakpoints)}"
        
        breakpoint = DebugBreakpoint(
            id=breakpoint_id,
            rule_name=rule_name,
            step_type=step_type,
            step_index=step_index,
            condition=condition
        )
        
        self.breakpoints[breakpoint_id] = breakpoint
        self.logger.info(f"Added breakpoint: {breakpoint_id}")
        return breakpoint_id
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """Remove a breakpoint"""
        if breakpoint_id in self.breakpoints:
            del self.breakpoints[breakpoint_id]
            self.logger.info(f"Removed breakpoint: {breakpoint_id}")
            return True
        return False
    
    def toggle_breakpoint(self, breakpoint_id: str) -> bool:
        """Toggle breakpoint enabled/disabled"""
        if breakpoint_id in self.breakpoints:
            self.breakpoints[breakpoint_id].enabled = not self.breakpoints[breakpoint_id].enabled
            return True
        return False
    
    def set_variable(self, name: str, value: Any):
        """Set a debug variable"""
        self.context.variables[name] = value
        if self.on_variable_changed:
            self.on_variable_changed(name, value)
        self.logger.debug(f"Set variable {name} = {value}")
    
    def get_variable(self, name: str) -> Any:
        """Get a debug variable"""
        return self.context.variables.get(name)
    
    def start_debug(self, step_mode: bool = False):
        """Start debug execution"""
        self.step_mode = step_mode
        self.state = DebugState.STEP_BY_STEP if step_mode else DebugState.RUNNING
        self.continue_execution = True
        self.abort_execution = False
        
        if self.on_state_changed:
            self.on_state_changed(self.state)
        
        self.logger.info(f"Started debug session in {'step' if step_mode else 'run'} mode")
        
        try:
            self._execute_profile()
        except Exception as e:
            self.logger.error(f"Debug execution failed: {e}")
            self.state = DebugState.ERROR
            if self.on_state_changed:
                self.on_state_changed(self.state)
    
    def step_over(self):
        """Execute next step"""
        if self.state in [DebugState.PAUSED, DebugState.BREAKPOINT, DebugState.STEP_BY_STEP]:
            self.continue_execution = True
            self.step_mode = True
            self.logger.debug("Step over requested")
    
    def step_into(self):
        """Step into next operation"""
        if self.state in [DebugState.PAUSED, DebugState.BREAKPOINT, DebugState.STEP_BY_STEP]:
            self.continue_execution = True
            self.step_mode = True
            self.logger.debug("Step into requested")
    
    def continue_debug(self):
        """Continue execution until next breakpoint"""
        if self.state in [DebugState.PAUSED, DebugState.BREAKPOINT, DebugState.STEP_BY_STEP]:
            self.continue_execution = True
            self.step_mode = False
            self.state = DebugState.RUNNING
            if self.on_state_changed:
                self.on_state_changed(self.state)
            self.logger.debug("Continue execution requested")
    
    def pause_debug(self):
        """Pause execution"""
        if self.state == DebugState.RUNNING:
            self.state = DebugState.PAUSED
            self.continue_execution = False
            if self.on_state_changed:
                self.on_state_changed(self.state)
            self.logger.debug("Pause requested")
    
    def stop_debug(self):
        """Stop debug execution"""
        self.abort_execution = True
        self.continue_execution = False
        self.state = DebugState.COMPLETED
        if self.on_state_changed:
            self.on_state_changed(self.state)
        self.logger.info("Debug session stopped")
    
    def _execute_profile(self):
        """Execute profile with debug support"""
        self.logger.info("Starting profile execution with debugging")
        
        # Sort rules by priority
        enabled_rules = [rule for rule in self.profile.rules if rule.enabled]
        enabled_rules.sort(key=lambda r: r.priority)
        
        for rule in enabled_rules:
            if self.abort_execution:
                break
            
            self.context.current_rule = rule
            self._execute_rule_debug(rule)
        
        self.state = DebugState.COMPLETED
        if self.on_state_changed:
            self.on_state_changed(self.state)
        
        self.logger.info("Profile execution completed")
    
    def _execute_rule_debug(self, rule: Rule):
        """Execute rule with debug support"""
        self.logger.debug(f"Executing rule: {rule.name}")
        
        # Rule start breakpoint
        self._check_breakpoint(rule.name, "rule_start")
        if self.abort_execution:
            return
        
        # Create rule start step
        start_step = DebugStep(
            step_id=f"{rule.name}_start",
            rule_name=rule.name,
            step_type="rule_start",
            step_index=-1,
            step_name=f"Rule Start: {rule.name}",
            timestamp=datetime.now()
        )
        
        self._execute_step(start_step, lambda: self._rule_start_logic(rule))
        
        if self.abort_execution:
            return
        
        # Execute conditions
        conditions_passed = 0
        for i, condition in enumerate(rule.conditions):
            if self.abort_execution:
                break
            
            condition_step = DebugStep(
                step_id=f"{rule.name}_condition_{i}",
                rule_name=rule.name,
                step_type="condition",
                step_index=i,
                step_name=f"Condition {i+1}: {condition.condition_type.value}",
                timestamp=datetime.now()
            )
            
            # Check breakpoint
            self._check_breakpoint(rule.name, "condition", i)
            if self.abort_execution:
                break
            
            # Execute condition
            result = self._execute_step(condition_step, lambda: self._evaluate_condition_debug(condition))
            
            if result:
                conditions_passed += 1
        
        # Check if rule should execute
        should_execute = self._evaluate_rule_logic(rule, conditions_passed, len(rule.conditions))
        
        if should_execute and not self.abort_execution:
            # Execute actions
            for i, action in enumerate(rule.actions):
                if self.abort_execution:
                    break
                
                action_step = DebugStep(
                    step_id=f"{rule.name}_action_{i}",
                    rule_name=rule.name,
                    step_type="action",
                    step_index=i,
                    step_name=f"Action {i+1}: {action.action_type.value}",
                    timestamp=datetime.now()
                )
                
                # Check breakpoint
                self._check_breakpoint(rule.name, "action", i)
                if self.abort_execution:
                    break
                
                # Execute action
                self._execute_step(action_step, lambda: self._execute_action_debug(action))
        
        # Rule end breakpoint
        if not self.abort_execution:
            self._check_breakpoint(rule.name, "rule_end")
            
            end_step = DebugStep(
                step_id=f"{rule.name}_end",
                rule_name=rule.name,
                step_type="rule_end",
                step_index=-1,
                step_name=f"Rule End: {rule.name}",
                timestamp=datetime.now()
            )
            
            self._execute_step(end_step, lambda: self._rule_end_logic(rule))
    
    def _execute_step(self, step: DebugStep, step_function: Callable) -> Any:
        """Execute a debug step with error handling and timing"""
        self.context.current_step = step
        step.status = "executing"
        
        start_time = time.time()
        
        try:
            # Wait for continue signal if in step mode
            if self.step_mode:
                self._wait_for_continue()
            
            if self.abort_execution:
                step.status = "skipped"
                return None
            
            # Execute the step
            result = step_function()
            
            step.result = result
            step.status = "completed"
            step.execution_time = time.time() - start_time
            
            self.logger.debug(f"Step completed: {step.step_name}")
            
        except Exception as e:
            step.error = str(e)
            step.status = "failed"
            step.execution_time = time.time() - start_time
            
            self.logger.error(f"Step failed: {step.step_name} - {e}")
        
        # Add to execution history
        self.context.execution_history.append(step)
        
        # Notify UI
        if self.on_step_executed:
            self.on_step_executed(step)
        
        return step.result
    
    def _check_breakpoint(self, rule_name: str, step_type: str, step_index: int = -1):
        """Check if any breakpoint matches current execution point"""
        for breakpoint in self.breakpoints.values():
            if breakpoint.matches(rule_name, step_type, step_index):
                breakpoint.hit_count += 1
                
                # Check conditional breakpoint
                if breakpoint.condition:
                    try:
                        # Evaluate condition in context of current variables
                        if not eval(breakpoint.condition, {"__builtins__": {}}, self.context.variables):
                            continue
                    except Exception as e:
                        self.logger.warning(f"Breakpoint condition evaluation failed: {e}")
                        continue
                
                # Hit breakpoint
                self.state = DebugState.BREAKPOINT
                self.continue_execution = False
                
                if self.on_state_changed:
                    self.on_state_changed(self.state)
                
                if self.on_breakpoint_hit:
                    current_step = DebugStep(
                        step_id=f"{rule_name}_{step_type}_{step_index}",
                        rule_name=rule_name,
                        step_type=step_type,
                        step_index=step_index,
                        step_name=f"Breakpoint: {step_type}",
                        timestamp=datetime.now()
                    )
                    self.on_breakpoint_hit(breakpoint, current_step)
                
                self.logger.info(f"Breakpoint hit: {breakpoint.id}")
                
                # Wait for continue signal
                self._wait_for_continue()
                break
    
    def _wait_for_continue(self):
        """Wait for continue signal from user"""
        while not self.continue_execution and not self.abort_execution:
            time.sleep(0.1)  # Small delay to prevent busy waiting
        
        self.continue_execution = False  # Reset for next step
    
    def _rule_start_logic(self, rule: Rule) -> bool:
        """Logic executed at rule start"""
        self.context.call_stack.append(rule.name)
        self.set_variable("current_rule", rule.name)
        self.set_variable("rule_priority", rule.priority)
        return True
    
    def _rule_end_logic(self, rule: Rule) -> bool:
        """Logic executed at rule end"""
        if self.context.call_stack and self.context.call_stack[-1] == rule.name:
            self.context.call_stack.pop()
        return True
    
    def _evaluate_condition_debug(self, condition: Condition) -> bool:
        """Evaluate condition with debug context"""
        # This would integrate with actual condition evaluation
        # For now, simulate evaluation
        self.set_variable("last_condition_type", condition.condition_type.value)
        self.set_variable("last_condition_region", condition.region_name)
        
        # Simulate condition evaluation
        import random
        result = random.choice([True, False])
        self.set_variable("last_condition_result", result)
        
        return result
    
    def _execute_action_debug(self, action: Action) -> bool:
        """Execute action with debug context"""
        # This would integrate with actual action execution
        # For now, simulate execution
        self.set_variable("last_action_type", action.action_type.value)
        self.set_variable("last_action_target", action.target_region)
        
        # Simulate action execution
        import random
        result = random.choice([True, True, False])  # 67% success rate
        self.set_variable("last_action_result", result)
        
        return result
    
    def _evaluate_rule_logic(self, rule: Rule, conditions_passed: int, total_conditions: int) -> bool:
        """Evaluate if rule should execute based on logical operator"""
        if total_conditions == 0:
            return True
        
        if rule.logical_operator == "AND":
            return conditions_passed == total_conditions
        elif rule.logical_operator == "OR":
            return conditions_passed > 0
        else:
            return conditions_passed == total_conditions  # Default to AND
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get current debug information"""
        return {
            "state": self.state.value,
            "current_rule": self.context.current_rule.name if self.context.current_rule else None,
            "current_step": self.context.current_step.step_name if self.context.current_step else None,
            "variables": self.context.variables.copy(),
            "call_stack": self.context.call_stack.copy(),
            "breakpoints": {bp_id: {
                "rule_name": bp.rule_name,
                "step_type": bp.step_type,
                "step_index": bp.step_index,
                "enabled": bp.enabled,
                "hit_count": bp.hit_count
            } for bp_id, bp in self.breakpoints.items()},
            "execution_history_count": len(self.context.execution_history)
        }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history for analysis"""
        return [
            {
                "step_id": step.step_id,
                "rule_name": step.rule_name,
                "step_type": step.step_type,
                "step_name": step.step_name,
                "timestamp": step.timestamp.isoformat(),
                "status": step.status,
                "result": step.result,
                "error": step.error,
                "execution_time": step.execution_time
            }
            for step in self.context.execution_history
        ]