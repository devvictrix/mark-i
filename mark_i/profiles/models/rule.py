"""
Rule Models

Defines automation rules, conditions, and actions for profile execution.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
from enum import Enum


class ConditionType(Enum):
    """Available condition types for rules"""
    VISUAL_MATCH = "visual_match"
    OCR_CONTAINS = "ocr_contains"
    TEMPLATE_MATCH = "template_match"
    SYSTEM_STATE = "system_state"
    ALWAYS_TRUE = "always_true"
    COLOR_MATCH = "color_match"
    WINDOW_EXISTS = "window_exists"


class ActionType(Enum):
    """Available action types for rules"""
    CLICK = "click"
    TYPE_TEXT = "type_text"
    WAIT = "wait"
    WAIT_FOR_VISUAL_CUE = "wait_for_visual_cue"
    ASK_USER = "ask_user"
    RUN_COMMAND = "run_command"
    PRESS_KEY = "press_key"
    SCROLL = "scroll"
    DRAG = "drag"
    SCREENSHOT = "screenshot"
    LOG_MESSAGE = "log_message"


@dataclass
class Condition:
    """Rule condition definition"""
    type: str  # ConditionType value
    region: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    negate: bool = False
    
    def __post_init__(self):
        """Validate condition after initialization"""
        try:
            ConditionType(self.type)
        except ValueError:
            valid_types = [ct.value for ct in ConditionType]
            raise ValueError(f"Invalid condition type '{self.type}'. Valid types: {valid_types}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert condition to dictionary"""
        return {
            'type': self.type,
            'region': self.region,
            'parameters': self.parameters,
            'negate': self.negate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition':
        """Create condition from dictionary"""
        return cls(
            type=data['type'],
            region=data['region'],
            parameters=data.get('parameters', {}),
            negate=data.get('negate', False)
        )


@dataclass
class Action:
    """Action definition"""
    type: str  # ActionType value
    region: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    delay_before: float = 0.0
    delay_after: float = 0.0
    
    def __post_init__(self):
        """Validate action after initialization"""
        try:
            ActionType(self.type)
        except ValueError:
            valid_types = [at.value for at in ActionType]
            raise ValueError(f"Invalid action type '{self.type}'. Valid types: {valid_types}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary"""
        return {
            'type': self.type,
            'region': self.region,
            'parameters': self.parameters,
            'delay_before': self.delay_before,
            'delay_after': self.delay_after
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create action from dictionary"""
        return cls(
            type=data['type'],
            region=data.get('region'),
            parameters=data.get('parameters', {}),
            delay_before=data.get('delay_before', 0.0),
            delay_after=data.get('delay_after', 0.0)
        )


@dataclass
class Rule:
    """Automation rule with conditions and actions"""
    name: str
    description: str
    enabled: bool = True
    priority: int = 0
    
    # Conditions
    conditions: List[Condition] = field(default_factory=list)
    logical_operator: str = "AND"  # AND, OR
    
    # Actions
    actions: List[Action] = field(default_factory=list)
    
    # Execution settings
    max_retries: int = 3
    retry_delay: float = 1.0
    continue_on_failure: bool = False
    
    def __post_init__(self):
        """Validate rule after initialization"""
        if self.logical_operator not in ["AND", "OR"]:
            raise ValueError(f"Invalid logical operator '{self.logical_operator}'. Must be 'AND' or 'OR'")
        
        if self.priority < 0:
            raise ValueError("Rule priority must be non-negative")
        
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        
        if self.retry_delay < 0:
            raise ValueError("Retry delay must be non-negative")
    
    def add_condition(self, condition: Condition):
        """Add a condition to this rule"""
        self.conditions.append(condition)
    
    def add_action(self, action: Action):
        """Add an action to this rule"""
        self.actions.append(action)
    
    def remove_condition(self, index: int):
        """Remove condition at specified index"""
        if 0 <= index < len(self.conditions):
            del self.conditions[index]
    
    def remove_action(self, index: int):
        """Remove action at specified index"""
        if 0 <= index < len(self.actions):
            del self.actions[index]
    
    def get_referenced_regions(self) -> List[str]:
        """Get list of all regions referenced by this rule"""
        regions = set()
        
        # Add regions from conditions
        for condition in self.conditions:
            if condition.region:
                regions.add(condition.region)
        
        # Add regions from actions
        for action in self.actions:
            if action.region:
                regions.add(action.region)
        
        return list(regions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'priority': self.priority,
            'conditions': [c.to_dict() for c in self.conditions],
            'logical_operator': self.logical_operator,
            'actions': [a.to_dict() for a in self.actions],
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'continue_on_failure': self.continue_on_failure
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Create rule from dictionary"""
        rule = cls(
            name=data['name'],
            description=data['description'],
            enabled=data.get('enabled', True),
            priority=data.get('priority', 0),
            logical_operator=data.get('logical_operator', 'AND'),
            max_retries=data.get('max_retries', 3),
            retry_delay=data.get('retry_delay', 1.0),
            continue_on_failure=data.get('continue_on_failure', False)
        )
        
        # Add conditions
        for condition_data in data.get('conditions', []):
            rule.add_condition(Condition.from_dict(condition_data))
        
        # Add actions
        for action_data in data.get('actions', []):
            rule.add_action(Action.from_dict(action_data))
        
        return rule
    
    def to_json(self) -> str:
        """Convert rule to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Rule':
        """Create rule from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)