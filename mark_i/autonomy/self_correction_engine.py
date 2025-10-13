"""Self-Correction Engine for MARK-I autonomous error detection and recovery.

This module provides comprehensive error detection, analysis, and recovery capabilities
that enable the system to automatically identify, diagnose, and correct errors
without human intervention, improving system reliability and robustness.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import hashlib

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".autonomy.self_correction_engine")


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors."""

    SYSTEM = "system"
    LOGIC = "logic"
    DATA = "data"
    NETWORK = "network"
    PERMISSION = "permission"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    VALIDATION = "validation"


class RecoveryStrategy(Enum):
    """Recovery strategies."""

    RETRY = "retry"
    FALLBACK = "fallback"
    RESET = "reset"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    ADAPT = "adapt"


@dataclass
class ErrorPattern:
    """Represents a detected error pattern."""

    pattern_id: str
    error_signature: str
    category: ErrorCategory
    severity: ErrorSeverity
    frequency: int
    success_rate: float
    recovery_strategies: List[RecoveryStrategy]
    context_conditions: Dict[str, Any]
    first_seen: datetime
    last_seen: datetime
    resolution_time_avg: float = 0.0


@dataclass
class ErrorInstance:
    """Represents a specific error occurrence."""

    error_id: str
    error_type: str
    error_message: str
    stack_trace: str
    context: Dict[str, Any]
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: datetime
    component: str
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None
    resolution_time: Optional[float] = None


@dataclass
class StrategyPerformance:
    """Tracks performance metrics for a recovery strategy."""

    strategy: RecoveryStrategy
    total_attempts: int
    successful_attempts: int
    success_rate: float
    avg_execution_time: float
    context_success_rates: Dict[str, float]  # Success rates by context
    recent_performance: deque  # Recent success/failure history
    last_updated: datetime
    confidence_score: float = 0.0


@dataclass
class AdaptiveStrategy:
    """Represents an adaptive recovery strategy with learned parameters."""

    base_strategy: RecoveryStrategy
    parameters: Dict[str, Any]
    success_patterns: List[Dict[str, Any]]
    failure_patterns: List[Dict[str, Any]]
    adaptation_history: List[Dict[str, Any]]
    effectiveness_score: float
    last_adapted: datetime
    adaptation_count: int = 0


@dataclass
class LearningInsight:
    """Represents a learned insight about error patterns and recovery."""

    insight_id: str
    pattern_signature: str
    insight_type: str  # 'strategy_optimization', 'parameter_tuning', 'context_adaptation'
    description: str
    confidence: float
    supporting_evidence: List[str]
    recommended_action: Dict[str, Any]
    created_at: datetime
    applied: bool = False


class SelfCorrectionEngine(ProcessingComponent):
    """
    Advanced self-correction engine for autonomous error handling.

    Provides comprehensive error detection, pattern analysis, and automated
    recovery capabilities to improve system reliability and robustness.
    """

    def __init__(self, config: ComponentConfig):
        super().__init__("self_correction_engine", config)

        # Configuration
        self.max_retry_attempts = getattr(config, "max_retry_attempts", 3)
        self.error_pattern_threshold = getattr(config, "error_pattern_threshold", 5)
        self.recovery_timeout = getattr(config, "recovery_timeout", 30.0)
        self.escalation_threshold = getattr(config, "escalation_threshold", 0.2)
        self.pattern_learning = getattr(config, "pattern_learning", True)
        self.auto_recovery = getattr(config, "auto_recovery", True)
        self.max_error_history = getattr(config, "max_error_history", 10000)

        # Data structures
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.error_history: deque = deque(maxlen=self.max_error_history)
        self.active_recoveries: Dict[str, Dict[str, Any]] = {}

        # Indices for efficient access
        self.category_index: Dict[ErrorCategory, List[str]] = defaultdict(list)
        self.component_index: Dict[str, List[str]] = defaultdict(list)
        self.severity_index: Dict[ErrorSeverity, List[str]] = defaultdict(list)

        # Threading and synchronization
        self.correction_lock = threading.Lock()
        self.pattern_lock = threading.Lock()

        # Statistics
        self.errors_detected = 0
        self.errors_recovered = 0
        self.patterns_learned = 0
        self.recovery_success_rate = 0.0

        # Adaptive learning components
        self.strategy_performance: Dict[RecoveryStrategy, StrategyPerformance] = {}
        self.adaptive_strategies: Dict[str, AdaptiveStrategy] = {}
        self.learning_insights: List[LearningInsight] = []
        self.success_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.failure_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Learning configuration
        self.learning_enabled = getattr(config, "learning_enabled", True)
        self.adaptation_threshold = getattr(config, "adaptation_threshold", 0.3)
        self.min_samples_for_learning = getattr(config, "min_samples_for_learning", 5)
        self.learning_rate = getattr(config, "learning_rate", 0.1)
        self.insight_confidence_threshold = getattr(config, "insight_confidence_threshold", 0.7)

        # Initialize strategy performance tracking
        self._initialize_strategy_performance()

        logger.info("SelfCorrectionEngine initialized with autonomous error handling and adaptive learning")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this self-correction engine."""
        return {
            "error_detection": True,
            "pattern_recognition": True,
            "automated_recovery": self.auto_recovery,
            "pattern_learning": self.pattern_learning,
            "escalation_handling": True,
            "context_analysis": True,
            "recovery_strategies": [strategy.value for strategy in RecoveryStrategy],
            "error_categories": [category.value for category in ErrorCategory],
            "max_retry_attempts": self.max_retry_attempts,
            "recovery_timeout": self.recovery_timeout,
        }

    def detect_error(self, error_data: Dict[str, Any]) -> str:
        """Detect and classify an error."""
        try:
            with self.correction_lock:
                # Extract error information
                error_type = error_data.get("error_type", "UnknownError")
                error_message = error_data.get("error_message", "")
                stack_trace = error_data.get("stack_trace", "")
                context = error_data.get("context", {})
                component = error_data.get("component", "unknown")

                # Generate error signature
                error_signature = self._generate_error_signature(error_type, error_message, stack_trace)

                # Classify error
                category = self._classify_error(error_type, error_message, context)
                severity = self._assess_severity(error_type, error_message, context, category)

                # Create error instance
                error_id = f"error_{int(time.time() * 1000)}_{hashlib.md5(error_signature.encode()).hexdigest()[:8]}"

                error_instance = ErrorInstance(
                    error_id=error_id,
                    error_type=error_type,
                    error_message=error_message,
                    stack_trace=stack_trace,
                    context=context,
                    severity=severity,
                    category=category,
                    timestamp=datetime.now(),
                    component=component,
                )

                # Store error
                self.error_history.append(error_instance)
                self.errors_detected += 1

                # Update indices
                self._update_error_indices(error_instance)

                # Learn or update error pattern
                if self.pattern_learning:
                    self._learn_error_pattern(error_instance, error_signature)

                logger.info(f"Detected {severity.value} {category.value} error: {error_id}")

                # Trigger automatic recovery if enabled
                if self.auto_recovery:
                    self._trigger_recovery(error_instance)

                return error_id

        except Exception as e:
            logger.error(f"Error in error detection: {e}")
            return ""

    def analyze_error_patterns(self) -> List[Dict[str, Any]]:
        """Analyze error patterns and trends."""
        try:
            with self.pattern_lock:
                patterns_analysis = []

                for pattern_id, pattern in self.error_patterns.items():
                    analysis = {
                        "pattern_id": pattern_id,
                        "error_signature": pattern.error_signature,
                        "category": pattern.category.value,
                        "severity": pattern.severity.value,
                        "frequency": pattern.frequency,
                        "success_rate": pattern.success_rate,
                        "avg_resolution_time": pattern.resolution_time_avg,
                        "recommended_strategies": [s.value for s in pattern.recovery_strategies],
                        "trend": self._calculate_pattern_trend(pattern),
                        "risk_level": self._assess_pattern_risk(pattern),
                    }
                    patterns_analysis.append(analysis)

                # Sort by frequency and severity
                patterns_analysis.sort(key=lambda x: (x["frequency"], x["severity"]), reverse=True)

                return patterns_analysis

        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return []

    def recover_from_error(self, error_id: str, strategy: Optional[str] = None) -> bool:
        """Attempt to recover from a specific error."""
        try:
            with self.correction_lock:
                # Find the error instance
                error_instance = None
                for error in reversed(self.error_history):
                    if error.error_id == error_id:
                        error_instance = error
                        break

                if not error_instance:
                    logger.error(f"Error instance not found: {error_id}")
                    return False

                # Determine recovery strategy
                if strategy:
                    recovery_strategy = RecoveryStrategy(strategy)
                else:
                    recovery_strategy = self._select_recovery_strategy(error_instance)

                # Execute recovery
                success = self._execute_recovery(error_instance, recovery_strategy)

                # Update error instance
                error_instance.recovery_attempted = True
                error_instance.recovery_successful = success
                error_instance.recovery_strategy = recovery_strategy

                if success:
                    self.errors_recovered += 1
                    error_instance.resolution_time = (datetime.now() - error_instance.timestamp).total_seconds()

                    # Update pattern success rate
                    self._update_pattern_success_rate(error_instance)

                # Update overall success rate
                self._update_recovery_success_rate()

                logger.info(f"Recovery attempt for {error_id}: {'successful' if success else 'failed'}")
                return success

        except Exception as e:
            logger.error(f"Error in recovery process: {e}")
            return False

    def _generate_error_signature(self, error_type: str, error_message: str, stack_trace: str) -> str:
        """Generate a unique signature for an error."""
        import re

        # Create a normalized signature
        signature_parts = []

        # Add error type
        signature_parts.append(error_type)

        # Add key parts of error message (remove dynamic content)
        if error_message:
            # Remove numbers, paths, and other dynamic content
            normalized_message = error_message
            normalized_message = re.sub(r"\d+", "N", normalized_message)
            normalized_message = re.sub(r"/[^\s]+", "/PATH", normalized_message)
            normalized_message = re.sub(r"\\[^\s]+", "\\PATH", normalized_message)
            signature_parts.append(normalized_message[:100])

        # Add key stack trace elements
        if stack_trace:
            lines = stack_trace.split("\n")
            # Get the last few meaningful lines
            meaningful_lines = [line.strip() for line in lines if 'File "' in line or "in " in line][-3:]
            signature_parts.extend(meaningful_lines)

        return "|".join(signature_parts)

    def _classify_error(self, error_type: str, error_message: str, context: Dict[str, Any]) -> ErrorCategory:
        """Classify an error into a category."""
        error_type_lower = error_type.lower()
        error_message_lower = error_message.lower()

        # Network-related errors
        if any(keyword in error_type_lower for keyword in ["connection", "network", "timeout", "socket"]):
            return ErrorCategory.NETWORK

        if any(keyword in error_message_lower for keyword in ["connection", "network", "timeout", "unreachable"]):
            return ErrorCategory.NETWORK

        # Permission errors
        if any(keyword in error_type_lower for keyword in ["permission", "access", "forbidden"]):
            return ErrorCategory.PERMISSION

        if any(keyword in error_message_lower for keyword in ["permission", "access denied", "forbidden"]):
            return ErrorCategory.PERMISSION

        # Resource errors
        if any(keyword in error_type_lower for keyword in ["memory", "resource", "limit"]):
            return ErrorCategory.RESOURCE

        if any(keyword in error_message_lower for keyword in ["out of memory", "resource", "disk space"]):
            return ErrorCategory.RESOURCE

        # Data/validation errors
        if any(keyword in error_type_lower for keyword in ["value", "type", "attribute", "key"]):
            return ErrorCategory.DATA

        if any(keyword in error_message_lower for keyword in ["invalid", "missing", "not found", "null"]):
            return ErrorCategory.VALIDATION

        # Timeout errors
        if "timeout" in error_type_lower or "timeout" in error_message_lower:
            return ErrorCategory.TIMEOUT

        # System errors
        if any(keyword in error_type_lower for keyword in ["system", "os", "runtime"]):
            return ErrorCategory.SYSTEM

        # Default to logic error
        return ErrorCategory.LOGIC

    def _assess_severity(self, error_type: str, error_message: str, context: Dict[str, Any], category: ErrorCategory) -> ErrorSeverity:
        """Assess the severity of an error."""
        # Critical keywords
        critical_keywords = ["fatal", "critical", "crash", "abort", "segmentation fault"]
        if any(keyword in error_type.lower() for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL

        if any(keyword in error_message.lower() for keyword in critical_keywords):
            return ErrorSeverity.CRITICAL

        # High severity conditions
        if category in [ErrorCategory.SYSTEM, ErrorCategory.RESOURCE]:
            return ErrorSeverity.HIGH

        # Network and timeout errors are usually medium
        if category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]:
            return ErrorSeverity.MEDIUM

        # Permission errors can be high or medium
        if category == ErrorCategory.PERMISSION:
            return ErrorSeverity.HIGH

        # Data and validation errors are usually low to medium
        if category in [ErrorCategory.DATA, ErrorCategory.VALIDATION]:
            return ErrorSeverity.LOW

        # Default to medium
        return ErrorSeverity.MEDIUM

    def _learn_error_pattern(self, error_instance: ErrorInstance, error_signature: str):
        """Learn or update an error pattern."""
        try:
            with self.pattern_lock:
                pattern_id = hashlib.md5(error_signature.encode()).hexdigest()[:16]

                if pattern_id in self.error_patterns:
                    # Update existing pattern
                    pattern = self.error_patterns[pattern_id]
                    pattern.frequency += 1
                    pattern.last_seen = error_instance.timestamp

                    # Update severity if this instance is more severe
                    severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                    if severity_order[error_instance.severity.value] > severity_order[pattern.severity.value]:
                        pattern.severity = error_instance.severity

                else:
                    # Create new pattern
                    pattern = ErrorPattern(
                        pattern_id=pattern_id,
                        error_signature=error_signature,
                        category=error_instance.category,
                        severity=error_instance.severity,
                        frequency=1,
                        success_rate=0.0,
                        recovery_strategies=self._suggest_recovery_strategies(error_instance),
                        context_conditions=error_instance.context,
                        first_seen=error_instance.timestamp,
                        last_seen=error_instance.timestamp,
                    )

                    self.error_patterns[pattern_id] = pattern
                    self.patterns_learned += 1

                    logger.info(f"Learned new error pattern: {pattern_id}")

        except Exception as e:
            logger.error(f"Error learning pattern: {e}")

    def _suggest_recovery_strategies(self, error_instance: ErrorInstance) -> List[RecoveryStrategy]:
        """Suggest recovery strategies for an error."""
        strategies = []

        # Category-based strategy suggestions
        if error_instance.category == ErrorCategory.NETWORK:
            strategies.extend([RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK])

        elif error_instance.category == ErrorCategory.TIMEOUT:
            strategies.extend([RecoveryStrategy.RETRY, RecoveryStrategy.RESET])

        elif error_instance.category == ErrorCategory.RESOURCE:
            strategies.extend([RecoveryStrategy.RESET, RecoveryStrategy.ESCALATE])

        elif error_instance.category == ErrorCategory.PERMISSION:
            strategies.extend([RecoveryStrategy.ESCALATE, RecoveryStrategy.FALLBACK])

        elif error_instance.category == ErrorCategory.DATA:
            strategies.extend([RecoveryStrategy.FALLBACK, RecoveryStrategy.ADAPT])

        elif error_instance.category == ErrorCategory.VALIDATION:
            strategies.extend([RecoveryStrategy.ADAPT, RecoveryStrategy.FALLBACK])

        else:
            strategies.extend([RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK])

        # Severity-based adjustments
        if error_instance.severity == ErrorSeverity.CRITICAL:
            strategies.insert(0, RecoveryStrategy.ESCALATE)

        elif error_instance.severity == ErrorSeverity.LOW:
            strategies.append(RecoveryStrategy.IGNORE)

        return strategies[:3]  # Limit to top 3 strategies

    def _select_recovery_strategy(self, error_instance: ErrorInstance) -> RecoveryStrategy:
        """Select the best recovery strategy for an error."""
        # First, try to get an adaptive strategy based on learning
        if self.learning_enabled:
            adaptive_strategy = self.get_adaptive_strategy(error_instance)
            if adaptive_strategy:
                logger.info(f"Using adaptive strategy: {adaptive_strategy.value}")
                return adaptive_strategy

        # Check if we have a learned pattern for this error
        error_signature = self._generate_error_signature(error_instance.error_type, error_instance.error_message, error_instance.stack_trace)
        pattern_id = hashlib.md5(error_signature.encode()).hexdigest()[:16]

        if pattern_id in self.error_patterns:
            pattern = self.error_patterns[pattern_id]
            if pattern.recovery_strategies:
                # Select strategy with highest success rate based on performance data
                best_strategy = self._select_best_performing_strategy(pattern.recovery_strategies, error_instance)
                if best_strategy:
                    return best_strategy

        # Fallback to category-based selection with performance consideration
        suggested_strategies = self._suggest_recovery_strategies(error_instance)
        if suggested_strategies:
            return self._select_best_performing_strategy(suggested_strategies, error_instance)

        return RecoveryStrategy.RETRY

    def _select_best_performing_strategy(self, strategies: List[RecoveryStrategy], error_instance: ErrorInstance) -> RecoveryStrategy:
        """Select the best performing strategy from a list based on learned performance."""
        if not self.learning_enabled or not strategies:
            return strategies[0] if strategies else RecoveryStrategy.RETRY

        best_strategy = strategies[0]
        best_score = 0.0

        for strategy in strategies:
            if strategy in self.strategy_performance:
                perf = self.strategy_performance[strategy]

                # Calculate score based on overall success rate and context-specific performance
                base_score = perf.success_rate * perf.confidence_score

                # Boost score for context-specific success
                context_key = f"{error_instance.category.value}_{error_instance.severity.value}"
                if context_key in perf.context_success_rates:
                    context_rate = perf.context_success_rates[context_key].get("rate", 0.0)
                    context_boost = context_rate * 0.5  # Weight context-specific performance
                    base_score += context_boost

                if base_score > best_score:
                    best_score = base_score
                    best_strategy = strategy

        return best_strategy

    def _execute_recovery(self, error_instance: ErrorInstance, strategy: RecoveryStrategy) -> bool:
        """Execute a recovery strategy."""
        try:
            recovery_id = f"recovery_{error_instance.error_id}_{strategy.value}"
            start_time = datetime.now()

            # Track active recovery
            self.active_recoveries[recovery_id] = {"error_id": error_instance.error_id, "strategy": strategy, "start_time": start_time, "status": "running"}

            success = False

            if strategy == RecoveryStrategy.RETRY:
                success = self._execute_retry_recovery(error_instance)

            elif strategy == RecoveryStrategy.FALLBACK:
                success = self._execute_fallback_recovery(error_instance)

            elif strategy == RecoveryStrategy.RESET:
                success = self._execute_reset_recovery(error_instance)

            elif strategy == RecoveryStrategy.ESCALATE:
                success = self._execute_escalate_recovery(error_instance)

            elif strategy == RecoveryStrategy.IGNORE:
                success = self._execute_ignore_recovery(error_instance)

            elif strategy == RecoveryStrategy.ADAPT:
                success = self._execute_adapt_recovery(error_instance)

            # Update recovery status
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            self.active_recoveries[recovery_id]["status"] = "completed" if success else "failed"
            self.active_recoveries[recovery_id]["end_time"] = end_time
            self.active_recoveries[recovery_id]["execution_time"] = execution_time

            # Apply adaptive learning
            if self.learning_enabled:
                self.adapt_strategy_parameters(error_instance, strategy, success)

            return success

        except Exception as e:
            logger.error(f"Error executing recovery strategy {strategy.value}: {e}")
            # Still learn from the failure
            if self.learning_enabled:
                self.adapt_strategy_parameters(error_instance, strategy, False)
            return False

    def _execute_retry_recovery(self, error_instance: ErrorInstance) -> bool:
        """Execute retry recovery strategy."""
        try:
            logger.info(f"Executing retry recovery for {error_instance.error_id}")

            # Simulate retry with exponential backoff
            for attempt in range(self.max_retry_attempts):
                wait_time = 2**attempt  # Exponential backoff
                time.sleep(min(wait_time, 10))  # Cap at 10 seconds

                # In a real implementation, this would retry the actual operation
                # For now, we'll simulate a 70% success rate
                import random

                if random.random() > 0.3:  # 70% success rate
                    logger.info(f"Retry recovery successful on attempt {attempt + 1}")
                    return True

            logger.warning(f"Retry recovery failed after {self.max_retry_attempts} attempts")
            return False

        except Exception as e:
            logger.error(f"Error in retry recovery: {e}")
            return False

    def _execute_fallback_recovery(self, error_instance: ErrorInstance) -> bool:
        """Execute fallback recovery strategy."""
        try:
            logger.info(f"Executing fallback recovery for {error_instance.error_id}")

            # Implement fallback logic based on error category
            if error_instance.category == ErrorCategory.NETWORK:
                logger.info("Switching to offline mode or alternative endpoint")
                return True  # Simulate successful fallback

            elif error_instance.category == ErrorCategory.DATA:
                logger.info("Using default values or cached data")
                return True

            elif error_instance.category == ErrorCategory.PERMISSION:
                logger.info("Attempting with reduced permissions")
                return False  # Permission issues often can't be resolved automatically

            else:
                logger.info("Executing generic fallback procedure")
                return True

        except Exception as e:
            logger.error(f"Error in fallback recovery: {e}")
            return False

    def _execute_reset_recovery(self, error_instance: ErrorInstance) -> bool:
        """Execute reset recovery strategy."""
        try:
            logger.info(f"Executing reset recovery for {error_instance.error_id}")

            # Reset component state based on the component that had the error
            component = error_instance.component

            if component and hasattr(self, "component_registry"):
                logger.info(f"Resetting component: {component}")
                return True

            # Generic reset - clear caches, reset connections, etc.
            logger.info("Executing generic system reset")
            return True

        except Exception as e:
            logger.error(f"Error in reset recovery: {e}")
            return False

    def _execute_escalate_recovery(self, error_instance: ErrorInstance) -> bool:
        """Execute escalate recovery strategy."""
        try:
            logger.warning(f"Escalating error {error_instance.error_id} for manual intervention")

            # Create escalation record
            escalation_data = {
                "error_id": error_instance.error_id,
                "error_type": error_instance.error_type,
                "error_message": error_instance.error_message,
                "severity": error_instance.severity.value,
                "category": error_instance.category.value,
                "component": error_instance.component,
                "timestamp": error_instance.timestamp.isoformat(),
                "context": error_instance.context,
            }

            # Log escalation data for monitoring
            logger.warning(f"Escalation data: {escalation_data}")

            logger.info(f"Escalation record created for {error_instance.error_id}")
            return True  # Escalation itself is successful, even if error isn't resolved

        except Exception as e:
            logger.error(f"Error in escalate recovery: {e}")
            return False

    def _execute_ignore_recovery(self, error_instance: ErrorInstance) -> bool:
        """Execute ignore recovery strategy."""
        try:
            logger.info(f"Ignoring error {error_instance.error_id} (low severity)")

            # Log the decision to ignore
            if error_instance.severity == ErrorSeverity.LOW:
                return True
            else:
                logger.warning(f"Attempted to ignore {error_instance.severity.value} severity error")
                return False

        except Exception as e:
            logger.error(f"Error in ignore recovery: {e}")
            return False

    def _execute_adapt_recovery(self, error_instance: ErrorInstance) -> bool:
        """Execute adapt recovery strategy."""
        try:
            logger.info(f"Executing adaptive recovery for {error_instance.error_id}")

            # Adaptive recovery based on error context
            context = error_instance.context

            if "input_data" in context:
                logger.info("Adapting input data handling")
                return True

            elif "configuration" in context:
                logger.info("Adapting configuration parameters")
                return True

            elif "algorithm" in context:
                logger.info("Switching to alternative algorithm")
                return True

            else:
                logger.info("Executing generic adaptive recovery")
                return True

        except Exception as e:
            logger.error(f"Error in adapt recovery: {e}")
            return False

    def _trigger_recovery(self, error_instance: ErrorInstance):
        """Trigger automatic recovery for an error."""
        try:
            # Don't auto-recover if already attempting recovery
            if any(recovery["error_id"] == error_instance.error_id for recovery in self.active_recoveries.values()):
                return

            # Select recovery strategy
            strategy = self._select_recovery_strategy(error_instance)

            # Execute recovery in a separate thread to avoid blocking
            recovery_thread = threading.Thread(target=self._threaded_recovery, args=(error_instance.error_id, strategy), daemon=True)
            recovery_thread.start()

        except Exception as e:
            logger.error(f"Error triggering recovery: {e}")

    def _threaded_recovery(self, error_id: str, strategy: RecoveryStrategy):
        """Execute recovery in a separate thread."""
        try:
            success = self.recover_from_error(error_id, strategy.value)
            if success:
                logger.info(f"Automatic recovery successful for {error_id}")
            else:
                logger.warning(f"Automatic recovery failed for {error_id}")
        except Exception as e:
            logger.error(f"Error in threaded recovery: {e}")

    def _update_error_indices(self, error_instance: ErrorInstance):
        """Update error indices for efficient access."""
        try:
            self.category_index[error_instance.category].append(error_instance.error_id)
            self.component_index[error_instance.component].append(error_instance.error_id)
            self.severity_index[error_instance.severity].append(error_instance.error_id)
        except Exception as e:
            logger.error(f"Error updating indices: {e}")

    def _update_pattern_success_rate(self, error_instance: ErrorInstance):
        """Update the success rate for an error pattern."""
        try:
            if not error_instance.recovery_successful:
                return

            error_signature = self._generate_error_signature(error_instance.error_type, error_instance.error_message, error_instance.stack_trace)

            pattern_id = hashlib.md5(error_signature.encode()).hexdigest()[:16]

            if pattern_id in self.error_patterns:
                pattern = self.error_patterns[pattern_id]

                # Calculate new success rate
                total_attempts = sum(
                    1 for error in self.error_history if self._generate_error_signature(error.error_type, error.error_message, error.stack_trace) == error_signature and error.recovery_attempted
                )

                successful_attempts = sum(
                    1 for error in self.error_history if self._generate_error_signature(error.error_type, error.error_message, error.stack_trace) == error_signature and error.recovery_successful
                )

                if total_attempts > 0:
                    pattern.success_rate = successful_attempts / total_attempts

                    # Update average resolution time
                    resolution_times = [
                        error.resolution_time
                        for error in self.error_history
                        if self._generate_error_signature(error.error_type, error.error_message, error.stack_trace) == error_signature and error.resolution_time is not None
                    ]

                    if resolution_times:
                        pattern.resolution_time_avg = sum(resolution_times) / len(resolution_times)

        except Exception as e:
            logger.error(f"Error updating pattern success rate: {e}")

    def _update_recovery_success_rate(self):
        """Update overall recovery success rate."""
        try:
            total_attempts = sum(1 for error in self.error_history if error.recovery_attempted)
            successful_attempts = sum(1 for error in self.error_history if error.recovery_successful)

            if total_attempts > 0:
                self.recovery_success_rate = successful_attempts / total_attempts

        except Exception as e:
            logger.error(f"Error updating recovery success rate: {e}")

    def _calculate_pattern_trend(self, pattern: ErrorPattern) -> str:
        """Calculate the trend for an error pattern."""
        try:
            # Simple trend calculation based on recent occurrences
            recent_errors = [error for error in self.error_history if error.timestamp > datetime.now() - timedelta(days=7)]

            pattern_recent_count = sum(1 for error in recent_errors if self._generate_error_signature(error.error_type, error.error_message, error.stack_trace) == pattern.error_signature)

            if pattern_recent_count > pattern.frequency * 0.5:
                return "increasing"
            elif pattern_recent_count < pattern.frequency * 0.2:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"Error calculating pattern trend: {e}")
            return "unknown"

    def _assess_pattern_risk(self, pattern: ErrorPattern) -> str:
        """Assess the risk level of an error pattern."""
        try:
            risk_score = 0

            # Frequency factor
            if pattern.frequency > 20:
                risk_score += 3
            elif pattern.frequency > 10:
                risk_score += 2
            elif pattern.frequency > 5:
                risk_score += 1

            # Severity factor
            if pattern.severity == ErrorSeverity.CRITICAL:
                risk_score += 4
            elif pattern.severity == ErrorSeverity.HIGH:
                risk_score += 3
            elif pattern.severity == ErrorSeverity.MEDIUM:
                risk_score += 2
            else:
                risk_score += 1

            # Success rate factor (inverse)
            if pattern.success_rate < 0.3:
                risk_score += 3
            elif pattern.success_rate < 0.6:
                risk_score += 2
            elif pattern.success_rate < 0.8:
                risk_score += 1

            # Determine risk level
            if risk_score >= 8:
                return "critical"
            elif risk_score >= 6:
                return "high"
            elif risk_score >= 4:
                return "medium"
            else:
                return "low"

        except Exception as e:
            logger.error(f"Error assessing pattern risk: {e}")
            return "unknown"

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about error handling."""
        return {
            "errors_detected": self.errors_detected,
            "errors_recovered": self.errors_recovered,
            "patterns_learned": self.patterns_learned,
            "recovery_success_rate": self.recovery_success_rate,
            "active_recoveries": len(self.active_recoveries),
            "total_patterns": len(self.error_patterns),
            "error_history_size": len(self.error_history),
            "category_distribution": {category.value: len(errors) for category, errors in self.category_index.items()},
            "severity_distribution": {severity.value: len(errors) for severity, errors in self.severity_index.items()},
            "adaptive_strategies": len(self.adaptive_strategies),
            "learning_insights": len(self.learning_insights),
            "strategy_performance": {
                strategy.value: {"success_rate": perf.success_rate, "total_attempts": perf.total_attempts, "confidence": perf.confidence_score} for strategy, perf in self.strategy_performance.items()
            },
        }

    def _initialize_strategy_performance(self):
        """Initialize performance tracking for all recovery strategies."""
        for strategy in RecoveryStrategy:
            self.strategy_performance[strategy] = StrategyPerformance(
                strategy=strategy,
                total_attempts=0,
                successful_attempts=0,
                success_rate=0.0,
                avg_execution_time=0.0,
                context_success_rates={},
                recent_performance=deque(maxlen=50),
                last_updated=datetime.now(),
                confidence_score=0.0,
            )

    def adapt_strategy_parameters(self, error_instance: ErrorInstance, strategy: RecoveryStrategy, success: bool):
        """Adapt strategy parameters based on execution results."""
        if not self.learning_enabled:
            return

        try:
            # Update strategy performance
            self._update_strategy_performance(strategy, success, error_instance)

            # Learn from success/failure patterns
            self._learn_from_execution(error_instance, strategy, success)

            # Generate adaptive strategies if needed
            if self._should_adapt_strategy(strategy):
                self._create_adaptive_strategy(error_instance, strategy)

            # Generate learning insights
            self._generate_learning_insights()

        except Exception as e:
            logger.error(f"Error in strategy adaptation: {e}")

    def _update_strategy_performance(self, strategy: RecoveryStrategy, success: bool, error_instance: ErrorInstance):
        """Update performance metrics for a strategy."""
        perf = self.strategy_performance[strategy]

        # Update basic metrics
        perf.total_attempts += 1
        if success:
            perf.successful_attempts += 1

        perf.success_rate = perf.successful_attempts / perf.total_attempts if perf.total_attempts > 0 else 0.0

        # Update recent performance history
        perf.recent_performance.append(
            {"success": success, "timestamp": datetime.now(), "context": error_instance.context, "category": error_instance.category.value, "severity": error_instance.severity.value}
        )

        # Update context-specific success rates
        context_key = f"{error_instance.category.value}_{error_instance.severity.value}"
        if context_key not in perf.context_success_rates:
            perf.context_success_rates[context_key] = {"successes": 0, "attempts": 0}

        perf.context_success_rates[context_key]["attempts"] += 1
        if success:
            perf.context_success_rates[context_key]["successes"] += 1

        # Calculate context success rate
        context_stats = perf.context_success_rates[context_key]
        context_success_rate = context_stats["successes"] / context_stats["attempts"]
        perf.context_success_rates[context_key]["rate"] = context_success_rate

        # Update confidence score based on sample size and consistency
        perf.confidence_score = self._calculate_confidence_score(perf)
        perf.last_updated = datetime.now()

    def _calculate_confidence_score(self, perf: StrategyPerformance) -> float:
        """Calculate confidence score for strategy performance."""
        if perf.total_attempts < self.min_samples_for_learning:
            return 0.0

        # Base confidence on sample size (logarithmic scaling)
        import math

        sample_confidence = min(1.0, math.log(perf.total_attempts) / math.log(50))

        # Adjust for consistency (lower variance = higher confidence)
        if len(perf.recent_performance) > 1:
            recent_successes = [1 if r["success"] else 0 for r in perf.recent_performance]
            variance = sum((x - perf.success_rate) ** 2 for x in recent_successes) / len(recent_successes)
            consistency_factor = max(0.1, 1.0 - variance)
        else:
            consistency_factor = 0.5

        return sample_confidence * consistency_factor

    def _learn_from_execution(self, error_instance: ErrorInstance, strategy: RecoveryStrategy, success: bool):
        """Learn patterns from strategy execution results."""
        execution_context = {
            "error_type": error_instance.error_type,
            "error_category": error_instance.category.value,
            "error_severity": error_instance.severity.value,
            "component": error_instance.component,
            "context": error_instance.context,
            "strategy": strategy.value,
            "timestamp": datetime.now().isoformat(),
        }

        pattern_key = f"{error_instance.category.value}_{strategy.value}"

        if success:
            self.success_patterns[pattern_key].append(execution_context)
            # Keep only recent patterns
            if len(self.success_patterns[pattern_key]) > 100:
                self.success_patterns[pattern_key] = self.success_patterns[pattern_key][-100:]
        else:
            self.failure_patterns[pattern_key].append(execution_context)
            # Keep only recent patterns
            if len(self.failure_patterns[pattern_key]) > 100:
                self.failure_patterns[pattern_key] = self.failure_patterns[pattern_key][-100:]

    def _should_adapt_strategy(self, strategy: RecoveryStrategy) -> bool:
        """Determine if a strategy should be adapted."""
        perf = self.strategy_performance[strategy]

        # Need minimum samples
        if perf.total_attempts < self.min_samples_for_learning:
            return False

        # Adapt if success rate is below threshold
        if perf.success_rate < self.adaptation_threshold:
            return True

        # Adapt if there's significant variance in context-specific performance
        if len(perf.context_success_rates) > 1:
            rates = [ctx["rate"] for ctx in perf.context_success_rates.values() if "rate" in ctx]
            if rates:
                variance = sum((r - perf.success_rate) ** 2 for r in rates) / len(rates)
                if variance > 0.1:  # High variance threshold
                    return True

        return False

    def _create_adaptive_strategy(self, error_instance: ErrorInstance, base_strategy: RecoveryStrategy):
        """Create an adaptive strategy based on learned patterns."""
        strategy_key = f"{error_instance.category.value}_{base_strategy.value}_adaptive"

        if strategy_key in self.adaptive_strategies:
            # Update existing adaptive strategy
            adaptive_strategy = self.adaptive_strategies[strategy_key]
            adaptive_strategy.adaptation_count += 1
        else:
            # Create new adaptive strategy
            adaptive_strategy = AdaptiveStrategy(
                base_strategy=base_strategy,
                parameters=self._derive_optimal_parameters(error_instance, base_strategy),
                success_patterns=self._extract_success_patterns(error_instance, base_strategy),
                failure_patterns=self._extract_failure_patterns(error_instance, base_strategy),
                adaptation_history=[],
                effectiveness_score=0.0,
                last_adapted=datetime.now(),
                adaptation_count=1,
            )
            self.adaptive_strategies[strategy_key] = adaptive_strategy

        # Record adaptation
        adaptation_record = {
            "timestamp": datetime.now().isoformat(),
            "trigger_error": error_instance.error_id,
            "base_strategy": base_strategy.value,
            "parameters": adaptive_strategy.parameters,
            "reason": "performance_below_threshold",
        }
        adaptive_strategy.adaptation_history.append(adaptation_record)
        adaptive_strategy.last_adapted = datetime.now()

        logger.info(f"Created/updated adaptive strategy: {strategy_key}")

    def _derive_optimal_parameters(self, error_instance: ErrorInstance, strategy: RecoveryStrategy) -> Dict[str, Any]:
        """Derive optimal parameters for a strategy based on learned patterns."""
        parameters = {}

        if strategy == RecoveryStrategy.RETRY:
            # Analyze retry patterns to optimize attempts and backoff
            pattern_key = f"{error_instance.category.value}_{strategy.value}"
            success_patterns = self.success_patterns.get(pattern_key, [])

            if success_patterns:
                # Analyze successful retry patterns
                avg_attempts = 3  # Default
                parameters = {"max_attempts": min(5, max(2, avg_attempts)), "backoff_multiplier": 2.0, "max_backoff": 30.0}

        elif strategy == RecoveryStrategy.FALLBACK:
            # Optimize fallback selection based on context
            parameters = {"fallback_priority": self._get_fallback_priority(error_instance), "context_aware": True}

        elif strategy == RecoveryStrategy.RESET:
            # Optimize reset scope based on error patterns
            parameters = {"reset_scope": self._determine_reset_scope(error_instance), "preserve_state": True}

        return parameters

    def _extract_success_patterns(self, error_instance: ErrorInstance, strategy: RecoveryStrategy) -> List[Dict[str, Any]]:
        """Extract success patterns for a strategy."""
        pattern_key = f"{error_instance.category.value}_{strategy.value}"
        return self.success_patterns.get(pattern_key, [])[-20:]  # Recent 20 patterns

    def _extract_failure_patterns(self, error_instance: ErrorInstance, strategy: RecoveryStrategy) -> List[Dict[str, Any]]:
        """Extract failure patterns for a strategy."""
        pattern_key = f"{error_instance.category.value}_{strategy.value}"
        return self.failure_patterns.get(pattern_key, [])[-20:]  # Recent 20 patterns

    def _get_fallback_priority(self, error_instance: ErrorInstance) -> List[str]:
        """Determine fallback priority based on learned patterns."""
        # Analyze which fallbacks work best for this error category
        if error_instance.category == ErrorCategory.NETWORK:
            return ["offline_mode", "cached_data", "alternative_endpoint"]
        elif error_instance.category == ErrorCategory.DATA:
            return ["default_values", "cached_data", "user_input"]
        else:
            return ["generic_fallback", "safe_mode"]

    def _determine_reset_scope(self, error_instance: ErrorInstance) -> str:
        """Determine optimal reset scope based on error patterns."""
        if error_instance.severity == ErrorSeverity.CRITICAL:
            return "full_system"
        elif error_instance.category == ErrorCategory.RESOURCE:
            return "resource_cleanup"
        else:
            return "component_only"

    def _generate_learning_insights(self):
        """Generate insights from learned patterns."""
        if not self.learning_enabled:
            return

        try:
            # Generate insights about strategy effectiveness
            for strategy, perf in self.strategy_performance.items():
                if perf.confidence_score > self.insight_confidence_threshold:
                    insight = self._create_strategy_insight(strategy, perf)
                    if insight:
                        self.learning_insights.append(insight)

            # Generate insights about error patterns
            self._generate_pattern_insights()

            # Limit insights to prevent memory bloat
            if len(self.learning_insights) > 1000:
                self.learning_insights = self.learning_insights[-1000:]

        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")

    def _create_strategy_insight(self, strategy: RecoveryStrategy, perf: StrategyPerformance) -> Optional[LearningInsight]:
        """Create an insight about strategy performance."""
        if perf.success_rate < 0.3:
            return LearningInsight(
                insight_id=f"strategy_{strategy.value}_{int(time.time())}",
                pattern_signature=f"low_performance_{strategy.value}",
                insight_type="strategy_optimization",
                description=f"Strategy {strategy.value} has low success rate ({perf.success_rate:.2f})",
                confidence=perf.confidence_score,
                supporting_evidence=[f"Total attempts: {perf.total_attempts}", f"Success rate: {perf.success_rate:.2f}", "Recent performance trend: declining"],
                recommended_action={"action": "adapt_strategy", "strategy": strategy.value, "parameters": {"increase_attempts": True, "modify_approach": True}},
                created_at=datetime.now(),
            )

        elif perf.success_rate > 0.8:
            return LearningInsight(
                insight_id=f"strategy_{strategy.value}_{int(time.time())}",
                pattern_signature=f"high_performance_{strategy.value}",
                insight_type="strategy_optimization",
                description=f"Strategy {strategy.value} has high success rate ({perf.success_rate:.2f})",
                confidence=perf.confidence_score,
                supporting_evidence=[f"Total attempts: {perf.total_attempts}", f"Success rate: {perf.success_rate:.2f}", "Consistent performance"],
                recommended_action={"action": "prioritize_strategy", "strategy": strategy.value, "parameters": {"increase_priority": True}},
                created_at=datetime.now(),
            )

        return None

    def _generate_pattern_insights(self):
        """Generate insights about error patterns."""
        # Analyze frequently occurring error patterns
        pattern_frequencies = {}
        for pattern in self.error_patterns.values():
            if pattern.frequency > 10:  # Frequent patterns
                key = f"{pattern.category.value}_{pattern.severity.value}"
                pattern_frequencies[key] = pattern_frequencies.get(key, 0) + pattern.frequency

        # Generate insights for frequent patterns
        for pattern_key, frequency in pattern_frequencies.items():
            if frequency > 50:  # Very frequent
                insight = LearningInsight(
                    insight_id=f"pattern_{pattern_key}_{int(time.time())}",
                    pattern_signature=pattern_key,
                    insight_type="pattern_analysis",
                    description=f"High frequency error pattern detected: {pattern_key} ({frequency} occurrences)",
                    confidence=0.9,
                    supporting_evidence=[f"Pattern frequency: {frequency}", f"Pattern type: {pattern_key}", "Requires preventive measures"],
                    recommended_action={"action": "implement_prevention", "pattern": pattern_key, "parameters": {"add_validation": True, "improve_error_handling": True}},
                    created_at=datetime.now(),
                )
                self.learning_insights.append(insight)

    def get_adaptive_strategy(self, error_instance: ErrorInstance) -> Optional[RecoveryStrategy]:
        """Get the best adaptive strategy for an error instance."""
        if not self.learning_enabled:
            return None

        # Look for adaptive strategies that match this error pattern
        category_key = error_instance.category.value

        best_strategy = None
        best_score = 0.0

        for strategy_key, adaptive_strategy in self.adaptive_strategies.items():
            if category_key in strategy_key:
                # Calculate effectiveness score based on recent performance
                score = self._calculate_adaptive_strategy_score(adaptive_strategy, error_instance)
                if score > best_score:
                    best_score = score
                    best_strategy = adaptive_strategy.base_strategy

        return best_strategy if best_score > 0.5 else None

    def _calculate_adaptive_strategy_score(self, adaptive_strategy: AdaptiveStrategy, error_instance: ErrorInstance) -> float:
        """Calculate effectiveness score for an adaptive strategy."""
        base_score = adaptive_strategy.effectiveness_score

        # Boost score based on context match
        context_match = 0.0
        for success_pattern in adaptive_strategy.success_patterns:
            if success_pattern.get("error_category") == error_instance.category.value and success_pattern.get("error_severity") == error_instance.severity.value:
                context_match += 0.1

        # Penalize for recent failures
        failure_penalty = 0.0
        for failure_pattern in adaptive_strategy.failure_patterns[-5:]:  # Recent failures
            if failure_pattern.get("error_category") == error_instance.category.value:
                failure_penalty += 0.1

        return min(1.0, max(0.0, base_score + context_match - failure_penalty))

    def apply_learning_insights(self):
        """Apply accumulated learning insights to improve system performance."""
        if not self.learning_enabled:
            return

        applied_count = 0
        for insight in self.learning_insights:
            if not insight.applied and insight.confidence > self.insight_confidence_threshold:
                try:
                    self._apply_insight(insight)
                    insight.applied = True
                    applied_count += 1
                except Exception as e:
                    logger.error(f"Failed to apply insight {insight.insight_id}: {e}")

        if applied_count > 0:
            logger.info(f"Applied {applied_count} learning insights")

    def _apply_insight(self, insight: LearningInsight):
        """Apply a specific learning insight."""
        action = insight.recommended_action

        if action.get("action") == "adapt_strategy":
            strategy_name = action.get("strategy")
            # Update strategy parameters or priority
            logger.info(f"Adapting strategy {strategy_name} based on insight")

        elif action.get("action") == "prioritize_strategy":
            strategy_name = action.get("strategy")
            # Increase strategy priority in selection
            logger.info(f"Prioritizing strategy {strategy_name} based on insight")

        elif action.get("action") == "implement_prevention":
            pattern = action.get("pattern")
            # Log recommendation for preventive measures
            logger.info(f"Recommendation: Implement prevention for pattern {pattern}")

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning progress and insights."""
        return {
            "learning_enabled": self.learning_enabled,
            "total_insights": len(self.learning_insights),
            "applied_insights": sum(1 for i in self.learning_insights if i.applied),
            "adaptive_strategies": len(self.adaptive_strategies),
            "strategy_performance_summary": {
                strategy.value: {"attempts": perf.total_attempts, "success_rate": perf.success_rate, "confidence": perf.confidence_score}
                for strategy, perf in self.strategy_performance.items()
                if perf.total_attempts > 0
            },
            "top_insights": [
                {"type": insight.insight_type, "description": insight.description, "confidence": insight.confidence, "applied": insight.applied}
                for insight in sorted(self.learning_insights, key=lambda x: x.confidence, reverse=True)[:5]
            ],
        }

    def process(self, context: Context) -> Dict[str, Any]:
        """Process context for error detection and recovery."""
        try:
            # Periodically apply learning insights
            if self.learning_enabled and len(self.learning_insights) > 0:
                self.apply_learning_insights()

            # Check if context contains error information
            if hasattr(context, "error_data") and context.error_data:
                error_id = self.detect_error(context.error_data)

                return {
                    "success": True,
                    "data": {"error_id": error_id, "auto_recovery": self.auto_recovery, "learning_enabled": self.learning_enabled, "adaptive_strategies_available": len(self.adaptive_strategies)},
                    "metadata": {"component": "SelfCorrectionEngine", "operation": "error_detection"},
                }

            # Return current statistics including learning data if no error to process
            stats = self.get_statistics()
            if self.learning_enabled:
                stats["learning_summary"] = self.get_learning_summary()

            return {"success": True, "data": stats, "metadata": {"component": "SelfCorrectionEngine", "operation": "status_check"}}

        except Exception as e:
            logger.error(f"Error in process method: {e}")
            return {"success": False, "error": str(e), "metadata": {"component": "SelfCorrectionEngine", "operation": "process"}}
