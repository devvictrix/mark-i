"""Safety Prioritization Engine for MARK-I ethical learning and safety management.

This module provides advanced safety prioritization, ethical learning, and audit
capabilities that ensure user safety always takes precedence over task completion
and that the system continuously evolves its ethical understanding.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context, Action
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".engines.safety_prioritization")


class SafetyPriority(Enum):
    """Safety priority levels."""

    ABSOLUTE = "absolute"  # Safety overrides everything
    HIGH = "high"  # Safety strongly preferred
    MEDIUM = "medium"  # Safety balanced with task completion
    LOW = "low"  # Task completion preferred but safety considered


class LearningTrigger(Enum):
    """Triggers for ethical learning."""

    SAFETY_VIOLATION = "safety_violation"
    USER_FEEDBACK = "user_feedback"
    OUTCOME_ANALYSIS = "outcome_analysis"
    PATTERN_DETECTION = "pattern_detection"
    GUIDELINE_CONFLICT = "guideline_conflict"


class AuditEventType(Enum):
    """Types of audit events."""

    ETHICAL_DECISION = "ethical_decision"
    SAFETY_INTERVENTION = "safety_intervention"
    GUIDELINE_UPDATE = "guideline_update"
    LEARNING_EVENT = "learning_event"
    VIOLATION_DETECTED = "violation_detected"


@dataclass
class SafetyConstraint:
    """Represents a safety constraint."""

    constraint_id: str
    description: str
    priority: SafetyPriority
    conditions: Dict[str, Any]
    enforcement_actions: List[str]
    violation_consequences: List[str]
    created_at: datetime
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class EthicalLearningEvent:
    """Represents an ethical learning event."""

    event_id: str
    trigger: LearningTrigger
    context: Dict[str, Any]
    original_decision: Dict[str, Any]
    outcome: Dict[str, Any]
    lessons_learned: List[str]
    guideline_updates: List[Dict[str, Any]]
    confidence: float
    timestamp: datetime


@dataclass
class AuditRecord:
    """Comprehensive audit record for ethical decisions."""

    audit_id: str
    event_type: AuditEventType
    timestamp: datetime
    component: str
    action_evaluated: Optional[Action]
    decision_made: str
    reasoning: str
    safety_score: float
    ethical_score: float
    risk_level: str
    alternatives_considered: List[Dict[str, Any]]
    user_involved: bool
    outcome: Optional[str] = None
    lessons_learned: Optional[List[str]] = None


@dataclass
class SafetyMetrics:
    """Metrics for safety performance."""

    total_decisions: int
    safety_interventions: int
    tasks_aborted_for_safety: int
    user_safety_incidents: int
    false_positive_interventions: int
    learning_events_generated: int
    guidelines_updated: int
    average_safety_score: float
    last_updated: datetime


class SafetyPrioritizationEngine(ProcessingComponent):
    """
    Advanced safety prioritization engine for ethical learning and safety management.

    Ensures user safety always takes precedence over task completion and provides
    continuous ethical learning and comprehensive audit capabilities.
    """

    def __init__(self, config: ComponentConfig):
        super().__init__("safety_prioritization_engine", config)

        # Configuration
        self.safety_override_threshold = getattr(config, "safety_override_threshold", 0.3)
        self.learning_sensitivity = getattr(config, "learning_sensitivity", 0.1)
        self.audit_retention_days = getattr(config, "audit_retention_days", 365)
        self.max_learning_events = getattr(config, "max_learning_events", 10000)
        self.guideline_update_threshold = getattr(config, "guideline_update_threshold", 0.7)

        # Safety constraints and prioritization
        self.safety_constraints: Dict[str, SafetyConstraint] = {}
        self.priority_matrix: Dict[str, Dict[str, float]] = {}
        self.safety_overrides: List[Dict[str, Any]] = []

        # Ethical learning system
        self.learning_events: deque = deque(maxlen=self.max_learning_events)
        self.learned_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.guideline_evolution_history: List[Dict[str, Any]] = []

        # Audit and logging system
        self.audit_records: deque = deque(maxlen=50000)  # Large audit trail
        self.decision_outcomes: Dict[str, Dict[str, Any]] = {}
        self.violation_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Metrics and tracking
        self.safety_metrics = SafetyMetrics(
            total_decisions=0,
            safety_interventions=0,
            tasks_aborted_for_safety=0,
            user_safety_incidents=0,
            false_positive_interventions=0,
            learning_events_generated=0,
            guidelines_updated=0,
            average_safety_score=0.0,
            last_updated=datetime.now(),
        )

        # Threading and synchronization
        self.safety_lock = threading.Lock()
        self.learning_lock = threading.Lock()
        self.audit_lock = threading.Lock()

        # Initialize default safety constraints
        self._initialize_safety_constraints()
        self._initialize_priority_matrix()

        logger.info("SafetyPrioritizationEngine initialized for ethical learning and safety management")

    def prioritize_safety_over_task(self, action: Action, context: Context, task_importance: float, safety_concerns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prioritize safety over task completion when conflicts arise."""
        try:
            with self.safety_lock:
                # Calculate safety priority score
                safety_priority_score = self._calculate_safety_priority(safety_concerns, context)

                # Determine if safety should override task completion
                should_override = self._should_override_for_safety(safety_priority_score, task_importance, safety_concerns)

                # Create prioritization decision
                decision = {
                    "decision_id": f"safety_priority_{int(time.time() * 1000)}",
                    "safety_priority_score": safety_priority_score,
                    "task_importance": task_importance,
                    "safety_override": should_override,
                    "reasoning": self._generate_safety_reasoning(safety_priority_score, task_importance, safety_concerns, should_override),
                    "recommended_action": self._determine_safety_action(should_override, action, safety_concerns),
                    "alternatives": self._generate_safety_alternatives(action, safety_concerns) if should_override else [],
                    "timestamp": datetime.now(),
                }

                # Record safety intervention if override occurred
                if should_override:
                    self._record_safety_intervention(decision, action, context, safety_concerns)

                # Update metrics
                self._update_safety_metrics(decision)

                # Create audit record
                self._create_audit_record(AuditEventType.SAFETY_INTERVENTION if should_override else AuditEventType.ETHICAL_DECISION, action, decision, context)

                logger.info(f"Safety prioritization: override={should_override}, score={safety_priority_score:.2f}")
                return decision

        except Exception as e:
            logger.error(f"Error in safety prioritization: {e}")
            return {"error": str(e), "safety_override": True, "recommended_action": "abort"}  # Default to safe behavior

    def learn_from_ethical_outcome(self, decision_id: str, outcome: Dict[str, Any], user_feedback: Optional[Dict[str, Any]] = None) -> bool:
        """Learn from the outcome of an ethical decision."""
        try:
            with self.learning_lock:
                # Create learning event
                learning_event = self._create_learning_event(decision_id, outcome, user_feedback)

                if learning_event:
                    self.learning_events.append(learning_event)
                    self.safety_metrics.learning_events_generated += 1

                    # Analyze patterns and update guidelines if needed
                    guideline_updates = self._analyze_and_update_guidelines(learning_event)

                    if guideline_updates:
                        self.safety_metrics.guidelines_updated += len(guideline_updates)
                        self._record_guideline_evolution(guideline_updates, learning_event)

                    # Update learned patterns
                    self._update_learned_patterns(learning_event)

                    # Create audit record for learning
                    self._create_audit_record(AuditEventType.LEARNING_EVENT, None, learning_event.__dict__, None)

                    logger.info(f"Ethical learning completed: {learning_event.event_id}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Error in ethical learning: {e}")
            return False

    def update_ethical_guidelines(self, updates: List[Dict[str, Any]], learning_context: Optional[Dict[str, Any]] = None) -> bool:
        """Update ethical guidelines based on learning."""
        try:
            with self.learning_lock:
                successful_updates = []

                for update in updates:
                    if self._validate_guideline_update(update):
                        # Apply the update
                        success = self._apply_guideline_update(update)
                        if success:
                            successful_updates.append(update)

                            # Record the update
                            self._record_guideline_update(update, learning_context)

                if successful_updates:
                    # Create audit record
                    self._create_audit_record(AuditEventType.GUIDELINE_UPDATE, None, {"updates": successful_updates, "context": learning_context}, None)

                    logger.info(f"Updated {len(successful_updates)} ethical guidelines")
                    return True

                return False

        except Exception as e:
            logger.error(f"Error updating ethical guidelines: {e}")
            return False

    def create_comprehensive_audit_log(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Create comprehensive audit log for ethical decisions."""
        try:
            with self.audit_lock:
                # Filter records by date range
                if start_date is None:
                    start_date = datetime.now() - timedelta(days=30)  # Default to last 30 days
                if end_date is None:
                    end_date = datetime.now()

                filtered_records = [record for record in self.audit_records if start_date <= record.timestamp <= end_date]

                # Organize audit data
                audit_log = {
                    "audit_period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "total_records": len(filtered_records)},
                    "summary_statistics": self._generate_audit_statistics(filtered_records),
                    "safety_interventions": self._extract_safety_interventions(filtered_records),
                    "ethical_decisions": self._extract_ethical_decisions(filtered_records),
                    "learning_events": self._extract_learning_events(filtered_records),
                    "guideline_updates": self._extract_guideline_updates(filtered_records),
                    "violation_patterns": self._analyze_violation_patterns(filtered_records),
                    "recommendations": self._generate_audit_recommendations(filtered_records),
                    "generated_at": datetime.now().isoformat(),
                }

                logger.info(f"Generated comprehensive audit log: {len(filtered_records)} records")
                return audit_log

        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return {"error": str(e)}

    def detect_ethical_violations(self, recent_decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns of ethical violations."""
        try:
            violations = []

            # Analyze recent decisions for violation patterns
            for decision in recent_decisions:
                violation = self._analyze_decision_for_violations(decision)
                if violation:
                    violations.append(violation)

                    # Record violation pattern
                    violation_type = violation.get("type", "unknown")
                    self.violation_patterns[violation_type].append({"decision": decision, "violation": violation, "timestamp": datetime.now()})

            # Detect systemic patterns
            systemic_violations = self._detect_systemic_violations()
            violations.extend(systemic_violations)

            # Create audit records for violations
            for violation in violations:
                self._create_audit_record(AuditEventType.VIOLATION_DETECTED, None, violation, None)

            logger.info(f"Detected {len(violations)} ethical violations")
            return violations

        except Exception as e:
            logger.error(f"Error detecting violations: {e}")
            return []

    def _calculate_safety_priority(self, safety_concerns: List[Dict[str, Any]], context: Context) -> float:
        """Calculate safety priority score based on concerns and context."""
        if not safety_concerns:
            return 1.0  # No concerns = high safety

        priority_score = 1.0

        for concern in safety_concerns:
            severity = concern.get("severity", "medium")
            concern_type = concern.get("type", "unknown")

            # Apply severity weights
            severity_weights = {"critical": 0.9, "high": 0.7, "medium": 0.4, "low": 0.2}

            severity_impact = severity_weights.get(severity, 0.4)

            # Apply concern type weights
            type_weights = {"user_safety": 1.0, "data_loss": 0.8, "privacy_breach": 0.7, "system_damage": 0.6, "performance_impact": 0.3}

            type_impact = type_weights.get(concern_type, 0.5)

            # Calculate combined impact
            concern_impact = severity_impact * type_impact
            priority_score = min(priority_score, 1.0 - concern_impact)

        return max(0.0, priority_score)

    def _should_override_for_safety(self, safety_priority_score: float, task_importance: float, safety_concerns: List[Dict[str, Any]]) -> bool:
        """Determine if safety should override task completion."""
        # Always override for critical safety concerns
        critical_concerns = [c for c in safety_concerns if c.get("severity") == "critical"]
        if critical_concerns:
            return True

        # Override if safety score is below threshold
        if safety_priority_score < self.safety_override_threshold:
            return True

        # Consider task importance vs safety
        safety_weight = 1.0 - safety_priority_score
        task_weight = task_importance

        # Safety wins if it outweighs task importance significantly
        return safety_weight > task_weight * 1.5

    def _generate_safety_reasoning(self, safety_score: float, task_importance: float, safety_concerns: List[Dict[str, Any]], should_override: bool) -> str:
        """Generate reasoning for safety prioritization decision."""
        if should_override:
            critical_concerns = [c for c in safety_concerns if c.get("severity") in ["critical", "high"]]
            if critical_concerns:
                concern_types = [c.get("type", "unknown") for c in critical_concerns]
                return f"Safety override triggered due to {len(critical_concerns)} critical/high severity concerns: {', '.join(concern_types)}. User safety takes precedence over task completion."
            else:
                return f"Safety override triggered due to low safety score ({safety_score:.2f}) below threshold ({self.safety_override_threshold}). Prioritizing user safety."
        else:
            return f"Task completion approved with safety score {safety_score:.2f}. Safety concerns are manageable with proper precautions."

    def _determine_safety_action(self, should_override: bool, action: Action, safety_concerns: List[Dict[str, Any]]) -> str:
        """Determine the recommended safety action."""
        if not should_override:
            return "proceed_with_caution"

        # Determine action based on concern severity
        max_severity = max([c.get("severity", "low") for c in safety_concerns], default="low")

        if max_severity == "critical":
            return "abort_immediately"
        elif max_severity == "high":
            return "abort_and_suggest_alternatives"
        elif max_severity == "medium":
            return "require_user_confirmation"
        else:
            return "proceed_with_warnings"

    def _generate_safety_alternatives(self, action: Action, safety_concerns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate safer alternatives to the original action."""
        alternatives = []

        for concern in safety_concerns:
            concern_type = concern.get("type", "unknown")

            if concern_type == "user_safety":
                alternatives.append(
                    {
                        "action_type": "safe_mode_execution",
                        "description": "Execute action in safe mode with additional safety checks",
                        "safety_improvements": ["user_confirmation", "rollback_capability", "monitoring"],
                    }
                )

            elif concern_type == "data_loss":
                alternatives.append(
                    {"action_type": "backup_first_execution", "description": "Create backup before executing action", "safety_improvements": ["data_backup", "recovery_plan", "verification"]}
                )

            elif concern_type == "privacy_breach":
                alternatives.append(
                    {
                        "action_type": "privacy_preserving_execution",
                        "description": "Execute action with privacy protection measures",
                        "safety_improvements": ["data_anonymization", "consent_verification", "audit_trail"],
                    }
                )

            elif concern_type == "system_damage":
                alternatives.append(
                    {"action_type": "sandboxed_execution", "description": "Execute action in isolated environment", "safety_improvements": ["isolation", "resource_limits", "monitoring"]}
                )

        return alternatives[:3]  # Limit to top 3 alternatives

    def _record_safety_intervention(self, decision: Dict[str, Any], action: Action, context: Context, safety_concerns: List[Dict[str, Any]]):
        """Record a safety intervention."""
        intervention = {
            "intervention_id": decision["decision_id"],
            "timestamp": decision["timestamp"],
            "action": str(action),
            "safety_concerns": safety_concerns,
            "decision": decision,
            "context": getattr(context, "system_state", {}),
            "intervention_type": decision["recommended_action"],
        }

        self.safety_overrides.append(intervention)
        self.safety_metrics.safety_interventions += 1

        if decision["recommended_action"] in ["abort_immediately", "abort_and_suggest_alternatives"]:
            self.safety_metrics.tasks_aborted_for_safety += 1

    def _create_learning_event(self, decision_id: str, outcome: Dict[str, Any], user_feedback: Optional[Dict[str, Any]]) -> Optional[EthicalLearningEvent]:
        """Create a learning event from decision outcome."""
        # Find the original decision
        original_decision = None
        for record in reversed(self.audit_records):
            if hasattr(record, "audit_id") and decision_id in record.audit_id:
                original_decision = record.__dict__
                break

        if not original_decision:
            return None

        # Determine learning trigger
        trigger = self._determine_learning_trigger(outcome, user_feedback)

        # Extract lessons learned
        lessons_learned = self._extract_lessons_learned(original_decision, outcome, user_feedback)

        # Generate guideline updates
        guideline_updates = self._generate_guideline_updates(lessons_learned, original_decision)

        # Calculate confidence
        confidence = self._calculate_learning_confidence(outcome, user_feedback, lessons_learned)

        return EthicalLearningEvent(
            event_id=f"learning_{int(time.time() * 1000)}",
            trigger=trigger,
            context=original_decision,
            original_decision=original_decision,
            outcome=outcome,
            lessons_learned=lessons_learned,
            guideline_updates=guideline_updates,
            confidence=confidence,
            timestamp=datetime.now(),
        )

    def _determine_learning_trigger(self, outcome: Dict[str, Any], user_feedback: Optional[Dict[str, Any]]) -> LearningTrigger:
        """Determine what triggered the learning event."""
        if user_feedback:
            if user_feedback.get("safety_concern", False):
                return LearningTrigger.SAFETY_VIOLATION
            else:
                return LearningTrigger.USER_FEEDBACK

        if outcome.get("safety_incident", False):
            return LearningTrigger.SAFETY_VIOLATION

        if outcome.get("unexpected_result", False):
            return LearningTrigger.OUTCOME_ANALYSIS

        return LearningTrigger.OUTCOME_ANALYSIS

    def _extract_lessons_learned(self, original_decision: Dict[str, Any], outcome: Dict[str, Any], user_feedback: Optional[Dict[str, Any]]) -> List[str]:
        """Extract lessons learned from the decision outcome."""
        lessons = []

        # Analyze outcome vs expectation
        if outcome.get("success", True) != original_decision.get("expected_success", True):
            if outcome.get("success", False):
                lessons.append("Decision was more successful than expected - consider reducing caution level")
            else:
                lessons.append("Decision failed unexpectedly - increase safety checks for similar actions")

        # Analyze user feedback
        if user_feedback:
            satisfaction = user_feedback.get("satisfaction", 0.5)
            if satisfaction < 0.3:
                lessons.append("User dissatisfaction indicates need for better communication or different approach")
            elif satisfaction > 0.8:
                lessons.append("High user satisfaction - this approach should be reinforced")

            if user_feedback.get("safety_concern", False):
                lessons.append("User identified safety concern - review safety assessment procedures")

        # Analyze safety outcomes
        if outcome.get("safety_incident", False):
            lessons.append("Safety incident occurred - strengthen safety constraints and assessment")

        return lessons

    def _generate_guideline_updates(self, lessons_learned: List[str], original_decision: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate guideline updates based on lessons learned."""
        updates = []

        for lesson in lessons_learned:
            if "safety" in lesson.lower():
                updates.append(
                    {
                        "type": "safety_constraint_update",
                        "description": "Strengthen safety constraints based on incident",
                        "changes": {"increase_safety_threshold": 0.1, "add_additional_checks": True},
                        "confidence": 0.8,
                    }
                )

            elif "communication" in lesson.lower():
                updates.append(
                    {
                        "type": "communication_guideline_update",
                        "description": "Improve user communication and explanation",
                        "changes": {"require_detailed_explanation": True, "increase_transparency": True},
                        "confidence": 0.7,
                    }
                )

            elif "caution" in lesson.lower():
                if "reduce" in lesson.lower():
                    updates.append(
                        {"type": "risk_tolerance_update", "description": "Adjust risk tolerance based on successful outcomes", "changes": {"increase_risk_tolerance": 0.05}, "confidence": 0.6}
                    )
                else:
                    updates.append({"type": "risk_tolerance_update", "description": "Increase caution based on unexpected failures", "changes": {"decrease_risk_tolerance": 0.1}, "confidence": 0.8})

        return updates

    def _calculate_learning_confidence(self, outcome: Dict[str, Any], user_feedback: Optional[Dict[str, Any]], lessons_learned: List[str]) -> float:
        """Calculate confidence in the learning event."""
        confidence = 0.5  # Base confidence

        # Increase confidence with clear outcomes
        if outcome.get("clear_result", False):
            confidence += 0.2

        # Increase confidence with user feedback
        if user_feedback:
            confidence += 0.2
            if user_feedback.get("detailed", False):
                confidence += 0.1

        # Increase confidence with more lessons learned
        confidence += min(0.2, len(lessons_learned) * 0.05)

        return min(1.0, confidence)

    def _analyze_and_update_guidelines(self, learning_event: EthicalLearningEvent) -> List[Dict[str, Any]]:
        """Analyze learning event and update guidelines if confidence is high enough."""
        if learning_event.confidence < self.guideline_update_threshold:
            return []

        applied_updates = []

        for update in learning_event.guideline_updates:
            if update.get("confidence", 0.0) >= self.guideline_update_threshold:
                if self._apply_guideline_update(update):
                    applied_updates.append(update)

        return applied_updates

    def _validate_guideline_update(self, update: Dict[str, Any]) -> bool:
        """Validate a guideline update before applying it."""
        # Check required fields
        if not all(key in update for key in ["type", "description", "changes"]):
            return False

        # Check confidence threshold
        if update.get("confidence", 0.0) < self.guideline_update_threshold:
            return False

        # Validate specific update types
        update_type = update["type"]
        changes = update["changes"]

        if update_type == "safety_constraint_update":
            # Ensure safety changes are reasonable
            if "increase_safety_threshold" in changes:
                if changes["increase_safety_threshold"] > 0.2:  # Max 0.2 increase
                    return False

        elif update_type == "risk_tolerance_update":
            # Ensure risk tolerance changes are reasonable
            if "increase_risk_tolerance" in changes:
                if changes["increase_risk_tolerance"] > 0.1:  # Max 0.1 increase
                    return False
            if "decrease_risk_tolerance" in changes:
                if changes["decrease_risk_tolerance"] > 0.2:  # Max 0.2 decrease
                    return False

        return True

    def _apply_guideline_update(self, update: Dict[str, Any]) -> bool:
        """Apply a validated guideline update."""
        try:
            update_type = update["type"]
            changes = update["changes"]

            if update_type == "safety_constraint_update":
                if "increase_safety_threshold" in changes:
                    self.safety_override_threshold = max(0.1, self.safety_override_threshold + changes["increase_safety_threshold"])

                if "add_additional_checks" in changes and changes["add_additional_checks"]:
                    # Add new safety constraint
                    new_constraint = SafetyConstraint(
                        constraint_id=f"learned_{int(time.time())}",
                        description="Learned safety constraint from incident",
                        priority=SafetyPriority.HIGH,
                        conditions={"learned_from_incident": True},
                        enforcement_actions=["require_confirmation", "add_warnings"],
                        violation_consequences=["abort_action", "escalate_to_human"],
                        created_at=datetime.now(),
                    )
                    self.safety_constraints[new_constraint.constraint_id] = new_constraint

            elif update_type == "risk_tolerance_update":
                if "increase_risk_tolerance" in changes:
                    self.safety_override_threshold = max(0.0, self.safety_override_threshold - changes["increase_risk_tolerance"])

                if "decrease_risk_tolerance" in changes:
                    self.safety_override_threshold = min(1.0, self.safety_override_threshold + changes["decrease_risk_tolerance"])

            return True

        except Exception as e:
            logger.error(f"Error applying guideline update: {e}")
            return False

    def _create_audit_record(self, event_type: AuditEventType, action: Optional[Action], decision_data: Dict[str, Any], context: Optional[Context]):
        """Create a comprehensive audit record."""
        audit_record = AuditRecord(
            audit_id=f"audit_{event_type.value}_{int(time.time() * 1000)}",
            event_type=event_type,
            timestamp=datetime.now(),
            component="SafetyPrioritizationEngine",
            action_evaluated=action,
            decision_made=decision_data.get("decision", "unknown"),
            reasoning=decision_data.get("reasoning", ""),
            safety_score=decision_data.get("safety_priority_score", 0.0),
            ethical_score=decision_data.get("ethical_score", 0.0),
            risk_level=decision_data.get("risk_level", "unknown"),
            alternatives_considered=decision_data.get("alternatives", []),
            user_involved=decision_data.get("user_involved", False),
        )

        self.audit_records.append(audit_record)
        self.safety_metrics.total_decisions += 1

    def _update_safety_metrics(self, decision: Dict[str, Any]):
        """Update safety metrics based on decision."""
        # Update average safety score
        current_avg = self.safety_metrics.average_safety_score
        total_decisions = self.safety_metrics.total_decisions
        new_score = decision.get("safety_priority_score", 0.0)

        if total_decisions > 0:
            self.safety_metrics.average_safety_score = (current_avg * total_decisions + new_score) / (total_decisions + 1)
        else:
            self.safety_metrics.average_safety_score = new_score

        self.safety_metrics.last_updated = datetime.now()

    def _initialize_safety_constraints(self):
        """Initialize default safety constraints."""
        default_constraints = [
            {
                "id": "user_safety_absolute",
                "description": "User physical safety must never be compromised",
                "priority": SafetyPriority.ABSOLUTE,
                "conditions": {"involves_user_safety": True},
                "enforcement_actions": ["immediate_abort", "escalate_to_human"],
                "violation_consequences": ["system_shutdown", "incident_report"],
            },
            {
                "id": "data_protection_high",
                "description": "User data must be protected from loss or breach",
                "priority": SafetyPriority.HIGH,
                "conditions": {"involves_user_data": True},
                "enforcement_actions": ["require_confirmation", "create_backup"],
                "violation_consequences": ["abort_action", "notify_user"],
            },
            {
                "id": "system_integrity_medium",
                "description": "System integrity should be maintained",
                "priority": SafetyPriority.MEDIUM,
                "conditions": {"affects_system": True},
                "enforcement_actions": ["add_monitoring", "create_checkpoint"],
                "violation_consequences": ["rollback", "alert_admin"],
            },
        ]

        for constraint_data in default_constraints:
            constraint = SafetyConstraint(
                constraint_id=constraint_data["id"],
                description=constraint_data["description"],
                priority=constraint_data["priority"],
                conditions=constraint_data["conditions"],
                enforcement_actions=constraint_data["enforcement_actions"],
                violation_consequences=constraint_data["violation_consequences"],
                created_at=datetime.now(),
            )
            self.safety_constraints[constraint_data["id"]] = constraint

    def _initialize_priority_matrix(self):
        """Initialize priority matrix for different scenarios."""
        self.priority_matrix = {
            "user_safety_vs_task_completion": {"user_safety": 1.0, "task_completion": 0.1},
            "data_protection_vs_efficiency": {"data_protection": 0.8, "efficiency": 0.3},
            "privacy_vs_functionality": {"privacy": 0.7, "functionality": 0.4},
        }

    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status and metrics."""
        return {
            "safety_metrics": {
                "total_decisions": self.safety_metrics.total_decisions,
                "safety_interventions": self.safety_metrics.safety_interventions,
                "tasks_aborted_for_safety": self.safety_metrics.tasks_aborted_for_safety,
                "intervention_rate": (self.safety_metrics.safety_interventions / max(1, self.safety_metrics.total_decisions)),
                "average_safety_score": self.safety_metrics.average_safety_score,
                "learning_events_generated": self.safety_metrics.learning_events_generated,
                "guidelines_updated": self.safety_metrics.guidelines_updated,
            },
            "configuration": {
                "safety_override_threshold": self.safety_override_threshold,
                "learning_sensitivity": self.learning_sensitivity,
                "guideline_update_threshold": self.guideline_update_threshold,
            },
            "active_constraints": len(self.safety_constraints),
            "recent_overrides": len([o for o in self.safety_overrides if (datetime.now() - o["timestamp"]).days < 7]),
            "audit_records": len(self.audit_records),
            "learning_events": len(self.learning_events),
        }

    def process(self, context: Context) -> Dict[str, Any]:
        """Process context for safety prioritization."""
        try:
            # Return current safety status
            return {"success": True, "data": self.get_safety_status(), "metadata": {"component": "SafetyPrioritizationEngine", "operation": "status_check"}}

        except Exception as e:
            logger.error(f"Error in process method: {e}")
            return {"success": False, "error": str(e), "metadata": {"component": "SafetyPrioritizationEngine", "operation": "process"}}
