"""
Profile Validator

Comprehensive validation for automation profiles including regions, rules, and settings.
Provides dependency checking, configuration validation, and template compatibility.
"""

import logging
import re
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..models.profile import AutomationProfile
from ..models.region import Region
from ..models.rule import Rule, Condition, Action, ConditionType, ActionType


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'profile', 'region', 'rule', 'action', 'condition', 'settings'
    message: str
    location: str  # Where the issue was found
    suggestion: Optional[str] = None  # Suggested fix
    
    def __str__(self) -> str:
        result = f"[{self.severity.upper()}] {self.category}: {self.message}"
        if self.location:
            result += f" (Location: {self.location})"
        if self.suggestion:
            result += f" - Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationResult:
    """Result of profile validation"""
    is_valid: bool
    issues: List[ValidationIssue]
    validation_time: datetime
    profile_name: str
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get all error issues"""
        return [issue for issue in self.issues if issue.severity == 'error']
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get all warning issues"""
        return [issue for issue in self.issues if issue.severity == 'warning']
    
    @property
    def info(self) -> List[ValidationIssue]:
        """Get all info issues"""
        return [issue for issue in self.issues if issue.severity == 'info']
    
    def add_error(self, category: str, message: str, location: str = "", suggestion: str = None):
        """Add an error to the result"""
        self.issues.append(ValidationIssue('error', category, message, location, suggestion))
        self.is_valid = False
    
    def add_warning(self, category: str, message: str, location: str = "", suggestion: str = None):
        """Add a warning to the result"""
        self.issues.append(ValidationIssue('warning', category, message, location, suggestion))
    
    def add_info(self, category: str, message: str, location: str = "", suggestion: str = None):
        """Add an info message to the result"""
        self.issues.append(ValidationIssue('info', category, message, location, suggestion))
    
    def get_summary(self) -> str:
        """Get validation summary"""
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        info_count = len(self.info)
        
        status = "VALID" if self.is_valid else "INVALID"
        return f"Profile '{self.profile_name}' validation: {status} - {error_count} errors, {warning_count} warnings, {info_count} info"


class ProfileValidator:
    """Comprehensive validator for automation profiles"""
    
    def __init__(self):
        self.logger = logging.getLogger("mark_i.profiles.validation.validator")
        
        # Validation limits
        self.max_regions = 50
        self.max_rules = 100
        self.max_conditions_per_rule = 10
        self.max_actions_per_rule = 20
        self.min_region_size = 10
        self.max_region_size = 5000
        self.max_profile_name_length = 100
        self.max_description_length = 1000
        self.max_region_name_length = 50
        self.max_rule_name_length = 100
        
        # Screen size limits for validation
        self.max_screen_width = 7680  # 8K width
        self.max_screen_height = 4320  # 8K height
        
        # Valid parameter patterns
        self.valid_email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.valid_url_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
        self.valid_file_path_pattern = re.compile(r'^[a-zA-Z]:\\|^/|^\\\\|^[a-zA-Z0-9._-]+$')
        
        # Template compatibility rules
        self.template_inheritance_rules = {
            'email': ['outlook', 'gmail', 'thunderbird'],
            'web': ['chrome', 'firefox', 'edge', 'safari'],
            'system': ['windows', 'macos', 'linux']
        }
    
    def validate_profile(self, profile: AutomationProfile) -> ValidationResult:
        """
        Perform comprehensive validation of an automation profile
        
        Args:
            profile: Profile to validate
            
        Returns:
            ValidationResult with detailed issues and suggestions
        """
        result = ValidationResult(
            is_valid=True,
            issues=[],
            validation_time=datetime.now(),
            profile_name=profile.name
        )
        
        self.logger.info(f"Starting validation of profile: {profile.name}")
        
        try:
            # Core validation steps
            self._validate_basic_properties(profile, result)
            self._validate_regions(profile, result)
            self._validate_rules(profile, result)
            self._validate_conditions_and_actions(profile, result)
            self._validate_dependencies(profile, result)
            self._validate_settings(profile, result)
            
            # Advanced validation
            self._validate_execution_flow(profile, result)
            self._validate_template_compatibility(profile, result)
            self._validate_security_concerns(profile, result)
            
            # Best practices and optimization
            self._check_best_practices(profile, result)
            self._check_performance_concerns(profile, result)
            self._suggest_improvements(profile, result)
            
            self.logger.info(f"Validation completed: {result.get_summary()}")
            
        except Exception as e:
            self.logger.error(f"Validation failed with exception: {e}")
            result.add_error('validation', f"Validation process failed: {str(e)}", 
                           suggestion="Check profile structure and try again")
        
        return result
    
    def _validate_basic_properties(self, profile: AutomationProfile, result: ValidationResult):
        """Validate basic profile properties"""
        # Name validation
        if not profile.name or not profile.name.strip():
            result.add_error('profile', "Profile name cannot be empty", 
                           suggestion="Provide a descriptive name for the profile")
        elif len(profile.name) > self.max_profile_name_length:
            result.add_error('profile', f"Profile name is too long (max {self.max_profile_name_length} characters)",
                           suggestion="Shorten the profile name")
        elif len(profile.name) < 3:
            result.add_warning('profile', "Profile name is very short",
                             suggestion="Use a more descriptive name")
        
        # Description validation
        if not profile.description or not profile.description.strip():
            result.add_warning('profile', "Profile description is empty",
                             suggestion="Add a description explaining what this profile does")
        elif len(profile.description) > self.max_description_length:
            result.add_warning('profile', f"Profile description is very long (max {self.max_description_length} characters)",
                             suggestion="Consider shortening the description")
        
        # Category validation
        valid_categories = ['email', 'web', 'files', 'templates', 'custom']
        if profile.category not in valid_categories:
            result.add_error('profile', f"Invalid category '{profile.category}'",
                           suggestion=f"Use one of: {', '.join(valid_categories)}")
        
        # ID validation
        if not profile.id or len(profile.id) < 10:
            result.add_error('profile', "Profile ID is invalid or too short",
                           suggestion="Regenerate the profile ID")
        
        # Target application validation
        if not profile.target_application or not profile.target_application.strip():
            result.add_info('profile', "No target application specified",
                          suggestion="Specify the target application for better organization")
        
        # Tags validation
        if len(profile.tags) == 0:
            result.add_info('profile', "No tags specified",
                          suggestion="Add tags to help organize and find this profile")
        
        # Check for reserved names
        reserved_names = ['test', 'temp', 'example', 'sample', 'default']
        if profile.name.lower() in reserved_names:
            result.add_warning('profile', f"Profile name '{profile.name}' appears to be a placeholder",
                             suggestion="Use a more specific, descriptive name")
    
    def _validate_regions(self, profile: AutomationProfile, result: ValidationResult):
        """Validate profile regions"""
        if len(profile.regions) > self.max_regions:
            result.add_error(f"Too many regions ({len(profile.regions)}). Maximum allowed: {self.max_regions}")
        
        if len(profile.regions) == 0:
            result.add_warning("Profile has no regions defined")
        
        region_names = set()
        for region in profile.regions:
            # Check for duplicate names
            if region.name in region_names:
                result.add_error(f"Duplicate region name: '{region.name}'")
            region_names.add(region.name)
            
            # Validate region properties
            self._validate_region(region, result)
    
    def _validate_region(self, region: Region, result: ValidationResult):
        """Validate individual region"""
        if not region.name or not region.name.strip():
            result.add_error("Region name cannot be empty")
        
        if len(region.name) > 50:
            result.add_error(f"Region name '{region.name}' is too long (max 50 characters)")
        
        # Validate coordinates and dimensions
        if region.x < 0 or region.y < 0:
            result.add_error(f"Region '{region.name}' has negative coordinates")
        
        if region.width < self.min_region_size or region.height < self.min_region_size:
            result.add_error(f"Region '{region.name}' is too small (min {self.min_region_size}x{self.min_region_size})")
        
        if region.width > self.max_region_size or region.height > self.max_region_size:
            result.add_warning(f"Region '{region.name}' is very large - consider splitting it")
        
        # Validate timeout and retry settings
        if region.timeout_seconds <= 0:
            result.add_error(f"Region '{region.name}' timeout must be positive")
        
        if region.retry_count < 0:
            result.add_error(f"Region '{region.name}' retry count cannot be negative")
        
        if region.timeout_seconds > 60:
            result.add_warning(f"Region '{region.name}' has very long timeout ({region.timeout_seconds}s)")
    
    def _validate_rules(self, profile: AutomationProfile, result: ValidationResult):
        """Validate profile rules"""
        if len(profile.rules) > self.max_rules:
            result.add_error(f"Too many rules ({len(profile.rules)}). Maximum allowed: {self.max_rules}")
        
        if len(profile.rules) == 0:
            result.add_warning("Profile has no rules defined")
        
        rule_names = set()
        enabled_rules = 0
        
        for rule in profile.rules:
            # Check for duplicate names
            if rule.name in rule_names:
                result.add_error(f"Duplicate rule name: '{rule.name}'")
            rule_names.add(rule.name)
            
            if rule.enabled:
                enabled_rules += 1
            
            # Validate individual rule
            self._validate_rule(rule, result)
        
        if enabled_rules == 0:
            result.add_warning("No rules are enabled - profile will not perform any actions")
    
    def _validate_rule(self, rule: Rule, result: ValidationResult):
        """Validate individual rule"""
        if not rule.name or not rule.name.strip():
            result.add_error("Rule name cannot be empty")
        
        if len(rule.name) > 100:
            result.add_error(f"Rule name '{rule.name}' is too long (max 100 characters)")
        
        # Validate conditions
        if len(rule.conditions) == 0:
            result.add_error(f"Rule '{rule.name}' has no conditions")
        
        for i, condition in enumerate(rule.conditions):
            if not condition.region:
                result.add_error(f"Rule '{rule.name}' condition {i+1} has no region specified")
        
        # Validate actions
        if len(rule.actions) == 0:
            result.add_error(f"Rule '{rule.name}' has no actions")
        
        if len(rule.actions) > self.max_actions_per_rule:
            result.add_warning(f"Rule '{rule.name}' has many actions ({len(rule.actions)}) - consider splitting")
        
        # Validate execution settings
        if rule.max_retries < 0:
            result.add_error(f"Rule '{rule.name}' max_retries cannot be negative")
        
        if rule.retry_delay < 0:
            result.add_error(f"Rule '{rule.name}' retry_delay cannot be negative")
        
        if rule.max_retries > 10:
            result.add_warning(f"Rule '{rule.name}' has high retry count ({rule.max_retries})")
    
    def _validate_references(self, profile: AutomationProfile, result: ValidationResult):
        """Validate that all references point to existing regions"""
        region_names = {r.name for r in profile.regions}
        
        for rule in profile.rules:
            # Check condition references
            for condition in rule.conditions:
                if condition.region and condition.region not in region_names:
                    result.add_error(f"Rule '{rule.name}' condition references unknown region '{condition.region}'")
            
            # Check action references
            for action in rule.actions:
                if action.region and action.region not in region_names:
                    result.add_error(f"Rule '{rule.name}' action references unknown region '{action.region}'")
    
    def _validate_settings(self, profile: AutomationProfile, result: ValidationResult):
        """Validate profile settings"""
        settings = profile.settings
        
        if settings.monitoring_interval_seconds <= 0:
            result.add_error("Monitoring interval must be positive")
        
        if settings.monitoring_interval_seconds < 0.1:
            result.add_warning("Very short monitoring interval may impact performance")
        
        if settings.max_execution_time_seconds <= 0:
            result.add_error("Max execution time must be positive")
        
        if settings.template_match_threshold < 0 or settings.template_match_threshold > 1:
            result.add_error("Template match threshold must be between 0 and 1")
        
        if settings.ocr_confidence_threshold < 0 or settings.ocr_confidence_threshold > 100:
            result.add_error("OCR confidence threshold must be between 0 and 100")
        
        if settings.color_tolerance < 0 or settings.color_tolerance > 255:
            result.add_error("Color tolerance must be between 0 and 255")
    
    def _check_best_practices(self, profile: AutomationProfile, result: ValidationResult):
        """Check for best practices and provide recommendations"""
        # Check for descriptive names
        generic_names = ['test', 'temp', 'example', 'sample']
        if any(generic in profile.name.lower() for generic in generic_names):
            result.add_warning("Consider using a more descriptive profile name")
        
        # Check for tags
        if len(profile.tags) == 0:
            result.add_warning("Consider adding tags to help organize and find this profile")
        
        # Check for target application
        if not profile.target_application or not profile.target_application.strip():
            result.add_warning("Consider specifying the target application for better organization")
        
        # Check for region overlaps
        self._check_region_overlaps(profile, result)
        
        # Check for unused regions
        self._check_unused_regions(profile, result)
    
    def _check_region_overlaps(self, profile: AutomationProfile, result: ValidationResult):
        """Check for overlapping regions"""
        for i, region1 in enumerate(profile.regions):
            for j, region2 in enumerate(profile.regions[i+1:], i+1):
                if region1.overlaps_with(region2):
                    result.add_warning(f"Regions '{region1.name}' and '{region2.name}' overlap")
    
    def _check_unused_regions(self, profile: AutomationProfile, result: ValidationResult):
        """Check for regions that are not referenced by any rules"""
        region_names = {r.name for r in profile.regions}
        used_regions = set()
        
        for rule in profile.rules:
            for condition in rule.conditions:
                if condition.region:
                    used_regions.add(condition.region)
            for action in rule.actions:
                if action.region:
                    used_regions.add(action.region)
        
        unused_regions = region_names - used_regions
        for unused_region in unused_regions:
            result.add_warning(f"Region '{unused_region}' is defined but not used by any rules") 
   def _validate_conditions_and_actions(self, profile: AutomationProfile, result: ValidationResult):
        """Validate rule conditions and actions in detail"""
        for rule in profile.rules:
            rule_location = f"Rule '{rule.name}'"
            
            # Validate conditions
            for i, condition in enumerate(rule.conditions):
                condition_location = f"{rule_location}, Condition {i+1}"
                self._validate_condition(condition, result, condition_location)
            
            # Validate actions
            for i, action in enumerate(rule.actions):
                action_location = f"{rule_location}, Action {i+1}"
                self._validate_action(action, result, action_location)
    
    def _validate_condition(self, condition: Condition, result: ValidationResult, location: str):
        """Validate individual condition"""
        # Validate condition type
        if not isinstance(condition.condition_type, ConditionType):
            result.add_error('condition', "Invalid condition type", location,
                           suggestion="Use a valid ConditionType enum value")
        
        # Validate region reference
        if condition.condition_type in [ConditionType.VISUAL_MATCH, ConditionType.OCR_CONTAINS, 
                                      ConditionType.TEMPLATE_MATCH] and not condition.region_name:
            result.add_error('condition', "Visual/OCR conditions require a region", location,
                           suggestion="Specify a region for this condition")
        
        # Validate parameters based on condition type
        params = condition.parameters or {}
        
        if condition.condition_type == ConditionType.VISUAL_MATCH:
            self._validate_visual_match_params(params, result, location)
        elif condition.condition_type == ConditionType.OCR_CONTAINS:
            self._validate_ocr_params(params, result, location)
        elif condition.condition_type == ConditionType.TEMPLATE_MATCH:
            self._validate_template_params(params, result, location)
        elif condition.condition_type == ConditionType.SYSTEM_STATE:
            self._validate_system_state_params(params, result, location)
        elif condition.condition_type == ConditionType.TIME_BASED:
            self._validate_time_params(params, result, location)
    
    def _validate_action(self, action: Action, result: ValidationResult, location: str):
        """Validate individual action"""
        # Validate action type
        if not isinstance(action.action_type, ActionType):
            result.add_error('action', "Invalid action type", location,
                           suggestion="Use a valid ActionType enum value")
        
        # Validate target region for actions that need it
        if action.action_type in [ActionType.CLICK, ActionType.TYPE_TEXT] and not action.target_region:
            result.add_error('action', "Click/Type actions require a target region", location,
                           suggestion="Specify a target region for this action")
        
        # Validate parameters based on action type
        params = action.parameters or {}
        
        if action.action_type == ActionType.CLICK:
            self._validate_click_params(params, result, location)
        elif action.action_type == ActionType.TYPE_TEXT:
            self._validate_type_text_params(params, result, location)
        elif action.action_type == ActionType.WAIT:
            self._validate_wait_params(params, result, location)
        elif action.action_type == ActionType.ASK_USER:
            self._validate_ask_user_params(params, result, location)
        elif action.action_type == ActionType.RUN_COMMAND:
            self._validate_run_command_params(params, result, location)
    
    def _validate_visual_match_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate visual match condition parameters"""
        if 'template_path' not in params:
            result.add_error('condition', "Visual match requires template_path parameter", location)
        elif not params['template_path']:
            result.add_error('condition', "Template path cannot be empty", location)
        
        threshold = params.get('threshold', 0.8)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            result.add_error('condition', "Threshold must be a number between 0 and 1", location)
    
    def _validate_ocr_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate OCR condition parameters"""
        if 'text' not in params:
            result.add_error('condition', "OCR condition requires text parameter", location)
        elif not params['text'] or not params['text'].strip():
            result.add_error('condition', "OCR text cannot be empty", location)
        
        if len(params.get('text', '')) > 200:
            result.add_warning('condition', "OCR text is very long - may affect performance", location)
    
    def _validate_template_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate template match parameters"""
        if 'template_file' not in params:
            result.add_error('condition', "Template match requires template_file parameter", location)
        
        confidence = params.get('confidence', 0.8)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            result.add_error('condition', "Confidence must be a number between 0 and 1", location)
    
    def _validate_system_state_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate system state parameters"""
        valid_state_types = ['window_active', 'process_running', 'file_exists', 'network_connected']
        state_type = params.get('state_type')
        
        if not state_type:
            result.add_error('condition', "System state requires state_type parameter", location)
        elif state_type not in valid_state_types:
            result.add_error('condition', f"Invalid state_type. Valid types: {valid_state_types}", location)
        
        if 'state_value' not in params:
            result.add_error('condition', "System state requires state_value parameter", location)
    
    def _validate_time_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate time-based parameters"""
        valid_time_conditions = ['after_time', 'before_time', 'between_times', 'day_of_week']
        time_condition = params.get('time_condition')
        
        if not time_condition:
            result.add_error('condition', "Time condition requires time_condition parameter", location)
        elif time_condition not in valid_time_conditions:
            result.add_error('condition', f"Invalid time_condition. Valid types: {valid_time_conditions}", location)
        
        if 'time_value' not in params:
            result.add_error('condition', "Time condition requires time_value parameter", location)
    
    def _validate_click_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate click action parameters"""
        valid_click_types = ['left', 'right', 'double', 'middle']
        click_type = params.get('click_type', 'left')
        
        if click_type not in valid_click_types:
            result.add_error('action', f"Invalid click_type. Valid types: {valid_click_types}", location)
        
        # Validate offsets
        for offset_key in ['offset_x', 'offset_y']:
            if offset_key in params:
                offset = params[offset_key]
                if not isinstance(offset, int) or abs(offset) > 1000:
                    result.add_warning('action', f"Large {offset_key} offset may be inaccurate", location)
    
    def _validate_type_text_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate type text action parameters"""
        if 'text' not in params:
            result.add_error('action', "Type text action requires text parameter", location)
        elif not params['text']:
            result.add_warning('action', "Type text action has empty text", location)
        
        if len(params.get('text', '')) > 1000:
            result.add_warning('action', "Very long text may take time to type", location)
    
    def _validate_wait_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate wait action parameters"""
        duration = params.get('duration', 1.0)
        if not isinstance(duration, (int, float)) or duration < 0:
            result.add_error('action', "Wait duration must be a positive number", location)
        elif duration > 60:
            result.add_warning('action', "Very long wait duration", location)
        
        valid_wait_types = ['fixed', 'random', 'until_condition']
        wait_type = params.get('wait_type', 'fixed')
        if wait_type not in valid_wait_types:
            result.add_error('action', f"Invalid wait_type. Valid types: {valid_wait_types}", location)
    
    def _validate_ask_user_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate ask user action parameters"""
        if 'prompt' not in params:
            result.add_error('action', "Ask user action requires prompt parameter", location)
        elif not params['prompt'] or not params['prompt'].strip():
            result.add_error('action', "Ask user prompt cannot be empty", location)
        
        valid_input_types = ['text', 'yes_no', 'choice', 'file_path']
        input_type = params.get('input_type', 'text')
        if input_type not in valid_input_types:
            result.add_error('action', f"Invalid input_type. Valid types: {valid_input_types}", location)
    
    def _validate_run_command_params(self, params: Dict[str, Any], result: ValidationResult, location: str):
        """Validate run command action parameters"""
        if 'command' not in params:
            result.add_error('action', "Run command action requires command parameter", location)
        elif not params['command'] or not params['command'].strip():
            result.add_error('action', "Command cannot be empty", location)
        
        # Check for potentially dangerous commands
        dangerous_commands = ['rm -rf', 'del /f', 'format', 'shutdown', 'reboot']
        command = params.get('command', '').lower()
        for dangerous in dangerous_commands:
            if dangerous in command:
                result.add_warning('action', f"Potentially dangerous command detected: {dangerous}", location,
                                 suggestion="Ensure this command is safe to execute")
    
    def _validate_dependencies(self, profile: AutomationProfile, result: ValidationResult):
        """Validate dependencies between regions, rules, and variables"""
        region_names = {r.name for r in profile.regions}
        
        # Check region references in rules
        for rule in profile.rules:
            rule_location = f"Rule '{rule.name}'"
            
            # Check condition region references
            for i, condition in enumerate(rule.conditions):
                if condition.region_name and condition.region_name not in region_names:
                    result.add_error('rule', f"References unknown region '{condition.region_name}'",
                                   f"{rule_location}, Condition {i+1}",
                                   suggestion="Create the region or fix the reference")
            
            # Check action region references
            for i, action in enumerate(rule.actions):
                if action.target_region and action.target_region not in region_names:
                    result.add_error('rule', f"References unknown region '{action.target_region}'",
                                   f"{rule_location}, Action {i+1}",
                                   suggestion="Create the region or fix the reference")
        
        # Check for circular dependencies
        self._check_circular_dependencies(profile, result)
        
        # Check for unused regions
        self._check_unused_regions(profile, result)
    
    def _check_circular_dependencies(self, profile: AutomationProfile, result: ValidationResult):
        """Check for circular dependencies in rule execution"""
        # This is a simplified check - could be expanded for more complex dependency analysis
        rule_names = {rule.name for rule in profile.rules}
        
        for rule in profile.rules:
            # Check if rule actions might trigger other rules in a circular manner
            # This is a basic implementation - more sophisticated analysis could be added
            pass
    
    def _validate_execution_flow(self, profile: AutomationProfile, result: ValidationResult):
        """Validate the logical flow of rule execution"""
        enabled_rules = [rule for rule in profile.rules if rule.enabled]
        
        if not enabled_rules:
            result.add_warning('profile', "No enabled rules - profile will not execute any actions",
                             suggestion="Enable at least one rule")
            return
        
        # Check rule priorities
        priorities = [rule.priority for rule in enabled_rules]
        if len(set(priorities)) != len(priorities):
            result.add_warning('profile', "Multiple rules have the same priority",
                             suggestion="Assign unique priorities for predictable execution order")
        
        # Check for rules without conditions
        for rule in enabled_rules:
            if not rule.conditions:
                result.add_warning('rule', f"Rule '{rule.name}' has no conditions - will always execute",
                                 suggestion="Add conditions to control when the rule executes")
        
        # Check for rules without actions
        for rule in enabled_rules:
            if not rule.actions:
                result.add_error('rule', f"Rule '{rule.name}' has no actions - will do nothing",
                               suggestion="Add actions to make the rule useful")
    
    def _validate_template_compatibility(self, profile: AutomationProfile, result: ValidationResult):
        """Validate template compatibility and inheritance"""
        if profile.category in self.template_inheritance_rules:
            valid_targets = self.template_inheritance_rules[profile.category]
            
            # Check if target application matches category
            if profile.target_application:
                app_lower = profile.target_application.lower()
                if not any(target in app_lower for target in valid_targets):
                    result.add_info('profile', 
                                  f"Target application '{profile.target_application}' may not match category '{profile.category}'",
                                  suggestion=f"Consider using applications like: {', '.join(valid_targets)}")
        
        # Check for template-specific requirements
        if 'template' in profile.tags:
            if not profile.description:
                result.add_warning('profile', "Template profiles should have detailed descriptions",
                                 suggestion="Add a description explaining how to use this template")
    
    def _validate_security_concerns(self, profile: AutomationProfile, result: ValidationResult):
        """Check for potential security concerns"""
        for rule in profile.rules:
            for action in rule.actions:
                if action.action_type == ActionType.RUN_COMMAND:
                    command = action.parameters.get('command', '')
                    
                    # Check for shell injection risks
                    if any(char in command for char in ['|', '&', ';', '$(', '`']):
                        result.add_warning('action', "Command contains shell metacharacters",
                                         f"Rule '{rule.name}'",
                                         suggestion="Validate command safety and user input")
                    
                    # Check for network commands
                    network_commands = ['curl', 'wget', 'ssh', 'scp', 'ftp']
                    if any(cmd in command.lower() for cmd in network_commands):
                        result.add_info('action', "Command performs network operations",
                                      f"Rule '{rule.name}'",
                                      suggestion="Ensure network operations are intended and safe")
                
                elif action.action_type == ActionType.TYPE_TEXT:
                    text = action.parameters.get('text', '')
                    
                    # Check for potential password fields
                    if any(keyword in text.lower() for keyword in ['password', 'passwd', 'secret', 'key']):
                        result.add_warning('action', "Text may contain sensitive information",
                                         f"Rule '{rule.name}'",
                                         suggestion="Avoid hardcoding sensitive data")
    
    def _check_performance_concerns(self, profile: AutomationProfile, result: ValidationResult):
        """Check for potential performance issues"""
        # Check monitoring interval
        if profile.settings.monitoring_interval_seconds < 0.5:
            result.add_warning('settings', "Very short monitoring interval may impact performance",
                             suggestion="Consider using 0.5 seconds or longer")
        
        # Check for excessive regions
        if len(profile.regions) > 20:
            result.add_info('profile', f"Profile has many regions ({len(profile.regions)})",
                          suggestion="Consider grouping related regions or splitting the profile")
        
        # Check for excessive rules
        if len(profile.rules) > 10:
            result.add_info('profile', f"Profile has many rules ({len(profile.rules)})",
                          suggestion="Consider splitting complex profiles into smaller ones")
        
        # Check for large regions
        for region in profile.regions:
            area = region.width * region.height
            if area > 1000000:  # 1 million pixels
                result.add_warning('region', f"Region '{region.name}' is very large",
                                 suggestion="Large regions may slow down image processing")
    
    def _suggest_improvements(self, profile: AutomationProfile, result: ValidationResult):
        """Suggest improvements and optimizations"""
        # Suggest adding error handling
        has_error_handling = any(
            action.action_type == ActionType.ASK_USER 
            for rule in profile.rules 
            for action in rule.actions
        )
        
        if not has_error_handling:
            result.add_info('profile', "Consider adding error handling with user prompts",
                          suggestion="Add 'Ask User' actions to handle unexpected situations")
        
        # Suggest using tags for organization
        if len(profile.tags) < 2:
            result.add_info('profile', "Consider adding more tags for better organization",
                          suggestion="Add tags like 'productivity', 'daily', 'work', etc.")
        
        # Suggest region descriptions
        regions_without_descriptions = [r for r in profile.regions if not r.description]
        if regions_without_descriptions:
            result.add_info('profile', f"{len(regions_without_descriptions)} regions lack descriptions",
                          suggestion="Add descriptions to help understand region purposes")
    
    def validate_profile_compatibility(self, profile1: AutomationProfile, profile2: AutomationProfile) -> ValidationResult:
        """Check compatibility between two profiles for merging or inheritance"""
        result = ValidationResult(
            is_valid=True,
            issues=[],
            validation_time=datetime.now(),
            profile_name=f"{profile1.name} + {profile2.name}"
        )
        
        # Check category compatibility
        if profile1.category != profile2.category:
            result.add_warning('compatibility', 
                             f"Different categories: '{profile1.category}' vs '{profile2.category}'",
                             suggestion="Profiles with different categories may not work well together")
        
        # Check target application compatibility
        if profile1.target_application != profile2.target_application:
            result.add_warning('compatibility',
                             f"Different target applications: '{profile1.target_application}' vs '{profile2.target_application}'",
                             suggestion="Profiles targeting different applications may conflict")
        
        # Check for region name conflicts
        regions1 = {r.name for r in profile1.regions}
        regions2 = {r.name for r in profile2.regions}
        conflicts = regions1.intersection(regions2)
        
        if conflicts:
            result.add_error('compatibility', f"Region name conflicts: {', '.join(conflicts)}",
                           suggestion="Rename conflicting regions before merging")
        
        # Check for rule name conflicts
        rules1 = {r.name for r in profile1.rules}
        rules2 = {r.name for r in profile2.rules}
        rule_conflicts = rules1.intersection(rules2)
        
        if rule_conflicts:
            result.add_error('compatibility', f"Rule name conflicts: {', '.join(rule_conflicts)}",
                           suggestion="Rename conflicting rules before merging")
        
        return result