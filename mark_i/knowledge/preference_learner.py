"""
Advanced User Preference Learning System for MARK-I Knowledge Base.

This module provides sophisticated user preference tracking, learning, and adaptation
capabilities that go beyond basic preference storage to include behavioral analysis,
pattern recognition, and predictive preference modeling.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
import json
import os
import numpy as np

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context, ExecutionResult
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".knowledge.preference_learner")


class PreferenceType(Enum):
    """Types of user preferences that can be learned."""
    WORKFLOW = "workflow"
    INTERFACE = "interface"
    TIMING = "timing"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"


class PreferenceStrength(Enum):
    """Strength levels for learned preferences."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class PreferencePattern:
    """Represents a learned preference pattern."""
    pattern_id: str
    preference_type: PreferenceType
    pattern_data: Dict[str, Any]
    strength: PreferenceStrength
    confidence: float
    evidence_count: int
    success_correlation: float
    context_conditions: List[Dict[str, Any]]
    learned_from: List[str]  # Sources of learning
    created_at: datetime
    last_reinforced: datetime
    decay_rate: float = 0.05


@dataclass
class BehavioralInsight:
    """Insights derived from user behavior analysis."""
    insight_id: str
    category: str
    description: str
    supporting_evidence: List[Dict[str, Any]]
    confidence: float
    actionable_recommendations: List[str]
    discovered_at: datetime

class AdvancedPreferenceLearner(ProcessingComponent):
    """
    Advanced user preference learning system.
    
    Provides sophisticated behavioral analysis, pattern recognition, and predictive
    preference modeling to understand and adapt to user preferences over time.
    """
    
    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        
        # Configuration
        self.learning_rate = getattr(config, "learning_rate", 0.1)
        self.pattern_detection_threshold = getattr(config, "pattern_detection_threshold", 0.7)
        self.preference_decay_rate = getattr(config, "preference_decay_rate", 0.05)
        self.min_evidence_count = getattr(config, "min_evidence_count", 3)
        self.behavioral_analysis_window = getattr(config, "behavioral_analysis_window", 7)  # days
        
        # Data structures
        self.preference_patterns: Dict[str, PreferencePattern] = {}
        self.behavioral_insights: Dict[str, BehavioralInsight] = {}
        self.user_interactions: List[Dict[str, Any]] = []
        self.context_preference_map: Dict[str, List[str]] = defaultdict(list)
        
        # Threading
        self.learning_lock = threading.Lock()
        self.analysis_lock = threading.Lock()
        
        # Analysis tracking
        self.last_analysis_time = datetime.now()
        self.interaction_buffer: List[Dict[str, Any]] = []
        
        # Load existing data
        self._load_preference_data()
        
        logger.info("AdvancedPreferenceLearner initialized")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this preference learner."""
        return {
            "behavioral_analysis": True,
            "pattern_recognition": True,
            "predictive_modeling": True,
            "context_aware_preferences": True,
            "preference_strength_assessment": True,
            "automated_insight_generation": True,
            "preference_decay_modeling": True,
            "multi_source_learning": True
        }
    
    def learn_from_interaction(self, interaction: Dict[str, Any]) -> None:
        """Learn preferences from a user interaction."""
        try:
            with self.learning_lock:
                # Add timestamp if not present
                if "timestamp" not in interaction:
                    interaction["timestamp"] = datetime.now()
                
                # Store interaction
                self.user_interactions.append(interaction)
                self.interaction_buffer.append(interaction)
                
                # Limit interaction history
                if len(self.user_interactions) > 10000:
                    self.user_interactions = self.user_interactions[-10000:]
                
                # Extract preference signals
                self._extract_preference_signals(interaction)
                
                # Trigger analysis if buffer is full
                if len(self.interaction_buffer) >= 50:
                    self._analyze_interaction_batch()
                    self.interaction_buffer.clear()
                
                logger.debug("Learned from user interaction")
                
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")
    
    def _extract_preference_signals(self, interaction: Dict[str, Any]):
        """Extract preference signals from an interaction."""
        try:
            # Extract workflow preferences
            if "workflow_choice" in interaction:
                self._update_workflow_preference(interaction)
            
            # Extract interface preferences
            if "interface_action" in interaction:
                self._update_interface_preference(interaction)
            
            # Extract timing preferences
            if "timing_data" in interaction:
                self._update_timing_preference(interaction)
            
            # Extract quality preferences
            if "quality_feedback" in interaction:
                self._update_quality_preference(interaction)
            
        except Exception as e:
            logger.error(f"Error extracting preference signals: {e}")
    
    def _update_workflow_preference(self, interaction: Dict[str, Any]):
        """Update workflow preferences based on interaction."""
        workflow_choice = interaction.get("workflow_choice", {})
        context = interaction.get("context", {})
        success = interaction.get("success", False)
        
        pattern_id = f"workflow_{hash(str(workflow_choice))}"
        
        if pattern_id in self.preference_patterns:
            pattern = self.preference_patterns[pattern_id]
            pattern.evidence_count += 1
            pattern.last_reinforced = datetime.now()
            
            # Update success correlation
            if success:
                pattern.success_correlation = (pattern.success_correlation * 0.9 + 1.0 * 0.1)
            else:
                pattern.success_correlation = (pattern.success_correlation * 0.9 + 0.0 * 0.1)
            
            # Update confidence
            pattern.confidence = min(1.0, pattern.confidence + self.learning_rate)
            
        else:
            # Create new workflow preference pattern
            self.preference_patterns[pattern_id] = PreferencePattern(
                pattern_id=pattern_id,
                preference_type=PreferenceType.WORKFLOW,
                pattern_data=workflow_choice,
                strength=PreferenceStrength.WEAK,
                confidence=0.5,
                evidence_count=1,
                success_correlation=1.0 if success else 0.0,
                context_conditions=[context],
                learned_from=["user_interaction"],
                created_at=datetime.now(),
                last_reinforced=datetime.now()
            )
    
    def _update_interface_preference(self, interaction: Dict[str, Any]):
        """Update interface preferences based on interaction."""
        interface_action = interaction.get("interface_action", {})
        context = interaction.get("context", {})
        
        # Learn preferred interface elements
        if "preferred_element" in interface_action:
            element = interface_action["preferred_element"]
            pattern_id = f"interface_{hash(element)}"
            
            if pattern_id not in self.preference_patterns:
                self.preference_patterns[pattern_id] = PreferencePattern(
                    pattern_id=pattern_id,
                    preference_type=PreferenceType.INTERFACE,
                    pattern_data={"preferred_element": element},
                    strength=PreferenceStrength.WEAK,
                    confidence=0.5,
                    evidence_count=1,
                    success_correlation=0.8,
                    context_conditions=[context],
                    learned_from=["interface_interaction"],
                    created_at=datetime.now(),
                    last_reinforced=datetime.now()
                )
            else:
                pattern = self.preference_patterns[pattern_id]
                pattern.evidence_count += 1
                pattern.confidence = min(1.0, pattern.confidence + self.learning_rate)
                pattern.last_reinforced = datetime.now()
    
    def _update_timing_preference(self, interaction: Dict[str, Any]):
        """Update timing preferences based on interaction."""
        timing_data = interaction.get("timing_data", {})
        
        # Learn preferred work hours
        if "hour" in timing_data:
            hour = timing_data["hour"]
            pattern_id = f"timing_hour_{hour}"
            
            if pattern_id not in self.preference_patterns:
                self.preference_patterns[pattern_id] = PreferencePattern(
                    pattern_id=pattern_id,
                    preference_type=PreferenceType.TIMING,
                    pattern_data={"preferred_hour": hour},
                    strength=PreferenceStrength.WEAK,
                    confidence=0.3,
                    evidence_count=1,
                    success_correlation=0.7,
                    context_conditions=[],
                    learned_from=["timing_analysis"],
                    created_at=datetime.now(),
                    last_reinforced=datetime.now()
                )
            else:
                pattern = self.preference_patterns[pattern_id]
                pattern.evidence_count += 1
                pattern.confidence = min(1.0, pattern.confidence + 0.05)
                pattern.last_reinforced = datetime.now()
    
    def _update_quality_preference(self, interaction: Dict[str, Any]):
        """Update quality preferences based on feedback."""
        quality_feedback = interaction.get("quality_feedback", {})
        
        for aspect, rating in quality_feedback.items():
            pattern_id = f"quality_{aspect}"
            
            if pattern_id not in self.preference_patterns:
                self.preference_patterns[pattern_id] = PreferencePattern(
                    pattern_id=pattern_id,
                    preference_type=PreferenceType.QUALITY,
                    pattern_data={"quality_aspect": aspect, "preferred_level": rating},
                    strength=PreferenceStrength.MODERATE,
                    confidence=0.6,
                    evidence_count=1,
                    success_correlation=rating / 5.0,  # Assuming 1-5 scale
                    context_conditions=[],
                    learned_from=["quality_feedback"],
                    created_at=datetime.now(),
                    last_reinforced=datetime.now()
                )
            else:
                pattern = self.preference_patterns[pattern_id]
                pattern.evidence_count += 1
                # Update preferred level with exponential moving average
                current_level = pattern.pattern_data.get("preferred_level", 3.0)
                pattern.pattern_data["preferred_level"] = current_level * 0.8 + rating * 0.2
                pattern.confidence = min(1.0, pattern.confidence + self.learning_rate)
                pattern.last_reinforced = datetime.now()
    
    def _analyze_interaction_batch(self):
        """Analyze a batch of interactions for patterns."""
        try:
            with self.analysis_lock:
                if not self.interaction_buffer:
                    return
                
                # Analyze workflow patterns
                self._analyze_workflow_patterns()
                
                # Analyze temporal patterns
                self._analyze_temporal_patterns()
                
                # Generate behavioral insights
                self._generate_behavioral_insights()
                
                # Update preference strengths
                self._update_preference_strengths()
                
                logger.debug(f"Analyzed batch of {len(self.interaction_buffer)} interactions")
                
        except Exception as e:
            logger.error(f"Error analyzing interaction batch: {e}")
    
    def _analyze_workflow_patterns(self):
        """Analyze workflow patterns in recent interactions."""
        workflow_sequences = []
        
        for interaction in self.interaction_buffer:
            if "workflow_sequence" in interaction:
                workflow_sequences.append(interaction["workflow_sequence"])
        
        if len(workflow_sequences) >= 3:
            # Find common sequences
            sequence_counter = Counter(tuple(seq) for seq in workflow_sequences)
            
            for sequence, count in sequence_counter.items():
                if count >= 2:  # Pattern appears at least twice
                    pattern_id = f"workflow_sequence_{hash(sequence)}"
                    
                    if pattern_id not in self.preference_patterns:
                        self.preference_patterns[pattern_id] = PreferencePattern(
                            pattern_id=pattern_id,
                            preference_type=PreferenceType.WORKFLOW,
                            pattern_data={"preferred_sequence": list(sequence)},
                            strength=PreferenceStrength.MODERATE,
                            confidence=0.6,
                            evidence_count=count,
                            success_correlation=0.8,
                            context_conditions=[],
                            learned_from=["workflow_analysis"],
                            created_at=datetime.now(),
                            last_reinforced=datetime.now()
                        )
    
    def _analyze_temporal_patterns(self):
        """Analyze temporal patterns in user behavior."""
        hourly_activity = defaultdict(int)
        daily_activity = defaultdict(int)
        
        for interaction in self.interaction_buffer:
            timestamp = interaction.get("timestamp", datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            hourly_activity[timestamp.hour] += 1
            daily_activity[timestamp.weekday()] += 1
        
        # Find peak activity hours
        if hourly_activity:
            peak_hour = max(hourly_activity, key=hourly_activity.get)
            if hourly_activity[peak_hour] >= 3:
                pattern_id = f"peak_activity_hour_{peak_hour}"
                
                if pattern_id not in self.preference_patterns:
                    self.preference_patterns[pattern_id] = PreferencePattern(
                        pattern_id=pattern_id,
                        preference_type=PreferenceType.TIMING,
                        pattern_data={"peak_hour": peak_hour, "activity_count": hourly_activity[peak_hour]},
                        strength=PreferenceStrength.MODERATE,
                        confidence=0.7,
                        evidence_count=hourly_activity[peak_hour],
                        success_correlation=0.8,
                        context_conditions=[],
                        learned_from=["temporal_analysis"],
                        created_at=datetime.now(),
                        last_reinforced=datetime.now()
                    )
    
    def _generate_behavioral_insights(self):
        """Generate insights from behavioral patterns."""
        try:
            # Analyze preference consistency
            consistent_patterns = []
            for pattern in self.preference_patterns.values():
                if pattern.evidence_count >= self.min_evidence_count and pattern.confidence > 0.7:
                    consistent_patterns.append(pattern)
            
            if len(consistent_patterns) >= 3:
                insight_id = f"consistency_insight_{int(time.time())}"
                
                self.behavioral_insights[insight_id] = BehavioralInsight(
                    insight_id=insight_id,
                    category="consistency",
                    description=f"User shows consistent preferences across {len(consistent_patterns)} different areas",
                    supporting_evidence=[{"pattern_id": p.pattern_id, "confidence": p.confidence} for p in consistent_patterns],
                    confidence=0.8,
                    actionable_recommendations=[
                        "Prioritize automation in areas with consistent preferences",
                        "Use established patterns to predict user needs",
                        "Reduce confirmation requests for high-confidence preferences"
                    ],
                    discovered_at=datetime.now()
                )
            
            # Analyze efficiency patterns
            efficiency_patterns = [p for p in self.preference_patterns.values() 
                                 if p.preference_type == PreferenceType.EFFICIENCY and p.success_correlation > 0.8]
            
            if efficiency_patterns:
                insight_id = f"efficiency_insight_{int(time.time())}"
                
                self.behavioral_insights[insight_id] = BehavioralInsight(
                    insight_id=insight_id,
                    category="efficiency",
                    description="User demonstrates strong efficiency-focused behavior patterns",
                    supporting_evidence=[{"pattern_id": p.pattern_id, "success_rate": p.success_correlation} for p in efficiency_patterns],
                    confidence=0.9,
                    actionable_recommendations=[
                        "Prioritize speed and efficiency in automation suggestions",
                        "Offer keyboard shortcuts and quick actions",
                        "Minimize confirmation dialogs for routine tasks"
                    ],
                    discovered_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error generating behavioral insights: {e}")
    
    def _update_preference_strengths(self):
        """Update preference strengths based on evidence and success."""
        for pattern in self.preference_patterns.values():
            # Calculate strength based on evidence count, confidence, and success correlation
            strength_score = (
                min(pattern.evidence_count / 10.0, 1.0) * 0.4 +
                pattern.confidence * 0.4 +
                pattern.success_correlation * 0.2
            )
            
            if strength_score >= 0.8:
                pattern.strength = PreferenceStrength.VERY_STRONG
            elif strength_score >= 0.6:
                pattern.strength = PreferenceStrength.STRONG
            elif strength_score >= 0.4:
                pattern.strength = PreferenceStrength.MODERATE
            else:
                pattern.strength = PreferenceStrength.WEAK
    
    def get_preferences_for_context(self, context: Context) -> Dict[str, Any]:
        """Get relevant preferences for a given context."""
        try:
            relevant_preferences = {}
            
            # Create context signature
            context_sig = {
                "active_applications": context.active_applications or [],
                "user_activity": context.user_activity or "",
                "hour": context.timestamp.hour if context.timestamp else datetime.now().hour,
                "weekday": context.timestamp.weekday() if context.timestamp else datetime.now().weekday()
            }
            
            # Find matching preferences
            for pattern in self.preference_patterns.values():
                if pattern.confidence > 0.6:  # Only consider confident preferences
                    # Check context conditions
                    context_match = self._check_context_match(pattern, context_sig)
                    
                    if context_match:
                        pref_type = pattern.preference_type.value
                        if pref_type not in relevant_preferences:
                            relevant_preferences[pref_type] = []
                        
                        relevant_preferences[pref_type].append({
                            "pattern_data": pattern.pattern_data,
                            "strength": pattern.strength.value,
                            "confidence": pattern.confidence,
                            "success_correlation": pattern.success_correlation
                        })
            
            # Sort by strength and confidence
            for pref_type in relevant_preferences:
                relevant_preferences[pref_type].sort(
                    key=lambda x: (x["strength"], x["confidence"]), 
                    reverse=True
                )
            
            return relevant_preferences
            
        except Exception as e:
            logger.error(f"Error getting preferences for context: {e}")
            return {}
    
    def _check_context_match(self, pattern: PreferencePattern, context_sig: Dict[str, Any]) -> bool:
        """Check if a pattern matches the current context."""
        if not pattern.context_conditions:
            return True  # No specific context requirements
        
        for condition in pattern.context_conditions:
            # Check application match
            if "active_applications" in condition:
                pattern_apps = set(condition["active_applications"])
                current_apps = set(context_sig["active_applications"])
                if pattern_apps.intersection(current_apps):
                    return True
            
            # Check activity match
            if "user_activity" in condition:
                if condition["user_activity"] == context_sig["user_activity"]:
                    return True
            
            # Check time match
            if "hour" in condition:
                if abs(condition["hour"] - context_sig["hour"]) <= 1:
                    return True
        
        return False
    
    def get_behavioral_insights(self) -> List[Dict[str, Any]]:
        """Get current behavioral insights."""
        try:
            insights = []
            for insight in self.behavioral_insights.values():
                insights.append({
                    "category": insight.category,
                    "description": insight.description,
                    "confidence": insight.confidence,
                    "recommendations": insight.actionable_recommendations,
                    "discovered_at": insight.discovered_at.isoformat()
                })
            
            # Sort by confidence
            insights.sort(key=lambda x: x["confidence"], reverse=True)
            return insights
            
        except Exception as e:
            logger.error(f"Error getting behavioral insights: {e}")
            return []
    
    def predict_user_preference(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Predict user preference for a given scenario."""
        try:
            predictions = {}
            
            # Find relevant patterns
            relevant_patterns = []
            for pattern in self.preference_patterns.values():
                if pattern.confidence > 0.5:
                    # Simple relevance scoring based on scenario overlap
                    relevance_score = self._calculate_scenario_relevance(pattern, scenario)
                    if relevance_score > 0.3:
                        relevant_patterns.append((pattern, relevance_score))
            
            # Sort by relevance
            relevant_patterns.sort(key=lambda x: x[1], reverse=True)
            
            # Generate predictions
            for pattern, relevance in relevant_patterns[:5]:  # Top 5 most relevant
                pref_type = pattern.preference_type.value
                
                prediction = {
                    "preference_data": pattern.pattern_data,
                    "confidence": pattern.confidence * relevance,
                    "strength": pattern.strength.value,
                    "success_probability": pattern.success_correlation,
                    "evidence_count": pattern.evidence_count
                }
                
                if pref_type not in predictions:
                    predictions[pref_type] = []
                predictions[pref_type].append(prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting user preference: {e}")
            return {}
    
    def _calculate_scenario_relevance(self, pattern: PreferencePattern, scenario: Dict[str, Any]) -> float:
        """Calculate how relevant a pattern is to a given scenario."""
        relevance = 0.0
        
        # Check data overlap
        pattern_data = pattern.pattern_data
        for key, value in scenario.items():
            if key in pattern_data:
                if pattern_data[key] == value:
                    relevance += 0.3
                elif str(value).lower() in str(pattern_data[key]).lower():
                    relevance += 0.1
        
        # Boost relevance for strong patterns
        if pattern.strength == PreferenceStrength.VERY_STRONG:
            relevance *= 1.5
        elif pattern.strength == PreferenceStrength.STRONG:
            relevance *= 1.2
        
        return min(1.0, relevance)
    
    def decay_preferences(self):
        """Apply decay to preferences that haven't been reinforced recently."""
        try:
            current_time = datetime.now()
            
            for pattern in list(self.preference_patterns.values()):
                days_since_reinforcement = (current_time - pattern.last_reinforced).days
                
                if days_since_reinforcement > 30:  # Apply decay after 30 days
                    decay_amount = pattern.decay_rate * (days_since_reinforcement - 30)
                    pattern.confidence = max(0.1, pattern.confidence - decay_amount)
                    
                    # Remove very weak patterns
                    if pattern.confidence < 0.2 and pattern.evidence_count < 3:
                        del self.preference_patterns[pattern.pattern_id]
                        logger.debug(f"Removed decayed preference pattern: {pattern.pattern_id}")
            
        except Exception as e:
            logger.error(f"Error applying preference decay: {e}")
    
    def _load_preference_data(self):
        """Load preference data from storage."""
        try:
            data_file = "preference_learner_data.json"
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                # Load preference patterns
                for pattern_data in data.get("preference_patterns", []):
                    pattern = PreferencePattern(
                        pattern_id=pattern_data["pattern_id"],
                        preference_type=PreferenceType(pattern_data["preference_type"]),
                        pattern_data=pattern_data["pattern_data"],
                        strength=PreferenceStrength(pattern_data["strength"]),
                        confidence=pattern_data["confidence"],
                        evidence_count=pattern_data["evidence_count"],
                        success_correlation=pattern_data["success_correlation"],
                        context_conditions=pattern_data["context_conditions"],
                        learned_from=pattern_data["learned_from"],
                        created_at=datetime.fromisoformat(pattern_data["created_at"]),
                        last_reinforced=datetime.fromisoformat(pattern_data["last_reinforced"]),
                        decay_rate=pattern_data.get("decay_rate", 0.05)
                    )
                    self.preference_patterns[pattern.pattern_id] = pattern
                
                # Load behavioral insights
                for insight_data in data.get("behavioral_insights", []):
                    insight = BehavioralInsight(
                        insight_id=insight_data["insight_id"],
                        category=insight_data["category"],
                        description=insight_data["description"],
                        supporting_evidence=insight_data["supporting_evidence"],
                        confidence=insight_data["confidence"],
                        actionable_recommendations=insight_data["actionable_recommendations"],
                        discovered_at=datetime.fromisoformat(insight_data["discovered_at"])
                    )
                    self.behavioral_insights[insight.insight_id] = insight
                
                logger.info(f"Loaded {len(self.preference_patterns)} preference patterns and {len(self.behavioral_insights)} insights")
        
        except Exception as e:
            logger.warning(f"Could not load preference data: {e}")
    
    def save_preference_data(self):
        """Save preference data to storage."""
        try:
            data = {
                "preference_patterns": [],
                "behavioral_insights": []
            }
            
            # Save preference patterns
            for pattern in self.preference_patterns.values():
                pattern_data = {
                    "pattern_id": pattern.pattern_id,
                    "preference_type": pattern.preference_type.value,
                    "pattern_data": pattern.pattern_data,
                    "strength": pattern.strength.value,
                    "confidence": pattern.confidence,
                    "evidence_count": pattern.evidence_count,
                    "success_correlation": pattern.success_correlation,
                    "context_conditions": pattern.context_conditions,
                    "learned_from": pattern.learned_from,
                    "created_at": pattern.created_at.isoformat(),
                    "last_reinforced": pattern.last_reinforced.isoformat(),
                    "decay_rate": pattern.decay_rate
                }
                data["preference_patterns"].append(pattern_data)
            
            # Save behavioral insights
            for insight in self.behavioral_insights.values():
                insight_data = {
                    "insight_id": insight.insight_id,
                    "category": insight.category,
                    "description": insight.description,
                    "supporting_evidence": insight.supporting_evidence,
                    "confidence": insight.confidence,
                    "actionable_recommendations": insight.actionable_recommendations,
                    "discovered_at": insight.discovered_at.isoformat()
                }
                data["behavioral_insights"].append(insight_data)
            
            with open("preference_learner_data.json", 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Preference data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving preference data: {e}")
    
    def process(self, input_data: Any) -> ExecutionResult:
        """Process input through the preference learner."""
        try:
            if isinstance(input_data, dict):
                command = input_data.get("command")
                
                if command == "learn_interaction":
                    interaction = input_data.get("interaction", {})
                    self.learn_from_interaction(interaction)
                    return ExecutionResult(
                        success=True,
                        message="Interaction learned successfully",
                        data={}
                    )
                
                elif command == "get_preferences":
                    context = input_data.get("context")
                    if context and hasattr(context, 'timestamp'):
                        preferences = self.get_preferences_for_context(context)
                        return ExecutionResult(
                            success=True,
                            message="Preferences retrieved successfully",
                            data={"preferences": preferences}
                        )
                
                elif command == "get_insights":
                    insights = self.get_behavioral_insights()
                    return ExecutionResult(
                        success=True,
                        message="Behavioral insights retrieved",
                        data={"insights": insights}
                    )
                
                elif command == "predict_preference":
                    scenario = input_data.get("scenario", {})
                    predictions = self.predict_user_preference(scenario)
                    return ExecutionResult(
                        success=True,
                        message="Preference predictions generated",
                        data={"predictions": predictions}
                    )
                
                elif command == "decay_preferences":
                    self.decay_preferences()
                    return ExecutionResult(
                        success=True,
                        message="Preference decay applied",
                        data={}
                    )
            
            return ExecutionResult(
                success=False,
                message="Invalid input for AdvancedPreferenceLearner",
                data={}
            )
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return ExecutionResult(
                success=False,
                message=f"Processing error: {str(e)}",
                data={}
            )
    
    def cleanup(self):
        """Clean up resources and save data."""
        self.save_preference_data()
        logger.info("AdvancedPreferenceLearner cleanup completed")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass