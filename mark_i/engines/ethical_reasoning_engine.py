"""Ethical Reasoning Engine for MARK-I responsible decision making.

This module provides comprehensive ethical evaluation, risk assessment, and moral
reasoning capabilities to ensure all AI actions align with ethical principles
and prioritize user safety and well-being.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, deque
from enum import Enum
import hashlib

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import IEthicalReasoningEngine, Context, Action
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".engines.ethical_reasoning")


class RiskLevel(Enum):
    """Risk levels for actions."""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EthicalPrinciple(Enum):
    """Core ethical principles."""

    USER_SAFETY = "user_safety"
    PRIVACY = "privacy"
    AUTONOMY = "autonomy"
    BENEFICENCE = "beneficence"
    NON_MALEFICENCE = "non_maleficence"
    JUSTICE = "justice"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"


class EthicalViolationType(Enum):
    """Types of ethical violations."""

    SAFETY_RISK = "safety_risk"
    PRIVACY_BREACH = "privacy_breach"
    AUTONOMY_VIOLATION = "autonomy_violation"
    HARM_POTENTIAL = "harm_potential"
    DECEPTION = "deception"
    UNFAIRNESS = "unfairness"
    LACK_OF_TRANSPARENCY = "lack_of_transparency"


@dataclass
class EthicalGuideline:
    """Represents an ethical guideline."""

    guideline_id: str
    principle: EthicalPrinciple
    description: str
    priority: int  # 1-10, higher is more important
    conditions: Dict[str, Any]
    exceptions: List[str]
    last_updated: datetime


@dataclass
class EthicalEvaluation:
    """Results of ethical evaluation."""

    action_id: str
    overall_risk_level: RiskLevel
    ethical_score: float  # 0.0-1.0, higher is more ethical
    violations: List[Dict[str, Any]]
    concerns: List[str]
    recommendations: List[str]
    alternative_actions: List[Action]
    evaluation_timestamp: datetime
    confidence: float


@dataclass
class RiskAssessment:
    """Detailed risk assessment for an action."""

    risk_id: str
    action_description: str
    risk_factors: Dict[str, float]
    mitigation_strategies: List[str]
    probability: float
    impact_severity: float
    overall_risk_score: float
    risk_level: RiskLevel
    assessment_timestamp: datetime


@dataclass
class EthicalDecision:
    """Record of an ethical decision."""

    decision_id: str
    original_action: Action
    evaluation: EthicalEvaluation
    decision: str  # "approve", "reject", "modify"
    modified_action: Optional[Action]
    reasoning: str
    decision_maker: str  # "ai", "human", "collaborative"
    timestamp: datetime
    outcome: Optional[str] = None


class EthicalReasoningEngine(ProcessingComponent, IEthicalReasoningEngine):
    """
    Advanced ethical reasoning engine for responsible AI decision making.

    Provides comprehensive ethical evaluation, risk assessment, and moral
    reasoning to ensure all actions align with ethical principles and
    prioritize user safety and well-being.
    """

    def __init__(self, config: ComponentConfig):
        super().__init__("ethical_reasoning_engine", config)

        # Configuration
        self.safety_threshold = getattr(config, "safety_threshold", 0.8)
        self.risk_tolerance = getattr(config, "risk_tolerance", 0.3)
        self.ethical_score_threshold = getattr(config, "ethical_score_threshold", 0.7)
        self.require_human_approval_threshold = getattr(config, "require_human_approval_threshold", 0.6)
        self.max_decision_history = getattr(config, "max_decision_history", 10000)

        # Ethical guidelines and principles
        self.ethical_guidelines: Dict[str, EthicalGuideline] = {}
        self.principle_weights: Dict[EthicalPrinciple, float] = {}
        self.contextual_rules: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Decision tracking and learning
        self.decision_history: deque = deque(maxlen=self.max_decision_history)
        self.violation_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.successful_decisions: Dict[str, int] = defaultdict(int)
        self.failed_decisions: Dict[str, int] = defaultdict(int)

        # Risk assessment data
        self.risk_factors: Dict[str, float] = {}
        self.mitigation_strategies: Dict[str, List[str]] = defaultdict(list)
        self.risk_history: deque = deque(maxlen=5000)

        # Threading and synchronization
        self.evaluation_lock = threading.Lock()
        self.guidelines_lock = threading.Lock()

        # Statistics
        self.evaluations_performed = 0
        self.actions_approved = 0
        self.actions_rejected = 0
        self.actions_modified = 0
        self.safety_interventions = 0

        # Initialize default guidelines and principles
        self._initialize_default_guidelines()
        self._initialize_principle_weights()
        self._initialize_risk_factors()

        logger.info("EthicalReasoningEngine initialized for responsible AI decision making")

    def evaluate_action_ethics(self, action: Action, context: Context) -> Dict[str, Any]:
        """Evaluate the ethical implications of an action."""
        try:
            with self.evaluation_lock:
                # Create evaluation ID
                evaluation_id = f"eval_{int(time.time() * 1000)}_{hashlib.md5(str(action).encode()).hexdigest()[:8]}"

                # Perform comprehensive ethical evaluation
                evaluation = self._perform_ethical_evaluation(action, context, evaluation_id)

                # Record evaluation
                self.decision_history.append(evaluation)
                self.evaluations_performed += 1

                # Create response
                response = {
                    "evaluation_id": evaluation_id,
                    "ethical_score": evaluation.ethical_score,
                    "risk_level": evaluation.overall_risk_level.value,
                    "violations": evaluation.violations,
                    "concerns": evaluation.concerns,
                    "recommendations": evaluation.recommendations,
                    "requires_human_approval": evaluation.ethical_score < self.require_human_approval_threshold,
                    "safe_to_proceed": evaluation.overall_risk_level in [RiskLevel.MINIMAL, RiskLevel.LOW],
                    "alternative_actions": [self._action_to_dict(alt) for alt in evaluation.alternative_actions],
                    "confidence": evaluation.confidence,
                }

                logger.info(f"Ethical evaluation completed: {evaluation_id}, score: {evaluation.ethical_score:.2f}, risk: {evaluation.overall_risk_level.value}")
                return response

        except Exception as e:
            logger.error(f"Error in ethical evaluation: {e}")
            return {"error": str(e), "ethical_score": 0.0, "risk_level": RiskLevel.CRITICAL.value, "safe_to_proceed": False}

    def assess_risk_level(self, action: Action, context: Context) -> str:
        """Assess the risk level of an action."""
        try:
            # Perform risk assessment
            risk_assessment = self._perform_risk_assessment(action, context)

            # Record risk assessment
            self.risk_history.append(risk_assessment)

            logger.info(f"Risk assessment: {risk_assessment.risk_level.value} (score: {risk_assessment.overall_risk_score:.2f})")
            return risk_assessment.risk_level.value

        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return RiskLevel.CRITICAL.value

    def suggest_alternatives(self, action: Action, ethical_issues: Dict[str, Any]) -> List[Action]:
        """Suggest alternative actions when ethical issues are detected."""
        try:
            alternatives = []

            # Analyze ethical issues to determine alternative strategies
            violations = ethical_issues.get("violations", [])
            concerns = ethical_issues.get("concerns", [])

            # Generate alternatives based on violation types
            for violation in violations:
                violation_type = violation.get("type")
                alternatives.extend(self._generate_alternatives_for_violation(action, violation_type))

            # Generate alternatives based on concerns
            for concern in concerns:
                alternatives.extend(self._generate_alternatives_for_concern(action, concern))

            # Remove duplicates and validate alternatives
            unique_alternatives = self._deduplicate_alternatives(alternatives)
            validated_alternatives = self._validate_alternatives(unique_alternatives, action)

            logger.info(f"Generated {len(validated_alternatives)} alternative actions")
            return validated_alternatives

        except Exception as e:
            logger.error(f"Error generating alternatives: {e}")
            return []

    def update_ethical_guidelines(self, guidelines: Dict[str, Any]) -> None:
        """Update ethical guidelines."""
        try:
            with self.guidelines_lock:
                for guideline_id, guideline_data in guidelines.items():
                    if guideline_id in self.ethical_guidelines:
                        # Update existing guideline
                        existing = self.ethical_guidelines[guideline_id]
                        existing.description = guideline_data.get("description", existing.description)
                        existing.priority = guideline_data.get("priority", existing.priority)
                        existing.conditions = guideline_data.get("conditions", existing.conditions)
                        existing.exceptions = guideline_data.get("exceptions", existing.exceptions)
                        existing.last_updated = datetime.now()
                    else:
                        # Create new guideline
                        guideline = EthicalGuideline(
                            guideline_id=guideline_id,
                            principle=EthicalPrinciple(guideline_data["principle"]),
                            description=guideline_data["description"],
                            priority=guideline_data.get("priority", 5),
                            conditions=guideline_data.get("conditions", {}),
                            exceptions=guideline_data.get("exceptions", []),
                            last_updated=datetime.now(),
                        )
                        self.ethical_guidelines[guideline_id] = guideline

                logger.info(f"Updated {len(guidelines)} ethical guidelines")

        except Exception as e:
            logger.error(f"Error updating ethical guidelines: {e}")

    def get_ethical_guidelines(self) -> Dict[str, Any]:
        """Get current ethical guidelines."""
        try:
            with self.guidelines_lock:
                guidelines = {}
                for guideline_id, guideline in self.ethical_guidelines.items():
                    guidelines[guideline_id] = {
                        "principle": guideline.principle.value,
                        "description": guideline.description,
                        "priority": guideline.priority,
                        "conditions": guideline.conditions,
                        "exceptions": guideline.exceptions,
                        "last_updated": guideline.last_updated.isoformat(),
                    }

                return {
                    "guidelines": guidelines,
                    "principle_weights": {p.value: w for p, w in self.principle_weights.items()},
                    "safety_threshold": self.safety_threshold,
                    "risk_tolerance": self.risk_tolerance,
                    "ethical_score_threshold": self.ethical_score_threshold,
                }

        except Exception as e:
            logger.error(f"Error getting ethical guidelines: {e}")
            return {"error": str(e)}

    def _perform_ethical_evaluation(self, action: Action, context: Context, evaluation_id: str) -> EthicalEvaluation:
        """Perform comprehensive ethical evaluation."""
        # Assess each ethical principle
        principle_scores = {}
        violations = []
        concerns = []

        for principle in EthicalPrinciple:
            score, principle_violations, principle_concerns = self._evaluate_principle(action, context, principle)
            principle_scores[principle] = score
            violations.extend(principle_violations)
            concerns.extend(principle_concerns)

        # Calculate overall ethical score
        ethical_score = self._calculate_overall_ethical_score(principle_scores)

        # Assess risk level
        risk_assessment = self._perform_risk_assessment(action, context)

        # Generate recommendations
        recommendations = self._generate_recommendations(principle_scores, violations, concerns)

        # Generate alternative actions if needed
        alternative_actions = []
        if ethical_score < self.ethical_score_threshold or risk_assessment.overall_risk_score > self.risk_tolerance:
            alternative_actions = self.suggest_alternatives(action, {"violations": violations, "concerns": concerns})

        # Calculate confidence
        confidence = self._calculate_evaluation_confidence(principle_scores, risk_assessment)

        return EthicalEvaluation(
            action_id=evaluation_id,
            overall_risk_level=risk_assessment.risk_level,
            ethical_score=ethical_score,
            violations=violations,
            concerns=concerns,
            recommendations=recommendations,
            alternative_actions=alternative_actions,
            evaluation_timestamp=datetime.now(),
            confidence=confidence,
        )

    def _perform_risk_assessment(self, action: Action, context: Context) -> RiskAssessment:
        """Perform detailed risk assessment."""
        risk_id = f"risk_{int(time.time() * 1000)}"

        # Evaluate risk factors
        risk_factors = {}
        for factor_name, base_weight in self.risk_factors.items():
            factor_score = self._evaluate_risk_factor(action, context, factor_name)
            risk_factors[factor_name] = factor_score * base_weight

        # Calculate probability and impact
        probability = self._calculate_risk_probability(action, context, risk_factors)
        impact_severity = self._calculate_impact_severity(action, context, risk_factors)

        # Calculate overall risk score
        overall_risk_score = probability * impact_severity

        # Determine risk level
        risk_level = self._determine_risk_level(overall_risk_score)

        # Generate mitigation strategies
        mitigation_strategies = self._generate_mitigation_strategies(action, risk_factors)

        return RiskAssessment(
            risk_id=risk_id,
            action_description=str(action),
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            probability=probability,
            impact_severity=impact_severity,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            assessment_timestamp=datetime.now(),
        )

    def _evaluate_principle(self, action: Action, context: Context, principle: EthicalPrinciple) -> Tuple[float, List[Dict[str, Any]], List[str]]:
        """Evaluate an action against a specific ethical principle."""
        violations = []
        concerns = []
        score = 1.0  # Start with perfect score

        if principle == EthicalPrinciple.USER_SAFETY:
            score, principle_violations, principle_concerns = self._evaluate_user_safety(action, context)
            violations.extend(principle_violations)
            concerns.extend(principle_concerns)

        elif principle == EthicalPrinciple.PRIVACY:
            score, principle_violations, principle_concerns = self._evaluate_privacy(action, context)
            violations.extend(principle_violations)
            concerns.extend(principle_concerns)

        elif principle == EthicalPrinciple.AUTONOMY:
            score, principle_violations, principle_concerns = self._evaluate_autonomy(action, context)
            violations.extend(principle_violations)
            concerns.extend(principle_concerns)

        elif principle == EthicalPrinciple.BENEFICENCE:
            score, principle_violations, principle_concerns = self._evaluate_beneficence(action, context)
            violations.extend(principle_violations)
            concerns.extend(principle_concerns)

        elif principle == EthicalPrinciple.NON_MALEFICENCE:
            score, principle_violations, principle_concerns = self._evaluate_non_maleficence(action, context)
            violations.extend(principle_violations)
            concerns.extend(principle_concerns)

        elif principle == EthicalPrinciple.TRANSPARENCY:
            score, principle_violations, principle_concerns = self._evaluate_transparency(action, context)
            violations.extend(principle_violations)
            concerns.extend(principle_concerns)

        return score, violations, concerns

    def _evaluate_user_safety(self, action: Action, context: Context) -> Tuple[float, List[Dict[str, Any]], List[str]]:
        """Evaluate user safety implications."""
        violations = []
        concerns = []
        score = 1.0

        # Check for direct safety risks
        action_type = getattr(action, "action_type", "unknown")
        action_params = getattr(action, "parameters", {})

        # File system operations
        if action_type in ["file_delete", "file_modify", "system_command"]:
            if action_params.get("target", "").startswith("/"):
                # System file access
                violations.append(
                    {
                        "type": EthicalViolationType.SAFETY_RISK.value,
                        "severity": "high",
                        "description": "Action involves system file access which could compromise system safety",
                        "principle": EthicalPrinciple.USER_SAFETY.value,
                    }
                )
                score -= 0.5

        # Network operations
        if action_type in ["network_request", "data_upload"]:
            if not action_params.get("secure", True):
                concerns.append("Insecure network operation may expose user data")
                score -= 0.2

        # Data operations
        if action_type in ["data_delete", "data_modify"]:
            if not action_params.get("backup_created", False):
                concerns.append("Data modification without backup poses data loss risk")
                score -= 0.3

        return max(0.0, score), violations, concerns

    def _evaluate_privacy(self, action: Action, context: Context) -> Tuple[float, List[Dict[str, Any]], List[str]]:
        """Evaluate privacy implications."""
        violations = []
        concerns = []
        score = 1.0

        action_type = getattr(action, "action_type", "unknown")
        action_params = getattr(action, "parameters", {})

        # Data access and collection
        if action_type in ["data_read", "data_collect", "screen_capture"]:
            if action_params.get("contains_personal_data", False):
                if not action_params.get("user_consent", False):
                    violations.append(
                        {
                            "type": EthicalViolationType.PRIVACY_BREACH.value,
                            "severity": "high",
                            "description": "Accessing personal data without explicit user consent",
                            "principle": EthicalPrinciple.PRIVACY.value,
                        }
                    )
                    score -= 0.6

        # Data sharing
        if action_type in ["data_share", "data_upload", "network_request"]:
            if action_params.get("third_party_access", False):
                if not action_params.get("privacy_policy_accepted", False):
                    concerns.append("Data sharing with third parties without privacy policy acceptance")
                    score -= 0.3

        return max(0.0, score), violations, concerns

    def _evaluate_autonomy(self, action: Action, context: Context) -> Tuple[float, List[Dict[str, Any]], List[str]]:
        """Evaluate user autonomy implications."""
        violations = []
        concerns = []
        score = 1.0

        action_type = getattr(action, "action_type", "unknown")
        action_params = getattr(action, "parameters", {})

        # Actions that limit user choice
        if action_type in ["setting_change", "preference_update", "auto_execute"]:
            if not action_params.get("user_initiated", False):
                if action_params.get("reversible", True):
                    concerns.append("Autonomous action without user initiation (but reversible)")
                    score -= 0.2
                else:
                    violations.append(
                        {
                            "type": EthicalViolationType.AUTONOMY_VIOLATION.value,
                            "severity": "medium",
                            "description": "Irreversible autonomous action without user initiation",
                            "principle": EthicalPrinciple.AUTONOMY.value,
                        }
                    )
                    score -= 0.4

        return max(0.0, score), violations, concerns

    def _evaluate_beneficence(self, action: Action, context: Context) -> Tuple[float, List[Dict[str, Any]], List[str]]:
        """Evaluate beneficence (doing good) implications."""
        violations = []
        concerns = []
        score = 0.5  # Neutral starting point

        action_type = getattr(action, "action_type", "unknown")
        action_params = getattr(action, "parameters", {})

        # Positive actions
        if action_type in ["help_user", "optimize_performance", "provide_information"]:
            score += 0.3

        # Actions with unclear benefit
        if action_type in ["data_collect", "monitor_activity"]:
            if not action_params.get("clear_benefit_to_user", False):
                concerns.append("Action benefit to user is unclear")
                score -= 0.2

        return max(0.0, min(1.0, score)), violations, concerns

    def _evaluate_non_maleficence(self, action: Action, context: Context) -> Tuple[float, List[Dict[str, Any]], List[str]]:
        """Evaluate non-maleficence (do no harm) implications."""
        violations = []
        concerns = []
        score = 1.0

        action_type = getattr(action, "action_type", "unknown")
        action_params = getattr(action, "parameters", {})

        # Potentially harmful actions
        if action_type in ["system_command", "file_delete", "data_delete"]:
            if action_params.get("destructive", False):
                violations.append(
                    {
                        "type": EthicalViolationType.HARM_POTENTIAL.value,
                        "severity": "high",
                        "description": "Action has potential for irreversible harm",
                        "principle": EthicalPrinciple.NON_MALEFICENCE.value,
                    }
                )
                score -= 0.7

        # Actions with side effects
        if action_params.get("side_effects", []):
            concerns.append("Action may have unintended side effects")
            score -= 0.2

        return max(0.0, score), violations, concerns

    def _evaluate_transparency(self, action: Action, context: Context) -> Tuple[float, List[Dict[str, Any]], List[str]]:
        """Evaluate transparency implications."""
        violations = []
        concerns = []
        score = 1.0

        action_params = getattr(action, "parameters", {})

        # Hidden or opaque actions
        if action_params.get("hidden_from_user", False):
            violations.append(
                {
                    "type": EthicalViolationType.LACK_OF_TRANSPARENCY.value,
                    "severity": "medium",
                    "description": "Action is hidden from user without justification",
                    "principle": EthicalPrinciple.TRANSPARENCY.value,
                }
            )
            score -= 0.5

        # Actions without clear explanation
        if not action_params.get("explanation_available", True):
            concerns.append("Action lacks clear explanation for user")
            score -= 0.3

        return max(0.0, score), violations, concerns

    def _calculate_overall_ethical_score(self, principle_scores: Dict[EthicalPrinciple, float]) -> float:
        """Calculate overall ethical score from principle scores."""
        weighted_sum = 0.0
        total_weight = 0.0

        for principle, score in principle_scores.items():
            weight = self.principle_weights.get(principle, 1.0)
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _evaluate_risk_factor(self, action: Action, context: Context, factor_name: str) -> float:
        """Evaluate a specific risk factor."""
        action_type = getattr(action, "action_type", "unknown")
        action_params = getattr(action, "parameters", {})

        if factor_name == "data_sensitivity":
            return 1.0 if action_params.get("contains_personal_data", False) else 0.3

        elif factor_name == "system_impact":
            if action_type in ["system_command", "setting_change"]:
                return 0.8
            elif action_type in ["file_modify", "data_modify"]:
                return 0.5
            else:
                return 0.2

        elif factor_name == "reversibility":
            return 0.9 if not action_params.get("reversible", True) else 0.1

        elif factor_name == "user_consent":
            return 0.8 if not action_params.get("user_consent", False) else 0.1

        elif factor_name == "network_exposure":
            return 0.7 if action_type in ["network_request", "data_upload"] else 0.1

        else:
            return 0.3  # Default moderate risk

    def _calculate_risk_probability(self, action: Action, context: Context, risk_factors: Dict[str, float]) -> float:
        """Calculate probability of risk occurrence."""
        # Base probability on action type
        action_type = getattr(action, "action_type", "unknown")

        base_probability = {"system_command": 0.6, "file_delete": 0.5, "data_delete": 0.4, "network_request": 0.3, "file_read": 0.1, "data_read": 0.1}.get(action_type, 0.2)

        # Adjust based on risk factors
        factor_adjustment = sum(risk_factors.values()) / len(risk_factors) if risk_factors else 0.0

        return min(1.0, base_probability + factor_adjustment * 0.3)

    def _calculate_impact_severity(self, action: Action, context: Context, risk_factors: Dict[str, float]) -> float:
        """Calculate severity of potential impact."""
        action_params = getattr(action, "parameters", {})

        # Base severity on action characteristics
        base_severity = 0.3

        if action_params.get("destructive", False):
            base_severity += 0.4

        if action_params.get("contains_personal_data", False):
            base_severity += 0.3

        if not action_params.get("reversible", True):
            base_severity += 0.3

        # Adjust based on risk factors
        high_risk_factors = [f for f, score in risk_factors.items() if score > 0.6]
        severity_adjustment = len(high_risk_factors) * 0.1

        return min(1.0, base_severity + severity_adjustment)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from risk score."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL

    def _generate_mitigation_strategies(self, action: Action, risk_factors: Dict[str, float]) -> List[str]:
        """Generate mitigation strategies for identified risks."""
        strategies = []

        for factor, score in risk_factors.items():
            if score > 0.5:  # High risk factor
                if factor == "data_sensitivity":
                    strategies.extend(["Encrypt sensitive data before processing", "Request explicit user consent for data access", "Implement data anonymization where possible"])
                elif factor == "system_impact":
                    strategies.extend(["Create system backup before making changes", "Implement rollback mechanism", "Test changes in safe environment first"])
                elif factor == "reversibility":
                    strategies.extend(["Create undo functionality", "Implement change logging for recovery", "Request user confirmation before irreversible actions"])
                elif factor == "network_exposure":
                    strategies.extend(["Use encrypted connections (HTTPS/TLS)", "Validate server certificates", "Implement timeout and retry mechanisms"])

        return list(set(strategies))  # Remove duplicates

    def _generate_recommendations(self, principle_scores: Dict[EthicalPrinciple, float], violations: List[Dict[str, Any]], concerns: List[str]) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []

        # Recommendations based on low principle scores
        for principle, score in principle_scores.items():
            if score < 0.6:
                if principle == EthicalPrinciple.USER_SAFETY:
                    recommendations.append("Implement additional safety checks and user warnings")
                elif principle == EthicalPrinciple.PRIVACY:
                    recommendations.append("Add privacy protection measures and user consent mechanisms")
                elif principle == EthicalPrinciple.AUTONOMY:
                    recommendations.append("Provide user control options and clear opt-out mechanisms")
                elif principle == EthicalPrinciple.TRANSPARENCY:
                    recommendations.append("Add clear explanations and make actions visible to user")

        # Recommendations based on violations
        for violation in violations:
            if violation["severity"] == "high":
                recommendations.append(f"Address critical {violation['type']} violation immediately")
            else:
                recommendations.append(f"Consider mitigating {violation['type']} concern")

        # General recommendations based on concerns
        if len(concerns) > 3:
            recommendations.append("Consider alternative approach due to multiple ethical concerns")

        return recommendations

    def _generate_alternatives_for_violation(self, action: Action, violation_type: str) -> List[Action]:
        """Generate alternative actions for a specific violation type."""
        alternatives = []
        action_type = getattr(action, "action_type", "unknown")
        action_params = getattr(action, "parameters", {})

        if violation_type == EthicalViolationType.SAFETY_RISK.value:
            # Create safer version of the action
            safe_params = action_params.copy()
            safe_params["safe_mode"] = True
            safe_params["user_confirmation_required"] = True
            alternatives.append(Action(action_type=f"safe_{action_type}", parameters=safe_params))

        elif violation_type == EthicalViolationType.PRIVACY_BREACH.value:
            # Create privacy-preserving version
            private_params = action_params.copy()
            private_params["anonymize_data"] = True
            private_params["request_consent"] = True
            alternatives.append(Action(action_type=f"private_{action_type}", parameters=private_params))

        elif violation_type == EthicalViolationType.AUTONOMY_VIOLATION.value:
            # Create user-controlled version
            controlled_params = action_params.copy()
            controlled_params["user_initiated"] = True
            controlled_params["user_approval_required"] = True
            alternatives.append(Action(action_type=f"user_controlled_{action_type}", parameters=controlled_params))

        return alternatives

    def _generate_alternatives_for_concern(self, action: Action, concern: str) -> List[Action]:
        """Generate alternative actions for a specific concern."""
        alternatives = []
        action_type = getattr(action, "action_type", "unknown")
        action_params = getattr(action, "parameters", {})

        if "backup" in concern.lower():
            # Create version with backup
            backup_params = action_params.copy()
            backup_params["create_backup"] = True
            alternatives.append(Action(action_type=f"backup_{action_type}", parameters=backup_params))

        elif "explanation" in concern.lower():
            # Create version with explanation
            explained_params = action_params.copy()
            explained_params["provide_explanation"] = True
            explained_params["show_reasoning"] = True
            alternatives.append(Action(action_type=f"explained_{action_type}", parameters=explained_params))

        return alternatives

    def _deduplicate_alternatives(self, alternatives: List[Action]) -> List[Action]:
        """Remove duplicate alternative actions."""
        seen = set()
        unique_alternatives = []

        for action in alternatives:
            action_signature = f"{getattr(action, 'action_type', 'unknown')}_{hash(str(getattr(action, 'parameters', {})))}"
            if action_signature not in seen:
                seen.add(action_signature)
                unique_alternatives.append(action)

        return unique_alternatives

    def _validate_alternatives(self, alternatives: List[Action], original_action: Action) -> List[Action]:
        """Validate that alternatives are actually better than original."""
        validated = []

        for alternative in alternatives:
            # Quick ethical check on alternative
            try:
                # Create minimal context for validation
                validation_context = Context(timestamp=datetime.now())
                alt_evaluation = self._perform_ethical_evaluation(alternative, validation_context, "validation")

                # Only include if alternative is ethically better
                if alt_evaluation.ethical_score > 0.6:  # Minimum acceptable score
                    validated.append(alternative)
            except Exception as e:
                logger.warning(f"Failed to validate alternative: {e}")
                continue

        return validated[:5]  # Limit to top 5 alternatives

    def _calculate_evaluation_confidence(self, principle_scores: Dict[EthicalPrinciple, float], risk_assessment: RiskAssessment) -> float:
        """Calculate confidence in the evaluation."""
        # Base confidence on consistency of principle scores
        scores = list(principle_scores.values())
        if scores:
            score_variance = sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)
            consistency_factor = max(0.1, 1.0 - score_variance)
        else:
            consistency_factor = 0.5

        # Adjust based on risk assessment confidence
        risk_confidence = 1.0 - abs(risk_assessment.probability - 0.5)  # Higher confidence when probability is clear

        # Combine factors
        overall_confidence = (consistency_factor + risk_confidence) / 2

        return min(1.0, max(0.1, overall_confidence))

    def _action_to_dict(self, action: Action) -> Dict[str, Any]:
        """Convert action to dictionary representation."""
        return {
            "action_type": getattr(action, "action_type", "unknown"),
            "parameters": getattr(action, "parameters", {}),
            "description": getattr(action, "description", ""),
            "estimated_duration": getattr(action, "estimated_duration", 0),
        }

    def _initialize_default_guidelines(self):
        """Initialize default ethical guidelines."""
        default_guidelines = [
            {
                "id": "user_safety_priority",
                "principle": EthicalPrinciple.USER_SAFETY,
                "description": "User safety must be the highest priority in all actions",
                "priority": 10,
                "conditions": {},
                "exceptions": [],
            },
            {
                "id": "privacy_protection",
                "principle": EthicalPrinciple.PRIVACY,
                "description": "User privacy must be protected and consent obtained for data access",
                "priority": 9,
                "conditions": {"data_access": True},
                "exceptions": ["emergency_situations"],
            },
            {
                "id": "user_autonomy",
                "principle": EthicalPrinciple.AUTONOMY,
                "description": "Users must maintain control over their systems and data",
                "priority": 8,
                "conditions": {},
                "exceptions": ["safety_critical_situations"],
            },
            {
                "id": "do_no_harm",
                "principle": EthicalPrinciple.NON_MALEFICENCE,
                "description": "Actions must not cause harm to users or their systems",
                "priority": 9,
                "conditions": {},
                "exceptions": [],
            },
            {
                "id": "transparency_requirement",
                "principle": EthicalPrinciple.TRANSPARENCY,
                "description": "Actions and reasoning must be transparent to users",
                "priority": 7,
                "conditions": {},
                "exceptions": ["security_sensitive_operations"],
            },
        ]

        for guideline_data in default_guidelines:
            guideline = EthicalGuideline(
                guideline_id=guideline_data["id"],
                principle=guideline_data["principle"],
                description=guideline_data["description"],
                priority=guideline_data["priority"],
                conditions=guideline_data["conditions"],
                exceptions=guideline_data["exceptions"],
                last_updated=datetime.now(),
            )
            self.ethical_guidelines[guideline_data["id"]] = guideline

    def _initialize_principle_weights(self):
        """Initialize weights for ethical principles."""
        self.principle_weights = {
            EthicalPrinciple.USER_SAFETY: 1.0,
            EthicalPrinciple.NON_MALEFICENCE: 0.9,
            EthicalPrinciple.PRIVACY: 0.8,
            EthicalPrinciple.AUTONOMY: 0.7,
            EthicalPrinciple.TRANSPARENCY: 0.6,
            EthicalPrinciple.BENEFICENCE: 0.5,
            EthicalPrinciple.JUSTICE: 0.5,
            EthicalPrinciple.ACCOUNTABILITY: 0.4,
        }

    def _initialize_risk_factors(self):
        """Initialize risk factors and their base weights."""
        self.risk_factors = {"data_sensitivity": 0.8, "system_impact": 0.7, "reversibility": 0.6, "user_consent": 0.5, "network_exposure": 0.4, "complexity": 0.3, "novelty": 0.2}

    def get_ethics_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ethics statistics."""
        return {
            "evaluations_performed": self.evaluations_performed,
            "actions_approved": self.actions_approved,
            "actions_rejected": self.actions_rejected,
            "actions_modified": self.actions_modified,
            "safety_interventions": self.safety_interventions,
            "approval_rate": self.actions_approved / max(1, self.evaluations_performed),
            "safety_intervention_rate": self.safety_interventions / max(1, self.evaluations_performed),
            "total_guidelines": len(self.ethical_guidelines),
            "recent_evaluations": len([e for e in self.decision_history if (datetime.now() - e.evaluation_timestamp).days < 1]),
            "average_ethical_score": sum(e.ethical_score for e in self.decision_history) / max(1, len(self.decision_history)),
            "risk_level_distribution": {level.value: len([e for e in self.decision_history if e.overall_risk_level == level]) for level in RiskLevel},
        }

    def process(self, context: Context) -> Dict[str, Any]:
        """Process context for ethical reasoning."""
        try:
            # Return current ethics status and statistics
            return {
                "success": True,
                "data": {
                    "ethics_engine_ready": True,
                    "safety_threshold": self.safety_threshold,
                    "risk_tolerance": self.risk_tolerance,
                    "ethical_score_threshold": self.ethical_score_threshold,
                    "statistics": self.get_ethics_statistics(),
                    "active_guidelines": len(self.ethical_guidelines),
                },
                "metadata": {"component": "EthicalReasoningEngine", "operation": "status_check"},
            }

        except Exception as e:
            logger.error(f"Error in process method: {e}")
            return {"success": False, "error": str(e), "metadata": {"component": "EthicalReasoningEngine", "operation": "process"}}
