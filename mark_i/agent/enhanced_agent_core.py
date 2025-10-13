"""
Enhanced Agent Core for MARK-I hierarchical AI architecture.

This module provides the enhanced Agent Core implementation that handles tactical
execution using ReAct (Reason+Act) cognitive loops, implementing the IAgentCore interface.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

import numpy as np

from mark_i.core.base_component import BaseComponent
from mark_i.core.interfaces import (
    IAgentCore, Context, Goal, Action, Observation, ExecutionResult, Priority
)
from mark_i.core.architecture_config import AgentCoreConfig
from mark_i.core.interfaces import IActionExecutor, IToolbelt, IWorldModel

logger = logging.getLogger("mark_i.agent.enhanced_agent_core")


class ReActPhase(Enum):
    """Phases of the ReAct cognitive loop."""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"


class UncertaintyType(Enum):
    """Types of uncertainty that can occur during execution."""
    AMBIGUOUS_COMMAND = "ambiguous_command"
    UNCLEAR_CONTEXT = "unclear_context"
    MULTIPLE_OPTIONS = "multiple_options"
    MISSING_INFORMATION = "missing_information"
    UNEXPECTED_STATE = "unexpected_state"
    TOOL_FAILURE = "tool_failure"


@dataclass
class ReActStep:
    """Represents a single step in the ReAct loop."""
    step_number: int
    phase: ReActPhase
    thought: str
    action: Optional[Action] = None
    observation: Optional[Observation] = None
    result: Optional[ExecutionResult] = None
    timestamp: datetime = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class UncertaintyEvent:
    """Represents an uncertainty event that requires handling."""
    id: str
    type: UncertaintyType
    description: str
    context: Dict[str, Any]
    possible_resolutions: List[str]
    confidence_threshold: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EnhancedAgentCore(BaseComponent, IAgentCore):
    """
    Enhanced Agent Core implementing tactical execution with ReAct loops.
    
    Provides command execution, goal decomposition, context-aware decision making,
    and tool coordination using the ReAct (Reason+Act+Observe) cognitive pattern.
    """
    
    def __init__(self, 
                 action_executor: IActionExecutor,
                 toolbelt: IToolbelt,
                 world_model: IWorldModel,
                 config: Optional[AgentCoreConfig] = None):
        """Initialize the Enhanced Agent Core."""
        super().__init__("enhanced_agent_core", config)
        
        # Core dependencies
        self.action_executor = action_executor
        self.toolbelt = toolbelt
        self.world_model = world_model
        
        # Configuration
        self.agent_config = config or AgentCoreConfig()
        
        # ReAct loop state
        self.current_goal: Optional[Goal] = None
        self.react_history: List[ReActStep] = []
        self.step_counter = 0
        
        # Uncertainty handling
        self.uncertainty_events: List[UncertaintyEvent] = []
        self.uncertainty_counter = 0
        
        # Context and decision making
        self.current_context: Optional[Context] = None
        self.decision_history: List[Dict[str, Any]] = []
        
        # Tool coordination
        self.active_tools: Dict[str, Any] = {}
        self.tool_usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Status callbacks
        self.status_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
    def _initialize_component(self) -> bool:
        """Initialize the Enhanced Agent Core component."""
        try:
            # Initialize dependencies
            if not self.action_executor.initialize():
                self.logger.error("Failed to initialize ActionExecutor")
                return False
                
            if not self.toolbelt.initialize():
                self.logger.error("Failed to initialize Toolbelt")
                return False
                
            if not self.world_model.initialize():
                self.logger.error("Failed to initialize WorldModel")
                return False
            
            # Initialize tool usage tracking
            self._initialize_tool_tracking()
            
            self.logger.info("Enhanced Agent Core initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Enhanced Agent Core: {e}")
            return False
    
    def execute_command(self, command: str, context: Optional[Context] = None) -> ExecutionResult:
        """Execute a direct command using ReAct loops."""
        try:
            # Create a goal from the command
            goal = Goal(
                description=command,
                priority=Priority.MEDIUM,
                success_criteria=[f"Successfully execute: {command}"],
                context=context
            )
            
            return self.execute_goal(goal)
            
        except Exception as e:
            error_msg = f"Failed to execute command '{command}': {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def execute_goal(self, goal: Goal) -> ExecutionResult:
        """Execute a goal using ReAct loops."""
        try:
            self.logger.info(f"Starting goal execution: {goal.description}")
            
            # Set current goal and reset state
            self.current_goal = goal
            self.react_history = []
            self.step_counter = 0
            
            # Update context
            if goal.context:
                self.current_context = goal.context
            
            # Notify observers
            self._notify_observers({
                'type': 'goal_execution_started',
                'goal': asdict(goal),
                'timestamp': datetime.now().isoformat()
            })
            
            # Execute ReAct loop
            max_steps = getattr(self.agent_config, 'max_react_steps', 15)
            
            for step in range(max_steps):
                self.step_counter = step + 1
                
                # Execute one ReAct cycle
                step_result = self._execute_react_step()
                
                if step_result.success:
                    # Check if goal is completed
                    if self._is_goal_completed(goal):
                        success_msg = f"Goal completed successfully in {step + 1} steps"
                        self.logger.info(success_msg)
                        
                        self._notify_observers({
                            'type': 'goal_execution_completed',
                            'goal': asdict(goal),
                            'steps': step + 1,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        return ExecutionResult(
                            success=True,
                            message=success_msg,
                            data={'steps': step + 1, 'history': self.react_history}
                        )
                else:
                    # Handle step failure
                    if not self._handle_step_failure(step_result):
                        error_msg = f"Goal execution failed at step {step + 1}: {step_result.message}"
                        self.logger.error(error_msg)
                        return ExecutionResult(success=False, message=error_msg)
            
            # Max steps reached
            error_msg = f"Goal execution failed: Maximum steps ({max_steps}) reached"
            self.logger.warning(error_msg)
            return ExecutionResult(success=False, message=error_msg)
            
        except Exception as e:
            error_msg = f"Failed to execute goal: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def think(self, context: Context) -> Dict[str, Any]:
        """Perform reasoning step in ReAct loop."""
        try:
            self.current_context = context
            
            # Analyze current situation
            situation_analysis = self._analyze_situation(context)
            
            # Generate reasoning based on goal and context
            reasoning = self._generate_reasoning(situation_analysis)
            
            # Determine next action
            next_action = self._determine_next_action(reasoning, context)
            
            thought_result = {
                'situation_analysis': situation_analysis,
                'reasoning': reasoning,
                'next_action': next_action,
                'confidence': reasoning.get('confidence', 0.5),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.debug(f"Think step completed: {reasoning.get('summary', 'No summary')}")
            
            return thought_result
            
        except Exception as e:
            self.logger.error(f"Failed to perform think step: {e}")
            return {
                'error': str(e),
                'reasoning': 'Think step failed',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }
    
    def act(self, action: Action, context: Context) -> ExecutionResult:
        """Perform action step in ReAct loop."""
        try:
            self.logger.debug(f"Executing action: {action.name}")
            
            # Update tool usage stats
            self._update_tool_usage_stats(action.name)
            
            # Execute action based on type
            if action.name in ['click', 'type_text', 'key_press', 'drag', 'scroll']:
                # Direct GUI actions
                result = self._execute_gui_action(action, context)
            else:
                # Tool-based actions
                result = self._execute_tool_action(action, context)
            
            # Record action in history
            react_step = ReActStep(
                step_number=self.step_counter,
                phase=ReActPhase.ACT,
                thought="",  # Will be filled by think step
                action=action,
                result=result,
                confidence=action.confidence
            )
            
            self.react_history.append(react_step)
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to execute action '{action.name}': {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def observe(self, result: ExecutionResult) -> Observation:
        """Perform observation step in ReAct loop."""
        try:
            # Capture current state
            current_state = self._capture_current_state()
            
            # Analyze the result and state change
            observation_data = {
                'execution_result': asdict(result),
                'current_state': current_state,
                'state_changes': self._detect_state_changes(),
                'world_model_update': self._update_world_model_from_result(result)
            }
            
            observation = Observation(
                timestamp=datetime.now(),
                data=observation_data,
                source="enhanced_agent_core",
                confidence=result.data.get('confidence', 0.8) if result.data else 0.8
            )
            
            # Update world model
            self.world_model.update_state(observation)
            
            # Record observation in history
            if self.react_history:
                self.react_history[-1].observation = observation
            
            self.logger.debug("Observation step completed")
            
            return observation
            
        except Exception as e:
            self.logger.error(f"Failed to perform observation step: {e}")
            return Observation(
                timestamp=datetime.now(),
                data={'error': str(e)},
                source="enhanced_agent_core",
                confidence=0.0
            )
    
    def handle_uncertainty(self, uncertainty: Dict[str, Any]) -> Dict[str, Any]:
        """Handle uncertainty by asking for clarification or making assumptions."""
        try:
            uncertainty_type = UncertaintyType(uncertainty.get('type', 'unclear_context'))
            
            # Create uncertainty event
            uncertainty_event = UncertaintyEvent(
                id=f"uncertainty_{self.uncertainty_counter}",
                type=uncertainty_type,
                description=uncertainty.get('description', 'Unknown uncertainty'),
                context=uncertainty.get('context', {}),
                possible_resolutions=uncertainty.get('possible_resolutions', []),
                confidence_threshold=uncertainty.get('confidence_threshold', 0.5)
            )
            
            self.uncertainty_counter += 1
            self.uncertainty_events.append(uncertainty_event)
            
            # Handle based on uncertainty type
            resolution = self._resolve_uncertainty(uncertainty_event)
            
            self.logger.info(f"Handled uncertainty: {uncertainty_type.value}")
            
            return {
                'uncertainty_id': uncertainty_event.id,
                'resolution': resolution,
                'confidence': resolution.get('confidence', 0.5),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to handle uncertainty: {e}")
            return {
                'error': str(e),
                'resolution': 'uncertainty_handling_failed',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }
    
    def add_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add a status update callback."""
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a status update callback."""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    # Private helper methods
    
    def _execute_react_step(self) -> ExecutionResult:
        """Execute one complete ReAct step (Think-Act-Observe)."""
        try:
            # THINK phase
            if not self.current_context:
                self.current_context = self._build_current_context()
            
            think_result = self.think(self.current_context)
            
            if 'error' in think_result:
                return ExecutionResult(
                    success=False,
                    message=f"Think phase failed: {think_result['error']}"
                )
            
            # Create action from think result
            next_action_data = think_result.get('next_action', {})
            action = Action(
                name=next_action_data.get('name', 'unknown'),
                parameters=next_action_data.get('parameters', {}),
                expected_outcome=next_action_data.get('expected_outcome'),
                confidence=think_result.get('confidence', 0.5)
            )
            
            # ACT phase
            act_result = self.act(action, self.current_context)
            
            if not act_result.success:
                return act_result
            
            # OBSERVE phase
            observation = self.observe(act_result)
            
            # Record complete ReAct step
            react_step = ReActStep(
                step_number=self.step_counter,
                phase=ReActPhase.OBSERVE,  # Final phase
                thought=think_result.get('reasoning', {}).get('summary', ''),
                action=action,
                observation=observation,
                result=act_result,
                confidence=min(think_result.get('confidence', 0.5), action.confidence)
            )
            
            # Update the last step in history or add new one
            if self.react_history and self.react_history[-1].step_number == self.step_counter:
                self.react_history[-1] = react_step
            else:
                self.react_history.append(react_step)
            
            # Notify status callbacks
            self._notify_status_callbacks({
                'type': 'react_step_completed',
                'step': self.step_counter,
                'thought': react_step.thought,
                'action': action.name,
                'result': act_result.success
            })
            
            return ExecutionResult(
                success=True,
                message=f"ReAct step {self.step_counter} completed",
                data={'step': asdict(react_step)}
            )
            
        except Exception as e:
            error_msg = f"ReAct step {self.step_counter} failed: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def _analyze_situation(self, context: Context) -> Dict[str, Any]:
        """Analyze the current situation based on context."""
        try:
            analysis = {
                'timestamp': context.timestamp.isoformat(),
                'active_applications': context.active_applications or [],
                'user_activity': context.user_activity,
                'system_state': context.system_state or {},
                'world_state': self.world_model.get_current_state(),
                'available_tools': self.toolbelt.get_available_tools(),
                'goal_progress': self._assess_goal_progress()
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze situation: {e}")
            return {'error': str(e)}
    
    def _generate_reasoning(self, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reasoning based on situation analysis."""
        try:
            if not self.current_goal:
                return {
                    'summary': 'No active goal',
                    'confidence': 0.0,
                    'reasoning_chain': []
                }
            
            # Analyze goal progress
            goal_progress = situation_analysis.get('goal_progress', {})
            
            # Generate reasoning chain
            reasoning_chain = []
            
            # Step 1: Assess current state
            reasoning_chain.append({
                'step': 'assess_state',
                'description': f"Current goal: {self.current_goal.description}",
                'analysis': goal_progress
            })
            
            # Step 2: Identify next action needed
            next_action_needed = self._identify_next_action_needed(situation_analysis)
            reasoning_chain.append({
                'step': 'identify_action',
                'description': f"Next action needed: {next_action_needed}",
                'rationale': self._explain_action_rationale(next_action_needed, situation_analysis)
            })
            
            # Step 3: Consider constraints and risks
            constraints = self._identify_constraints(situation_analysis)
            reasoning_chain.append({
                'step': 'consider_constraints',
                'description': f"Constraints: {constraints}",
                'impact': self._assess_constraint_impact(constraints)
            })
            
            # Calculate confidence
            confidence = self._calculate_reasoning_confidence(reasoning_chain, situation_analysis)
            
            return {
                'summary': f"Need to {next_action_needed} to progress toward goal",
                'confidence': confidence,
                'reasoning_chain': reasoning_chain,
                'next_action_needed': next_action_needed
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate reasoning: {e}")
            return {
                'summary': f'Reasoning failed: {e}',
                'confidence': 0.0,
                'reasoning_chain': [],
                'error': str(e)
            }
    
    def _determine_next_action(self, reasoning: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Determine the next action based on reasoning."""
        try:
            next_action_needed = reasoning.get('next_action_needed', 'unknown')
            
            # Map reasoning to specific action
            action_mapping = {
                'click_element': self._create_click_action,
                'type_text': self._create_type_action,
                'press_key': self._create_key_action,
                'use_tool': self._create_tool_action,
                'wait': self._create_wait_action,
                'analyze': self._create_analysis_action
            }
            
            action_creator = action_mapping.get(next_action_needed, self._create_default_action)
            action_data = action_creator(reasoning, context)
            
            return action_data
            
        except Exception as e:
            self.logger.error(f"Failed to determine next action: {e}")
            return {
                'name': 'error',
                'parameters': {'error': str(e)},
                'expected_outcome': 'Error handling',
                'confidence': 0.0
            }
    
    def _execute_gui_action(self, action: Action, context: Context) -> ExecutionResult:
        """Execute a GUI action using the ActionExecutor."""
        try:
            if action.name == 'click':
                return self.action_executor.click(
                    action.parameters.get('x', 0),
                    action.parameters.get('y', 0),
                    action.parameters.get('button', 'left')
                )
            elif action.name == 'type_text':
                return self.action_executor.type_text(
                    action.parameters.get('text', '')
                )
            elif action.name == 'key_press':
                return self.action_executor.key_press(
                    action.parameters.get('key', '')
                )
            elif action.name == 'drag':
                return self.action_executor.drag(
                    action.parameters.get('start_x', 0),
                    action.parameters.get('start_y', 0),
                    action.parameters.get('end_x', 0),
                    action.parameters.get('end_y', 0)
                )
            elif action.name == 'scroll':
                return self.action_executor.scroll(
                    action.parameters.get('x', 0),
                    action.parameters.get('y', 0),
                    action.parameters.get('direction', 'up'),
                    action.parameters.get('amount', 3)
                )
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Unknown GUI action: {action.name}"
                )
                
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"GUI action failed: {e}"
            )
    
    def _execute_tool_action(self, action: Action, context: Context) -> ExecutionResult:
        """Execute a tool-based action using the Toolbelt."""
        try:
            result = self.toolbelt.execute_tool(action.name, action.parameters)
            
            return ExecutionResult(
                success=True,
                message=f"Tool {action.name} executed successfully",
                data={'tool_result': result}
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Tool execution failed: {e}"
            )
    
    def _resolve_uncertainty(self, uncertainty_event: UncertaintyEvent) -> Dict[str, Any]:
        """Resolve an uncertainty event."""
        try:
            if uncertainty_event.type == UncertaintyType.AMBIGUOUS_COMMAND:
                return self._resolve_ambiguous_command(uncertainty_event)
            elif uncertainty_event.type == UncertaintyType.UNCLEAR_CONTEXT:
                return self._resolve_unclear_context(uncertainty_event)
            elif uncertainty_event.type == UncertaintyType.MULTIPLE_OPTIONS:
                return self._resolve_multiple_options(uncertainty_event)
            elif uncertainty_event.type == UncertaintyType.MISSING_INFORMATION:
                return self._resolve_missing_information(uncertainty_event)
            elif uncertainty_event.type == UncertaintyType.UNEXPECTED_STATE:
                return self._resolve_unexpected_state(uncertainty_event)
            elif uncertainty_event.type == UncertaintyType.TOOL_FAILURE:
                return self._resolve_tool_failure(uncertainty_event)
            else:
                return self._resolve_generic_uncertainty(uncertainty_event)
                
        except Exception as e:
            return {
                'resolution_type': 'error',
                'action': 'log_error',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _is_goal_completed(self, goal: Goal) -> bool:
        """Check if the goal has been completed."""
        try:
            # Check success criteria
            if goal.success_criteria:
                for criterion in goal.success_criteria:
                    if not self._check_success_criterion(criterion):
                        return False
                return True
            
            # Fallback: check if we've made significant progress
            progress = self._assess_goal_progress()
            return progress.get('completion_percentage', 0) >= 90
            
        except Exception as e:
            self.logger.error(f"Failed to check goal completion: {e}")
            return False
    
    def _handle_step_failure(self, step_result: ExecutionResult) -> bool:
        """Handle a failed ReAct step."""
        try:
            # Check if we should retry
            error_recovery_attempts = getattr(self.agent_config, 'error_recovery_attempts', 3)
            
            if self.step_counter <= error_recovery_attempts:
                self.logger.warning(f"Step failed, attempting recovery: {step_result.message}")
                
                # Try to recover by adjusting approach
                recovery_action = self._generate_recovery_action(step_result)
                if recovery_action:
                    return True  # Continue execution
            
            return False  # Stop execution
            
        except Exception as e:
            self.logger.error(f"Failed to handle step failure: {e}")
            return False
    
    # Utility methods for action creation
    
    def _create_click_action(self, reasoning: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Create a click action based on reasoning."""
        return {
            'name': 'click',
            'parameters': {
                'x': 100,  # Would be determined by visual analysis
                'y': 100,
                'button': 'left'
            },
            'expected_outcome': 'Element clicked successfully',
            'confidence': reasoning.get('confidence', 0.5)
        }
    
    def _create_type_action(self, reasoning: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Create a type text action based on reasoning."""
        return {
            'name': 'type_text',
            'parameters': {
                'text': reasoning.get('text_to_type', '')
            },
            'expected_outcome': 'Text typed successfully',
            'confidence': reasoning.get('confidence', 0.5)
        }
    
    def _create_key_action(self, reasoning: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Create a key press action based on reasoning."""
        return {
            'name': 'key_press',
            'parameters': {
                'key': reasoning.get('key_to_press', 'enter')
            },
            'expected_outcome': 'Key pressed successfully',
            'confidence': reasoning.get('confidence', 0.5)
        }
    
    def _create_tool_action(self, reasoning: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Create a tool action based on reasoning."""
        return {
            'name': reasoning.get('tool_name', 'unknown_tool'),
            'parameters': reasoning.get('tool_parameters', {}),
            'expected_outcome': 'Tool executed successfully',
            'confidence': reasoning.get('confidence', 0.5)
        }
    
    def _create_wait_action(self, reasoning: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Create a wait action based on reasoning."""
        return {
            'name': 'wait',
            'parameters': {
                'duration': reasoning.get('wait_duration', 1.0)
            },
            'expected_outcome': 'Wait completed',
            'confidence': 0.9
        }
    
    def _create_analysis_action(self, reasoning: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Create an analysis action based on reasoning."""
        return {
            'name': 'analyze_screen',
            'parameters': {},
            'expected_outcome': 'Screen analyzed',
            'confidence': 0.8
        }
    
    def _create_default_action(self, reasoning: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Create a default action when specific action cannot be determined."""
        return {
            'name': 'analyze_screen',
            'parameters': {},
            'expected_outcome': 'Default analysis completed',
            'confidence': 0.3
        }
    
    # Helper methods for various assessments and operations
    
    def _build_current_context(self) -> Context:
        """Build current context from available information."""
        return Context(
            timestamp=datetime.now(),
            screen_state=None,  # Would be captured from screen
            active_applications=[],  # Would be detected from system
            user_activity=None,
            system_state={'agent_active': True}
        )
    
    def _assess_goal_progress(self) -> Dict[str, Any]:
        """Assess progress toward current goal."""
        if not self.current_goal:
            return {'completion_percentage': 0, 'status': 'no_goal'}
        
        # Simple progress assessment based on steps taken
        max_steps = getattr(self.agent_config, 'max_react_steps', 15)
        progress_percentage = min((self.step_counter / max_steps) * 100, 100)
        
        return {
            'completion_percentage': progress_percentage,
            'steps_taken': self.step_counter,
            'status': 'in_progress' if progress_percentage < 100 else 'completed'
        }
    
    def _identify_next_action_needed(self, situation_analysis: Dict[str, Any]) -> str:
        """Identify what action is needed next."""
        # Simple heuristic - would be more sophisticated in real implementation
        if not situation_analysis.get('world_state'):
            return 'analyze'
        
        goal_progress = situation_analysis.get('goal_progress', {})
        if goal_progress.get('completion_percentage', 0) < 50:
            return 'click_element'
        else:
            return 'use_tool'
    
    def _explain_action_rationale(self, action_needed: str, situation_analysis: Dict[str, Any]) -> str:
        """Explain why a particular action is needed."""
        rationales = {
            'click_element': 'Need to interact with UI element to progress',
            'type_text': 'Need to input text to complete form or command',
            'press_key': 'Need to use keyboard shortcut or navigation',
            'use_tool': 'Need to use specialized tool for this task',
            'wait': 'Need to wait for system response or loading',
            'analyze': 'Need to analyze current state before proceeding'
        }
        
        return rationales.get(action_needed, 'Action needed to progress toward goal')
    
    def _identify_constraints(self, situation_analysis: Dict[str, Any]) -> List[str]:
        """Identify constraints that might affect action execution."""
        constraints = []
        
        # Check system constraints
        system_state = situation_analysis.get('system_state', {})
        if system_state.get('high_cpu_usage'):
            constraints.append('high_system_load')
        
        # Check application constraints
        active_apps = situation_analysis.get('active_applications', [])
        if not active_apps:
            constraints.append('no_active_applications')
        
        return constraints
    
    def _assess_constraint_impact(self, constraints: List[str]) -> str:
        """Assess the impact of identified constraints."""
        if not constraints:
            return 'no_constraints'
        elif len(constraints) == 1:
            return 'minor_impact'
        else:
            return 'significant_impact'
    
    def _calculate_reasoning_confidence(self, reasoning_chain: List[Dict[str, Any]], situation_analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the reasoning process."""
        base_confidence = 0.7
        
        # Adjust based on available information
        if situation_analysis.get('world_state'):
            base_confidence += 0.1
        
        if situation_analysis.get('goal_progress', {}).get('completion_percentage', 0) > 0:
            base_confidence += 0.1
        
        # Adjust based on reasoning chain completeness
        if len(reasoning_chain) >= 3:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _capture_current_state(self) -> Dict[str, Any]:
        """Capture current system/application state."""
        return {
            'timestamp': datetime.now().isoformat(),
            'world_model_state': self.world_model.get_current_state(),
            'active_tools': list(self.active_tools.keys()),
            'step_count': self.step_counter
        }
    
    def _detect_state_changes(self) -> Dict[str, Any]:
        """Detect changes in state since last observation."""
        # Simple implementation - would compare with previous state
        return {
            'changes_detected': True,
            'change_types': ['world_model_update'],
            'significance': 'minor'
        }
    
    def _update_world_model_from_result(self, result: ExecutionResult) -> Dict[str, Any]:
        """Update world model based on execution result."""
        try:
            # Create observation from result
            observation = Observation(
                timestamp=datetime.now(),
                data=asdict(result),
                source="action_result",
                confidence=0.8
            )
            
            # Update world model
            self.world_model.update_state(observation)
            
            return {'updated': True, 'observation_id': 'action_result'}
            
        except Exception as e:
            self.logger.error(f"Failed to update world model: {e}")
            return {'updated': False, 'error': str(e)}
    
    def _check_success_criterion(self, criterion: str) -> bool:
        """Check if a success criterion has been met."""
        # Simple implementation - would be more sophisticated
        return "successfully" in criterion.lower()
    
    def _generate_recovery_action(self, step_result: ExecutionResult) -> Optional[Dict[str, Any]]:
        """Generate a recovery action for a failed step."""
        # Simple recovery strategy
        return {
            'name': 'analyze_screen',
            'parameters': {},
            'expected_outcome': 'Recovery analysis completed'
        }
    
    def _initialize_tool_tracking(self) -> None:
        """Initialize tool usage tracking."""
        available_tools = self.toolbelt.get_available_tools()
        for tool_name in available_tools:
            self.tool_usage_stats[tool_name] = {
                'usage_count': 0,
                'success_count': 0,
                'failure_count': 0,
                'average_execution_time': 0.0
            }
    
    def _update_tool_usage_stats(self, tool_name: str) -> None:
        """Update usage statistics for a tool."""
        if tool_name in self.tool_usage_stats:
            self.tool_usage_stats[tool_name]['usage_count'] += 1
    
    def _notify_status_callbacks(self, status_data: Dict[str, Any]) -> None:
        """Notify all registered status callbacks."""
        for callback in self.status_callbacks:
            try:
                callback(status_data)
            except Exception as e:
                self.logger.error(f"Status callback failed: {e}")
    
    # Uncertainty resolution methods
    
    def _resolve_ambiguous_command(self, uncertainty_event: UncertaintyEvent) -> Dict[str, Any]:
        """Resolve ambiguous command uncertainty."""
        return {
            'resolution_type': 'clarification_request',
            'action': 'ask_user_for_clarification',
            'question': f"The command '{uncertainty_event.description}' is ambiguous. Please clarify.",
            'confidence': 0.8
        }
    
    def _resolve_unclear_context(self, uncertainty_event: UncertaintyEvent) -> Dict[str, Any]:
        """Resolve unclear context uncertainty."""
        return {
            'resolution_type': 'context_analysis',
            'action': 'analyze_current_context',
            'confidence': 0.6
        }
    
    def _resolve_multiple_options(self, uncertainty_event: UncertaintyEvent) -> Dict[str, Any]:
        """Resolve multiple options uncertainty."""
        # Choose the first option as default
        options = uncertainty_event.possible_resolutions
        if options:
            return {
                'resolution_type': 'option_selection',
                'action': 'select_option',
                'selected_option': options[0],
                'confidence': 0.5
            }
        
        return {
            'resolution_type': 'no_options',
            'action': 'request_guidance',
            'confidence': 0.3
        }
    
    def _resolve_missing_information(self, uncertainty_event: UncertaintyEvent) -> Dict[str, Any]:
        """Resolve missing information uncertainty."""
        return {
            'resolution_type': 'information_gathering',
            'action': 'gather_missing_information',
            'confidence': 0.7
        }
    
    def _resolve_unexpected_state(self, uncertainty_event: UncertaintyEvent) -> Dict[str, Any]:
        """Resolve unexpected state uncertainty."""
        return {
            'resolution_type': 'state_recovery',
            'action': 'attempt_state_recovery',
            'confidence': 0.4
        }
    
    def _resolve_tool_failure(self, uncertainty_event: UncertaintyEvent) -> Dict[str, Any]:
        """Resolve tool failure uncertainty."""
        return {
            'resolution_type': 'tool_retry',
            'action': 'retry_with_alternative_tool',
            'confidence': 0.6
        }
    
    def _resolve_generic_uncertainty(self, uncertainty_event: UncertaintyEvent) -> Dict[str, Any]:
        """Resolve generic uncertainty."""
        return {
            'resolution_type': 'generic_handling',
            'action': 'proceed_with_caution',
            'confidence': 0.3
        }
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Enhanced Agent Core specific status."""
        return {
            'current_goal': self.current_goal.description if self.current_goal else None,
            'react_steps_completed': len(self.react_history),
            'uncertainty_events': len(self.uncertainty_events),
            'active_tools_count': len(self.active_tools),
            'tool_usage_stats': self.tool_usage_stats,
            'max_react_steps': getattr(self.agent_config, 'max_react_steps', 15),
            'uncertainty_threshold': getattr(self.agent_config, 'uncertainty_threshold', 0.5),
        }