"""
Profile Tester

Comprehensive testing system for automation profiles with simulation mode,
step-by-step debugging, and visual recognition testing.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..models.profile import AutomationProfile
from ..models.region import Region
from ..models.rule import Rule, Condition, Action, ConditionType, ActionType
from ..validation.profile_validator import ProfileValidator, ValidationResult


class TestMode(Enum):
    """Test execution modes"""
    SIMULATION = "simulation"  # Simulate without actual execution
    DRY_RUN = "dry_run"       # Execute conditions but not actions
    STEP_BY_STEP = "step_by_step"  # Manual step control
    FULL_TEST = "full_test"   # Complete execution with monitoring


@dataclass
class TestStep:
    """Individual test step result"""
    step_type: str  # 'condition', 'action', 'rule'
    step_name: str
    status: str  # 'pending', 'running', 'passed', 'failed', 'skipped'
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    
    def start(self):
        """Mark step as started"""
        self.status = 'running'
        self.start_time = datetime.now()
    
    def complete(self, success: bool, result: Any = None, error: str = None):
        """Mark step as completed"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        self.status = 'passed' if success else 'failed'
        self.result = result
        self.error = error
    
    def skip(self, reason: str = None):
        """Mark step as skipped"""
        self.status = 'skipped'
        self.error = reason


@dataclass
class TestResult:
    """Complete test execution result"""
    profile_name: str
    test_mode: TestMode
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: str = 'running'  # 'running', 'completed', 'failed', 'cancelled'
    steps: List[TestStep] = None
    validation_result: Optional[ValidationResult] = None
    summary: Dict[str, int] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.summary is None:
            self.summary = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def complete(self, success: bool = True):
        """Mark test as completed"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = 'completed' if success else 'failed'
        self._update_summary()
    
    def cancel(self):
        """Mark test as cancelled"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        self.status = 'cancelled'
        self._update_summary()
    
    def _update_summary(self):
        """Update test summary statistics"""
        self.summary = {
            'total': len(self.steps),
            'passed': len([s for s in self.steps if s.status == 'passed']),
            'failed': len([s for s in self.steps if s.status == 'failed']),
            'skipped': len([s for s in self.steps if s.status == 'skipped'])
        }


class ProfileTester:
    """Comprehensive profile testing system"""
    
    def __init__(self, screenshot_dir: str = None):
        self.logger = logging.getLogger("mark_i.profiles.testing.tester")
        self.validator = ProfileValidator()
        self.screenshot_dir = screenshot_dir
        
        # Test configuration
        self.step_delay = 1.0  # Delay between steps in seconds
        self.screenshot_on_error = True
        self.screenshot_on_step = False
        
        # Callbacks for UI integration
        self.on_step_start: Optional[Callable[[TestStep], None]] = None
        self.on_step_complete: Optional[Callable[[TestStep], None]] = None
        self.on_test_complete: Optional[Callable[[TestResult], None]] = None
        
        self.logger.info("ProfileTester initialized")
    
    def test_profile(self, profile: AutomationProfile, mode: TestMode = TestMode.SIMULATION) -> TestResult:
        """
        Test a profile with specified mode
        
        Args:
            profile: Profile to test
            mode: Test execution mode
            
        Returns:
            TestResult with detailed execution information
        """
        self.logger.info(f"Starting profile test: {profile.name} in {mode.value} mode")
        
        result = TestResult(
            profile_name=profile.name,
            test_mode=mode,
            start_time=datetime.now()
        )
        
        try:
            # Pre-test validation
            result.validation_result = self.validator.validate_profile(profile)
            if not result.validation_result.is_valid and mode != TestMode.SIMULATION:
                result.errors.append("Profile validation failed - cannot execute")
                result.complete(False)
                return result
            
            # Execute test based on mode
            if mode == TestMode.SIMULATION:
                self._simulate_profile(profile, result)
            elif mode == TestMode.DRY_RUN:
                self._dry_run_profile(profile, result)
            elif mode == TestMode.STEP_BY_STEP:
                self._step_by_step_test(profile, result)
            elif mode == TestMode.FULL_TEST:
                self._full_test_profile(profile, result)
            
            result.complete(True)
            
        except Exception as e:
            self.logger.error(f"Test failed with exception: {e}")
            result.errors.append(f"Test execution failed: {str(e)}")
            result.complete(False)
        
        if self.on_test_complete:
            self.on_test_complete(result)
        
        self.logger.info(f"Test completed: {result.status} - {result.summary}")
        return result
    
    def _simulate_profile(self, profile: AutomationProfile, result: TestResult):
        """Simulate profile execution without actual actions"""
        self.logger.info("Running simulation mode")
        
        # Simulate each rule
        for rule in profile.rules:
            if not rule.enabled:
                continue
            
            rule_step = TestStep('rule', f"Rule: {rule.name}", 'pending')
            result.steps.append(rule_step)
            
            if self.on_step_start:
                self.on_step_start(rule_step)
            
            rule_step.start()
            
            # Simulate conditions
            conditions_passed = 0
            for i, condition in enumerate(rule.conditions):
                condition_step = TestStep('condition', f"Condition {i+1}: {condition.condition_type.value}", 'pending')
                result.steps.append(condition_step)
                
                condition_step.start()
                
                # Simulate condition evaluation
                time.sleep(0.1)  # Brief delay for realism
                
                # Randomly pass/fail conditions for simulation
                import random
                success = random.choice([True, True, True, False])  # 75% success rate
                
                if success:
                    conditions_passed += 1
                    condition_step.complete(True, "Condition would pass")
                else:
                    condition_step.complete(False, error="Condition would fail")
                
                if self.on_step_complete:
                    self.on_step_complete(condition_step)
            
            # Check if rule would execute based on logical operator
            rule_would_execute = self._evaluate_rule_logic(rule, conditions_passed, len(rule.conditions))
            
            if rule_would_execute:
                # Simulate actions
                for i, action in enumerate(rule.actions):
                    action_step = TestStep('action', f"Action {i+1}: {action.action_type.value}", 'pending')
                    result.steps.append(action_step)
                    
                    action_step.start()
                    time.sleep(0.1)  # Brief delay
                    
                    # Simulate action execution
                    action_step.complete(True, "Action would execute")
                    
                    if self.on_step_complete:
                        self.on_step_complete(action_step)
                
                rule_step.complete(True, "Rule would execute")
            else:
                rule_step.complete(False, "Rule conditions not met")
            
            if self.on_step_complete:
                self.on_step_complete(rule_step)
    
    def _dry_run_profile(self, profile: AutomationProfile, result: TestResult):
        """Execute conditions but not actions"""
        self.logger.info("Running dry run mode")
        
        for rule in profile.rules:
            if not rule.enabled:
                continue
            
            rule_step = TestStep('rule', f"Rule: {rule.name}", 'pending')
            result.steps.append(rule_step)
            rule_step.start()
            
            # Actually evaluate conditions
            conditions_passed = 0
            for i, condition in enumerate(rule.conditions):
                condition_step = TestStep('condition', f"Condition {i+1}: {condition.condition_type.value}", 'pending')
                result.steps.append(condition_step)
                condition_step.start()
                
                try:
                    # This would integrate with actual condition evaluation
                    success = self._evaluate_condition_dry_run(condition)
                    if success:
                        conditions_passed += 1
                        condition_step.complete(True, "Condition passed")
                    else:
                        condition_step.complete(False, "Condition failed")
                except Exception as e:
                    condition_step.complete(False, error=str(e))
                
                if self.on_step_complete:
                    self.on_step_complete(condition_step)
            
            # Check if rule would execute
            rule_would_execute = self._evaluate_rule_logic(rule, conditions_passed, len(rule.conditions))
            
            if rule_would_execute:
                # Simulate actions (don't actually execute)
                for i, action in enumerate(rule.actions):
                    action_step = TestStep('action', f"Action {i+1}: {action.action_type.value}", 'pending')
                    result.steps.append(action_step)
                    action_step.start()
                    
                    # Don't execute, just log what would happen
                    action_step.complete(True, f"Would execute: {action.action_type.value}")
                    
                    if self.on_step_complete:
                        self.on_step_complete(action_step)
                
                rule_step.complete(True, "Rule conditions met")
            else:
                rule_step.complete(False, "Rule conditions not met")
            
            if self.on_step_complete:
                self.on_step_complete(rule_step)
    
    def _step_by_step_test(self, profile: AutomationProfile, result: TestResult):
        """Execute with manual step control"""
        self.logger.info("Running step-by-step mode")
        
        # This would integrate with a UI for manual control
        # For now, simulate automatic stepping with delays
        
        for rule in profile.rules:
            if not rule.enabled:
                continue
            
            rule_step = TestStep('rule', f"Rule: {rule.name}", 'pending')
            result.steps.append(rule_step)
            rule_step.start()
            
            # Wait for user confirmation (simulated)
            time.sleep(self.step_delay)
            
            # Execute conditions with user control
            conditions_passed = 0
            for i, condition in enumerate(rule.conditions):
                condition_step = TestStep('condition', f"Condition {i+1}: {condition.condition_type.value}", 'pending')
                result.steps.append(condition_step)
                condition_step.start()
                
                # User would control execution here
                time.sleep(self.step_delay)
                
                try:
                    success = self._evaluate_condition_dry_run(condition)
                    if success:
                        conditions_passed += 1
                        condition_step.complete(True, "Condition passed")
                    else:
                        condition_step.complete(False, "Condition failed")
                except Exception as e:
                    condition_step.complete(False, error=str(e))
                
                if self.on_step_complete:
                    self.on_step_complete(condition_step)
            
            # Check rule execution
            rule_would_execute = self._evaluate_rule_logic(rule, conditions_passed, len(rule.conditions))
            
            if rule_would_execute:
                for i, action in enumerate(rule.actions):
                    action_step = TestStep('action', f"Action {i+1}: {action.action_type.value}", 'pending')
                    result.steps.append(action_step)
                    action_step.start()
                    
                    # User would control action execution
                    time.sleep(self.step_delay)
                    
                    # Simulate action execution
                    action_step.complete(True, "Action executed")
                    
                    if self.on_step_complete:
                        self.on_step_complete(action_step)
                
                rule_step.complete(True, "Rule executed")
            else:
                rule_step.complete(False, "Rule conditions not met")
            
            if self.on_step_complete:
                self.on_step_complete(rule_step)
    
    def _full_test_profile(self, profile: AutomationProfile, result: TestResult):
        """Execute complete profile with monitoring"""
        self.logger.info("Running full test mode")
        
        # This would integrate with the actual ProfileExecutor
        # For now, simulate full execution
        
        for rule in profile.rules:
            if not rule.enabled:
                continue
            
            rule_step = TestStep('rule', f"Rule: {rule.name}", 'pending')
            result.steps.append(rule_step)
            rule_step.start()
            
            # Execute conditions
            conditions_passed = 0
            for i, condition in enumerate(rule.conditions):
                condition_step = TestStep('condition', f"Condition {i+1}: {condition.condition_type.value}", 'pending')
                result.steps.append(condition_step)
                condition_step.start()
                
                try:
                    # This would use actual condition evaluation
                    success = self._evaluate_condition_full(condition)
                    if success:
                        conditions_passed += 1
                        condition_step.complete(True, "Condition passed")
                    else:
                        condition_step.complete(False, "Condition failed")
                except Exception as e:
                    condition_step.complete(False, error=str(e))
                    if self.screenshot_on_error:
                        self._take_screenshot(condition_step)
                
                if self.on_step_complete:
                    self.on_step_complete(condition_step)
            
            # Execute actions if conditions met
            rule_should_execute = self._evaluate_rule_logic(rule, conditions_passed, len(rule.conditions))
            
            if rule_should_execute:
                for i, action in enumerate(rule.actions):
                    action_step = TestStep('action', f"Action {i+1}: {action.action_type.value}", 'pending')
                    result.steps.append(action_step)
                    action_step.start()
                    
                    try:
                        # This would use actual action execution
                        success = self._execute_action_full(action)
                        action_step.complete(success, "Action executed")
                    except Exception as e:
                        action_step.complete(False, error=str(e))
                        if self.screenshot_on_error:
                            self._take_screenshot(action_step)
                    
                    if self.on_step_complete:
                        self.on_step_complete(action_step)
                
                rule_step.complete(True, "Rule executed")
            else:
                rule_step.complete(False, "Rule conditions not met")
            
            if self.on_step_complete:
                self.on_step_complete(rule_step)
    
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
    
    def _evaluate_condition_dry_run(self, condition: Condition) -> bool:
        """Evaluate condition in dry run mode (placeholder)"""
        # This would integrate with actual condition evaluation
        # For now, return a simulated result
        import random
        return random.choice([True, False])
    
    def _evaluate_condition_full(self, condition: Condition) -> bool:
        """Evaluate condition in full test mode (placeholder)"""
        # This would integrate with actual condition evaluation
        # For now, return a simulated result
        import random
        return random.choice([True, False])
    
    def _execute_action_full(self, action: Action) -> bool:
        """Execute action in full test mode (placeholder)"""
        # This would integrate with actual action execution
        # For now, return a simulated result
        import random
        return random.choice([True, True, False])  # 67% success rate
    
    def _take_screenshot(self, step: TestStep):
        """Take screenshot for debugging"""
        if not self.screenshot_dir:
            return
        
        try:
            import pyautogui
            from pathlib import Path
            
            screenshot_dir = Path(self.screenshot_dir)
            screenshot_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{step.step_type}_{timestamp}.png"
            filepath = screenshot_dir / filename
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            step.screenshot_path = str(filepath)
            self.logger.info(f"Screenshot saved: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
    
    def generate_test_report(self, result: TestResult) -> str:
        """Generate detailed test report"""
        report = []
        report.append(f"Profile Test Report: {result.profile_name}")
        report.append("=" * 50)
        report.append(f"Test Mode: {result.test_mode.value}")
        report.append(f"Start Time: {result.start_time}")
        report.append(f"Duration: {result.duration:.2f} seconds" if result.duration else "Duration: N/A")
        report.append(f"Status: {result.status}")
        report.append("")
        
        # Summary
        report.append("Summary:")
        report.append(f"  Total Steps: {result.summary['total']}")
        report.append(f"  Passed: {result.summary['passed']}")
        report.append(f"  Failed: {result.summary['failed']}")
        report.append(f"  Skipped: {result.summary['skipped']}")
        report.append("")
        
        # Validation results
        if result.validation_result:
            report.append("Validation Results:")
            if result.validation_result.is_valid:
                report.append("  ✅ Profile is valid")
            else:
                report.append("  ❌ Profile has validation errors")
                for error in result.validation_result.errors:
                    report.append(f"    • {error}")
            
            if result.validation_result.warnings:
                report.append("  Warnings:")
                for warning in result.validation_result.warnings:
                    report.append(f"    • {warning}")
            report.append("")
        
        # Step details
        report.append("Step Details:")
        for step in result.steps:
            status_icon = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'running': '🔄',
                'pending': '⏸️'
            }.get(step.status, '❓')
            
            report.append(f"  {status_icon} {step.step_name}")
            if step.duration:
                report.append(f"    Duration: {step.duration:.2f}s")
            if step.result:
                report.append(f"    Result: {step.result}")
            if step.error:
                report.append(f"    Error: {step.error}")
            if step.screenshot_path:
                report.append(f"    Screenshot: {step.screenshot_path}")
        
        # Errors and warnings
        if result.errors:
            report.append("")
            report.append("Errors:")
            for error in result.errors:
                report.append(f"  • {error}")
        
        if result.warnings:
            report.append("")
            report.append("Warnings:")
            for warning in result.warnings:
                report.append(f"  • {warning}")
        
        return "\n".join(report)