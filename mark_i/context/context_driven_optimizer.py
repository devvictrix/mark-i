"""
Context-Driven Decision Making and Optimization for MARK-I

This module provides context-aware strategy selection, parameter tuning,
environmental adaptation, and optimization mechanisms based on comprehensive
environmental understanding and historical patterns.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import json
import statistics

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
from mark_i.context.environment_monitor import EnvironmentMonitor, SystemHealthStatus

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".context.context_driven_optimizer")


class OptimizationStrategy(Enum):
    """Available optimization strategies."""
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


class ContextState(Enum):
    """Context-based system states."""
    IDLE = "idle"
    LIGHT_USAGE = "light_usage"
    MODERATE_USAGE = "moderate_usage"
    HEAVY_USAGE = "heavy_usage"
    CRITICAL_LOAD = "critical_load"


class AdaptationMode(Enum):
    """Adaptation modes for different scenarios."""
    REACTIVE = "reactive"      # React to changes after they occur
    PREDICTIVE = "predictive"  # Predict and adapt before changes
    PROACTIVE = "proactive"    # Continuously optimize based on patterns


@dataclass
class OptimizationParameters:
    """Parameters for system optimization."""
    monitoring_frequency: float = 5.0
    processing_intensity: float = 1.0
    memory_usage_target: float = 0.7
    cpu_usage_target: float = 0.6
    response_time_target: float = 1.0
    background_task_priority: float = 0.3
    cache_size_multiplier: float = 1.0
    parallel_processing_factor: float = 1.0
    resource_allocation_weights: Dict[str, float] = field(default_factory=lambda: {
        "cpu": 0.4, "memory": 0.3, "disk": 0.2, "network": 0.1
    })


@dataclass
class ContextPattern:
    """Represents a learned context pattern for optimization."""
    pattern_id: str
    context_signature: str
    typical_duration: timedelta
    resource_requirements: Dict[str, float]
    optimal_parameters: OptimizationParameters
    success_rate: float
    usage_frequency: int
    last_used: datetime
    performance_metrics: Dict[str, float]


@dataclass
class OptimizationDecision:
    """Represents an optimization decision."""
    decision_id: str
    context_state: ContextState
    strategy: OptimizationStrategy
    parameters: OptimizationParameters
    reasoning: List[str]
    confidence: float
    expected_impact: Dict[str, float]
    timestamp: datetime
    applied: bool = False
    actual_impact: Optional[Dict[str, float]] = None


class ContextDrivenOptimizer(ProcessingComponent):
    """
    Context-driven decision making and optimization engine that provides
    intelligent strategy selection, parameter tuning, and environmental
    adaptation based on comprehensive context understanding.
    """
    
    def __init__(self, config: ComponentConfig, environment_monitor: EnvironmentMonitor):
        super().__init__("context_driven_optimizer", config)
        
        # Dependencies
        self.environment_monitor = environment_monitor
        
        # Configuration
        self.adaptation_mode = AdaptationMode(getattr(config, "adaptation_mode", "predictive"))
        self.optimization_interval = getattr(config, "optimization_interval", 30.0)
        self.learning_rate = getattr(config, "learning_rate", 0.1)
        self.pattern_matching_threshold = getattr(config, "pattern_matching_threshold", 0.7)
        self.max_optimization_history = getattr(config, "max_optimization_history", 1000)
        
        # Current state
        self.current_context_state = ContextState.IDLE
        self.current_strategy = OptimizationStrategy.BALANCED
        self.current_parameters = OptimizationParameters()
        
        # Pattern learning and matching
        self.learned_patterns: Dict[str, ContextPattern] = {}
        self.context_history: deque = deque(maxlen=self.max_optimization_history)
        self.pattern_performance: Dict[str, List[float]] = defaultdict(list)
        
        # Decision tracking
        self.optimization_decisions: deque = deque(maxlen=500)
        self.decision_callbacks: Dict[str, Callable] = {}
        self.parameter_bounds: Dict[str, Tuple[float, float]] = {
            "monitoring_frequency": (1.0, 60.0),
            "processing_intensity": (0.1, 2.0),
            "memory_usage_target": (0.3, 0.9),
            "cpu_usage_target": (0.2, 0.8),
            "response_time_target": (0.1, 5.0),
            "background_task_priority": (0.1, 1.0),
            "cache_size_multiplier": (0.5, 3.0),
            "parallel_processing_factor": (0.5, 4.0)
        }
        
        # Optimization state
        self.optimization_active = False
        self.last_optimization = None
        self.optimization_metrics: Dict[str, deque] = {
            "response_time": deque(maxlen=100),
            "resource_efficiency": deque(maxlen=100),
            "user_satisfaction": deque(maxlen=100),
            "system_stability": deque(maxlen=100)
        }
        
        # Threading
        self.optimizer_lock = threading.Lock()
        self.optimizer_thread: Optional[threading.Thread] = None
        self.stop_optimization = threading.Event()
        
        # Statistics
        self.optimization_cycles = 0
        self.decisions_made = 0
        self.patterns_learned = 0
        self.successful_optimizations = 0
        
        logger.info(f"ContextDrivenOptimizer initialized with {self.adaptation_mode.value} mode")
    
    def start_optimization(self) -> bool:
        """Start context-driven optimization."""
        try:
            if self.optimization_active:
                logger.warning("Context-driven optimization already active")
                return True
            
            self.optimization_active = True
            self.stop_optimization.clear()
            
            # Start optimization thread
            self.optimizer_thread = threading.Thread(
                target=self._optimization_loop,
                name="ContextDrivenOptimizer",
                daemon=True
            )
            self.optimizer_thread.start()
            
            logger.info("Context-driven optimization started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting context-driven optimization: {e}")
            return False
    
    def stop_optimization(self) -> bool:
        """Stop context-driven optimization."""
        try:
            if not self.optimization_active:
                return True
            
            self.optimization_active = False
            self.stop_optimization.set()
            
            if self.optimizer_thread and self.optimizer_thread.is_alive():
                self.optimizer_thread.join(timeout=10.0)
            
            logger.info("Context-driven optimization stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping context-driven optimization: {e}")
            return False
    
    def get_optimal_parameters(self, context: Optional[Dict[str, Any]] = None) -> OptimizationParameters:
        """Get optimal parameters for current or specified context."""
        try:
            if not context:
                context = self.environment_monitor.get_current_environment()
            
            if not context:
                return self.current_parameters
            
            # Determine context state
            context_state = self._determine_context_state(context)
            
            # Find matching pattern
            matching_pattern = self._find_matching_pattern(context)
            
            if matching_pattern and matching_pattern.success_rate > 0.7:
                # Use learned pattern parameters
                logger.debug(f"Using learned pattern: {matching_pattern.pattern_id}")
                return matching_pattern.optimal_parameters
            else:
                # Generate parameters based on context state
                return self._generate_context_parameters(context_state, context)
                
        except Exception as e:
            logger.error(f"Error getting optimal parameters: {e}")
            return self.current_parameters
    
    def make_optimization_decision(self, context: Dict[str, Any]) -> OptimizationDecision:
        """Make an optimization decision based on current context."""
        try:
            # Determine context state
            context_state = self._determine_context_state(context)
            
            # Select optimization strategy
            strategy = self._select_optimization_strategy(context_state, context)
            
            # Generate optimal parameters
            parameters = self.get_optimal_parameters(context)
            
            # Generate reasoning
            reasoning = self._generate_optimization_reasoning(context_state, strategy, context)
            
            # Calculate confidence
            confidence = self._calculate_decision_confidence(context_state, strategy, context)
            
            # Estimate impact
            expected_impact = self._estimate_optimization_impact(strategy, parameters, context)
            
            decision = OptimizationDecision(
                decision_id=f"opt_{int(time.time() * 1000)}",
                context_state=context_state,
                strategy=strategy,
                parameters=parameters,
                reasoning=reasoning,
                confidence=confidence,
                expected_impact=expected_impact,
                timestamp=datetime.now()
            )
            
            self.optimization_decisions.append(decision)
            self.decisions_made += 1
            
            return decision
            
        except Exception as e:
            logger.error(f"Error making optimization decision: {e}")
            return OptimizationDecision(
                decision_id="error",
                context_state=ContextState.IDLE,
                strategy=OptimizationStrategy.CONSERVATIVE,
                parameters=self.current_parameters,
                reasoning=["Error in decision making"],
                confidence=0.0,
                expected_impact={},
                timestamp=datetime.now()
            )
    
    def apply_optimization(self, decision: OptimizationDecision) -> bool:
        """Apply an optimization decision."""
        try:
            # Validate parameters
            validated_params = self._validate_parameters(decision.parameters)
            
            # Apply parameters using callbacks
            success = True
            for param_name, callback in self.decision_callbacks.items():
                try:
                    if not callback(validated_params):
                        success = False
                        logger.warning(f"Failed to apply parameter: {param_name}")
                except Exception as e:
                    logger.error(f"Error applying parameter {param_name}: {e}")
                    success = False
            
            if success:
                with self.optimizer_lock:
                    self.current_parameters = validated_params
                    self.current_strategy = decision.strategy
                    self.current_context_state = decision.context_state
                
                decision.applied = True
                self.successful_optimizations += 1
                
                logger.info(f"Applied optimization: {decision.strategy.value} strategy")
                return True
            else:
                logger.warning("Failed to apply optimization decision")
                return False
                
        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return False
    
    def learn_from_optimization(self, decision: OptimizationDecision, 
                               performance_metrics: Dict[str, float]):
        """Learn from optimization results to improve future decisions."""
        try:
            # Update decision with actual impact
            decision.actual_impact = performance_metrics
            
            # Calculate success score
            success_score = self._calculate_success_score(decision.expected_impact, 
                                                        performance_metrics)
            
            # Update pattern learning
            context_signature = self._generate_context_signature(decision.context_state)
            
            if context_signature in self.learned_patterns:
                # Update existing pattern
                pattern = self.learned_patterns[context_signature]
                pattern.usage_frequency += 1
                pattern.last_used = datetime.now()
                
                # Update success rate with exponential moving average
                pattern.success_rate = (pattern.success_rate * 0.9 + success_score * 0.1)
                
                # Update optimal parameters if this was more successful
                if success_score > pattern.success_rate:
                    pattern.optimal_parameters = decision.parameters
                    pattern.performance_metrics = performance_metrics
            else:
                # Create new pattern
                self.learned_patterns[context_signature] = ContextPattern(
                    pattern_id=f"pattern_{len(self.learned_patterns)}",
                    context_signature=context_signature,
                    typical_duration=timedelta(minutes=30),  # Default duration
                    resource_requirements=self._extract_resource_requirements(decision),
                    optimal_parameters=decision.parameters,
                    success_rate=success_score,
                    usage_frequency=1,
                    last_used=datetime.now(),
                    performance_metrics=performance_metrics
                )
                self.patterns_learned += 1
            
            # Update optimization metrics
            for metric_name, value in performance_metrics.items():
                if metric_name in self.optimization_metrics:
                    self.optimization_metrics[metric_name].append(value)
            
            logger.debug(f"Learned from optimization: success_score={success_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error learning from optimization: {e}")
    
    def register_parameter_callback(self, parameter_name: str, 
                                   callback: Callable[[OptimizationParameters], bool]):
        """Register a callback for applying specific optimization parameters."""
        self.decision_callbacks[parameter_name] = callback
        logger.info(f"Registered parameter callback: {parameter_name}")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status and metrics."""
        try:
            with self.optimizer_lock:
                recent_decisions = list(self.optimization_decisions)[-10:]
                recent_success_rate = sum(1 for d in recent_decisions 
                                        if d.actual_impact and 
                                        self._calculate_success_score(d.expected_impact, d.actual_impact) > 0.7) / max(1, len(recent_decisions))
                
                status = {
                    "optimization_active": self.optimization_active,
                    "current_state": {
                        "context_state": self.current_context_state.value,
                        "strategy": self.current_strategy.value,
                        "parameters": self._parameters_to_dict(self.current_parameters)
                    },
                    "statistics": {
                        "optimization_cycles": self.optimization_cycles,
                        "decisions_made": self.decisions_made,
                        "patterns_learned": self.patterns_learned,
                        "successful_optimizations": self.successful_optimizations,
                        "recent_success_rate": recent_success_rate
                    },
                    "learned_patterns": len(self.learned_patterns),
                    "performance_metrics": {
                        metric: list(values)[-5:] if values else []
                        for metric, values in self.optimization_metrics.items()
                    }
                }
                
                return status
                
        except Exception as e:
            logger.error(f"Error getting optimization status: {e}")
            return {"error": str(e)}
    
    def _optimization_loop(self):
        """Main optimization loop for context-driven decision making."""
        logger.info("Context-driven optimization loop started")
        
        while not self.stop_optimization.is_set():
            try:
                # Get current environment context
                context = self.environment_monitor.get_current_environment()
                
                if context:
                    # Make optimization decision
                    decision = self.make_optimization_decision(context)
                    
                    # Apply optimization if confidence is high enough
                    if decision.confidence > 0.6:
                        if self.adaptation_mode == AdaptationMode.PROACTIVE:
                            self.apply_optimization(decision)
                        elif self.adaptation_mode == AdaptationMode.PREDICTIVE:
                            # Only apply if significant change is predicted
                            if self._predict_context_change(context):
                                self.apply_optimization(decision)
                    
                    # Update context history
                    self.context_history.append({
                        "timestamp": datetime.now(),
                        "context": context,
                        "decision": decision
                    })
                    
                    # Learn from recent optimizations
                    self._update_learning_from_recent_decisions()
                
                self.optimization_cycles += 1
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
            
            # Wait for next optimization cycle
            self.stop_optimization.wait(self.optimization_interval)
        
        logger.info("Context-driven optimization loop stopped")
    
    def _determine_context_state(self, context: Dict[str, Any]) -> ContextState:
        """Determine context state based on environment information."""
        try:
            system_metrics = context.get("system_metrics", {})
            
            cpu_usage = system_metrics.get("cpu_usage", 0)
            memory_usage = system_metrics.get("memory_percent", 0)
            active_apps = len(context.get("applications", {}))
            
            # Calculate overall load score
            load_score = (cpu_usage * 0.4 + memory_usage * 0.4 + min(active_apps * 5, 50) * 0.2)
            
            if load_score > 80:
                return ContextState.CRITICAL_LOAD
            elif load_score > 60:
                return ContextState.HEAVY_USAGE
            elif load_score > 30:
                return ContextState.MODERATE_USAGE
            elif load_score > 10:
                return ContextState.LIGHT_USAGE
            else:
                return ContextState.IDLE
                
        except Exception as e:
            logger.error(f"Error determining context state: {e}")
            return ContextState.IDLE
    
    def _select_optimization_strategy(self, context_state: ContextState, 
                                    context: Dict[str, Any]) -> OptimizationStrategy:
        """Select optimal strategy based on context state."""
        try:
            system_health = context.get("system_health", "good")
            
            if context_state == ContextState.CRITICAL_LOAD:
                return OptimizationStrategy.AGGRESSIVE
            elif context_state == ContextState.HEAVY_USAGE:
                if system_health in ["poor", "critical"]:
                    return OptimizationStrategy.AGGRESSIVE
                else:
                    return OptimizationStrategy.PERFORMANCE
            elif context_state == ContextState.MODERATE_USAGE:
                return OptimizationStrategy.BALANCED
            elif context_state == ContextState.LIGHT_USAGE:
                return OptimizationStrategy.EFFICIENCY
            else:  # IDLE
                return OptimizationStrategy.CONSERVATIVE
                
        except Exception as e:
            logger.error(f"Error selecting optimization strategy: {e}")
            return OptimizationStrategy.BALANCED
    
    def _generate_context_parameters(self, context_state: ContextState, 
                                   context: Dict[str, Any]) -> OptimizationParameters:
        """Generate optimization parameters based on context state."""
        try:
            base_params = OptimizationParameters()
            
            if context_state == ContextState.CRITICAL_LOAD:
                # Aggressive optimization for critical load
                base_params.monitoring_frequency = 2.0  # More frequent monitoring
                base_params.processing_intensity = 0.5  # Reduce processing intensity
                base_params.memory_usage_target = 0.5   # Lower memory target
                base_params.cpu_usage_target = 0.4      # Lower CPU target
                base_params.background_task_priority = 0.1  # Minimize background tasks
                base_params.cache_size_multiplier = 0.7     # Reduce cache size
                
            elif context_state == ContextState.HEAVY_USAGE:
                # Performance optimization
                base_params.monitoring_frequency = 3.0
                base_params.processing_intensity = 0.8
                base_params.memory_usage_target = 0.6
                base_params.cpu_usage_target = 0.5
                base_params.background_task_priority = 0.2
                base_params.parallel_processing_factor = 1.5
                
            elif context_state == ContextState.MODERATE_USAGE:
                # Balanced approach
                base_params.monitoring_frequency = 5.0
                base_params.processing_intensity = 1.0
                base_params.memory_usage_target = 0.7
                base_params.cpu_usage_target = 0.6
                base_params.background_task_priority = 0.3
                
            elif context_state == ContextState.LIGHT_USAGE:
                # Efficiency optimization
                base_params.monitoring_frequency = 10.0
                base_params.processing_intensity = 1.2
                base_params.memory_usage_target = 0.8
                base_params.cpu_usage_target = 0.7
                base_params.background_task_priority = 0.5
                base_params.cache_size_multiplier = 1.3
                
            else:  # IDLE
                # Conservative approach
                base_params.monitoring_frequency = 15.0
                base_params.processing_intensity = 1.5
                base_params.memory_usage_target = 0.9
                base_params.cpu_usage_target = 0.8
                base_params.background_task_priority = 0.8
                base_params.cache_size_multiplier = 1.5
            
            return base_params
            
        except Exception as e:
            logger.error(f"Error generating context parameters: {e}")
            return OptimizationParameters()
    
    def _find_matching_pattern(self, context: Dict[str, Any]) -> Optional[ContextPattern]:
        """Find a matching learned pattern for the current context."""
        try:
            context_state = self._determine_context_state(context)
            context_signature = self._generate_context_signature(context_state)
            
            # Look for exact match first
            if context_signature in self.learned_patterns:
                return self.learned_patterns[context_signature]
            
            # Look for similar patterns
            best_match = None
            best_similarity = 0.0
            
            for pattern in self.learned_patterns.values():
                similarity = self._calculate_pattern_similarity(context_signature, 
                                                              pattern.context_signature)
                if similarity > best_similarity and similarity > self.pattern_matching_threshold:
                    best_similarity = similarity
                    best_match = pattern
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding matching pattern: {e}")
            return None
    
    def _generate_context_signature(self, context_state: ContextState) -> str:
        """Generate a signature for context pattern matching."""
        # This is a simplified signature - could be enhanced with more context details
        return f"state_{context_state.value}"
    
    def _calculate_pattern_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between two context signatures."""
        # Simple similarity calculation - could be enhanced
        if sig1 == sig2:
            return 1.0
        
        # Extract state information
        state1 = sig1.split("_")[-1] if "_" in sig1 else sig1
        state2 = sig2.split("_")[-1] if "_" in sig2 else sig2
        
        # Define state similarity matrix
        state_similarity = {
            ("idle", "light_usage"): 0.7,
            ("light_usage", "moderate_usage"): 0.8,
            ("moderate_usage", "heavy_usage"): 0.8,
            ("heavy_usage", "critical_load"): 0.7,
        }
        
        key = (state1, state2) if (state1, state2) in state_similarity else (state2, state1)
        return state_similarity.get(key, 0.0)
    
    def _generate_optimization_reasoning(self, context_state: ContextState, 
                                       strategy: OptimizationStrategy, 
                                       context: Dict[str, Any]) -> List[str]:
        """Generate reasoning for optimization decision."""
        reasoning = []
        
        reasoning.append(f"Context state: {context_state.value}")
        reasoning.append(f"Selected strategy: {strategy.value}")
        
        system_metrics = context.get("system_metrics", {})
        cpu_usage = system_metrics.get("cpu_usage", 0)
        memory_usage = system_metrics.get("memory_percent", 0)
        
        if cpu_usage > 70:
            reasoning.append(f"High CPU usage detected: {cpu_usage:.1f}%")
        if memory_usage > 80:
            reasoning.append(f"High memory usage detected: {memory_usage:.1f}%")
        
        active_apps = len(context.get("applications", {}))
        if active_apps > 10:
            reasoning.append(f"Many active applications: {active_apps}")
        
        return reasoning
    
    def _calculate_decision_confidence(self, context_state: ContextState, 
                                     strategy: OptimizationStrategy, 
                                     context: Dict[str, Any]) -> float:
        """Calculate confidence in optimization decision."""
        try:
            confidence = 0.5  # Base confidence
            
            # Increase confidence based on clear context indicators
            system_metrics = context.get("system_metrics", {})
            cpu_usage = system_metrics.get("cpu_usage", 0)
            memory_usage = system_metrics.get("memory_percent", 0)
            
            # Clear high load indicators
            if context_state in [ContextState.HEAVY_USAGE, ContextState.CRITICAL_LOAD]:
                if cpu_usage > 80 or memory_usage > 85:
                    confidence += 0.3
            
            # Clear low load indicators
            if context_state in [ContextState.IDLE, ContextState.LIGHT_USAGE]:
                if cpu_usage < 20 and memory_usage < 40:
                    confidence += 0.2
            
            # Pattern matching confidence
            matching_pattern = self._find_matching_pattern(context)
            if matching_pattern and matching_pattern.success_rate > 0.7:
                confidence += 0.2
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Error calculating decision confidence: {e}")
            return 0.5
    
    def _estimate_optimization_impact(self, strategy: OptimizationStrategy, 
                                    parameters: OptimizationParameters, 
                                    context: Dict[str, Any]) -> Dict[str, float]:
        """Estimate the impact of optimization decision."""
        try:
            impact = {
                "performance_improvement": 0.0,
                "resource_efficiency": 0.0,
                "response_time_improvement": 0.0,
                "system_stability": 0.0
            }
            
            if strategy == OptimizationStrategy.AGGRESSIVE:
                impact["performance_improvement"] = 0.4
                impact["resource_efficiency"] = 0.6
                impact["response_time_improvement"] = 0.3
                impact["system_stability"] = 0.2
                
            elif strategy == OptimizationStrategy.PERFORMANCE:
                impact["performance_improvement"] = 0.6
                impact["resource_efficiency"] = 0.2
                impact["response_time_improvement"] = 0.5
                impact["system_stability"] = 0.3
                
            elif strategy == OptimizationStrategy.EFFICIENCY:
                impact["performance_improvement"] = 0.2
                impact["resource_efficiency"] = 0.7
                impact["response_time_improvement"] = 0.1
                impact["system_stability"] = 0.4
                
            elif strategy == OptimizationStrategy.CONSERVATIVE:
                impact["performance_improvement"] = 0.1
                impact["resource_efficiency"] = 0.3
                impact["response_time_improvement"] = 0.0
                impact["system_stability"] = 0.6
                
            else:  # BALANCED
                impact["performance_improvement"] = 0.3
                impact["resource_efficiency"] = 0.4
                impact["response_time_improvement"] = 0.2
                impact["system_stability"] = 0.4
            
            return impact
            
        except Exception as e:
            logger.error(f"Error estimating optimization impact: {e}")
            return {}
    
    def _validate_parameters(self, parameters: OptimizationParameters) -> OptimizationParameters:
        """Validate and clamp optimization parameters to safe bounds."""
        validated = OptimizationParameters()
        
        # Validate each parameter against bounds
        for param_name, (min_val, max_val) in self.parameter_bounds.items():
            current_val = getattr(parameters, param_name, getattr(validated, param_name))
            clamped_val = max(min_val, min(max_val, current_val))
            setattr(validated, param_name, clamped_val)
        
        # Copy resource allocation weights
        validated.resource_allocation_weights = parameters.resource_allocation_weights.copy()
        
        return validated
    
    def _calculate_success_score(self, expected: Dict[str, float], 
                               actual: Dict[str, float]) -> float:
        """Calculate success score by comparing expected vs actual impact."""
        try:
            if not expected or not actual:
                return 0.5
            
            scores = []
            for metric in expected:
                if metric in actual:
                    expected_val = expected[metric]
                    actual_val = actual[metric]
                    
                    if expected_val == 0:
                        score = 1.0 if actual_val >= 0 else 0.0
                    else:
                        # Calculate how close actual is to expected
                        ratio = actual_val / expected_val if expected_val > 0 else 0.0
                        score = min(1.0, ratio) if ratio > 0 else 0.0
                    
                    scores.append(score)
            
            return sum(scores) / len(scores) if scores else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating success score: {e}")
            return 0.5
    
    def _extract_resource_requirements(self, decision: OptimizationDecision) -> Dict[str, float]:
        """Extract resource requirements from optimization decision."""
        return {
            "cpu": decision.parameters.cpu_usage_target,
            "memory": decision.parameters.memory_usage_target,
            "processing": decision.parameters.processing_intensity,
            "monitoring": decision.parameters.monitoring_frequency
        }
    
    def _parameters_to_dict(self, parameters: OptimizationParameters) -> Dict[str, Any]:
        """Convert OptimizationParameters to dictionary."""
        return {
            "monitoring_frequency": parameters.monitoring_frequency,
            "processing_intensity": parameters.processing_intensity,
            "memory_usage_target": parameters.memory_usage_target,
            "cpu_usage_target": parameters.cpu_usage_target,
            "response_time_target": parameters.response_time_target,
            "background_task_priority": parameters.background_task_priority,
            "cache_size_multiplier": parameters.cache_size_multiplier,
            "parallel_processing_factor": parameters.parallel_processing_factor,
            "resource_allocation_weights": parameters.resource_allocation_weights
        }
    
    def _predict_context_change(self, context: Dict[str, Any]) -> bool:
        """Predict if significant context change is likely."""
        try:
            if len(self.context_history) < 5:
                return False
            
            # Analyze recent context trends
            recent_contexts = list(self.context_history)[-5:]
            
            # Check for trending resource usage
            cpu_values = []
            memory_values = []
            
            for ctx_entry in recent_contexts:
                ctx = ctx_entry.get("context", {})
                system_metrics = ctx.get("system_metrics", {})
                cpu_values.append(system_metrics.get("cpu_usage", 0))
                memory_values.append(system_metrics.get("memory_percent", 0))
            
            # Calculate trends
            cpu_trend = self._calculate_trend(cpu_values)
            memory_trend = self._calculate_trend(memory_values)
            
            # Predict change if strong upward trend
            return cpu_trend > 5.0 or memory_trend > 5.0
            
        except Exception as e:
            logger.error(f"Error predicting context change: {e}")
            return False
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction for a series of values."""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        # Calculate slope
        if n * x2_sum - x_sum * x_sum == 0:
            return 0.0
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        return slope
    
    def _update_learning_from_recent_decisions(self):
        """Update learning from recent optimization decisions."""
        try:
            # Get recent decisions with actual impact data
            recent_decisions = [d for d in list(self.optimization_decisions)[-10:] 
                              if d.actual_impact is not None]
            
            if len(recent_decisions) < 3:
                return
            
            # Calculate average success rate
            success_scores = [self._calculate_success_score(d.expected_impact, d.actual_impact) 
                            for d in recent_decisions]
            avg_success = sum(success_scores) / len(success_scores)
            
            # Adjust learning rate based on success
            if avg_success > 0.8:
                self.learning_rate = min(0.2, self.learning_rate * 1.1)
            elif avg_success < 0.5:
                self.learning_rate = max(0.05, self.learning_rate * 0.9)
            
            logger.debug(f"Updated learning rate: {self.learning_rate:.3f} (avg_success: {avg_success:.2f})")
            
        except Exception as e:
            logger.error(f"Error updating learning from recent decisions: {e}")