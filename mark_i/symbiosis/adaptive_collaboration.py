"""Adaptive Collaboration Engine for MARK-I symbiotic intelligence.

This module provides advanced behavior adaptation, trust management, and combined
intelligence optimization for seamless human-AI collaboration that evolves and
improves over time based on user feedback and interaction patterns.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Set
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, deque
from enum import Enum

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".symbiosis.adaptive_collaboration")


class CollaborationStyle(Enum):
    """Different collaboration styles for human-AI interaction."""

    LEADING = "leading"  # AI takes initiative
    FOLLOWING = "following"  # AI follows human lead
    EQUAL_PARTNER = "equal_partner"  # Balanced collaboration
    SUPPORTIVE = "supportive"  # AI provides support/assistance
    CONSULTATIVE = "consultative"  # AI acts as consultant


class AdaptationTrigger(Enum):
    """Triggers for behavior adaptation."""

    USER_FEEDBACK = "user_feedback"
    PERFORMANCE_DECLINE = "performance_decline"
    TRUST_CHANGE = "trust_change"
    TASK_COMPLEXITY = "task_complexity"
    CONTEXT_SHIFT = "context_shift"


class IntelligenceMode(Enum):
    """Modes for combined intelligence optimization."""

    HUMAN_DOMINANT = "human_dominant"
    AI_DOMINANT = "ai_dominant"
    BALANCED = "balanced"
    DYNAMIC = "dynamic"
    SPECIALIZED = "specialized"


@dataclass
class BehaviorPattern:
    """Represents a learned behavior pattern."""

    pattern_id: str
    context_signature: str
    collaboration_style: CollaborationStyle
    success_rate: float
    user_satisfaction: float
    efficiency_score: float
    usage_count: int
    last_used: datetime
    adaptation_history: List[Dict[str, Any]]


@dataclass
class TrustEvent:
    """Represents an event that affects trust."""

    event_id: str
    event_type: str
    impact_score: float  # -1.0 to 1.0
    context: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False


@dataclass
class CollaborationMetrics:
    """Metrics for collaboration effectiveness."""

    task_completion_rate: float
    average_task_time: float
    user_satisfaction_score: float
    efficiency_ratio: float  # AI contribution / Total effort
    communication_effectiveness: float
    trust_stability: float
    adaptation_success_rate: float
    last_updated: datetime


@dataclass
class AutonomyBoundary:
    """Defines autonomy boundaries for different contexts."""

    boundary_id: str
    context_pattern: str
    max_autonomy_level: float
    required_permissions: Set[str]
    escalation_triggers: List[str]
    trust_threshold: float
    last_updated: datetime


class AdaptiveCollaborationEngine(ProcessingComponent):
    """
    Advanced adaptive collaboration engine for symbiotic intelligence.

    Provides behavior adaptation, trust management, and combined intelligence
    optimization that evolves based on user feedback and interaction patterns.
    """

    def __init__(self, config: ComponentConfig):
        super().__init__("adaptive_collaboration_engine", config)

        # Configuration
        self.adaptation_sensitivity = getattr(config, "adaptation_sensitivity", 0.1)
        self.trust_update_rate = getattr(config, "trust_update_rate", 0.05)
        self.behavior_learning_rate = getattr(config, "behavior_learning_rate", 0.1)
        self.min_pattern_samples = getattr(config, "min_pattern_samples", 5)
        self.trust_decay_period = getattr(config, "trust_decay_period", 86400)  # 24 hours
        self.max_behavior_patterns = getattr(config, "max_behavior_patterns", 1000)

        # Collaboration state
        self.current_collaboration_style = CollaborationStyle.EQUAL_PARTNER
        self.current_intelligence_mode = IntelligenceMode.BALANCED
        self.current_trust_level = 0.5  # Start with medium trust

        # Learning and adaptation
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}
        self.trust_events: deque = deque(maxlen=10000)
        self.autonomy_boundaries: Dict[str, AutonomyBoundary] = {}
        self.collaboration_history: deque = deque(maxlen=5000)

        # Metrics and tracking
        self.collaboration_metrics = CollaborationMetrics(
            task_completion_rate=0.0,
            average_task_time=0.0,
            user_satisfaction_score=0.5,
            efficiency_ratio=0.5,
            communication_effectiveness=0.5,
            trust_stability=0.5,
            adaptation_success_rate=0.0,
            last_updated=datetime.now(),
        )

        # Context tracking
        self.context_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.successful_adaptations: Dict[str, int] = defaultdict(int)
        self.failed_adaptations: Dict[str, int] = defaultdict(int)

        # Threading and synchronization
        self.adaptation_lock = threading.Lock()
        self.trust_lock = threading.Lock()
        self.metrics_lock = threading.Lock()

        # Initialize default autonomy boundaries
        self._initialize_default_boundaries()

        logger.info("AdaptiveCollaborationEngine initialized for symbiotic intelligence")

    def adapt_behavior(self, feedback: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Adapt behavior based on user feedback and context."""
        try:
            with self.adaptation_lock:
                # Analyze feedback to determine adaptation needs
                adaptation_needed = self._analyze_adaptation_needs(feedback, context)

                if not adaptation_needed:
                    return False

                # Determine adaptation strategy
                adaptation_strategy = self._determine_adaptation_strategy(feedback, context)

                # Apply behavioral adaptations
                success = self._apply_behavioral_adaptation(adaptation_strategy, context)

                # Learn from adaptation results
                self._learn_from_adaptation(adaptation_strategy, success, context)

                # Update collaboration metrics
                self._update_collaboration_metrics(feedback, success)

                logger.info(f"Behavior adaptation {'successful' if success else 'failed'}: {adaptation_strategy.get('type', 'unknown')}")
                return success

        except Exception as e:
            logger.error(f"Error in behavior adaptation: {e}")
            return False

    def assess_and_update_trust(self, interaction_data: Dict[str, Any]) -> float:
        """Assess and update trust level based on interaction data."""
        try:
            with self.trust_lock:
                # Create trust event
                trust_event = self._create_trust_event(interaction_data)
                self.trust_events.append(trust_event)

                # Calculate trust impact
                trust_impact = self._calculate_trust_impact(trust_event, interaction_data)

                # Update trust level
                old_trust = self.current_trust_level
                self.current_trust_level = self._update_trust_level(trust_impact)

                # Update autonomy boundaries if trust changed significantly
                if abs(self.current_trust_level - old_trust) > 0.1:
                    self._update_autonomy_boundaries()

                # Update trust stability metric
                self._update_trust_stability()

                logger.info(f"Trust updated: {old_trust:.3f} -> {self.current_trust_level:.3f} (impact: {trust_impact:+.3f})")
                return self.current_trust_level

        except Exception as e:
            logger.error(f"Error updating trust: {e}")
            return self.current_trust_level

    def optimize_combined_intelligence(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize the combination of human and AI intelligence for a task."""
        try:
            # Analyze task requirements
            task_analysis = self._analyze_task_requirements(task_context)

            # Determine optimal intelligence distribution
            intelligence_distribution = self._calculate_optimal_distribution(task_analysis)

            # Select collaboration style
            optimal_style = self._select_optimal_collaboration_style(task_analysis, intelligence_distribution)

            # Create optimization plan
            optimization_plan = {
                "collaboration_style": optimal_style.value,
                "intelligence_mode": self._determine_intelligence_mode(intelligence_distribution),
                "human_responsibilities": intelligence_distribution["human_tasks"],
                "ai_responsibilities": intelligence_distribution["ai_tasks"],
                "coordination_points": intelligence_distribution["coordination_points"],
                "success_metrics": self._define_success_metrics(task_analysis),
                "adaptation_triggers": self._identify_adaptation_triggers(task_context),
            }

            # Update current collaboration style
            self.current_collaboration_style = optimal_style

            logger.info(f"Optimized combined intelligence: {optimal_style.value} style")
            return optimization_plan

        except Exception as e:
            logger.error(f"Error optimizing combined intelligence: {e}")
            return {"error": str(e)}

    def manage_autonomy_boundaries(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage autonomy boundaries based on trust and context."""
        try:
            # Get context signature
            context_signature = self._generate_context_signature(context)

            # Find or create autonomy boundary
            boundary = self._get_or_create_boundary(context_signature, context)

            # Adjust boundary based on current trust level
            adjusted_boundary = self._adjust_boundary_for_trust(boundary)

            # Create autonomy guidelines
            autonomy_guidelines = {
                "max_autonomy_level": adjusted_boundary.max_autonomy_level,
                "auto_execute_threshold": self._calculate_auto_execute_threshold(adjusted_boundary),
                "required_permissions": list(adjusted_boundary.required_permissions),
                "escalation_triggers": adjusted_boundary.escalation_triggers.copy(),
                "trust_based_adjustments": self._get_trust_based_adjustments(),
                "context_specific_rules": self._get_context_specific_rules(context),
            }

            logger.info(f"Managed autonomy boundaries: max_level={adjusted_boundary.max_autonomy_level:.2f}")
            return autonomy_guidelines

        except Exception as e:
            logger.error(f"Error managing autonomy boundaries: {e}")
            return {"error": str(e)}

    def coordinate_intelligence(self, human_input: Dict[str, Any], ai_capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate human and AI intelligence for optimal collaboration."""
        try:
            # Analyze human strengths and preferences
            human_analysis = self._analyze_human_capabilities(human_input)

            # Analyze AI capabilities and limitations
            ai_analysis = self._analyze_ai_capabilities(ai_capabilities)

            # Find optimal coordination strategy
            coordination_strategy = self._find_optimal_coordination(human_analysis, ai_analysis)

            # Create coordination plan
            coordination_plan = {
                "strategy": coordination_strategy["type"],
                "human_lead_areas": coordination_strategy["human_strengths"],
                "ai_lead_areas": coordination_strategy["ai_strengths"],
                "collaborative_areas": coordination_strategy["shared_areas"],
                "handoff_points": coordination_strategy["transitions"],
                "communication_protocol": self._design_communication_protocol(coordination_strategy),
                "success_indicators": coordination_strategy["success_metrics"],
            }

            # Update intelligence mode
            self.current_intelligence_mode = IntelligenceMode(coordination_strategy["intelligence_mode"])

            logger.info(f"Coordinated intelligence: {coordination_strategy['type']} strategy")
            return coordination_plan

        except Exception as e:
            logger.error(f"Error coordinating intelligence: {e}")
            return {"error": str(e)}

    def _analyze_adaptation_needs(self, feedback: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Analyze if behavior adaptation is needed."""
        # Check satisfaction threshold
        satisfaction = feedback.get("satisfaction", 0.5)
        if satisfaction < 0.4:
            return True

        # Check performance metrics
        efficiency = feedback.get("efficiency", 0.5)
        if efficiency < 0.4:
            return True

        # Check for explicit adaptation requests
        if feedback.get("request_adaptation", False):
            return True

        # Check for context changes
        if self._detect_context_shift(context):
            return True

        return False

    def _determine_adaptation_strategy(self, feedback: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best adaptation strategy."""
        strategy = {"type": "behavioral_adjustment", "target_areas": [], "adjustments": {}, "confidence": 0.0}

        # Analyze feedback components
        if feedback.get("communication_issues"):
            strategy["target_areas"].append("communication")
            strategy["adjustments"]["communication_style"] = feedback.get("preferred_communication", "collaborative")

        if feedback.get("autonomy_issues"):
            strategy["target_areas"].append("autonomy")
            strategy["adjustments"]["autonomy_level"] = feedback.get("preferred_autonomy", "medium")

        if feedback.get("collaboration_issues"):
            strategy["target_areas"].append("collaboration")
            strategy["adjustments"]["collaboration_style"] = feedback.get("preferred_collaboration", "equal_partner")

        # Calculate confidence based on feedback clarity
        strategy["confidence"] = min(1.0, len(strategy["target_areas"]) * 0.3 + feedback.get("clarity", 0.5))

        return strategy

    def _apply_behavioral_adaptation(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Apply behavioral adaptation based on strategy."""
        try:
            success = True

            for area in strategy["target_areas"]:
                if area == "communication":
                    success &= self._adapt_communication_behavior(strategy["adjustments"], context)
                elif area == "autonomy":
                    success &= self._adapt_autonomy_behavior(strategy["adjustments"], context)
                elif area == "collaboration":
                    success &= self._adapt_collaboration_behavior(strategy["adjustments"], context)

            return success

        except Exception as e:
            logger.error(f"Error applying behavioral adaptation: {e}")
            return False

    def _adapt_communication_behavior(self, adjustments: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Adapt communication behavior."""
        try:
            # Update communication patterns based on adjustments
            new_style = adjustments.get("communication_style", "collaborative")

            # Create or update behavior pattern
            pattern_id = f"comm_{self._generate_context_signature(context)}"

            if pattern_id in self.behavior_patterns:
                pattern = self.behavior_patterns[pattern_id]
                pattern.collaboration_style = CollaborationStyle(new_style)
                pattern.usage_count += 1
                pattern.last_used = datetime.now()
            else:
                pattern = BehaviorPattern(
                    pattern_id=pattern_id,
                    context_signature=self._generate_context_signature(context),
                    collaboration_style=CollaborationStyle(new_style),
                    success_rate=0.5,
                    user_satisfaction=0.5,
                    efficiency_score=0.5,
                    usage_count=1,
                    last_used=datetime.now(),
                    adaptation_history=[],
                )
                self.behavior_patterns[pattern_id] = pattern

            return True

        except Exception as e:
            logger.error(f"Error adapting communication behavior: {e}")
            return False

    def _adapt_autonomy_behavior(self, adjustments: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Adapt autonomy behavior."""
        try:
            autonomy_level = adjustments.get("autonomy_level", "medium")

            # Convert to numeric value
            autonomy_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
            numeric_level = autonomy_map.get(autonomy_level, 0.6)

            # Update autonomy boundaries
            context_signature = self._generate_context_signature(context)
            if context_signature in self.autonomy_boundaries:
                boundary = self.autonomy_boundaries[context_signature]
                boundary.max_autonomy_level = numeric_level
                boundary.last_updated = datetime.now()

            return True

        except Exception as e:
            logger.error(f"Error adapting autonomy behavior: {e}")
            return False

    def _adapt_collaboration_behavior(self, adjustments: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Adapt collaboration behavior."""
        try:
            collaboration_style = adjustments.get("collaboration_style", "equal_partner")
            self.current_collaboration_style = CollaborationStyle(collaboration_style)

            # Update behavior patterns
            context_signature = self._generate_context_signature(context)
            pattern_id = f"collab_{context_signature}"

            if pattern_id in self.behavior_patterns:
                pattern = self.behavior_patterns[pattern_id]
                pattern.collaboration_style = self.current_collaboration_style
                pattern.last_used = datetime.now()

            return True

        except Exception as e:
            logger.error(f"Error adapting collaboration behavior: {e}")
            return False

    def _create_trust_event(self, interaction_data: Dict[str, Any]) -> TrustEvent:
        """Create a trust event from interaction data."""
        event_id = f"trust_{int(time.time() * 1000)}"
        event_type = interaction_data.get("event_type", "interaction")

        # Calculate impact score based on interaction outcome
        impact_score = 0.0

        if interaction_data.get("successful", False):
            impact_score += 0.1
        else:
            impact_score -= 0.1

        # Adjust based on user satisfaction
        satisfaction = interaction_data.get("satisfaction", 0.5)
        impact_score += (satisfaction - 0.5) * 0.2

        # Adjust based on task complexity
        complexity = interaction_data.get("complexity", 0.5)
        if complexity > 0.7 and interaction_data.get("successful", False):
            impact_score += 0.1  # Bonus for handling complex tasks well

        return TrustEvent(event_id=event_id, event_type=event_type, impact_score=max(-1.0, min(1.0, impact_score)), context=interaction_data.get("context", {}), timestamp=datetime.now())

    def _calculate_trust_impact(self, trust_event: TrustEvent, interaction_data: Dict[str, Any]) -> float:
        """Calculate the impact of a trust event on overall trust."""
        base_impact = trust_event.impact_score

        # Weight recent events more heavily
        time_weight = 1.0  # Recent events have full weight

        # Adjust based on event type
        type_multipliers = {"task_completion": 1.2, "permission_request": 1.0, "error_recovery": 1.5, "communication": 0.8, "autonomy_violation": -2.0}

        type_multiplier = type_multipliers.get(trust_event.event_type, 1.0)

        # Apply learning rate
        final_impact = base_impact * type_multiplier * time_weight * self.trust_update_rate

        return max(-0.5, min(0.5, final_impact))

    def _update_trust_level(self, trust_impact: float) -> float:
        """Update the current trust level."""
        # Apply trust impact with momentum
        new_trust = self.current_trust_level + trust_impact

        # Apply bounds
        new_trust = max(0.0, min(1.0, new_trust))

        # Apply time decay if no recent positive interactions
        recent_events = [e for e in self.trust_events if (datetime.now() - e.timestamp).seconds < 3600]
        if not recent_events or all(e.impact_score <= 0 for e in recent_events[-5:]):
            decay_factor = 1.0 - (1.0 / self.trust_decay_period) * 0.01
            new_trust *= decay_factor

        return new_trust

    def _update_autonomy_boundaries(self):
        """Update autonomy boundaries based on current trust level."""
        try:
            for boundary in self.autonomy_boundaries.values():
                # Adjust max autonomy level based on trust
                trust_factor = self.current_trust_level

                # High trust allows more autonomy
                if trust_factor > 0.8:
                    boundary.max_autonomy_level = min(1.0, boundary.max_autonomy_level * 1.2)
                elif trust_factor < 0.3:
                    boundary.max_autonomy_level = max(0.1, boundary.max_autonomy_level * 0.8)

                # Update trust threshold
                boundary.trust_threshold = max(0.1, trust_factor - 0.1)
                boundary.last_updated = datetime.now()

        except Exception as e:
            logger.error(f"Error updating autonomy boundaries: {e}")

    def _update_trust_stability(self):
        """Update trust stability metric."""
        try:
            if len(self.trust_events) < 10:
                return

            # Calculate variance in recent trust impacts
            recent_impacts = [e.impact_score for e in list(self.trust_events)[-20:]]
            if recent_impacts:
                mean_impact = sum(recent_impacts) / len(recent_impacts)
                variance = sum((x - mean_impact) ** 2 for x in recent_impacts) / len(recent_impacts)
            else:
                variance = 0.0

            # Stability is inverse of variance
            stability = max(0.0, 1.0 - variance * 2.0)

            with self.metrics_lock:
                self.collaboration_metrics.trust_stability = stability

        except Exception as e:
            logger.error(f"Error updating trust stability: {e}")

    def _analyze_task_requirements(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task requirements for intelligence optimization."""
        analysis = {
            "complexity": task_context.get("complexity", 0.5),
            "creativity_required": task_context.get("creativity_required", 0.3),
            "analytical_depth": task_context.get("analytical_depth", 0.5),
            "domain_expertise": task_context.get("domain_expertise", 0.5),
            "time_pressure": task_context.get("time_pressure", 0.3),
            "risk_level": task_context.get("risk_level", 0.3),
            "human_judgment_critical": task_context.get("human_judgment_critical", 0.5),
            "automation_potential": task_context.get("automation_potential", 0.7),
        }

        # Calculate overall task profile
        analysis["human_advantage_score"] = analysis["creativity_required"] * 0.3 + analysis["human_judgment_critical"] * 0.4 + analysis["domain_expertise"] * 0.3

        analysis["ai_advantage_score"] = analysis["analytical_depth"] * 0.3 + analysis["automation_potential"] * 0.4 + (1.0 - analysis["creativity_required"]) * 0.3

        return analysis

    def _calculate_optimal_distribution(self, task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal distribution of human and AI responsibilities."""
        human_score = task_analysis["human_advantage_score"]
        ai_score = task_analysis["ai_advantage_score"]

        # Determine task distribution
        if human_score > ai_score + 0.2:
            distribution_type = "human_dominant"
            human_weight = 0.7
        elif ai_score > human_score + 0.2:
            distribution_type = "ai_dominant"
            human_weight = 0.3
        else:
            distribution_type = "balanced"
            human_weight = 0.5

        # Define specific responsibilities
        human_tasks = []
        ai_tasks = []
        coordination_points = []

        if task_analysis["creativity_required"] > 0.6:
            human_tasks.append("creative_ideation")
            coordination_points.append("idea_evaluation")

        if task_analysis["analytical_depth"] > 0.6:
            ai_tasks.append("data_analysis")
            coordination_points.append("insight_validation")

        if task_analysis["human_judgment_critical"] > 0.6:
            human_tasks.append("final_decision")
            coordination_points.append("recommendation_review")

        if task_analysis["automation_potential"] > 0.6:
            ai_tasks.append("process_automation")
            coordination_points.append("automation_oversight")

        return {"type": distribution_type, "human_weight": human_weight, "ai_weight": 1.0 - human_weight, "human_tasks": human_tasks, "ai_tasks": ai_tasks, "coordination_points": coordination_points}

    def _select_optimal_collaboration_style(self, task_analysis: Dict[str, Any], intelligence_distribution: Dict[str, Any]) -> CollaborationStyle:
        """Select the optimal collaboration style."""
        distribution_type = intelligence_distribution["type"]
        trust_level = self.current_trust_level

        # Base selection on distribution type
        if distribution_type == "human_dominant":
            if trust_level > 0.7:
                return CollaborationStyle.SUPPORTIVE
            else:
                return CollaborationStyle.FOLLOWING

        elif distribution_type == "ai_dominant":
            if trust_level > 0.7:
                return CollaborationStyle.LEADING
            else:
                return CollaborationStyle.CONSULTATIVE

        else:  # balanced
            if trust_level > 0.8:
                return CollaborationStyle.EQUAL_PARTNER
            elif trust_level > 0.5:
                return CollaborationStyle.COLLABORATIVE
            else:
                return CollaborationStyle.SUPPORTIVE

    def _determine_intelligence_mode(self, intelligence_distribution: Dict[str, Any]) -> str:
        """Determine the intelligence mode based on distribution."""
        distribution_type = intelligence_distribution["type"]

        mode_mapping = {"human_dominant": IntelligenceMode.HUMAN_DOMINANT.value, "ai_dominant": IntelligenceMode.AI_DOMINANT.value, "balanced": IntelligenceMode.BALANCED.value}

        return mode_mapping.get(distribution_type, IntelligenceMode.DYNAMIC.value)

    def _define_success_metrics(self, task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Define success metrics for the collaboration."""
        return {"task_completion": 1.0, "quality_threshold": 0.8, "efficiency_target": 0.7, "user_satisfaction_target": 0.8, "time_budget_adherence": 0.9, "error_rate_threshold": 0.1}

    def _identify_adaptation_triggers(self, task_context: Dict[str, Any]) -> List[str]:
        """Identify potential adaptation triggers for the task."""
        triggers = []

        if task_context.get("complexity", 0.5) > 0.7:
            triggers.append("complexity_increase")

        if task_context.get("time_pressure", 0.3) > 0.7:
            triggers.append("time_pressure")

        if task_context.get("risk_level", 0.3) > 0.6:
            triggers.append("risk_escalation")

        triggers.extend(["user_feedback", "performance_decline", "trust_change"])

        return triggers

    def _generate_context_signature(self, context: Dict[str, Any]) -> str:
        """Generate a signature for the current context."""
        # Create a simplified signature based on key context elements
        key_elements = [context.get("task_type", "unknown"), context.get("domain", "general"), str(int(context.get("complexity", 0.5) * 10)), str(int(context.get("urgency", 0.3) * 10))]

        return "_".join(key_elements)

    def _get_or_create_boundary(self, context_signature: str, context: Dict[str, Any]) -> AutonomyBoundary:
        """Get existing or create new autonomy boundary."""
        if context_signature in self.autonomy_boundaries:
            return self.autonomy_boundaries[context_signature]

        # Create new boundary
        boundary = AutonomyBoundary(
            boundary_id=f"boundary_{context_signature}",
            context_pattern=context_signature,
            max_autonomy_level=0.6,  # Default medium autonomy
            required_permissions={"medium_risk", "data_access"},
            escalation_triggers=["high_risk", "user_safety", "data_privacy"],
            trust_threshold=0.5,
            last_updated=datetime.now(),
        )

        self.autonomy_boundaries[context_signature] = boundary
        return boundary

    def _adjust_boundary_for_trust(self, boundary: AutonomyBoundary) -> AutonomyBoundary:
        """Adjust autonomy boundary based on current trust level."""
        adjusted_boundary = AutonomyBoundary(
            boundary_id=boundary.boundary_id,
            context_pattern=boundary.context_pattern,
            max_autonomy_level=min(1.0, boundary.max_autonomy_level * (0.5 + self.current_trust_level)),
            required_permissions=boundary.required_permissions.copy(),
            escalation_triggers=boundary.escalation_triggers.copy(),
            trust_threshold=boundary.trust_threshold,
            last_updated=datetime.now(),
        )

        # Adjust permissions based on trust
        if self.current_trust_level > 0.8:
            adjusted_boundary.required_permissions.discard("low_risk")
        elif self.current_trust_level < 0.3:
            adjusted_boundary.required_permissions.add("all_actions")

        return adjusted_boundary

    def _calculate_auto_execute_threshold(self, boundary: AutonomyBoundary) -> float:
        """Calculate threshold for automatic execution."""
        base_threshold = boundary.max_autonomy_level
        trust_adjustment = self.current_trust_level * 0.3

        return min(1.0, base_threshold + trust_adjustment)

    def _get_trust_based_adjustments(self) -> Dict[str, Any]:
        """Get trust-based adjustments for autonomy."""
        return {
            "confirmation_required": self.current_trust_level < 0.6,
            "detailed_explanations": self.current_trust_level < 0.4,
            "step_by_step_approval": self.current_trust_level < 0.3,
            "full_transparency": self.current_trust_level < 0.5,
        }

    def _get_context_specific_rules(self, context: Dict[str, Any]) -> List[str]:
        """Get context-specific autonomy rules."""
        rules = []

        if context.get("risk_level", 0.3) > 0.7:
            rules.append("require_explicit_permission_for_high_risk")

        if context.get("data_sensitive", False):
            rules.append("no_data_modification_without_approval")

        if context.get("user_present", True):
            rules.append("prefer_collaboration_over_automation")

        return rules

    def _detect_context_shift(self, context: Dict[str, Any]) -> bool:
        """Detect if there has been a significant context shift."""
        if not self.context_patterns:
            return False

        current_signature = self._generate_context_signature(context)
        recent_patterns = list(self.context_patterns.keys())[-10:]

        # Check if current context is significantly different from recent patterns
        return current_signature not in recent_patterns

    def _learn_from_adaptation(self, strategy: Dict[str, Any], success: bool, context: Dict[str, Any]):
        """Learn from adaptation results."""
        try:
            adaptation_key = f"{strategy['type']}_{self._generate_context_signature(context)}"

            if success:
                self.successful_adaptations[adaptation_key] += 1
            else:
                self.failed_adaptations[adaptation_key] += 1

            with self.metrics_lock:
                # Update overall adaptation success rate
                all_successful = sum(self.successful_adaptations.values())
                all_total = all_successful + sum(self.failed_adaptations.values())

                if all_total > 0:
                    self.collaboration_metrics.adaptation_success_rate = all_successful / all_total

        except Exception as e:
            logger.error(f"Error learning from adaptation: {e}")

    def _update_collaboration_metrics(self, feedback: Dict[str, Any], adaptation_success: bool):
        """Update collaboration metrics based on feedback."""
        try:
            with self.metrics_lock:
                # Update user satisfaction
                if "satisfaction" in feedback:
                    current_satisfaction = self.collaboration_metrics.user_satisfaction_score
                    new_satisfaction = feedback["satisfaction"]
                    # Exponential moving average
                    self.collaboration_metrics.user_satisfaction_score = current_satisfaction * 0.8 + new_satisfaction * 0.2

                # Update efficiency ratio
                if "efficiency" in feedback:
                    current_efficiency = self.collaboration_metrics.efficiency_ratio
                    new_efficiency = feedback["efficiency"]
                    self.collaboration_metrics.efficiency_ratio = current_efficiency * 0.8 + new_efficiency * 0.2

                # Update communication effectiveness
                if "communication_effectiveness" in feedback:
                    current_comm = self.collaboration_metrics.communication_effectiveness
                    new_comm = feedback["communication_effectiveness"]
                    self.collaboration_metrics.communication_effectiveness = current_comm * 0.8 + new_comm * 0.2

                self.collaboration_metrics.last_updated = datetime.now()

        except Exception as e:
            logger.error(f"Error updating collaboration metrics: {e}")

    def _initialize_default_boundaries(self):
        """Initialize default autonomy boundaries."""
        default_contexts = [
            ("general_task", {"max_autonomy": 0.6, "permissions": {"medium_risk"}}),
            ("data_analysis", {"max_autonomy": 0.8, "permissions": {"data_access"}}),
            ("creative_task", {"max_autonomy": 0.4, "permissions": {"low_risk"}}),
            ("high_risk_task", {"max_autonomy": 0.2, "permissions": {"high_risk", "explicit_approval"}}),
        ]

        for context_name, config in default_contexts:
            boundary = AutonomyBoundary(
                boundary_id=f"default_{context_name}",
                context_pattern=context_name,
                max_autonomy_level=config["max_autonomy"],
                required_permissions=set(config["permissions"]),
                escalation_triggers=["user_safety", "data_privacy", "high_risk"],
                trust_threshold=0.5,
                last_updated=datetime.now(),
            )
            self.autonomy_boundaries[context_name] = boundary

    def get_collaboration_status(self) -> Dict[str, Any]:
        """Get current collaboration status and metrics."""
        return {
            "current_collaboration_style": self.current_collaboration_style.value,
            "current_intelligence_mode": self.current_intelligence_mode.value,
            "current_trust_level": self.current_trust_level,
            "behavior_patterns_learned": len(self.behavior_patterns),
            "autonomy_boundaries_defined": len(self.autonomy_boundaries),
            "collaboration_metrics": {
                "task_completion_rate": self.collaboration_metrics.task_completion_rate,
                "user_satisfaction_score": self.collaboration_metrics.user_satisfaction_score,
                "efficiency_ratio": self.collaboration_metrics.efficiency_ratio,
                "communication_effectiveness": self.collaboration_metrics.communication_effectiveness,
                "trust_stability": self.collaboration_metrics.trust_stability,
                "adaptation_success_rate": self.collaboration_metrics.adaptation_success_rate,
            },
            "recent_adaptations": {"successful": sum(list(self.successful_adaptations.values())[-10:]), "failed": sum(list(self.failed_adaptations.values())[-10:])},
        }

    def process(self, context: Context) -> Dict[str, Any]:
        """Process context for adaptive collaboration."""
        try:
            # Update context patterns
            context_dict = getattr(context, "system_state", {})
            context_signature = self._generate_context_signature(context_dict)
            self.context_patterns[context_signature].append({"timestamp": datetime.now().isoformat(), "context": context_dict})

            # Return current collaboration status
            return {"success": True, "data": self.get_collaboration_status(), "metadata": {"component": "AdaptiveCollaborationEngine", "operation": "status_check"}}

        except Exception as e:
            logger.error(f"Error in process method: {e}")
            return {"success": False, "error": str(e), "metadata": {"component": "AdaptiveCollaborationEngine", "operation": "process"}}
