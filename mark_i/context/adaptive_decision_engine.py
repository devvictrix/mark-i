"""
Adaptive Decision Engine for MARK-I

This module provides advanced context-driven decision making with adaptive learning,
multi-criteria optimization, and intelligent strategy selection based on
comprehensive environmental understanding and historical performance data.
"""

import logging
import threading
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import json
import statistics
import math

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
from mark_i.context.environment_monitor import EnvironmentMonitor, SystemHealthStatus
from mark_i.context.context_driven_optimizer import ContextDrivenOptimizer, OptimizationStrategy, ContextState

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".context.adaptive_decision_engine")


class DecisionCriteria(Enum):
    """Criteria for decision making."""
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    STABILITY = "stability"
    USER_EXPERIENCE = "user_experience"
    RESOURCE_CONSERVATION = "resource_conservation"
    RESPONSIVENESS = "responsiveness"
    RELIABILITY = "reliability"


class DecisionConfidence(Enum):
    """Confidence levels for decisions."""
    VERY_LOW = "very_low"      # 0.0 - 0.2
    LOW = "low"                # 0.2 - 0.4
    MODERATE = "moderate"      # 0.4 - 0.6
    HIGH = "high"              # 0.6 - 0.8
    VERY_HIGH = "very_high"    # 0.8 - 1.0


class LearningMode(Enum):
    """Learning modes for adaptive decision making."""
    SUPERVISED = "supervised"      # Learn from explicit feedback
    REINFORCEMENT = "reinforcement"  # Learn from rewards/penalties
    UNSUPERVISED = "unsupervised"   # Learn from patterns
    HYBRID = "hybrid"              # Combination of approaches


@dataclass
class DecisionCriteriaWeights:
    """Weights for different decision criteria."""
    performance: float = 0.25
    efficiency: float = 0.20
    stability: float = 0.15
    user_experience: float = 0.20
    resource_conservation: float = 0.10
    responsiveness: float = 0.05
    reliability: float = 0.05
    
    def normalize(self):
        """Normalize weights to sum to 1.0."""
        total = sum([self.performance, self.efficiency, self.stability, 
                    self.user_experience, self.resource_conservation, 
                    self.responsiveness, self.reliability])
        if total > 0:
            self.performance /= total
            self.efficiency /= total
            self.stability /= total
            self.user_experience /= total
            self.resource_conservation /= total
            self.responsiveness /= total
            self.reliability /= total


@dataclass
class ContextualDecision:
    """Represents a contextual decision with multi-criteria evaluation."""
    decision_id: str
    context_signature: str
    decision_type: str
    alternatives: List[Dict[str, Any]]
    selected_alternative: Dict[str, Any]
    criteria_scores: Dict[DecisionCriteria, float]
    overall_score: float
    confidence: DecisionConfidence
    reasoning: List[str]
    expected_outcomes: Dict[str, float]
    timestamp: datetime
    executed: bool = False
    actual_outcomes: Optional[Dict[str, float]] = None
    feedback_score: Optional[float] = None


@dataclass
class DecisionPattern:
    """Learned decision pattern for similar contexts."""
    pattern_id: str
    context_features: Dict[str, float]
    successful_decisions: List[str]
    failed_decisions: List[str]
    success_rate: float
    confidence_trend: List[float]
    performance_metrics: Dict[str, List[float]]
    last_updated: datetime
    usage_count: int


class AdaptiveDecisionEngine(ProcessingComponent):
    """
    Advanced adaptive decision engine that provides context-driven decision making
    with multi-criteria optimization, learning capabilities, and intelligent
    strategy adaptation based on comprehensive environmental understanding.
    """
    
    def __init__(self, config: ComponentConfig, environment_monitor: EnvironmentMonitor, 
                 optimizer: ContextDrivenOptimizer):
        super().__init__("adaptive_decision_engine", config)
        
        # Dependencies
        self.environment_monitor = environment_monitor
        self.optimizer = optimizer
        
        # Configuration
        self.learning_mode = LearningMode(getattr(config, "learning_mode", "hybrid"))
        self.decision_interval = getattr(config, "decision_interval", 10.0)
        self.confidence_threshold = getattr(config, "confidence_threshold", 0.6)
        self.learning_rate = getattr(config, "learning_rate", 0.1)
        self.pattern_similarity_threshold = getattr(config, "pattern_similarity_threshold", 0.8)
        self.max_alternatives = getattr(config, "max_alternatives", 5)
        
        # Decision criteria weights (can be adapted based on context)
        self.criteria_weights = DecisionCriteriaWeights()
        self.criteria_weights.normalize()
        
        # Decision state
        self.decision_active = False
        self.current_decision: Optional[ContextualDecision] = None
        self.decision_history: deque = deque(maxlen=1000)
        self.learned_patterns: Dict[str, DecisionPattern] = {}
        
        # Multi-criteria decision making
        self.criteria_evaluators: Dict[DecisionCriteria, Callable] = {}
        self.alternative_generators: List[Callable] = []
        self.outcome_predictors: Dict[str, Callable] = {}
        
        # Learning and adaptation
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.feedback_buffer: deque = deque(maxlen=50)
        self.adaptation_triggers: List[str] = []
        
        # Context tracking
        self.context_features: Dict[str, float] = {}
        self.context_history: deque = deque(maxlen=500)
        self.feature_importance: Dict[str, float] = {}
        
        # Threading
        self.decision_lock = threading.Lock()
        self.decision_thread: Optional[threading.Thread] = None
        self.stop_decision_making = threading.Event()
        
        # Statistics
        self.decisions_made = 0
        self.successful_decisions = 0
        self.patterns_learned = 0
        self.adaptations_performed = 0
        
        # Initialize default evaluators
        self._initialize_default_evaluators()
        
        logger.info(f"AdaptiveDecisionEngine initialized with {self.learning_mode.value} learning mode")
    
    def start_decision_making(self) -> bool:
        """Start adaptive decision making process."""
        try:
            if self.decision_active:
                logger.warning("Adaptive decision making already active")
                return True
            
            self.decision_active = True
            self.stop_decision_making.clear()
            
            # Start decision making thread
            self.decision_thread = threading.Thread(
                target=self._decision_making_loop,
                name="AdaptiveDecisionEngine",
                daemon=True
            )
            self.decision_thread.start()
            
            logger.info("Adaptive decision making started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting adaptive decision making: {e}")
            return False
    
    def stop_decision_making(self) -> bool:
        """Stop adaptive decision making process."""
        try:
            if not self.decision_active:
                return True
            
            self.decision_active = False
            self.stop_decision_making.set()
            
            if self.decision_thread and self.decision_thread.is_alive():
                self.decision_thread.join(timeout=10.0)
            
            logger.info("Adaptive decision making stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping adaptive decision making: {e}")
            return False
    
    def make_contextual_decision(self, decision_type: str, context: Optional[Dict[str, Any]] = None) -> ContextualDecision:
        """Make a contextual decision using multi-criteria evaluation."""
        try:
            if not context:
                context = self.environment_monitor.get_current_environment()
            
            if not context:
                raise ValueError("No context available for decision making")
            
            # Extract context features
            context_features = self._extract_context_features(context)
            context_signature = self._generate_context_signature(context_features)
            
            # Generate alternatives
            alternatives = self._generate_alternatives(decision_type, context)
            
            # Evaluate alternatives using multi-criteria analysis
            evaluated_alternatives = []
            for alternative in alternatives:
                criteria_scores = self._evaluate_alternative(alternative, context)
                overall_score = self._calculate_overall_score(criteria_scores)
                
                evaluated_alternatives.append({
                    "alternative": alternative,
                    "criteria_scores": criteria_scores,
                    "overall_score": overall_score
                })
            
            # Select best alternative
            best_alternative = max(evaluated_alternatives, key=lambda x: x["overall_score"])
            
            # Calculate confidence
            confidence = self._calculate_decision_confidence(evaluated_alternatives, context)
            
            # Generate reasoning
            reasoning = self._generate_decision_reasoning(best_alternative, evaluated_alternatives, context)
            
            # Predict outcomes
            expected_outcomes = self._predict_outcomes(best_alternative["alternative"], context)
            
            # Create decision
            decision = ContextualDecision(
                decision_id=f"decision_{int(time.time() * 1000)}",
                context_signature=context_signature,
                decision_type=decision_type,
                alternatives=[alt["alternative"] for alt in evaluated_alternatives],
                selected_alternative=best_alternative["alternative"],
                criteria_scores=best_alternative["criteria_scores"],
                overall_score=best_alternative["overall_score"],
                confidence=self._score_to_confidence(confidence),
                reasoning=reasoning,
                expected_outcomes=expected_outcomes,
                timestamp=datetime.now()
            )
            
            # Store decision
            with self.decision_lock:
                self.decision_history.append(decision)
                self.current_decision = decision
                self.decisions_made += 1
            
            logger.info(f"Made contextual decision: {decision_type} with confidence {confidence:.2f}")
            return decision
            
        except Exception as e:
            logger.error(f"Error making contextual decision: {e}")
            return self._create_fallback_decision(decision_type)
    
    def execute_decision(self, decision: ContextualDecision) -> bool:
        """Execute a contextual decision."""
        try:
            if decision.executed:
                logger.warning(f"Decision {decision.decision_id} already executed")
                return True
            
            # Execute the selected alternative
            success = self._execute_alternative(decision.selected_alternative, decision.decision_type)
            
            if success:
                decision.executed = True
                logger.info(f"Successfully executed decision: {decision.decision_id}")
                return True
            else:
                logger.warning(f"Failed to execute decision: {decision.decision_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing decision: {e}")
            return False
    
    def provide_feedback(self, decision_id: str, feedback_score: float, outcomes: Dict[str, float]):
        """Provide feedback on decision outcomes for learning."""
        try:
            # Find the decision
            decision = None
            for d in self.decision_history:
                if d.decision_id == decision_id:
                    decision = d
                    break
            
            if not decision:
                logger.warning(f"Decision {decision_id} not found for feedback")
                return
            
            # Update decision with feedback
            decision.feedback_score = feedback_score
            decision.actual_outcomes = outcomes
            
            # Learn from feedback
            self._learn_from_feedback(decision)
            
            # Update performance metrics
            self._update_performance_metrics(decision)
            
            # Adapt criteria weights if needed
            self._adapt_criteria_weights(decision)
            
            logger.info(f"Processed feedback for decision {decision_id}: score={feedback_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
    
    def adapt_decision_criteria(self, new_weights: DecisionCriteriaWeights):
        """Adapt decision criteria weights based on changing priorities."""
        try:
            new_weights.normalize()
            
            with self.decision_lock:
                old_weights = self.criteria_weights
                self.criteria_weights = new_weights
                self.adaptations_performed += 1
            
            logger.info("Adapted decision criteria weights")
            logger.debug(f"Performance: {old_weights.performance:.3f} -> {new_weights.performance:.3f}")
            logger.debug(f"Efficiency: {old_weights.efficiency:.3f} -> {new_weights.efficiency:.3f}")
            
        except Exception as e:
            logger.error(f"Error adapting decision criteria: {e}")
    
    def get_decision_insights(self) -> Dict[str, Any]:
        """Get insights about decision making performance and patterns."""
        try:
            with self.decision_lock:
                recent_decisions = list(self.decision_history)[-20:]
                
                # Calculate success rate
                decisions_with_feedback = [d for d in recent_decisions if d.feedback_score is not None]
                success_rate = sum(1 for d in decisions_with_feedback if d.feedback_score > 0.7) / max(1, len(decisions_with_feedback))
                
                # Calculate average confidence
                avg_confidence = statistics.mean([self._confidence_to_score(d.confidence) for d in recent_decisions]) if recent_decisions else 0.0
                
                # Analyze criteria performance
                criteria_performance = {}
                for criteria in DecisionCriteria:
                    scores = [d.criteria_scores.get(criteria, 0.0) for d in recent_decisions if d.criteria_scores]
                    criteria_performance[criteria.value] = {
                        "average_score": statistics.mean(scores) if scores else 0.0,
                        "weight": getattr(self.criteria_weights, criteria.value.replace('_', ''), 0.0)
                    }
                
                insights = {
                    "decision_statistics": {
                        "total_decisions": self.decisions_made,
                        "successful_decisions": self.successful_decisions,
                        "success_rate": success_rate,
                        "patterns_learned": self.patterns_learned,
                        "adaptations_performed": self.adaptations_performed
                    },
                    "performance_metrics": {
                        "average_confidence": avg_confidence,
                        "recent_decisions": len(recent_decisions),
                        "decisions_with_feedback": len(decisions_with_feedback)
                    },
                    "criteria_analysis": criteria_performance,
                    "learning_insights": {
                        "learning_mode": self.learning_mode.value,
                        "feature_importance": dict(list(self.feature_importance.items())[:5]),  # Top 5
                        "adaptation_triggers": self.adaptation_triggers[-5:]  # Recent 5
                    }
                }
                
                return insights
                
        except Exception as e:
            logger.error(f"Error getting decision insights: {e}")
            return {"error": str(e)}
    
    def register_criteria_evaluator(self, criteria: DecisionCriteria, evaluator: Callable):
        """Register a custom criteria evaluator."""
        self.criteria_evaluators[criteria] = evaluator
        logger.info(f"Registered custom evaluator for {criteria.value}")
    
    def register_alternative_generator(self, generator: Callable):
        """Register a custom alternative generator."""
        self.alternative_generators.append(generator)
        logger.info("Registered custom alternative generator")
    
    def _decision_making_loop(self):
        """Main decision making loop for continuous adaptive decisions."""
        logger.info("Adaptive decision making loop started")
        
        while not self.stop_decision_making.is_set():
            try:
                # Get current context
                context = self.environment_monitor.get_current_environment()
                
                if context:
                    # Update context features
                    self._update_context_features(context)
                    
                    # Check if decision making is needed
                    if self._should_make_decision(context):
                        decision = self.make_contextual_decision("optimization", context)
                        
                        # Execute decision if confidence is high enough
                        if self._confidence_to_score(decision.confidence) >= self.confidence_threshold:
                            self.execute_decision(decision)
                    
                    # Learn from recent decisions
                    self._update_learning()
                    
                    # Adapt patterns
                    self._update_decision_patterns()
                
            except Exception as e:
                logger.error(f"Error in decision making loop: {e}")
            
            # Wait for next decision cycle
            self.stop_decision_making.wait(self.decision_interval)
        
        logger.info("Adaptive decision making loop stopped")
    
    def _initialize_default_evaluators(self):
        """Initialize default criteria evaluators."""
        
        def evaluate_performance(alternative: Dict[str, Any], context: Dict[str, Any]) -> float:
            """Evaluate performance criteria."""
            # Simple performance evaluation based on expected improvements
            expected_improvement = alternative.get("expected_performance_improvement", 0.0)
            return min(1.0, max(0.0, expected_improvement))
        
        def evaluate_efficiency(alternative: Dict[str, Any], context: Dict[str, Any]) -> float:
            """Evaluate efficiency criteria."""
            resource_efficiency = alternative.get("resource_efficiency", 0.5)
            return min(1.0, max(0.0, resource_efficiency))
        
        def evaluate_stability(alternative: Dict[str, Any], context: Dict[str, Any]) -> float:
            """Evaluate stability criteria."""
            system_health = context.get("system_health", "fair")
            health_scores = {"excellent": 1.0, "good": 0.8, "fair": 0.6, "poor": 0.4, "critical": 0.2}
            base_score = health_scores.get(system_health, 0.5)
            
            # Adjust based on alternative risk
            risk_factor = alternative.get("risk_factor", 0.5)
            return base_score * (1.0 - risk_factor * 0.5)
        
        def evaluate_user_experience(alternative: Dict[str, Any], context: Dict[str, Any]) -> float:
            """Evaluate user experience criteria."""
            responsiveness = alternative.get("responsiveness_improvement", 0.0)
            disruption = alternative.get("user_disruption", 0.0)
            return min(1.0, max(0.0, 0.5 + responsiveness - disruption))
        
        # Register default evaluators
        self.criteria_evaluators[DecisionCriteria.PERFORMANCE] = evaluate_performance
        self.criteria_evaluators[DecisionCriteria.EFFICIENCY] = evaluate_efficiency
        self.criteria_evaluators[DecisionCriteria.STABILITY] = evaluate_stability
        self.criteria_evaluators[DecisionCriteria.USER_EXPERIENCE] = evaluate_user_experience
    
    def _extract_context_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from context for decision making."""
        features = {}
        
        try:
            system_metrics = context.get("system_metrics", {})
            
            # System resource features
            features["cpu_usage"] = system_metrics.get("cpu_usage", 0.0) / 100.0
            features["memory_usage"] = system_metrics.get("memory_percent", 0.0) / 100.0
            features["disk_usage"] = system_metrics.get("disk_percent", 0.0) / 100.0
            
            # Application features
            applications = context.get("applications", {})
            features["active_applications"] = min(len(applications) / 20.0, 1.0)  # Normalize to 0-1
            
            # System health feature
            health_mapping = {"excellent": 1.0, "good": 0.8, "fair": 0.6, "poor": 0.4, "critical": 0.2}
            features["system_health"] = health_mapping.get(context.get("system_health", "fair"), 0.5)
            
            # Time-based features
            current_hour = datetime.now().hour
            features["time_of_day"] = current_hour / 24.0
            features["is_business_hours"] = 1.0 if 9 <= current_hour <= 17 else 0.0
            
            # Recent changes feature
            recent_changes = context.get("recent_changes", [])
            features["change_activity"] = min(len(recent_changes) / 10.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error extracting context features: {e}")
        
        return features
    
    def _generate_context_signature(self, features: Dict[str, float]) -> str:
        """Generate a signature for context pattern matching."""
        try:
            # Create a simplified signature based on key features
            cpu_level = "high" if features.get("cpu_usage", 0) > 0.7 else "medium" if features.get("cpu_usage", 0) > 0.3 else "low"
            memory_level = "high" if features.get("memory_usage", 0) > 0.8 else "medium" if features.get("memory_usage", 0) > 0.5 else "low"
            app_level = "many" if features.get("active_applications", 0) > 0.5 else "few"
            health_level = "good" if features.get("system_health", 0) > 0.7 else "poor"
            
            return f"cpu_{cpu_level}_mem_{memory_level}_apps_{app_level}_health_{health_level}"
            
        except Exception as e:
            logger.error(f"Error generating context signature: {e}")
            return "unknown_context"
    
    def _generate_alternatives(self, decision_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate decision alternatives."""
        alternatives = []
        
        try:
            if decision_type == "optimization":
                # Generate optimization alternatives
                strategies = [OptimizationStrategy.CONSERVATIVE, OptimizationStrategy.BALANCED, 
                            OptimizationStrategy.PERFORMANCE, OptimizationStrategy.EFFICIENCY]
                
                for strategy in strategies:
                    alternative = {
                        "type": "optimization_strategy",
                        "strategy": strategy.value,
                        "expected_performance_improvement": self._estimate_performance_improvement(strategy, context),
                        "resource_efficiency": self._estimate_resource_efficiency(strategy, context),
                        "risk_factor": self._estimate_risk_factor(strategy, context),
                        "responsiveness_improvement": self._estimate_responsiveness_improvement(strategy, context),
                        "user_disruption": self._estimate_user_disruption(strategy, context)
                    }
                    alternatives.append(alternative)
            
            # Use custom generators
            for generator in self.alternative_generators:
                try:
                    custom_alternatives = generator(decision_type, context)
                    if custom_alternatives:
                        alternatives.extend(custom_alternatives)
                except Exception as e:
                    logger.error(f"Error in custom alternative generator: {e}")
            
            # Limit number of alternatives
            return alternatives[:self.max_alternatives]
            
        except Exception as e:
            logger.error(f"Error generating alternatives: {e}")
            return [self._create_fallback_alternative()]
    
    def _evaluate_alternative(self, alternative: Dict[str, Any], context: Dict[str, Any]) -> Dict[DecisionCriteria, float]:
        """Evaluate an alternative against all criteria."""
        scores = {}
        
        for criteria in DecisionCriteria:
            try:
                if criteria in self.criteria_evaluators:
                    score = self.criteria_evaluators[criteria](alternative, context)
                    scores[criteria] = max(0.0, min(1.0, score))  # Clamp to [0, 1]
                else:
                    # Default scoring
                    scores[criteria] = 0.5
            except Exception as e:
                logger.error(f"Error evaluating {criteria.value}: {e}")
                scores[criteria] = 0.5
        
        return scores
    
    def _calculate_overall_score(self, criteria_scores: Dict[DecisionCriteria, float]) -> float:
        """Calculate overall score using weighted criteria."""
        try:
            total_score = 0.0
            total_weight = 0.0
            
            for criteria, score in criteria_scores.items():
                weight = getattr(self.criteria_weights, criteria.value.replace('_', ''), 0.0)
                total_score += score * weight
                total_weight += weight
            
            return total_score / max(total_weight, 0.001)  # Avoid division by zero
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.5
    
    def _calculate_decision_confidence(self, evaluated_alternatives: List[Dict[str, Any]], 
                                     context: Dict[str, Any]) -> float:
        """Calculate confidence in the decision."""
        try:
            if len(evaluated_alternatives) < 2:
                return 0.5
            
            scores = [alt["overall_score"] for alt in evaluated_alternatives]
            best_score = max(scores)
            second_best_score = sorted(scores, reverse=True)[1]
            
            # Confidence based on score separation
            score_separation = best_score - second_best_score
            base_confidence = min(1.0, score_separation * 2.0)  # Scale separation
            
            # Adjust based on context stability
            system_health = context.get("system_health", "fair")
            health_bonus = {"excellent": 0.2, "good": 0.1, "fair": 0.0, "poor": -0.1, "critical": -0.2}
            
            # Adjust based on pattern matching
            context_features = self._extract_context_features(context)
            pattern_bonus = 0.1 if self._find_matching_pattern(context_features) else 0.0
            
            final_confidence = base_confidence + health_bonus.get(system_health, 0.0) + pattern_bonus
            return max(0.0, min(1.0, final_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating decision confidence: {e}")
            return 0.5
    
    def _generate_decision_reasoning(self, best_alternative: Dict[str, Any], 
                                   all_alternatives: List[Dict[str, Any]], 
                                   context: Dict[str, Any]) -> List[str]:
        """Generate human-readable reasoning for the decision."""
        reasoning = []
        
        try:
            # Explain why this alternative was chosen
            best_score = best_alternative["overall_score"]
            reasoning.append(f"Selected alternative with overall score: {best_score:.2f}")
            
            # Explain top criteria
            criteria_scores = best_alternative["criteria_scores"]
            top_criteria = sorted(criteria_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for criteria, score in top_criteria:
                weight = getattr(self.criteria_weights, criteria.value.replace('_', ''), 0.0)
                reasoning.append(f"Strong {criteria.value}: {score:.2f} (weight: {weight:.2f})")
            
            # Context-specific reasoning
            system_metrics = context.get("system_metrics", {})
            cpu_usage = system_metrics.get("cpu_usage", 0)
            memory_usage = system_metrics.get("memory_percent", 0)
            
            if cpu_usage > 70:
                reasoning.append(f"High CPU usage ({cpu_usage:.1f}%) influenced decision")
            if memory_usage > 80:
                reasoning.append(f"High memory usage ({memory_usage:.1f}%) considered")
            
            # Alternative comparison
            if len(all_alternatives) > 1:
                scores = [alt["overall_score"] for alt in all_alternatives]
                avg_score = statistics.mean(scores)
                reasoning.append(f"Outperformed average alternative by {best_score - avg_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            reasoning.append("Decision made based on available criteria")
        
        return reasoning
    
    def _predict_outcomes(self, alternative: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        """Predict outcomes of executing the alternative."""
        outcomes = {}
        
        try:
            # Use custom predictors if available
            for outcome_type, predictor in self.outcome_predictors.items():
                try:
                    outcomes[outcome_type] = predictor(alternative, context)
                except Exception as e:
                    logger.error(f"Error in custom predictor {outcome_type}: {e}")
            
            # Default predictions
            if "performance_change" not in outcomes:
                outcomes["performance_change"] = alternative.get("expected_performance_improvement", 0.0)
            
            if "resource_impact" not in outcomes:
                outcomes["resource_impact"] = alternative.get("resource_efficiency", 0.5) - 0.5
            
            if "stability_impact" not in outcomes:
                risk = alternative.get("risk_factor", 0.5)
                outcomes["stability_impact"] = 0.1 - risk * 0.2
            
        except Exception as e:
            logger.error(f"Error predicting outcomes: {e}")
        
        return outcomes
    
    def _score_to_confidence(self, score: float) -> DecisionConfidence:
        """Convert numerical score to confidence level."""
        if score >= 0.8:
            return DecisionConfidence.VERY_HIGH
        elif score >= 0.6:
            return DecisionConfidence.HIGH
        elif score >= 0.4:
            return DecisionConfidence.MODERATE
        elif score >= 0.2:
            return DecisionConfidence.LOW
        else:
            return DecisionConfidence.VERY_LOW
    
    def _confidence_to_score(self, confidence: DecisionConfidence) -> float:
        """Convert confidence level to numerical score."""
        mapping = {
            DecisionConfidence.VERY_HIGH: 0.9,
            DecisionConfidence.HIGH: 0.7,
            DecisionConfidence.MODERATE: 0.5,
            DecisionConfidence.LOW: 0.3,
            DecisionConfidence.VERY_LOW: 0.1
        }
        return mapping.get(confidence, 0.5)
    
    def _create_fallback_decision(self, decision_type: str) -> ContextualDecision:
        """Create a fallback decision when normal decision making fails."""
        return ContextualDecision(
            decision_id=f"fallback_{int(time.time() * 1000)}",
            context_signature="fallback",
            decision_type=decision_type,
            alternatives=[],
            selected_alternative={"type": "no_action", "description": "Maintain current state"},
            criteria_scores={},
            overall_score=0.5,
            confidence=DecisionConfidence.LOW,
            reasoning=["Fallback decision due to error in normal decision making"],
            expected_outcomes={},
            timestamp=datetime.now()
        )
    
    def _create_fallback_alternative(self) -> Dict[str, Any]:
        """Create a fallback alternative."""
        return {
            "type": "no_change",
            "description": "Maintain current configuration",
            "expected_performance_improvement": 0.0,
            "resource_efficiency": 0.5,
            "risk_factor": 0.1,
            "responsiveness_improvement": 0.0,
            "user_disruption": 0.0
        }
    
    def _execute_alternative(self, alternative: Dict[str, Any], decision_type: str) -> bool:
        """Execute the selected alternative."""
        try:
            alt_type = alternative.get("type", "unknown")
            
            if alt_type == "optimization_strategy":
                # Execute optimization strategy through the optimizer
                strategy_name = alternative.get("strategy", "balanced")
                strategy = OptimizationStrategy(strategy_name)
                
                # This would integrate with the actual system to apply the strategy
                logger.info(f"Executing optimization strategy: {strategy.value}")
                return True
            
            elif alt_type == "no_action" or alt_type == "no_change":
                # No action needed
                logger.info("Executing no-action alternative")
                return True
            
            else:
                logger.warning(f"Unknown alternative type: {alt_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing alternative: {e}")
            return False
    
    def _should_make_decision(self, context: Dict[str, Any]) -> bool:
        """Determine if a decision should be made based on current context."""
        try:
            # Check if enough time has passed since last decision
            if self.current_decision:
                time_since_last = (datetime.now() - self.current_decision.timestamp).total_seconds()
                if time_since_last < self.decision_interval:
                    return False
            
            # Check if context has changed significantly
            current_features = self._extract_context_features(context)
            
            if hasattr(self, '_last_context_features'):
                feature_change = sum(abs(current_features.get(k, 0) - self._last_context_features.get(k, 0)) 
                                   for k in set(current_features.keys()) | set(self._last_context_features.keys()))
                
                # Make decision if significant change detected
                return feature_change > 0.2
            
            self._last_context_features = current_features
            return True
            
        except Exception as e:
            logger.error(f"Error checking if decision should be made: {e}")
            return False
    
    def _update_context_features(self, context: Dict[str, Any]):
        """Update context features for tracking."""
        try:
            features = self._extract_context_features(context)
            self.context_features = features
            
            # Update context history
            self.context_history.append({
                "timestamp": datetime.now(),
                "features": features.copy()
            })
            
        except Exception as e:
            logger.error(f"Error updating context features: {e}")
    
    def _update_learning(self):
        """Update learning from recent decisions and feedback."""
        try:
            # Process recent feedback
            recent_decisions = [d for d in list(self.decision_history)[-10:] 
                              if d.feedback_score is not None]
            
            if len(recent_decisions) >= 3:
                # Update feature importance based on successful decisions
                self._update_feature_importance(recent_decisions)
                
                # Adapt criteria weights based on performance
                self._adapt_criteria_weights_from_performance(recent_decisions)
            
        except Exception as e:
            logger.error(f"Error updating learning: {e}")
    
    def _update_decision_patterns(self):
        """Update learned decision patterns."""
        try:
            # Group recent decisions by context signature
            recent_decisions = list(self.decision_history)[-50:]
            pattern_groups = defaultdict(list)
            
            for decision in recent_decisions:
                if decision.feedback_score is not None:
                    pattern_groups[decision.context_signature].append(decision)
            
            # Update patterns with sufficient data
            for signature, decisions in pattern_groups.items():
                if len(decisions) >= 5:
                    self._update_pattern(signature, decisions)
                    
        except Exception as e:
            logger.error(f"Error updating decision patterns: {e}")
    
    def _estimate_performance_improvement(self, strategy: OptimizationStrategy, context: Dict[str, Any]) -> float:
        """Estimate performance improvement for a strategy."""
        # Simplified estimation - in practice this would be more sophisticated
        strategy_benefits = {
            OptimizationStrategy.CONSERVATIVE: 0.1,
            OptimizationStrategy.BALANCED: 0.3,
            OptimizationStrategy.PERFORMANCE: 0.6,
            OptimizationStrategy.EFFICIENCY: 0.4,
            OptimizationStrategy.AGGRESSIVE: 0.8
        }
        
        base_improvement = strategy_benefits.get(strategy, 0.3)
        
        # Adjust based on current system state
        system_metrics = context.get("system_metrics", {})
        cpu_usage = system_metrics.get("cpu_usage", 0) / 100.0
        
        # Higher potential improvement when system is under stress
        stress_multiplier = 1.0 + cpu_usage
        
        return min(1.0, base_improvement * stress_multiplier)
    
    def _estimate_resource_efficiency(self, strategy: OptimizationStrategy, context: Dict[str, Any]) -> float:
        """Estimate resource efficiency for a strategy."""
        efficiency_ratings = {
            OptimizationStrategy.CONSERVATIVE: 0.9,
            OptimizationStrategy.BALANCED: 0.7,
            OptimizationStrategy.PERFORMANCE: 0.4,
            OptimizationStrategy.EFFICIENCY: 0.9,
            OptimizationStrategy.AGGRESSIVE: 0.3
        }
        
        return efficiency_ratings.get(strategy, 0.5)
    
    def _estimate_risk_factor(self, strategy: OptimizationStrategy, context: Dict[str, Any]) -> float:
        """Estimate risk factor for a strategy."""
        risk_levels = {
            OptimizationStrategy.CONSERVATIVE: 0.1,
            OptimizationStrategy.BALANCED: 0.3,
            OptimizationStrategy.PERFORMANCE: 0.5,
            OptimizationStrategy.EFFICIENCY: 0.2,
            OptimizationStrategy.AGGRESSIVE: 0.8
        }
        
        base_risk = risk_levels.get(strategy, 0.3)
        
        # Adjust based on system health
        system_health = context.get("system_health", "fair")
        health_risk_multiplier = {"excellent": 0.8, "good": 0.9, "fair": 1.0, "poor": 1.3, "critical": 1.5}
        
        return min(1.0, base_risk * health_risk_multiplier.get(system_health, 1.0))
    
    def _estimate_responsiveness_improvement(self, strategy: OptimizationStrategy, context: Dict[str, Any]) -> float:
        """Estimate responsiveness improvement for a strategy."""
        responsiveness_benefits = {
            OptimizationStrategy.CONSERVATIVE: 0.0,
            OptimizationStrategy.BALANCED: 0.2,
            OptimizationStrategy.PERFORMANCE: 0.7,
            OptimizationStrategy.EFFICIENCY: 0.1,
            OptimizationStrategy.AGGRESSIVE: 0.5
        }
        
        return responsiveness_benefits.get(strategy, 0.2)
    
    def _estimate_user_disruption(self, strategy: OptimizationStrategy, context: Dict[str, Any]) -> float:
        """Estimate user disruption for a strategy."""
        disruption_levels = {
            OptimizationStrategy.CONSERVATIVE: 0.0,
            OptimizationStrategy.BALANCED: 0.1,
            OptimizationStrategy.PERFORMANCE: 0.3,
            OptimizationStrategy.EFFICIENCY: 0.1,
            OptimizationStrategy.AGGRESSIVE: 0.6
        }
        
        return disruption_levels.get(strategy, 0.2)
    
    def _learn_from_feedback(self, decision: ContextualDecision):
        """Learn from decision feedback."""
        try:
            if decision.feedback_score is None:
                return
            
            # Update success statistics
            if decision.feedback_score > 0.7:
                self.successful_decisions += 1
            
            # Store feedback for pattern learning
            self.feedback_buffer.append({
                "decision": decision,
                "feedback_score": decision.feedback_score,
                "timestamp": datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error learning from feedback: {e}")
    
    def _update_performance_metrics(self, decision: ContextualDecision):
        """Update performance metrics based on decision outcomes."""
        try:
            if decision.actual_outcomes:
                for metric, value in decision.actual_outcomes.items():
                    self.performance_history[metric].append(value)
                    
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _adapt_criteria_weights(self, decision: ContextualDecision):
        """Adapt criteria weights based on decision feedback."""
        try:
            if decision.feedback_score is None or decision.feedback_score < 0.3:
                return  # Only adapt from reasonably successful decisions
            
            # Simple adaptation: slightly increase weights of criteria that scored well
            feedback_strength = decision.feedback_score - 0.5  # Center around 0
            adaptation_rate = self.learning_rate * feedback_strength
            
            for criteria, score in decision.criteria_scores.items():
                if score > 0.6:  # Criteria that performed well
                    current_weight = getattr(self.criteria_weights, criteria.value.replace('_', ''), 0.0)
                    new_weight = current_weight + adaptation_rate * 0.1
                    setattr(self.criteria_weights, criteria.value.replace('_', ''), max(0.0, min(1.0, new_weight)))
            
            # Renormalize weights
            self.criteria_weights.normalize()
            
        except Exception as e:
            logger.error(f"Error adapting criteria weights: {e}")
    
    def _find_matching_pattern(self, context_features: Dict[str, float]) -> Optional[DecisionPattern]:
        """Find a matching decision pattern for the current context."""
        try:
            best_match = None
            best_similarity = 0.0
            
            for pattern in self.learned_patterns.values():
                similarity = self._calculate_feature_similarity(context_features, pattern.context_features)
                
                if similarity > best_similarity and similarity > self.pattern_similarity_threshold:
                    best_similarity = similarity
                    best_match = pattern
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding matching pattern: {e}")
            return None
    
    def _calculate_feature_similarity(self, features1: Dict[str, float], features2: Dict[str, float]) -> float:
        """Calculate similarity between two feature sets."""
        try:
            common_features = set(features1.keys()) & set(features2.keys())
            
            if not common_features:
                return 0.0
            
            # Calculate cosine similarity
            dot_product = sum(features1[f] * features2[f] for f in common_features)
            norm1 = math.sqrt(sum(features1[f] ** 2 for f in common_features))
            norm2 = math.sqrt(sum(features2[f] ** 2 for f in common_features))
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Error calculating feature similarity: {e}")
            return 0.0
    
    def _update_feature_importance(self, successful_decisions: List[ContextualDecision]):
        """Update feature importance based on successful decisions."""
        try:
            # This is a simplified approach - in practice would use more sophisticated methods
            for decision in successful_decisions:
                context_features = self._extract_context_features({"system_metrics": {}})  # Simplified
                
                for feature, value in context_features.items():
                    if feature not in self.feature_importance:
                        self.feature_importance[feature] = 0.0
                    
                    # Increase importance for features present in successful decisions
                    self.feature_importance[feature] += 0.1 * decision.feedback_score
            
            # Normalize importance scores
            total_importance = sum(self.feature_importance.values())
            if total_importance > 0:
                for feature in self.feature_importance:
                    self.feature_importance[feature] /= total_importance
                    
        except Exception as e:
            logger.error(f"Error updating feature importance: {e}")
    
    def _adapt_criteria_weights_from_performance(self, recent_decisions: List[ContextualDecision]):
        """Adapt criteria weights based on recent performance."""
        try:
            # Calculate average feedback score for each criteria
            criteria_performance = defaultdict(list)
            
            for decision in recent_decisions:
                for criteria, score in decision.criteria_scores.items():
                    criteria_performance[criteria].append(decision.feedback_score * score)
            
            # Adjust weights based on performance
            for criteria, scores in criteria_performance.items():
                if len(scores) >= 3:
                    avg_performance = statistics.mean(scores)
                    current_weight = getattr(self.criteria_weights, criteria.value.replace('_', ''), 0.0)
                    
                    # Increase weight if performance is good, decrease if poor
                    adjustment = (avg_performance - 0.5) * self.learning_rate * 0.1
                    new_weight = current_weight + adjustment
                    setattr(self.criteria_weights, criteria.value.replace('_', ''), max(0.01, min(0.8, new_weight)))
            
            # Renormalize
            self.criteria_weights.normalize()
            
        except Exception as e:
            logger.error(f"Error adapting criteria weights from performance: {e}")
    
    def _update_pattern(self, signature: str, decisions: List[ContextualDecision]):
        """Update a decision pattern with new data."""
        try:
            successful_decisions = [d.decision_id for d in decisions if d.feedback_score and d.feedback_score > 0.7]
            failed_decisions = [d.decision_id for d in decisions if d.feedback_score and d.feedback_score < 0.3]
            
            success_rate = len(successful_decisions) / len(decisions) if decisions else 0.0
            
            if signature in self.learned_patterns:
                # Update existing pattern
                pattern = self.learned_patterns[signature]
                pattern.successful_decisions.extend(successful_decisions)
                pattern.failed_decisions.extend(failed_decisions)
                pattern.success_rate = (pattern.success_rate + success_rate) / 2  # Simple average
                pattern.last_updated = datetime.now()
                pattern.usage_count += len(decisions)
            else:
                # Create new pattern
                avg_features = {}
                for decision in decisions:
                    decision_features = self._extract_context_features({})  # Simplified
                    for feature, value in decision_features.items():
                        if feature not in avg_features:
                            avg_features[feature] = []
                        avg_features[feature].append(value)
                
                # Average the features
                for feature in avg_features:
                    avg_features[feature] = statistics.mean(avg_features[feature])
                
                self.learned_patterns[signature] = DecisionPattern(
                    pattern_id=f"pattern_{len(self.learned_patterns)}",
                    context_features=avg_features,
                    successful_decisions=successful_decisions,
                    failed_decisions=failed_decisions,
                    success_rate=success_rate,
                    confidence_trend=[],
                    performance_metrics={},
                    last_updated=datetime.now(),
                    usage_count=len(decisions)
                )
                
                self.patterns_learned += 1
                
        except Exception as e:
            logger.error(f"Error updating pattern: {e}")