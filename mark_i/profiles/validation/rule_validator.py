"""
Rule Validator

Specialized validation for automation rules, conditions, and actions.
"""

from typing import List, Dict, Any
from ..models.rule import Rule, Condition, Action, ConditionType, ActionType
from .profile_validator import ValidationResult


class RuleValidator:
    """Validates automation rules for correctness and best practices"""
    
    def __init__(self):
        self.max_conditions_per_rule = 10
        self.max_actions_per_rule = 20
        self.max_delay_seconds = 60
    
    def validate_rule(self, rule: Rule, available_regions: List[str]) -> ValidationResult:
        """
        Validate a single rule
        
        Args:
            rule: Rule to validate
            available_regions: List of available region names
            
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Validate basic rule properties
        self._validate_rule_properties(rule, result)
        
        # Validate conditions
        self._validate_conditions(rule, available_regions, result)
        
        # Validate actions
        self._validate_actions(rule, available_regions, result)
        
        # Check for logical issues
        self._check_rule_logic(rule, result)
        
        return result
    
    def _validate_rule_properties(self, rule: Rule, result: ValidationResult):
        """Validate basic rule properties"""
        if not rule.name or not rule.name.strip():
            result.add_error("Rule name cannot be empty")
        
        if len(rule.name) > 100:
            result.add_error("Rule name is too long (max 100 characters)")
        
        if not rule.description or not rule.description.strip():
            result.add_warning("Rule description is empty - consider adding a description")
        
        if rule.priority < 0:
            result.add_error("Rule priority cannot be negative")
        
        if rule.priority > 100:
            result.add_warning("Very high rule priority - ensure this is intentional")
        
        if rule.logical_operator not in ["AND", "OR"]:
            result.add_error(f"Invalid logical operator '{rule.logical_operator}'. Must be 'AND' or 'OR'")
        
        if rule.max_retries < 0:
            result.add_error("Max retries cannot be negative")
        
        if rule.max_retries > 10:
            result.add_warning("High retry count may cause long delays on failure")
        
        if rule.retry_delay < 0:
            result.add_error("Retry delay cannot be negative")
        
        if rule.retry_delay > 30:
            result.add_warning("Long retry delay may cause slow execution")
    
    def _validate_conditions(self, rule: Rule, available_regions: List[str], result: ValidationResult):
        """Validate rule conditions"""
        if len(rule.conditions) == 0:
            result.add_error("Rule must have at least one condition")
        
        if len(rule.conditions) > self.max_conditions_per_rule:
            result.add_warning(f"Rule has many conditions ({len(rule.conditions)}) - consider simplifying")
        
        for i, condition in enumerate(rule.conditions):
            self._validate_condition(condition, available_regions, result, i + 1)
    
    def _validate_condition(self, condition: Condition, available_regions: List[str], 
                          result: ValidationResult, condition_num: int):
        """Validate individual condition"""
        # Validate condition type
        try:
            ConditionType(condition.type)
        except ValueError:
            valid_types = [ct.value for ct in ConditionType]
            result.add_error(f"Condition {condition_num}: Invalid type '{condition.type}'. Valid types: {valid_types}")
        
        # Validate region reference
        if not condition.region:
            result.add_error(f"Condition {condition_num}: No region specified")
        elif condition.region not in available_regions:
            result.add_error(f"Condition {condition_num}: Unknown region '{condition.region}'")
        
        # Validate condition-specific parameters
        self._validate_condition_parameters(condition, result, condition_num)
    
    def _validate_condition_parameters(self, condition: Condition, result: ValidationResult, condition_num: int):
        """Validate condition-specific parameters"""
        if condition.type == ConditionType.OCR_CONTAINS.value:
            if 'text' not in condition.parameters:
                result.add_error(f"Condition {condition_num}: OCR condition missing 'text' parameter")
            elif not condition.parameters['text']:
                result.add_error(f"Condition {condition_num}: OCR text cannot be empty")
        
        elif condition.type == ConditionType.TEMPLATE_MATCH.value:
            if 'template_path' not in condition.parameters:
                result.add_error(f"Condition {condition_num}: Template match missing 'template_path' parameter")
            
            threshold = condition.parameters.get('threshold', 0.8)
            if not 0 <= threshold <= 1:
                result.add_error(f"Condition {condition_num}: Template threshold must be between 0 and 1")
        
        elif condition.type == ConditionType.COLOR_MATCH.value:
            if 'expected_color' not in condition.parameters:
                result.add_error(f"Condition {condition_num}: Color match missing 'expected_color' parameter")
            else:
                color = condition.parameters['expected_color']
                if not isinstance(color, (list, tuple)) or len(color) != 3:
                    result.add_error(f"Condition {condition_num}: Color must be [R, G, B] format")
                elif not all(0 <= c <= 255 for c in color):
                    result.add_error(f"Condition {condition_num}: Color values must be 0-255")
    
    def _validate_actions(self, rule: Rule, available_regions: List[str], result: ValidationResult):
        """Validate rule actions"""
        if len(rule.actions) == 0:
            result.add_error("Rule must have at least one action")
        
        if len(rule.actions) > self.max_actions_per_rule:
            result.add_warning(f"Rule has many actions ({len(rule.actions)}) - consider splitting into multiple rules")
        
        for i, action in enumerate(rule.actions):
            self._validate_action(action, available_regions, result, i + 1)
    
    def _validate_action(self, action: Action, available_regions: List[str], 
                        result: ValidationResult, action_num: int):
        """Validate individual action"""
        # Validate action type
        try:
            ActionType(action.type)
        except ValueError:
            valid_types = [at.value for at in ActionType]
            result.add_error(f"Action {action_num}: Invalid type '{action.type}'. Valid types: {valid_types}")
        
        # Validate region reference (if required)
        region_required_actions = [
            ActionType.CLICK.value,
            ActionType.DRAG.value,
            ActionType.SCROLL.value,
            ActionType.WAIT_FOR_VISUAL_CUE.value
        ]
        
        if action.type in region_required_actions:
            if not action.region:
                result.add_error(f"Action {action_num}: '{action.type}' requires a region")
            elif action.region not in available_regions:
                result.add_error(f"Action {action_num}: Unknown region '{action.region}'")
        
        # Validate delays
        if action.delay_before < 0:
            result.add_error(f"Action {action_num}: delay_before cannot be negative")
        
        if action.delay_after < 0:
            result.add_error(f"Action {action_num}: delay_after cannot be negative")
        
        if action.delay_before > self.max_delay_seconds:
            result.add_warning(f"Action {action_num}: Very long delay_before ({action.delay_before}s)")
        
        if action.delay_after > self.max_delay_seconds:
            result.add_warning(f"Action {action_num}: Very long delay_after ({action.delay_after}s)")
        
        # Validate action-specific parameters
        self._validate_action_parameters(action, result, action_num)
    
    def _validate_action_parameters(self, action: Action, result: ValidationResult, action_num: int):
        """Validate action-specific parameters"""
        if action.type == ActionType.TYPE_TEXT.value:
            if 'text' not in action.parameters:
                result.add_error(f"Action {action_num}: TYPE_TEXT missing 'text' parameter")
            elif not action.parameters['text']:
                result.add_warning(f"Action {action_num}: TYPE_TEXT has empty text")
        
        elif action.type == ActionType.WAIT.value:
            if 'seconds' not in action.parameters:
                result.add_error(f"Action {action_num}: WAIT missing 'seconds' parameter")
            else:
                wait_time = action.parameters['seconds']
                if not isinstance(wait_time, (int, float)) or wait_time <= 0:
                    result.add_error(f"Action {action_num}: WAIT seconds must be positive number")
                elif wait_time > 60:
                    result.add_warning(f"Action {action_num}: Very long wait time ({wait_time}s)")
        
        elif action.type == ActionType.PRESS_KEY.value:
            if 'key' not in action.parameters:
                result.add_error(f"Action {action_num}: PRESS_KEY missing 'key' parameter")
            elif not action.parameters['key']:
                result.add_error(f"Action {action_num}: PRESS_KEY key cannot be empty")
        
        elif action.type == ActionType.ASK_USER.value:
            if 'question' not in action.parameters:
                result.add_error(f"Action {action_num}: ASK_USER missing 'question' parameter")
            elif not action.parameters['question']:
                result.add_error(f"Action {action_num}: ASK_USER question cannot be empty")
        
        elif action.type == ActionType.RUN_COMMAND.value:
            if 'command' not in action.parameters:
                result.add_error(f"Action {action_num}: RUN_COMMAND missing 'command' parameter")
            elif not action.parameters['command']:
                result.add_error(f"Action {action_num}: RUN_COMMAND command cannot be empty")
            else:
                result.add_warning(f"Action {action_num}: RUN_COMMAND can be dangerous - ensure command is safe")
    
    def _check_rule_logic(self, rule: Rule, result: ValidationResult):
        """Check for logical issues in rule structure"""
        # Check for conflicting conditions
        if rule.logical_operator == "AND":
            self._check_and_logic_conflicts(rule, result)
        
        # Check for redundant actions
        self._check_redundant_actions(rule, result)
        
        # Check for action order issues
        self._check_action_order(rule, result)
    
    def _check_and_logic_conflicts(self, rule: Rule, result: ValidationResult):
        """Check for conflicting conditions in AND logic"""
        # This is a simplified check - could be expanded
        always_true_count = sum(1 for c in rule.conditions if c.type == ConditionType.ALWAYS_TRUE.value)
        if always_true_count > 1:
            result.add_warning("Multiple 'always_true' conditions in AND logic is redundant")
    
    def _check_redundant_actions(self, rule: Rule, result: ValidationResult):
        """Check for redundant or duplicate actions"""
        action_signatures = []
        for action in rule.actions:
            signature = (action.type, action.region, str(action.parameters))
            if signature in action_signatures:
                result.add_warning("Rule contains duplicate actions")
            action_signatures.append(signature)
    
    def _check_action_order(self, rule: Rule, result: ValidationResult):
        """Check for potential action order issues"""
        # Check if ASK_USER comes after other actions that might fail
        ask_user_indices = [i for i, a in enumerate(rule.actions) if a.type == ActionType.ASK_USER.value]
        
        if ask_user_indices:
            for ask_index in ask_user_indices:
                if ask_index > 0:
                    result.add_warning("ASK_USER action after other actions - consider placing it earlier")