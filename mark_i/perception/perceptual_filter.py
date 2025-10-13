"""
Perceptual Filter for MARK-I intelligent focus and attention management.
"""

import logging
import threading
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context, ExecutionResult, IPerceptualFilter
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".perception.perceptual_filter")


@dataclass
class Rectangle:
    """Represents a rectangular region."""

    x: int
    y: int
    width: int
    height: int


@dataclass
class FocusTarget:
    """Represents a focus target for attention management."""

    target_id: str
    application: str
    window_title: str
    window_bounds: Rectangle
    relevance_score: float
    attention_weight: float
    confidence: float
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class IgnorePattern:
    """Represents a learned pattern to ignore during focus."""
    pattern_id: str
    pattern_type: str  # "application", "window_title", "region", "content"
    pattern_value: str
    confidence: float
    learned_from_feedback: bool = False
    usage_count: int = 0
    success_rate: float = 0.0
    last_used: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FocusStrategy:
    """Represents an adaptive focus strategy."""
    strategy_id: str
    strategy_type: str  # "window_based", "content_based", "context_based", "adaptive"
    parameters: Dict[str, Any]
    effectiveness_score: float = 0.5
    usage_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContextPattern:
    """Represents a learned context pattern for focus adaptation."""
    pattern_id: str
    context_features: Dict[str, Any]  # user_activity, time_of_day, active_apps, etc.
    preferred_focus_strategy: str
    effectiveness_history: List[float] = field(default_factory=list)
    confidence: float = 0.5
    last_updated: datetime = field(default_factory=datetime.now)


class PerceptualFilter(ProcessingComponent, IPerceptualFilter):
    """
    Intelligent focus and attention management system.
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)

        # Configuration
        self.noise_threshold = getattr(config, "noise_threshold", 0.3)
        self.processing_optimization = getattr(config, "processing_optimization", True)
        self.ignore_pattern_learning = getattr(config, "ignore_pattern_learning", True)
        self.context_awareness_depth = getattr(config, "context_awareness_depth", 3)
        self.efficiency_target = getattr(config, "efficiency_target", 0.85)
        self.focus_adaptation_rate = getattr(config, "focus_adaptation_rate", 0.2)

        # State management
        self.focus_targets: Dict[str, FocusTarget] = {}
        self.ignore_patterns: Dict[str, IgnorePattern] = {}
        self.focus_strategies: Dict[str, FocusStrategy] = {}
        self.context_patterns: Dict[str, ContextPattern] = {}
        
        # Threading and synchronization
        self.focus_lock = threading.Lock()
        self.pattern_lock = threading.Lock()
        self.strategy_lock = threading.Lock()
        
        # Performance tracking
        self.distractions_filtered = 0
        self.focus_switches = 0
        self.efficiency_history: List[float] = []
        self.current_strategy = "adaptive"
        
        # Learning and adaptation
        self.feedback_history: List[Dict[str, Any]] = []
        self.context_history: List[Context] = []
        
        # Initialize default strategies
        self._initialize_default_strategies()
        
        # Load learned patterns and strategies
        self._load_learned_data()

        logger.info("PerceptualFilter initialized with adaptive learning capabilities")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this perceptual filter."""
        return {
            "focus_targeting": True,
            "attention_filtering": True,
            "pattern_learning": True,
            "strategy_adaptation": True,
            "efficiency_optimization": True,
            "supported_image_formats": ["numpy_array"],
            "max_targets": 100,
        }

    def identify_focus_targets(self, context: Context) -> List[Dict[str, Any]]:
        """Identify potential focus targets from the current context."""
        targets = []

        try:
            active_apps = context.active_applications or []

            for i, app in enumerate(active_apps):
                target_id = f"app_{i}_{int(time.time())}"

                bounds = Rectangle(x=100 + i * 50, y=100 + i * 50, width=800, height=600)
                relevance_score = self._calculate_relevance_score_adaptive(app, context)

                target = FocusTarget(
                    target_id=target_id, application=app, window_title=f"{app} Window", window_bounds=bounds, relevance_score=relevance_score, attention_weight=relevance_score, confidence=0.8
                )

                # Convert to dict for interface compliance
                target_dict = {
                    "target_id": target.target_id,
                    "application": target.application,
                    "window_title": target.window_title,
                    "window_bounds": {"x": target.window_bounds.x, "y": target.window_bounds.y, "width": target.window_bounds.width, "height": target.window_bounds.height},
                    "relevance_score": target.relevance_score,
                    "attention_weight": target.attention_weight,
                    "confidence": target.confidence,
                }

                targets.append(target_dict)

                with self.focus_lock:
                    self.focus_targets[target_id] = target

            logger.debug(f"Identified {len(targets)} focus targets")
            return targets

        except Exception as e:
            logger.error(f"Error identifying focus targets: {e}")
            return []

    def _calculate_relevance_score(self, application: str, context: Context) -> float:
        """Calculate relevance score for an application."""
        base_score = 0.5

        # Boost score for development tools
        dev_tools = ["vscode", "pycharm", "intellij", "eclipse", "vim", "emacs"]
        if any(tool in application.lower() for tool in dev_tools):
            base_score += 0.3

        # Boost score for browsers
        browsers = ["chrome", "firefox", "safari", "edge"]
        if any(browser in application.lower() for browser in browsers):
            base_score += 0.2

        return max(0.0, min(1.0, base_score))

    def _initialize_default_strategies(self):
        """Initialize default focus strategies."""
        with self.strategy_lock:
            # Window-based strategy
            self.focus_strategies["window_based"] = FocusStrategy(
                strategy_id="window_based",
                strategy_type="window_based",
                parameters={
                    "window_priority_weights": {"development": 0.8, "browser": 0.6, "communication": 0.4},
                    "size_weight_factor": 0.2,
                    "position_weight_factor": 0.1
                }
            )
            
            # Content-based strategy
            self.focus_strategies["content_based"] = FocusStrategy(
                strategy_id="content_based",
                strategy_type="content_based",
                parameters={
                    "content_analysis_depth": 2,
                    "text_density_weight": 0.3,
                    "visual_complexity_weight": 0.2
                }
            )
            
            # Context-based strategy
            self.focus_strategies["context_based"] = FocusStrategy(
                strategy_id="context_based",
                strategy_type="context_based",
                parameters={
                    "time_of_day_weight": 0.2,
                    "user_activity_weight": 0.5,
                    "historical_preference_weight": 0.3
                }
            )
            
            # Adaptive strategy (combines others)
            self.focus_strategies["adaptive"] = FocusStrategy(
                strategy_id="adaptive",
                strategy_type="adaptive",
                parameters={
                    "strategy_weights": {"window_based": 0.4, "content_based": 0.3, "context_based": 0.3},
                    "adaptation_rate": self.focus_adaptation_rate,
                    "min_confidence_threshold": 0.6
                }
            )

    def _calculate_relevance_score_adaptive(self, application: str, context: Context) -> float:
        """Calculate relevance score using adaptive strategies."""
        try:
            # Get current strategy
            current_strategy = self.focus_strategies.get(self.current_strategy)
            if not current_strategy:
                return self._calculate_relevance_score(application, context)
            
            base_score = self._calculate_relevance_score(application, context)
            
            # Apply strategy-specific adjustments
            if current_strategy.strategy_type == "window_based":
                score = self._apply_window_based_strategy(application, context, base_score, current_strategy.parameters)
            elif current_strategy.strategy_type == "content_based":
                score = self._apply_content_based_strategy(application, context, base_score, current_strategy.parameters)
            elif current_strategy.strategy_type == "context_based":
                score = self._apply_context_based_strategy(application, context, base_score, current_strategy.parameters)
            elif current_strategy.strategy_type == "adaptive":
                score = self._apply_adaptive_strategy(application, context, base_score, current_strategy.parameters)
            else:
                score = base_score
            
            # Apply ignore patterns
            score = self._apply_ignore_patterns(application, score)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error in adaptive relevance calculation: {e}")
            return self._calculate_relevance_score(application, context)

    def _apply_window_based_strategy(self, application: str, context: Context, base_score: float, params: Dict[str, Any]) -> float:
        """Apply window-based focus strategy."""
        priority_weights = params.get("window_priority_weights", {})
        
        # Check application category
        for category, weight in priority_weights.items():
            if category in application.lower():
                base_score *= weight
                break
        
        return base_score

    def _apply_content_based_strategy(self, application: str, context: Context, base_score: float, params: Dict[str, Any]) -> float:
        """Apply content-based focus strategy."""
        # In a real implementation, this would analyze window content
        # For now, we'll use application type as a proxy
        text_apps = ["notepad", "word", "writer", "editor"]
        if any(app in application.lower() for app in text_apps):
            base_score *= 1.2
        
        return base_score

    def _apply_context_based_strategy(self, application: str, context: Context, base_score: float, params: Dict[str, Any]) -> float:
        """Apply context-based focus strategy."""
        # Time-based adjustments
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Work hours
            work_apps = ["vscode", "pycharm", "excel", "word"]
            if any(app in application.lower() for app in work_apps):
                base_score *= 1.3
        
        # User activity adjustments
        if context.user_activity:
            activity = context.user_activity.lower()
            if "coding" in activity and any(tool in application.lower() for tool in ["vscode", "pycharm", "intellij"]):
                base_score *= 1.4
            elif "research" in activity and any(browser in application.lower() for browser in ["chrome", "firefox"]):
                base_score *= 1.2
        
        return base_score

    def _apply_adaptive_strategy(self, application: str, context: Context, base_score: float, params: Dict[str, Any]) -> float:
        """Apply adaptive strategy that combines multiple approaches."""
        strategy_weights = params.get("strategy_weights", {})
        
        # Calculate scores from different strategies
        window_score = self._apply_window_based_strategy(application, context, base_score, 
                                                       self.focus_strategies["window_based"].parameters)
        content_score = self._apply_content_based_strategy(application, context, base_score,
                                                         self.focus_strategies["content_based"].parameters)
        context_score = self._apply_context_based_strategy(application, context, base_score,
                                                         self.focus_strategies["context_based"].parameters)
        
        # Weighted combination
        combined_score = (
            window_score * strategy_weights.get("window_based", 0.4) +
            content_score * strategy_weights.get("content_based", 0.3) +
            context_score * strategy_weights.get("context_based", 0.3)
        )
        
        return combined_score

    def _apply_ignore_patterns(self, application: str, score: float) -> float:
        """Apply learned ignore patterns to adjust relevance score."""
        with self.pattern_lock:
            for pattern in self.ignore_patterns.values():
                if pattern.pattern_type == "application":
                    if pattern.pattern_value.lower() in application.lower():
                        # Reduce score based on pattern confidence and success rate
                        reduction_factor = pattern.confidence * (1.0 + pattern.success_rate) / 2.0
                        score *= (1.0 - reduction_factor)
                        pattern.usage_count += 1
                        pattern.last_used = datetime.now()
        
        return score

    def learn_ignore_pattern_from_feedback(self, application: str, pattern_type: str, confidence: float = 0.8):
        """Learn a new ignore pattern from user feedback."""
        if not self.ignore_pattern_learning:
            return
        
        pattern_id = f"{pattern_type}_{hash(application)}_{int(time.time())}"
        
        pattern = IgnorePattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            pattern_value=application,
            confidence=confidence,
            learned_from_feedback=True
        )
        
        with self.pattern_lock:
            self.ignore_patterns[pattern_id] = pattern
        
        logger.info(f"Learned ignore pattern: {pattern_type}='{application}' (confidence: {confidence})")

    def adapt_context_strategy(self, context: Context, effectiveness_feedback: float):
        """Adapt focus strategy based on context and effectiveness feedback."""
        try:
            # Create context signature
            context_signature = self._create_context_signature(context)
            
            # Find or create context pattern
            pattern_id = f"context_{hash(str(context_signature))}"
            
            with self.strategy_lock:
                if pattern_id not in self.context_patterns:
                    self.context_patterns[pattern_id] = ContextPattern(
                        pattern_id=pattern_id,
                        context_features=context_signature,
                        preferred_focus_strategy=self.current_strategy
                    )
                
                pattern = self.context_patterns[pattern_id]
                pattern.effectiveness_history.append(effectiveness_feedback)
                
                # Limit history size
                if len(pattern.effectiveness_history) > 20:
                    pattern.effectiveness_history = pattern.effectiveness_history[-20:]
                
                # Update confidence based on consistency
                if len(pattern.effectiveness_history) >= 3:
                    recent_avg = sum(pattern.effectiveness_history[-3:]) / 3
                    pattern.confidence = min(1.0, pattern.confidence + 0.1 if recent_avg > 0.7 else pattern.confidence - 0.05)
                
                pattern.last_updated = datetime.now()
                
                # Adapt strategy if needed
                if effectiveness_feedback < 0.5 and pattern.confidence > 0.6:
                    self._switch_focus_strategy(context)
            
            logger.debug(f"Adapted context strategy: effectiveness={effectiveness_feedback:.2f}")
            
        except Exception as e:
            logger.error(f"Error adapting context strategy: {e}")

    def _create_context_signature(self, context: Context) -> Dict[str, Any]:
        """Create a signature for the current context."""
        signature = {
            "hour_of_day": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "active_app_count": len(context.active_applications or []),
            "primary_app_category": self._categorize_primary_app(context.active_applications or []),
            "user_activity": context.user_activity or "unknown"
        }
        return signature

    def _categorize_primary_app(self, active_apps: List[str]) -> str:
        """Categorize the primary application type."""
        if not active_apps:
            return "none"
        
        primary_app = active_apps[0].lower()
        
        if any(tool in primary_app for tool in ["vscode", "pycharm", "intellij", "vim", "emacs"]):
            return "development"
        elif any(browser in primary_app for browser in ["chrome", "firefox", "safari", "edge"]):
            return "browser"
        elif any(comm in primary_app for comm in ["slack", "teams", "discord", "telegram"]):
            return "communication"
        elif any(media in primary_app for media in ["spotify", "vlc", "youtube", "netflix"]):
            return "media"
        else:
            return "other"

    def _switch_focus_strategy(self, context: Context):
        """Switch to a different focus strategy based on context."""
        current_effectiveness = self.focus_strategies[self.current_strategy].effectiveness_score
        
        # Try different strategies and pick the best one
        best_strategy = self.current_strategy
        best_score = current_effectiveness
        
        for strategy_id, strategy in self.focus_strategies.items():
            if strategy_id != self.current_strategy and strategy.effectiveness_score > best_score:
                best_strategy = strategy_id
                best_score = strategy.effectiveness_score
        
        if best_strategy != self.current_strategy:
            self.current_strategy = best_strategy
            self.focus_switches += 1
            logger.info(f"Switched focus strategy to: {best_strategy} (score: {best_score:.2f})")

    def update_strategy_effectiveness(self, strategy_id: str, effectiveness: float):
        """Update the effectiveness score of a focus strategy."""
        with self.strategy_lock:
            if strategy_id in self.focus_strategies:
                strategy = self.focus_strategies[strategy_id]
                # Exponential moving average
                alpha = 0.3
                strategy.effectiveness_score = alpha * effectiveness + (1 - alpha) * strategy.effectiveness_score
                strategy.usage_count += 1
                strategy.last_used = datetime.now()

    def get_processing_efficiency_metrics(self) -> Dict[str, Any]:
        """Get detailed processing efficiency metrics."""
        try:
            total_targets = len(self.focus_targets)
            active_targets = sum(1 for t in self.focus_targets.values() 
                               if t.attention_weight > self.noise_threshold)
            
            focus_efficiency = active_targets / max(1, total_targets)
            
            # Calculate strategy effectiveness
            current_strategy = self.focus_strategies.get(self.current_strategy)
            strategy_effectiveness = current_strategy.effectiveness_score if current_strategy else 0.5
            
            # Calculate learning progress
            pattern_count = len(self.ignore_patterns)
            context_pattern_count = len(self.context_patterns)
            
            # Overall efficiency
            overall_efficiency = (focus_efficiency + strategy_effectiveness) / 2.0
            
            # Store in history
            self.efficiency_history.append(overall_efficiency)
            if len(self.efficiency_history) > 100:
                self.efficiency_history = self.efficiency_history[-100:]
            
            # Calculate trend
            efficiency_trend = 0.0
            if len(self.efficiency_history) >= 10:
                recent_avg = sum(self.efficiency_history[-5:]) / 5
                older_avg = sum(self.efficiency_history[-10:-5]) / 5
                efficiency_trend = recent_avg - older_avg
            
            metrics = {
                "focus_efficiency": focus_efficiency,
                "strategy_effectiveness": strategy_effectiveness,
                "overall_efficiency": overall_efficiency,
                "efficiency_trend": efficiency_trend,
                "distractions_filtered": self.distractions_filtered,
                "focus_switches": self.focus_switches,
                "total_targets": total_targets,
                "active_targets": active_targets,
                "learned_patterns": pattern_count,
                "context_patterns": context_pattern_count,
                "current_strategy": self.current_strategy,
                "noise_threshold": self.noise_threshold
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating efficiency metrics: {e}")
            return {"overall_efficiency": 0.5}

    def _load_learned_data(self):
        """Load learned patterns and strategies from disk."""
        try:
            data_dir = os.path.join(os.path.dirname(__file__), "learned_data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Load ignore patterns
            patterns_file = os.path.join(data_dir, "ignore_patterns.json")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                
                with self.pattern_lock:
                    for pattern_data in patterns_data:
                        pattern = IgnorePattern(
                            pattern_id=pattern_data["pattern_id"],
                            pattern_type=pattern_data["pattern_type"],
                            pattern_value=pattern_data["pattern_value"],
                            confidence=pattern_data["confidence"],
                            learned_from_feedback=pattern_data.get("learned_from_feedback", False),
                            usage_count=pattern_data.get("usage_count", 0),
                            success_rate=pattern_data.get("success_rate", 0.0),
                            last_used=datetime.fromisoformat(pattern_data.get("last_used", datetime.now().isoformat())),
                            created_at=datetime.fromisoformat(pattern_data.get("created_at", datetime.now().isoformat()))
                        )
                        self.ignore_patterns[pattern.pattern_id] = pattern
                
                logger.info(f"Loaded {len(patterns_data)} ignore patterns")
            
            # Load context patterns
            context_file = os.path.join(data_dir, "context_patterns.json")
            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    context_data = json.load(f)
                
                with self.strategy_lock:
                    for context_pattern_data in context_data:
                        pattern = ContextPattern(
                            pattern_id=context_pattern_data["pattern_id"],
                            context_features=context_pattern_data["context_features"],
                            preferred_focus_strategy=context_pattern_data["preferred_focus_strategy"],
                            effectiveness_history=context_pattern_data.get("effectiveness_history", []),
                            confidence=context_pattern_data.get("confidence", 0.5),
                            last_updated=datetime.fromisoformat(context_pattern_data.get("last_updated", datetime.now().isoformat()))
                        )
                        self.context_patterns[pattern.pattern_id] = pattern
                
                logger.info(f"Loaded {len(context_data)} context patterns")
        
        except Exception as e:
            logger.warning(f"Could not load learned data: {e}")

    def _save_learned_data(self):
        """Save learned patterns and strategies to disk."""
        try:
            data_dir = os.path.join(os.path.dirname(__file__), "learned_data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Save ignore patterns
            patterns_file = os.path.join(data_dir, "ignore_patterns.json")
            with self.pattern_lock:
                patterns_data = []
                for pattern in self.ignore_patterns.values():
                    pattern_dict = {
                        "pattern_id": pattern.pattern_id,
                        "pattern_type": pattern.pattern_type,
                        "pattern_value": pattern.pattern_value,
                        "confidence": pattern.confidence,
                        "learned_from_feedback": pattern.learned_from_feedback,
                        "usage_count": pattern.usage_count,
                        "success_rate": pattern.success_rate,
                        "last_used": pattern.last_used.isoformat(),
                        "created_at": pattern.created_at.isoformat()
                    }
                    patterns_data.append(pattern_dict)
            
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
            
            # Save context patterns
            context_file = os.path.join(data_dir, "context_patterns.json")
            with self.strategy_lock:
                context_data = []
                for pattern in self.context_patterns.values():
                    pattern_dict = {
                        "pattern_id": pattern.pattern_id,
                        "context_features": pattern.context_features,
                        "preferred_focus_strategy": pattern.preferred_focus_strategy,
                        "effectiveness_history": pattern.effectiveness_history,
                        "confidence": pattern.confidence,
                        "last_updated": pattern.last_updated.isoformat()
                    }
                    context_data.append(pattern_dict)
            
            with open(context_file, 'w') as f:
                json.dump(context_data, f, indent=2)
            
            logger.info(f"Saved {len(patterns_data)} ignore patterns and {len(context_data)} context patterns")
        
        except Exception as e:
            logger.warning(f"Could not save learned data: {e}")

    def apply_attention_filter(self, image: np.ndarray, targets: List[Dict[str, Any]]) -> np.ndarray:
        """Apply attention filter to focus on relevant regions."""
        if not targets or not self.processing_optimization:
            return image

        try:
            # Create attention mask
            attention_mask = np.ones(image.shape[:2], dtype=np.float32) * 0.1

            # Apply attention weights to target regions
            for target_dict in targets:
                attention_weight = target_dict.get("attention_weight", 0.0)
                if attention_weight > self.noise_threshold:
                    bounds = target_dict.get("window_bounds", {})
                    x1 = max(0, bounds.get("x", 0))
                    y1 = max(0, bounds.get("y", 0))
                    x2 = min(image.shape[1], x1 + bounds.get("width", 0))
                    y2 = min(image.shape[0], y1 + bounds.get("height", 0))

                    if x2 > x1 and y2 > y1:
                        attention_mask[y1:y2, x1:x2] = attention_weight

            # Apply attention filter
            if len(image.shape) == 3:
                filtered_image = image.copy()
                for c in range(image.shape[2]):
                    filtered_image[:, :, c] = (filtered_image[:, :, c] * attention_mask).astype(np.uint8)
            else:
                filtered_image = (image * attention_mask).astype(np.uint8)

            self.distractions_filtered += 1
            return filtered_image

        except Exception as e:
            logger.error(f"Error applying attention filter: {e}")
            return image

    def learn_ignore_patterns(self, patterns: List[Dict[str, Any]]) -> None:
        """Learn patterns that should be ignored."""
        for pattern_dict in patterns:
            pattern_type = pattern_dict.get("pattern_type", "application")
            pattern_value = pattern_dict.get("pattern_value", "")
            confidence = pattern_dict.get("confidence", 0.8)
            
            if pattern_value:
                self.learn_ignore_pattern_from_feedback(pattern_value, pattern_type, confidence)

    def adapt_focus_strategy(self, feedback: Dict[str, Any]) -> None:
        """Adapt focus strategy based on user feedback."""
        try:
            effectiveness = feedback.get("effectiveness", 0.5)
            focus_accuracy = feedback.get("focus_accuracy", 0.5)
            
            # Store feedback for learning
            self.feedback_history.append({
                "effectiveness": effectiveness,
                "focus_accuracy": focus_accuracy,
                "timestamp": datetime.now(),
                "strategy": self.current_strategy
            })
            
            # Limit feedback history
            if len(self.feedback_history) > 50:
                self.feedback_history = self.feedback_history[-50:]
            
            # Adapt noise threshold
            if effectiveness > 0.8:
                self.noise_threshold = max(0.1, self.noise_threshold * 0.95)
            elif effectiveness < 0.4:
                self.noise_threshold = min(0.6, self.noise_threshold * 1.05)
            
            # Update current strategy effectiveness
            self.update_strategy_effectiveness(self.current_strategy, effectiveness)
            
            # Learn ignore patterns from negative feedback
            if "ignore_application" in feedback:
                self.learn_ignore_pattern_from_feedback(feedback["ignore_application"], "application", 0.9)
            
            if "ignore_window" in feedback:
                self.learn_ignore_pattern_from_feedback(feedback["ignore_window"], "window_title", 0.9)
            
            # Adapt context strategy if context is provided
            if "context" in feedback:
                self.adapt_context_strategy(feedback["context"], effectiveness)
            
            logger.debug(f"Adapted focus strategy: effectiveness={effectiveness}, threshold={self.noise_threshold}")

        except Exception as e:
            logger.error(f"Error adapting focus strategy: {e}")

    def optimize_processing_efficiency(self) -> Dict[str, Any]:
        """Optimize processing efficiency and return metrics."""
        return self.get_processing_efficiency_metrics()

    def process(self, input_data: Any) -> ExecutionResult:
        """Process input through the perceptual filter."""
        try:
            if isinstance(input_data, dict):
                command = input_data.get("command")

                if command == "identify_targets":
                    context = input_data.get("context")
                    if context and isinstance(context, Context):
                        targets = self.identify_focus_targets(context)
                        return ExecutionResult(success=True, message=f"Identified {len(targets)} focus targets", data={"targets": targets})

                elif command == "get_metrics":
                    metrics = self.optimize_processing_efficiency()
                    return ExecutionResult(success=True, message="Processing efficiency metrics retrieved", data=metrics)
                
                elif command == "adapt_strategy":
                    feedback = input_data.get("feedback", {})
                    self.adapt_focus_strategy(feedback)
                    return ExecutionResult(success=True, message="Focus strategy adapted based on feedback", data={})
                
                elif command == "learn_pattern":
                    pattern_type = input_data.get("pattern_type", "application")
                    pattern_value = input_data.get("pattern_value", "")
                    confidence = input_data.get("confidence", 0.8)
                    
                    if pattern_value:
                        self.learn_ignore_pattern_from_feedback(pattern_value, pattern_type, confidence)
                        return ExecutionResult(success=True, message="Ignore pattern learned successfully", data={})
                
                elif command == "get_strategies":
                    strategies = {sid: {"type": s.strategy_type, "effectiveness": s.effectiveness_score, "usage_count": s.usage_count} 
                                for sid, s in self.focus_strategies.items()}
                    return ExecutionResult(success=True, message="Focus strategies retrieved", data={"strategies": strategies, "current": self.current_strategy})
                
                elif command == "switch_strategy":
                    strategy_id = input_data.get("strategy_id")
                    if strategy_id in self.focus_strategies:
                        self.current_strategy = strategy_id
                        self.focus_switches += 1
                        return ExecutionResult(success=True, message=f"Switched to strategy: {strategy_id}", data={})
                    else:
                        return ExecutionResult(success=False, message=f"Unknown strategy: {strategy_id}", data={})

            return ExecutionResult(success=False, message="Invalid input for PerceptualFilter", data={})

        except Exception as e:
            logger.error(f"Error processing input in PerceptualFilter: {e}")
            return ExecutionResult(success=False, message=f"Processing error: {str(e)}", data={})
    
    def cleanup(self):
        """Clean up resources and save learned data."""
        self._save_learned_data()
        logger.info("PerceptualFilter cleanup completed")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass
