"""
Context History Tracker for MARK-I

This module provides comprehensive context history tracking and pattern recognition
capabilities for understanding long-term system behavior and user patterns.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import pickle
import os

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".context.context_history_tracker")


class PatternType(Enum):
    """Types of patterns that can be detected."""

    TEMPORAL = "temporal"  # Time-based patterns
    USAGE = "usage"  # Application usage patterns
    RESOURCE = "resource"  # Resource consumption patterns
    BEHAVIORAL = "behavioral"  # User behavior patterns
    SYSTEM = "system"  # System state patterns


class PatternFrequency(Enum):
    """Frequency of pattern occurrence."""

    RARE = "rare"  # < 5% of time
    OCCASIONAL = "occasional"  # 5-20% of time
    FREQUENT = "frequent"  # 20-50% of time
    COMMON = "common"  # 50-80% of time
    DOMINANT = "dominant"  # > 80% of time


@dataclass
class ContextSnapshot:
    """A snapshot of system context at a specific time."""

    timestamp: datetime
    system_metrics: Dict[str, float]
    active_applications: List[str]
    user_activity_level: float
    environment_state: str
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextPattern:
    """A detected pattern in context history."""

    pattern_id: str
    pattern_type: PatternType
    description: str
    frequency: PatternFrequency
    confidence: float
    first_detected: datetime
    last_seen: datetime
    occurrence_count: int
    typical_duration: timedelta
    conditions: Dict[str, Any]
    associated_contexts: List[str]
    prediction_accuracy: float = 0.0


class ContextHistoryTracker(ProcessingComponent):
    """
    Comprehensive context history tracking and pattern recognition system
    for understanding long-term system behavior and user patterns.
    """

    def __init__(self, config: ComponentConfig):
        super().__init__("context_history_tracker", config)

        # Configuration
        self.tracking_interval = getattr(config, "tracking_interval", 30.0)
        self.max_history_size = getattr(config, "max_history_size", 10000)
        self.pattern_detection_threshold = getattr(config, "pattern_detection_threshold", 0.7)
        self.storage_path = getattr(config, "storage_path", "storage/context_history")
        self.enable_persistence = getattr(config, "enable_persistence", True)

        # History storage
        self.context_history: deque = deque(maxlen=self.max_history_size)
        self.detected_patterns: Dict[str, ContextPattern] = {}
        self.pattern_predictions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Pattern detection
        self.pattern_detectors: Dict[PatternType, Callable] = {}
        self.pattern_cache: Dict[str, Any] = {}
        self.last_pattern_detection = None

        # Tracking state
        self.tracking_active = False
        self.last_snapshot_time = None

        # Threading
        self.tracking_lock = threading.Lock()
        self.tracking_thread: Optional[threading.Thread] = None
        self.stop_tracking = threading.Event()

        # Statistics
        self.snapshots_captured = 0
        self.patterns_detected = 0
        self.predictions_made = 0
        self.prediction_accuracy = 0.0

        # Initialize storage
        self._initialize_storage()

        # Initialize pattern detectors
        self._initialize_pattern_detectors()

        logger.info("ContextHistoryTracker initialized")

    def start_tracking(self) -> bool:
        """Start context history tracking."""
        try:
            if self.tracking_active:
                logger.warning("Context history tracking already active")
                return True

            # Load existing history if available
            self._load_history()

            self.tracking_active = True
            self.stop_tracking.clear()

            # Start tracking thread
            self.tracking_thread = threading.Thread(target=self._tracking_loop, name="ContextHistoryTracker", daemon=True)
            self.tracking_thread.start()

            logger.info("Context history tracking started")
            return True

        except Exception as e:
            logger.error(f"Error starting context history tracking: {e}")
            return False

    def stop_tracking(self) -> bool:
        """Stop context history tracking."""
        try:
            if not self.tracking_active:
                return True

            self.tracking_active = False
            self.stop_tracking.set()

            if self.tracking_thread and self.tracking_thread.is_alive():
                self.tracking_thread.join(timeout=10.0)

            # Save history before stopping
            if self.enable_persistence:
                self._save_history()

            logger.info("Context history tracking stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping context history tracking: {e}")
            return False

    def add_context_snapshot(self, context: Dict[str, Any]) -> bool:
        """Add a context snapshot to the history."""
        try:
            # Extract relevant information
            system_metrics = context.get("system_metrics", {})
            applications = context.get("applications", {})

            snapshot = ContextSnapshot(
                timestamp=datetime.now(),
                system_metrics={
                    "cpu_usage": system_metrics.get("cpu_usage", 0.0),
                    "memory_usage": system_metrics.get("memory_percent", 0.0),
                    "disk_usage": system_metrics.get("disk_percent", 0.0),
                    "network_activity": system_metrics.get("network_bytes_sent", 0) + system_metrics.get("network_bytes_recv", 0),
                },
                active_applications=list(applications.keys())[:10],  # Limit to top 10
                user_activity_level=self._estimate_user_activity(context),
                environment_state=context.get("system_health", "unknown"),
                custom_metrics={},
            )

            with self.tracking_lock:
                self.context_history.append(snapshot)
                self.snapshots_captured += 1
                self.last_snapshot_time = datetime.now()

            return True

        except Exception as e:
            logger.error(f"Error adding context snapshot: {e}")
            return False

    def detect_patterns(self) -> List[ContextPattern]:
        """Detect patterns in the context history."""
        try:
            if len(self.context_history) < 50:  # Need sufficient data
                return []

            new_patterns = []

            # Run pattern detection for each type
            for pattern_type, detector in self.pattern_detectors.items():
                try:
                    patterns = detector(list(self.context_history))
                    for pattern in patterns:
                        if pattern.confidence >= self.pattern_detection_threshold:
                            pattern_key = f"{pattern_type.value}_{pattern.pattern_id}"

                            if pattern_key not in self.detected_patterns:
                                self.detected_patterns[pattern_key] = pattern
                                new_patterns.append(pattern)
                                self.patterns_detected += 1
                            else:
                                # Update existing pattern
                                existing = self.detected_patterns[pattern_key]
                                existing.last_seen = pattern.last_seen
                                existing.occurrence_count += 1
                                existing.confidence = (existing.confidence + pattern.confidence) / 2

                except Exception as e:
                    logger.error(f"Error in {pattern_type.value} pattern detection: {e}")

            self.last_pattern_detection = datetime.now()

            if new_patterns:
                logger.info(f"Detected {len(new_patterns)} new patterns")

            return new_patterns

        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []

    def predict_context_changes(self, horizon_minutes: int = 30) -> List[Dict[str, Any]]:
        """Predict context changes based on historical patterns."""
        try:
            predictions = []
            current_time = datetime.now()
            prediction_time = current_time + timedelta(minutes=horizon_minutes)

            # Use detected patterns to make predictions
            for pattern in self.detected_patterns.values():
                if pattern.pattern_type == PatternType.TEMPORAL:
                    prediction = self._predict_from_temporal_pattern(pattern, prediction_time)
                    if prediction:
                        predictions.append(prediction)

                elif pattern.pattern_type == PatternType.USAGE:
                    prediction = self._predict_from_usage_pattern(pattern, prediction_time)
                    if prediction:
                        predictions.append(prediction)

            self.predictions_made += len(predictions)

            # Store predictions for accuracy tracking
            for prediction in predictions:
                self.pattern_predictions[prediction["pattern_id"]].append({"prediction": prediction, "made_at": current_time, "target_time": prediction_time})

            return predictions

        except Exception as e:
            logger.error(f"Error predicting context changes: {e}")
            return []

    def get_context_summary(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get a summary of context history for the specified time range."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            recent_snapshots = [s for s in self.context_history if s.timestamp > cutoff_time]

            if not recent_snapshots:
                return {"error": "No data available for the specified time range"}

            # Calculate statistics
            cpu_values = [s.system_metrics.get("cpu_usage", 0) for s in recent_snapshots]
            memory_values = [s.system_metrics.get("memory_usage", 0) for s in recent_snapshots]

            # Find most common applications
            app_counter = defaultdict(int)
            for snapshot in recent_snapshots:
                for app in snapshot.active_applications:
                    app_counter[app] += 1

            top_apps = sorted(app_counter.items(), key=lambda x: x[1], reverse=True)[:5]

            # Analyze user activity patterns
            activity_levels = [s.user_activity_level for s in recent_snapshots]

            summary = {
                "time_range_hours": time_range_hours,
                "snapshots_analyzed": len(recent_snapshots),
                "system_metrics": {
                    "cpu_usage": {"average": statistics.mean(cpu_values), "max": max(cpu_values), "min": min(cpu_values)},
                    "memory_usage": {"average": statistics.mean(memory_values), "max": max(memory_values), "min": min(memory_values)},
                },
                "top_applications": [{"name": app, "frequency": count} for app, count in top_apps],
                "user_activity": {"average_level": statistics.mean(activity_levels), "peak_activity": max(activity_levels), "low_activity": min(activity_levels)},
                "patterns_detected": len(self.detected_patterns),
                "tracking_statistics": {
                    "total_snapshots": self.snapshots_captured,
                    "patterns_detected": self.patterns_detected,
                    "predictions_made": self.predictions_made,
                    "prediction_accuracy": self.prediction_accuracy,
                },
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            return {"error": str(e)}

    def get_pattern_insights(self) -> Dict[str, Any]:
        """Get insights about detected patterns."""
        try:
            if not self.detected_patterns:
                return {"message": "No patterns detected yet"}

            # Group patterns by type
            patterns_by_type = defaultdict(list)
            for pattern in self.detected_patterns.values():
                patterns_by_type[pattern.pattern_type.value].append(pattern)

            # Analyze pattern characteristics
            insights = {"total_patterns": len(self.detected_patterns), "patterns_by_type": {}, "most_confident_patterns": [], "most_frequent_patterns": [], "recent_patterns": []}

            for pattern_type, patterns in patterns_by_type.items():
                insights["patterns_by_type"][pattern_type] = {
                    "count": len(patterns),
                    "average_confidence": statistics.mean([p.confidence for p in patterns]),
                    "frequency_distribution": self._analyze_frequency_distribution(patterns),
                }

            # Find most confident patterns
            all_patterns = list(self.detected_patterns.values())
            insights["most_confident_patterns"] = [
                {"pattern_id": p.pattern_id, "type": p.pattern_type.value, "description": p.description, "confidence": p.confidence}
                for p in sorted(all_patterns, key=lambda x: x.confidence, reverse=True)[:5]
            ]

            # Find most frequent patterns
            insights["most_frequent_patterns"] = [
                {"pattern_id": p.pattern_id, "type": p.pattern_type.value, "description": p.description, "frequency": p.frequency.value, "occurrence_count": p.occurrence_count}
                for p in sorted(all_patterns, key=lambda x: x.occurrence_count, reverse=True)[:5]
            ]

            # Find recently detected patterns
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_patterns = [p for p in all_patterns if p.first_detected > recent_cutoff]
            insights["recent_patterns"] = [
                {"pattern_id": p.pattern_id, "type": p.pattern_type.value, "description": p.description, "detected_at": p.first_detected.isoformat()} for p in recent_patterns
            ]

            return insights

        except Exception as e:
            logger.error(f"Error getting pattern insights: {e}")
            return {"error": str(e)}

    def _tracking_loop(self):
        """Main tracking loop for continuous context history collection."""
        logger.info("Context history tracking loop started")

        while not self.stop_tracking.is_set():
            try:
                # Pattern detection runs less frequently than snapshot collection
                if not self.last_pattern_detection or (datetime.now() - self.last_pattern_detection).total_seconds() > 300:  # Every 5 minutes
                    self.detect_patterns()

                # Update prediction accuracy
                self._update_prediction_accuracy()

                # Periodic cleanup
                if self.snapshots_captured % 100 == 0:
                    self._cleanup_old_predictions()

                # Save history periodically
                if self.enable_persistence and self.snapshots_captured % 50 == 0:
                    self._save_history()

            except Exception as e:
                logger.error(f"Error in tracking loop: {e}")

            # Wait for next cycle
            self.stop_tracking.wait(self.tracking_interval)

        logger.info("Context history tracking loop stopped")

    def _initialize_storage(self):
        """Initialize storage directories."""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            logger.debug(f"Initialized storage at {self.storage_path}")
        except Exception as e:
            logger.error(f"Error initializing storage: {e}")

    def _initialize_pattern_detectors(self):
        """Initialize pattern detection algorithms."""

        def detect_temporal_patterns(snapshots: List[ContextSnapshot]) -> List[ContextPattern]:
            """Detect time-based patterns."""
            patterns = []

            try:
                # Group snapshots by hour of day
                hourly_activity = defaultdict(list)
                for snapshot in snapshots:
                    hour = snapshot.timestamp.hour
                    hourly_activity[hour].append(snapshot.user_activity_level)

                # Find peak activity hours
                for hour, activities in hourly_activity.items():
                    if len(activities) >= 5:  # Need sufficient data
                        avg_activity = statistics.mean(activities)
                        if avg_activity > 0.7:  # High activity threshold
                            pattern = ContextPattern(
                                pattern_id=f"peak_hour_{hour}",
                                pattern_type=PatternType.TEMPORAL,
                                description=f"High user activity typically occurs at {hour:02d}:00",
                                frequency=self._calculate_frequency(len(activities), len(snapshots)),
                                confidence=min(0.9, avg_activity),
                                first_detected=datetime.now(),
                                last_seen=datetime.now(),
                                occurrence_count=len(activities),
                                typical_duration=timedelta(hours=1),
                                conditions={"hour": hour, "min_activity": 0.7},
                                associated_contexts=[f"hour_{hour}"],
                            )
                            patterns.append(pattern)

            except Exception as e:
                logger.error(f"Error detecting temporal patterns: {e}")

            return patterns

        def detect_usage_patterns(snapshots: List[ContextSnapshot]) -> List[ContextPattern]:
            """Detect application usage patterns."""
            patterns = []

            try:
                # Find frequently co-occurring applications
                app_pairs = defaultdict(int)
                for snapshot in snapshots:
                    apps = snapshot.active_applications
                    for i, app1 in enumerate(apps):
                        for app2 in apps[i + 1 :]:
                            pair = tuple(sorted([app1, app2]))
                            app_pairs[pair] += 1

                # Identify significant co-occurrences
                total_snapshots = len(snapshots)
                for (app1, app2), count in app_pairs.items():
                    if count >= total_snapshots * 0.1:  # At least 10% co-occurrence
                        pattern = ContextPattern(
                            pattern_id=f"cooccur_{app1}_{app2}",
                            pattern_type=PatternType.USAGE,
                            description=f"{app1} and {app2} are frequently used together",
                            frequency=self._calculate_frequency(count, total_snapshots),
                            confidence=min(0.9, count / total_snapshots * 2),
                            first_detected=datetime.now(),
                            last_seen=datetime.now(),
                            occurrence_count=count,
                            typical_duration=timedelta(minutes=30),
                            conditions={"apps": [app1, app2]},
                            associated_contexts=[app1, app2],
                        )
                        patterns.append(pattern)

            except Exception as e:
                logger.error(f"Error detecting usage patterns: {e}")

            return patterns

        def detect_resource_patterns(snapshots: List[ContextSnapshot]) -> List[ContextPattern]:
            """Detect resource consumption patterns."""
            patterns = []

            try:
                # Analyze CPU usage patterns
                cpu_values = [s.system_metrics.get("cpu_usage", 0) for s in snapshots]
                high_cpu_periods = sum(1 for cpu in cpu_values if cpu > 70)

                if high_cpu_periods >= len(snapshots) * 0.2:  # High CPU in 20% of time
                    pattern = ContextPattern(
                        pattern_id="high_cpu_usage",
                        pattern_type=PatternType.RESOURCE,
                        description="System frequently experiences high CPU usage",
                        frequency=self._calculate_frequency(high_cpu_periods, len(snapshots)),
                        confidence=min(0.9, high_cpu_periods / len(snapshots) * 2),
                        first_detected=datetime.now(),
                        last_seen=datetime.now(),
                        occurrence_count=high_cpu_periods,
                        typical_duration=timedelta(minutes=15),
                        conditions={"cpu_threshold": 70},
                        associated_contexts=["high_cpu"],
                    )
                    patterns.append(pattern)

            except Exception as e:
                logger.error(f"Error detecting resource patterns: {e}")

            return patterns

        # Register pattern detectors
        self.pattern_detectors[PatternType.TEMPORAL] = detect_temporal_patterns
        self.pattern_detectors[PatternType.USAGE] = detect_usage_patterns
        self.pattern_detectors[PatternType.RESOURCE] = detect_resource_patterns

    def _estimate_user_activity(self, context: Dict[str, Any]) -> float:
        """Estimate user activity level from context."""
        try:
            # Simple heuristic based on system metrics and applications
            system_metrics = context.get("system_metrics", {})
            applications = context.get("applications", {})

            activity_score = 0.0

            # CPU activity contributes to user activity
            cpu_usage = system_metrics.get("cpu_usage", 0)
            if cpu_usage > 20:
                activity_score += min(0.4, cpu_usage / 100.0)

            # Number of active applications
            app_count = len(applications)
            activity_score += min(0.3, app_count / 10.0)

            # Recent changes indicate activity
            recent_changes = context.get("recent_changes", [])
            if recent_changes:
                activity_score += min(0.3, len(recent_changes) / 5.0)

            return min(1.0, activity_score)

        except Exception as e:
            logger.error(f"Error estimating user activity: {e}")
            return 0.5

    def _calculate_frequency(self, occurrences: int, total: int) -> PatternFrequency:
        """Calculate pattern frequency based on occurrence ratio."""
        ratio = occurrences / max(total, 1)

        if ratio > 0.8:
            return PatternFrequency.DOMINANT
        elif ratio > 0.5:
            return PatternFrequency.COMMON
        elif ratio > 0.2:
            return PatternFrequency.FREQUENT
        elif ratio > 0.05:
            return PatternFrequency.OCCASIONAL
        else:
            return PatternFrequency.RARE

    def _predict_from_temporal_pattern(self, pattern: ContextPattern, target_time: datetime) -> Optional[Dict[str, Any]]:
        """Make prediction based on temporal pattern."""
        try:
            if pattern.pattern_type != PatternType.TEMPORAL:
                return None

            target_hour = target_time.hour
            pattern_hour = pattern.conditions.get("hour")

            if pattern_hour is not None and abs(target_hour - pattern_hour) <= 1:
                return {
                    "pattern_id": pattern.pattern_id,
                    "prediction_type": "temporal",
                    "description": f"Expecting {pattern.description} around {target_time.strftime('%H:%M')}",
                    "confidence": pattern.confidence * 0.8,  # Slightly reduce confidence for predictions
                    "expected_change": "increased_user_activity",
                    "target_time": target_time.isoformat(),
                }

            return None

        except Exception as e:
            logger.error(f"Error predicting from temporal pattern: {e}")
            return None

    def _predict_from_usage_pattern(self, pattern: ContextPattern, target_time: datetime) -> Optional[Dict[str, Any]]:
        """Make prediction based on usage pattern."""
        try:
            if pattern.pattern_type != PatternType.USAGE:
                return None

            # Simple prediction: if one app in the pattern is active, predict the other
            apps = pattern.conditions.get("apps", [])
            if len(apps) == 2:
                return {
                    "pattern_id": pattern.pattern_id,
                    "prediction_type": "usage",
                    "description": f"If {apps[0]} becomes active, expect {apps[1]} to be used as well",
                    "confidence": pattern.confidence * 0.7,
                    "expected_change": "application_co_occurrence",
                    "target_time": target_time.isoformat(),
                    "related_apps": apps,
                }

            return None

        except Exception as e:
            logger.error(f"Error predicting from usage pattern: {e}")
            return None

    def _update_prediction_accuracy(self):
        """Update prediction accuracy based on actual outcomes."""
        try:
            current_time = datetime.now()
            total_predictions = 0
            correct_predictions = 0

            # Check predictions that should have occurred by now
            for pattern_id, predictions in self.pattern_predictions.items():
                for pred_data in predictions:
                    target_time = pred_data["target_time"]
                    if current_time > target_time + timedelta(minutes=30):  # Grace period
                        total_predictions += 1

                        # Simple accuracy check - in practice this would be more sophisticated
                        if self._check_prediction_accuracy(pred_data):
                            correct_predictions += 1

            if total_predictions > 0:
                self.prediction_accuracy = correct_predictions / total_predictions

        except Exception as e:
            logger.error(f"Error updating prediction accuracy: {e}")

    def _check_prediction_accuracy(self, prediction_data: Dict[str, Any]) -> bool:
        """Check if a prediction was accurate."""
        try:
            # Simplified accuracy check
            # In practice, this would compare predicted changes with actual context changes
            prediction = prediction_data["prediction"]
            target_time = prediction_data["target_time"]

            # Find snapshots around the target time
            time_window = timedelta(minutes=30)
            relevant_snapshots = [s for s in self.context_history if abs((s.timestamp - target_time).total_seconds()) < time_window.total_seconds()]

            if not relevant_snapshots:
                return False

            # Check if predicted change occurred
            prediction_type = prediction.get("prediction_type")
            if prediction_type == "temporal":
                # Check if user activity increased as predicted
                avg_activity = statistics.mean([s.user_activity_level for s in relevant_snapshots])
                return avg_activity > 0.6

            elif prediction_type == "usage":
                # Check if predicted apps were used together
                related_apps = prediction.get("related_apps", [])
                for snapshot in relevant_snapshots:
                    if all(app in snapshot.active_applications for app in related_apps):
                        return True
                return False

            return False

        except Exception as e:
            logger.error(f"Error checking prediction accuracy: {e}")
            return False

    def _cleanup_old_predictions(self):
        """Clean up old prediction data."""
        try:
            cutoff_time = datetime.now() - timedelta(days=7)

            for pattern_id in list(self.pattern_predictions.keys()):
                predictions = self.pattern_predictions[pattern_id]
                # Keep only recent predictions
                recent_predictions = [p for p in predictions if p["made_at"] > cutoff_time]

                if recent_predictions:
                    self.pattern_predictions[pattern_id] = recent_predictions
                else:
                    del self.pattern_predictions[pattern_id]

        except Exception as e:
            logger.error(f"Error cleaning up old predictions: {e}")

    def _analyze_frequency_distribution(self, patterns: List[ContextPattern]) -> Dict[str, int]:
        """Analyze frequency distribution of patterns."""
        distribution = defaultdict(int)
        for pattern in patterns:
            distribution[pattern.frequency.value] += 1
        return dict(distribution)

    def _save_history(self):
        """Save context history to persistent storage."""
        try:
            if not self.enable_persistence:
                return

            history_file = os.path.join(self.storage_path, "context_history.pkl")
            patterns_file = os.path.join(self.storage_path, "detected_patterns.pkl")

            # Save history snapshots
            with open(history_file, "wb") as f:
                pickle.dump(list(self.context_history), f)

            # Save detected patterns
            with open(patterns_file, "wb") as f:
                pickle.dump(self.detected_patterns, f)

            logger.debug("Context history saved to persistent storage")

        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def _load_history(self):
        """Load context history from persistent storage."""
        try:
            if not self.enable_persistence:
                return

            history_file = os.path.join(self.storage_path, "context_history.pkl")
            patterns_file = os.path.join(self.storage_path, "detected_patterns.pkl")

            # Load history snapshots
            if os.path.exists(history_file):
                with open(history_file, "rb") as f:
                    loaded_history = pickle.load(f)
                    self.context_history.extend(loaded_history)
                    self.snapshots_captured = len(self.context_history)

            # Load detected patterns
            if os.path.exists(patterns_file):
                with open(patterns_file, "rb") as f:
                    self.detected_patterns = pickle.load(f)
                    self.patterns_detected = len(self.detected_patterns)

            logger.info(f"Loaded {len(self.context_history)} snapshots and {len(self.detected_patterns)} patterns")

        except Exception as e:
            logger.error(f"Error loading history: {e}")
