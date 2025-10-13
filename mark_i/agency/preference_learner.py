"""
User Preference Learner for MARK-I Agency Core.

This module provides adaptive user preference learning capabilities,
analyzing user interactions and feedback to continuously improve
the system's understanding of user preferences and behavior patterns.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json

from mark_i.core.base_component import BaseComponent
from mark_i.core.interfaces import Context
from mark_i.core.architecture_config import ComponentConfig
import logging

logger = logging.getLogger("mark_i.agency.preference_learner")


class InteractionType(Enum):
    """Types of user interactions."""
    ACCEPT = "accept"
    DECLINE = "decline"
    MODIFY = "modify"
    IGNORE = "ignore"
    FEEDBACK = "feedback"
    EXPLICIT_PREFERENCE = "explicit_preference"


class PreferenceCategory(Enum):
    """Categories of user preferences."""
    AUTOMATION_LEVEL = "automation_level"
    COMMUNICATION_STYLE = "communication_style"
    INTERRUPTION_TOLERANCE = "interruption_tolerance"
    TASK_PRIORITIES = "task_priorities"
    WORKFLOW_PREFERENCES = "workflow_preferences"
    TIMING_PREFERENCES = "timing_preferences"
    CONTEXT_PREFERENCES = "context_preferences"


@dataclass
class UserInteraction:
    """Represents a user interaction for learning."""
    id: str
    interaction_type: InteractionType
    context: Dict[str, Any]
    suggestion_data: Dict[str, Any]
    user_response: Dict[str, Any]
    timestamp: datetime
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PreferencePattern:
    """Represents a learned preference pattern."""
    id: str
    category: PreferenceCategory
    pattern_description: str
    context_conditions: List[str]
    preference_value: Any
    confidence: float
    evidence_count: int
    last_updated: datetime
    success_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdaptationRule:
    """Represents a rule for adapting behavior based on preferences."""
    id: str
    name: str
    condition: str
    action: str
    preference_category: PreferenceCategory
    priority: int
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PreferenceLearner(BaseComponent):
    """
    User preference learning component for adaptive behavior.
    
    Analyzes user interactions, feedback, and behavior patterns to
    continuously learn and adapt to user preferences.
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize the Preference Learner."""
        super().__init__("preference_learner", config)
        
        # Interaction tracking
        self.interactions: Dict[str, UserInteraction] = {}
        self.interaction_counter = 0
        
        # Preference patterns
        self.preference_patterns: Dict[str, PreferencePattern] = {}
        self.pattern_counter = 0
        
        # Adaptation rules
        self.adaptation_rules: Dict[str, AdaptationRule] = {}
        self.rule_counter = 0
        
        # Current user preferences (learned and explicit)
        self.learned_preferences: Dict[str, Any] = {
            'automation_level': 0.5,
            'interruption_tolerance': 0.5,
            'communication_style': 'balanced',
            'preferred_timing': {},
            'task_priorities': {},
            'context_preferences': {},
            'workflow_preferences': {}
        }
        
        # Learning parameters
        self.learning_rate = 0.1
        self.confidence_threshold = 0.7
        self.min_evidence_count = 3
        
        # Temporal patterns
        self.temporal_patterns: Dict[str, List[Dict[str, Any]]] = {
            'hourly': [],
            'daily': [],
            'weekly': []
        }
        
    def _initialize_component(self) -> bool:
        """Initialize the Preference Learner component."""
        try:
            # Initialize default adaptation rules
            self._initialize_default_rules()
            
            # Load any persisted preferences
            self._load_persisted_preferences()
            
            self.logger.info("Preference Learner initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Preference Learner: {e}")
            return False
    
    def record_interaction(self, 
                          interaction_type: InteractionType,
                          context: Context,
                          suggestion_data: Dict[str, Any],
                          user_response: Dict[str, Any],
                          confidence: float = 1.0) -> str:
        """Record a user interaction for learning."""
        try:
            interaction = UserInteraction(
                id=f"interaction_{self.interaction_counter}",
                interaction_type=interaction_type,
                context=asdict(context),
                suggestion_data=suggestion_data,
                user_response=user_response,
                timestamp=datetime.now(),
                confidence=confidence
            )
            
            self.interaction_counter += 1
            self.interactions[interaction.id] = interaction
            
            # Immediately learn from this interaction
            self._learn_from_interaction(interaction)
            
            self.logger.debug(f"Recorded interaction: {interaction_type.value}")
            
            # Notify observers
            self._notify_observers({
                'type': 'interaction_recorded',
                'interaction': interaction.to_dict(),
                'timestamp': datetime.now().isoformat()
            })
            
            return interaction.id
            
        except Exception as e:
            self.logger.error(f"Failed to record interaction: {e}")
            return ""
    
    def learn_explicit_preference(self, 
                                category: PreferenceCategory,
                                preference_value: Any,
                                context: Optional[Context] = None) -> None:
        """Learn from explicit user preference statements."""
        try:
            # Create a high-confidence preference pattern
            pattern = PreferencePattern(
                id=f"pattern_{self.pattern_counter}",
                category=category,
                pattern_description=f"Explicit preference: {category.value} = {preference_value}",
                context_conditions=self._extract_context_conditions(context) if context else [],
                preference_value=preference_value,
                confidence=1.0,  # Explicit preferences have maximum confidence
                evidence_count=1,
                last_updated=datetime.now(),
                success_rate=1.0
            )
            
            self.pattern_counter += 1
            self.preference_patterns[pattern.id] = pattern
            
            # Update learned preferences immediately
            self._update_learned_preferences(pattern)
            
            self.logger.info(f"Learned explicit preference: {category.value} = {preference_value}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn explicit preference: {e}")
    
    def adapt_behavior(self, context: Context, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt behavior based on learned preferences."""
        try:
            adapted_suggestion = suggestion.copy()
            
            # Apply adaptation rules
            for rule in self.adaptation_rules.values():
                if rule.active and self._evaluate_rule_condition(rule, context, suggestion):
                    adapted_suggestion = self._apply_rule_action(rule, adapted_suggestion, context)
            
            # Apply preference-based adaptations
            adapted_suggestion = self._apply_preference_adaptations(adapted_suggestion, context)
            
            self.logger.debug("Applied behavioral adaptations to suggestion")
            
            return adapted_suggestion
            
        except Exception as e:
            self.logger.error(f"Failed to adapt behavior: {e}")
            return suggestion
    
    def get_preference_insights(self) -> Dict[str, Any]:
        """Get insights about learned user preferences."""
        try:
            insights = {
                'preference_summary': self._summarize_preferences(),
                'confidence_levels': self._calculate_confidence_levels(),
                'learning_progress': self._assess_learning_progress(),
                'adaptation_effectiveness': self._measure_adaptation_effectiveness(),
                'temporal_patterns': self._analyze_temporal_patterns(),
                'recommendations': self._generate_preference_recommendations()
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate preference insights: {e}")
            return {}
    
    def update_preferences_from_feedback(self, feedback: Dict[str, Any]) -> None:
        """Update preferences based on user feedback."""
        try:
            feedback_type = feedback.get('type', 'general')
            feedback_data = feedback.get('data', {})
            
            if feedback_type == 'automation_level':
                self._update_automation_preference(feedback_data)
            elif feedback_type == 'communication_style':
                self._update_communication_preference(feedback_data)
            elif feedback_type == 'timing':
                self._update_timing_preference(feedback_data)
            elif feedback_type == 'task_priority':
                self._update_task_priority_preference(feedback_data)
            
            self.logger.info(f"Updated preferences from {feedback_type} feedback")
            
        except Exception as e:
            self.logger.error(f"Failed to update preferences from feedback: {e}")
    
    def predict_user_response(self, suggestion: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Predict likely user response to a suggestion."""
        try:
            # Find similar past interactions
            similar_interactions = self._find_similar_interactions(suggestion, context)
            
            if not similar_interactions:
                return {
                    'predicted_response': 'unknown',
                    'confidence': 0.5,
                    'reasoning': 'No similar interactions found'
                }
            
            # Analyze response patterns
            response_counts = {}
            total_confidence = 0.0
            
            for interaction in similar_interactions:
                response_type = interaction.user_response.get('type', 'unknown')
                response_counts[response_type] = response_counts.get(response_type, 0) + 1
                total_confidence += interaction.confidence
            
            # Predict most likely response
            most_likely_response = max(response_counts, key=response_counts.get)
            prediction_confidence = (response_counts[most_likely_response] / len(similar_interactions)) * (total_confidence / len(similar_interactions))
            
            return {
                'predicted_response': most_likely_response,
                'confidence': prediction_confidence,
                'reasoning': f"Based on {len(similar_interactions)} similar interactions",
                'response_distribution': response_counts
            }
            
        except Exception as e:
            self.logger.error(f"Failed to predict user response: {e}")
            return {
                'predicted_response': 'unknown',
                'confidence': 0.5,
                'reasoning': 'Prediction failed'
            }
    
    # Private helper methods
    
    def _learn_from_interaction(self, interaction: UserInteraction) -> None:
        """Learn preferences from a single interaction."""
        try:
            # Extract preference signals from the interaction
            preference_signals = self._extract_preference_signals(interaction)
            
            for signal in preference_signals:
                self._update_or_create_pattern(signal, interaction)
            
            # Update temporal patterns
            self._update_temporal_patterns(interaction)
            
        except Exception as e:
            self.logger.error(f"Failed to learn from interaction: {e}")
    
    def _extract_preference_signals(self, interaction: UserInteraction) -> List[Dict[str, Any]]:
        """Extract preference signals from an interaction."""
        signals = []
        
        try:
            response_type = interaction.user_response.get('type', 'unknown')
            
            # Automation level signals
            if interaction.interaction_type in [InteractionType.ACCEPT, InteractionType.DECLINE]:
                automation_signal = {
                    'category': PreferenceCategory.AUTOMATION_LEVEL,
                    'value': 1.0 if interaction.interaction_type == InteractionType.ACCEPT else 0.0,
                    'context': interaction.context,
                    'confidence': interaction.confidence
                }
                signals.append(automation_signal)
            
            # Timing preference signals
            hour = interaction.timestamp.hour
            if response_type in ['accept', 'decline']:
                timing_signal = {
                    'category': PreferenceCategory.TIMING_PREFERENCES,
                    'value': {'hour': hour, 'response': response_type},
                    'context': interaction.context,
                    'confidence': interaction.confidence
                }
                signals.append(timing_signal)
            
            # Task priority signals
            suggestion_type = interaction.suggestion_data.get('type', 'unknown')
            if response_type in ['accept', 'decline']:
                priority_signal = {
                    'category': PreferenceCategory.TASK_PRIORITIES,
                    'value': {suggestion_type: 1.0 if response_type == 'accept' else 0.0},
                    'context': interaction.context,
                    'confidence': interaction.confidence
                }
                signals.append(priority_signal)
            
            # Context preference signals
            if interaction.context.get('active_applications'):
                context_signal = {
                    'category': PreferenceCategory.CONTEXT_PREFERENCES,
                    'value': {
                        'applications': interaction.context['active_applications'],
                        'response': response_type
                    },
                    'context': interaction.context,
                    'confidence': interaction.confidence
                }
                signals.append(context_signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Failed to extract preference signals: {e}")
            return []
    
    def _update_or_create_pattern(self, signal: Dict[str, Any], interaction: UserInteraction) -> None:
        """Update existing pattern or create new one from signal."""
        try:
            category = signal['category']
            
            # Look for existing similar pattern
            existing_pattern = self._find_similar_pattern(signal)
            
            if existing_pattern:
                # Update existing pattern
                self._update_pattern(existing_pattern, signal, interaction)
            else:
                # Create new pattern
                self._create_new_pattern(signal, interaction)
                
        except Exception as e:
            self.logger.error(f"Failed to update or create pattern: {e}")
    
    def _find_similar_pattern(self, signal: Dict[str, Any]) -> Optional[PreferencePattern]:
        """Find existing pattern similar to the signal."""
        try:
            category = signal['category']
            
            for pattern in self.preference_patterns.values():
                if pattern.category == category:
                    # Check if contexts are similar
                    if self._contexts_similar(pattern.context_conditions, signal.get('context', {})):
                        return pattern
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find similar pattern: {e}")
            return None
    
    def _contexts_similar(self, pattern_conditions: List[str], signal_context: Dict[str, Any]) -> bool:
        """Check if contexts are similar enough to merge patterns."""
        try:
            # Simple similarity check - could be made more sophisticated
            signal_conditions = self._extract_context_conditions_from_dict(signal_context)
            
            if not pattern_conditions and not signal_conditions:
                return True
            
            if not pattern_conditions or not signal_conditions:
                return False
            
            # Check for overlap
            overlap = len(set(pattern_conditions) & set(signal_conditions))
            total = len(set(pattern_conditions) | set(signal_conditions))
            
            similarity = overlap / total if total > 0 else 0.0
            return similarity > 0.5  # 50% similarity threshold
            
        except Exception as e:
            self.logger.error(f"Failed to check context similarity: {e}")
            return False
    
    def _update_pattern(self, pattern: PreferencePattern, signal: Dict[str, Any], interaction: UserInteraction) -> None:
        """Update an existing preference pattern."""
        try:
            # Update evidence count
            pattern.evidence_count += 1
            
            # Update preference value (weighted average)
            if isinstance(pattern.preference_value, (int, float)) and isinstance(signal['value'], (int, float)):
                old_weight = pattern.evidence_count - 1
                new_weight = 1
                total_weight = old_weight + new_weight
                
                pattern.preference_value = (
                    (pattern.preference_value * old_weight + signal['value'] * new_weight) / total_weight
                )
            elif isinstance(pattern.preference_value, dict) and isinstance(signal['value'], dict):
                # Merge dictionaries
                for key, value in signal['value'].items():
                    if key in pattern.preference_value:
                        if isinstance(value, (int, float)):
                            old_val = pattern.preference_value[key]
                            pattern.preference_value[key] = (old_val + value) / 2
                    else:
                        pattern.preference_value[key] = value
            
            # Update confidence based on consistency
            pattern.confidence = min(pattern.confidence + self.learning_rate * signal['confidence'], 1.0)
            
            # Update timestamp
            pattern.last_updated = datetime.now()
            
            # Update learned preferences if confidence is high enough
            if pattern.confidence >= self.confidence_threshold:
                self._update_learned_preferences(pattern)
                
        except Exception as e:
            self.logger.error(f"Failed to update pattern: {e}")
    
    def _create_new_pattern(self, signal: Dict[str, Any], interaction: UserInteraction) -> None:
        """Create a new preference pattern."""
        try:
            pattern = PreferencePattern(
                id=f"pattern_{self.pattern_counter}",
                category=signal['category'],
                pattern_description=f"Learned from {interaction.interaction_type.value}",
                context_conditions=self._extract_context_conditions_from_dict(signal.get('context', {})),
                preference_value=signal['value'],
                confidence=signal['confidence'] * self.learning_rate,
                evidence_count=1,
                last_updated=datetime.now()
            )
            
            self.pattern_counter += 1
            self.preference_patterns[pattern.id] = pattern
            
            self.logger.debug(f"Created new preference pattern: {pattern.category.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to create new pattern: {e}")
    
    def _extract_context_conditions(self, context: Context) -> List[str]:
        """Extract context conditions from a Context object."""
        return self._extract_context_conditions_from_dict(asdict(context))
    
    def _extract_context_conditions_from_dict(self, context_dict: Dict[str, Any]) -> List[str]:
        """Extract context conditions from a context dictionary."""
        conditions = []
        
        try:
            if 'active_applications' in context_dict and context_dict['active_applications']:
                for app in context_dict['active_applications']:
                    conditions.append(f"app:{app}")
            
            if 'user_activity' in context_dict and context_dict['user_activity']:
                conditions.append(f"activity:{context_dict['user_activity']}")
            
            if 'system_state' in context_dict and context_dict['system_state']:
                for key, value in context_dict['system_state'].items():
                    conditions.append(f"system:{key}:{value}")
            
            return conditions
            
        except Exception as e:
            self.logger.error(f"Failed to extract context conditions: {e}")
            return []
    
    def _update_learned_preferences(self, pattern: PreferencePattern) -> None:
        """Update the main learned preferences based on a pattern."""
        try:
            category = pattern.category.value
            
            if category in self.learned_preferences:
                if isinstance(pattern.preference_value, dict):
                    if isinstance(self.learned_preferences[category], dict):
                        self.learned_preferences[category].update(pattern.preference_value)
                    else:
                        self.learned_preferences[category] = pattern.preference_value
                else:
                    self.learned_preferences[category] = pattern.preference_value
            
        except Exception as e:
            self.logger.error(f"Failed to update learned preferences: {e}")
    
    def _update_temporal_patterns(self, interaction: UserInteraction) -> None:
        """Update temporal patterns based on interaction."""
        try:
            timestamp = interaction.timestamp
            response_type = interaction.user_response.get('type', 'unknown')
            
            # Hourly pattern
            hour_pattern = {
                'hour': timestamp.hour,
                'response': response_type,
                'timestamp': timestamp.isoformat()
            }
            self.temporal_patterns['hourly'].append(hour_pattern)
            
            # Keep only recent patterns
            cutoff_time = datetime.now() - timedelta(days=7)
            self.temporal_patterns['hourly'] = [
                p for p in self.temporal_patterns['hourly']
                if datetime.fromisoformat(p['timestamp']) > cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to update temporal patterns: {e}")
    
    def _initialize_default_rules(self) -> None:
        """Initialize default adaptation rules."""
        try:
            # Rule for high automation preference
            self._create_adaptation_rule(
                name="High Automation Preference",
                condition="automation_level > 0.7",
                action="increase_suggestion_frequency",
                category=PreferenceCategory.AUTOMATION_LEVEL,
                priority=1
            )
            
            # Rule for low interruption tolerance
            self._create_adaptation_rule(
                name="Low Interruption Tolerance",
                condition="interruption_tolerance < 0.3",
                action="reduce_interruption_risk",
                category=PreferenceCategory.INTERRUPTION_TOLERANCE,
                priority=2
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize default rules: {e}")
    
    def _create_adaptation_rule(self, name: str, condition: str, action: str, 
                              category: PreferenceCategory, priority: int) -> None:
        """Create an adaptation rule."""
        try:
            rule = AdaptationRule(
                id=f"rule_{self.rule_counter}",
                name=name,
                condition=condition,
                action=action,
                preference_category=category,
                priority=priority
            )
            
            self.rule_counter += 1
            self.adaptation_rules[rule.id] = rule
            
        except Exception as e:
            self.logger.error(f"Failed to create adaptation rule: {e}")
    
    def _evaluate_rule_condition(self, rule: AdaptationRule, context: Context, suggestion: Dict[str, Any]) -> bool:
        """Evaluate if a rule condition is met."""
        try:
            # Simple condition evaluation - could be made more sophisticated
            condition = rule.condition
            
            if "automation_level" in condition:
                automation_level = self.learned_preferences.get('automation_level', 0.5)
                return eval(condition.replace('automation_level', str(automation_level)))
            
            if "interruption_tolerance" in condition:
                interruption_tolerance = self.learned_preferences.get('interruption_tolerance', 0.5)
                return eval(condition.replace('interruption_tolerance', str(interruption_tolerance)))
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate rule condition: {e}")
            return False
    
    def _apply_rule_action(self, rule: AdaptationRule, suggestion: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Apply a rule action to adapt the suggestion."""
        try:
            adapted = suggestion.copy()
            
            if rule.action == "increase_suggestion_frequency":
                adapted['priority_boost'] = adapted.get('priority_boost', 0) + 0.2
            elif rule.action == "reduce_interruption_risk":
                adapted['interruption_risk'] = adapted.get('interruption_risk', 0.5) * 0.7
            elif rule.action == "adjust_communication_style":
                preferred_style = self.learned_preferences.get('communication_style', 'balanced')
                adapted['communication_style'] = preferred_style
            
            return adapted
            
        except Exception as e:
            self.logger.error(f"Failed to apply rule action: {e}")
            return suggestion
    
    def _apply_preference_adaptations(self, suggestion: Dict[str, Any], context: Context) -> Dict[str, Any]:
        """Apply general preference-based adaptations."""
        try:
            adapted = suggestion.copy()
            
            # Adjust based on task priorities
            suggestion_type = suggestion.get('type', 'unknown')
            task_priorities = self.learned_preferences.get('task_priorities', {})
            if suggestion_type in task_priorities:
                priority_multiplier = task_priorities[suggestion_type]
                adapted['priority_score'] = adapted.get('priority_score', 0.5) * priority_multiplier
            
            # Adjust based on timing preferences
            current_hour = datetime.now().hour
            timing_prefs = self.learned_preferences.get('preferred_timing', {})
            if str(current_hour) in timing_prefs:
                timing_factor = timing_prefs[str(current_hour)]
                adapted['timing_score'] = timing_factor
            
            return adapted
            
        except Exception as e:
            self.logger.error(f"Failed to apply preference adaptations: {e}")
            return suggestion
    
    def _find_similar_interactions(self, suggestion: Dict[str, Any], context: Context) -> List[UserInteraction]:
        """Find interactions similar to current suggestion and context."""
        try:
            similar = []
            
            suggestion_type = suggestion.get('type', 'unknown')
            context_apps = context.active_applications or []
            
            for interaction in self.interactions.values():
                # Check suggestion type similarity
                if interaction.suggestion_data.get('type') == suggestion_type:
                    # Check context similarity
                    interaction_apps = interaction.context.get('active_applications', [])
                    app_overlap = len(set(context_apps) & set(interaction_apps))
                    
                    if app_overlap > 0 or (not context_apps and not interaction_apps):
                        similar.append(interaction)
            
            # Sort by recency (most recent first)
            similar.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Return top 10 most similar
            return similar[:10]
            
        except Exception as e:
            self.logger.error(f"Failed to find similar interactions: {e}")
            return []
    
    def _summarize_preferences(self) -> Dict[str, Any]:
        """Summarize current learned preferences."""
        try:
            summary = {}
            
            for category, value in self.learned_preferences.items():
                if isinstance(value, dict):
                    summary[category] = {
                        'type': 'complex',
                        'keys': list(value.keys()),
                        'sample': dict(list(value.items())[:3])  # First 3 items as sample
                    }
                else:
                    summary[category] = {
                        'type': 'simple',
                        'value': value
                    }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to summarize preferences: {e}")
            return {}
    
    def _calculate_confidence_levels(self) -> Dict[str, float]:
        """Calculate confidence levels for each preference category."""
        try:
            confidence_levels = {}
            
            for category in PreferenceCategory:
                category_patterns = [
                    p for p in self.preference_patterns.values()
                    if p.category == category
                ]
                
                if category_patterns:
                    avg_confidence = sum(p.confidence for p in category_patterns) / len(category_patterns)
                    confidence_levels[category.value] = avg_confidence
                else:
                    confidence_levels[category.value] = 0.0
            
            return confidence_levels
            
        except Exception as e:
            self.logger.error(f"Failed to calculate confidence levels: {e}")
            return {}
    
    def _assess_learning_progress(self) -> Dict[str, Any]:
        """Assess the progress of preference learning."""
        try:
            total_interactions = len(self.interactions)
            total_patterns = len(self.preference_patterns)
            high_confidence_patterns = len([
                p for p in self.preference_patterns.values()
                if p.confidence >= self.confidence_threshold
            ])
            
            return {
                'total_interactions': total_interactions,
                'total_patterns': total_patterns,
                'high_confidence_patterns': high_confidence_patterns,
                'learning_rate': high_confidence_patterns / max(total_patterns, 1),
                'data_sufficiency': min(total_interactions / 50, 1.0)  # Assume 50 interactions for good learning
            }
            
        except Exception as e:
            self.logger.error(f"Failed to assess learning progress: {e}")
            return {}
    
    def _measure_adaptation_effectiveness(self) -> Dict[str, Any]:
        """Measure how effective the adaptations have been."""
        try:
            recent_interactions = [
                i for i in self.interactions.values()
                if i.timestamp > datetime.now() - timedelta(days=7)
            ]
            
            if not recent_interactions:
                return {'effectiveness': 0.5, 'sample_size': 0}
            
            positive_responses = len([
                i for i in recent_interactions
                if i.user_response.get('type') in ['accept', 'modify']
            ])
            
            effectiveness = positive_responses / len(recent_interactions)
            
            return {
                'effectiveness': effectiveness,
                'sample_size': len(recent_interactions),
                'positive_responses': positive_responses,
                'total_responses': len(recent_interactions)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to measure adaptation effectiveness: {e}")
            return {}
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal patterns in user behavior."""
        try:
            hourly_patterns = self.temporal_patterns.get('hourly', [])
            
            if not hourly_patterns:
                return {'status': 'insufficient_data'}
            
            # Analyze acceptance rates by hour
            hourly_acceptance = {}
            for pattern in hourly_patterns:
                hour = pattern['hour']
                response = pattern['response']
                
                if hour not in hourly_acceptance:
                    hourly_acceptance[hour] = {'accept': 0, 'total': 0}
                
                hourly_acceptance[hour]['total'] += 1
                if response == 'accept':
                    hourly_acceptance[hour]['accept'] += 1
            
            # Calculate acceptance rates
            acceptance_rates = {}
            for hour, data in hourly_acceptance.items():
                acceptance_rates[hour] = data['accept'] / data['total'] if data['total'] > 0 else 0
            
            # Find best and worst hours
            best_hour = max(acceptance_rates, key=acceptance_rates.get) if acceptance_rates else None
            worst_hour = min(acceptance_rates, key=acceptance_rates.get) if acceptance_rates else None
            
            return {
                'hourly_acceptance_rates': acceptance_rates,
                'best_hour': best_hour,
                'worst_hour': worst_hour,
                'data_points': len(hourly_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze temporal patterns: {e}")
            return {}
    
    def _generate_preference_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for improving preference learning."""
        try:
            recommendations = []
            
            # Check for insufficient data
            if len(self.interactions) < 10:
                recommendations.append({
                    'type': 'data_collection',
                    'message': 'More user interactions needed for reliable preference learning',
                    'priority': 'high'
                })
            
            # Check for low confidence patterns
            low_confidence_patterns = [
                p for p in self.preference_patterns.values()
                if p.confidence < self.confidence_threshold
            ]
            
            if len(low_confidence_patterns) > len(self.preference_patterns) * 0.5:
                recommendations.append({
                    'type': 'confidence_improvement',
                    'message': 'Many preference patterns have low confidence - consider explicit preference collection',
                    'priority': 'medium'
                })
            
            # Check for missing categories
            learned_categories = set(p.category for p in self.preference_patterns.values())
            all_categories = set(PreferenceCategory)
            missing_categories = all_categories - learned_categories
            
            if missing_categories:
                recommendations.append({
                    'type': 'category_coverage',
                    'message': f'Missing preference data for: {[c.value for c in missing_categories]}',
                    'priority': 'low'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate preference recommendations: {e}")
            return []
    
    def _update_automation_preference(self, feedback_data: Dict[str, Any]) -> None:
        """Update automation level preference from feedback."""
        try:
            new_level = feedback_data.get('level', self.learned_preferences.get('automation_level', 0.5))
            self.learned_preferences['automation_level'] = max(0.0, min(1.0, new_level))
            
        except Exception as e:
            self.logger.error(f"Failed to update automation preference: {e}")
    
    def _update_communication_preference(self, feedback_data: Dict[str, Any]) -> None:
        """Update communication style preference from feedback."""
        try:
            new_style = feedback_data.get('style', 'balanced')
            valid_styles = ['brief', 'balanced', 'detailed', 'interactive']
            if new_style in valid_styles:
                self.learned_preferences['communication_style'] = new_style
                
        except Exception as e:
            self.logger.error(f"Failed to update communication preference: {e}")
    
    def _update_timing_preference(self, feedback_data: Dict[str, Any]) -> None:
        """Update timing preference from feedback."""
        try:
            hour = feedback_data.get('hour')
            preference = feedback_data.get('preference', 0.5)
            
            if hour is not None:
                if 'preferred_timing' not in self.learned_preferences:
                    self.learned_preferences['preferred_timing'] = {}
                self.learned_preferences['preferred_timing'][str(hour)] = preference
                
        except Exception as e:
            self.logger.error(f"Failed to update timing preference: {e}")
    
    def _update_task_priority_preference(self, feedback_data: Dict[str, Any]) -> None:
        """Update task priority preference from feedback."""
        try:
            task_type = feedback_data.get('task_type')
            priority = feedback_data.get('priority', 0.5)
            
            if task_type:
                if 'task_priorities' not in self.learned_preferences:
                    self.learned_preferences['task_priorities'] = {}
                self.learned_preferences['task_priorities'][task_type] = priority
                
        except Exception as e:
            self.logger.error(f"Failed to update task priority preference: {e}")
    
    def _load_persisted_preferences(self) -> None:
        """Load persisted preferences (placeholder for future implementation)."""
        try:
            # This would load from persistent storage in a full implementation
            self.logger.debug("Preference loading placeholder")
            
        except Exception as e:
            self.logger.error(f"Failed to load persisted preferences: {e}")
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Preference Learner specific status."""
        return {
            'total_interactions': len(self.interactions),
            'preference_patterns': len(self.preference_patterns),
            'adaptation_rules': len(self.adaptation_rules),
            'high_confidence_patterns': len([
                p for p in self.preference_patterns.values()
                if p.confidence >= self.confidence_threshold
            ]),
            'learning_rate': self.learning_rate,
            'current_automation_level': self.learned_preferences.get('automation_level', 0.5),
        }