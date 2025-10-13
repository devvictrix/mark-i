"""
User Preference Learning System for MARK-I Knowledge Base.

This module provides user preference tracking, learning, and adaptation
capabilities that analyze user behavior patterns and feedback.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import json
import os

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context, ExecutionResult
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".knowledge.user_preference_learner")


class PreferenceCategory(Enum):
    """Categories of user preferences."""

    WORKFLOW = "workflow"
    INTERFACE = "interface"
    TIMING = "timing"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    FEEDBACK = "feedback"


@dataclass
class UserPreference:
    """Represents a learned user preference."""

    preference_id: str
    category: PreferenceCategory
    name: str
    value: Any
    strength: float
    confidence: float
    evidence_count: int
    last_reinforced: datetime
    created_at: datetime
    context_conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserBehaviorProfile:
    """User behavior profile."""

    profile_id: str
    user_id: str
    preferences: Dict[str, UserPreference]
    activity_history: List[Dict[str, Any]]
    created_at: datetime
    last_updated: datetime


class UserPreferenceLearner(ProcessingComponent):
    """User preference learning system."""

    def __init__(self, config: ComponentConfig):
        super().__init__(config)

        # Configuration
        self.learning_rate = getattr(config, "learning_rate", 0.1)
        self.confidence_threshold = getattr(config, "confidence_threshold", 0.7)

        # Data structures
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}

        # Threading
        self.learning_lock = threading.Lock()

        logger.info("UserPreferenceLearner initialized")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this preference learner."""
        return {"preference_learning": True, "behavior_analysis": True, "adaptive_personalization": True, "context_aware_preferences": True, "user_profiling": True, "feedback_integration": True}

    def learn_from_user_action(self, action_data: Dict[str, Any]) -> bool:
        """Learn user preferences from an observed action."""
        try:
            with self.learning_lock:
                user_id = action_data.get("user_id", "default_user")

                # Get or create user profile
                if user_id not in self.user_profiles:
                    self._create_user_profile(user_id)

                profile = self.user_profiles[user_id]

                # Extract preferences from action
                extracted_prefs = self._extract_preferences_from_action(action_data)

                # Update preferences
                for pref_data in extracted_prefs:
                    self._update_preference(profile, pref_data)

                # Update activity history
                profile.activity_history.append(
                    {"timestamp": datetime.now().isoformat(), "action_type": action_data.get("action_type"), "context": action_data.get("context", {}), "outcome": action_data.get("outcome", {})}
                )

                # Limit history size
                if len(profile.activity_history) > 1000:
                    profile.activity_history = profile.activity_history[-1000:]

                profile.last_updated = datetime.now()
                return True

        except Exception as e:
            logger.error(f"Error learning from user action: {e}")
            return False

    def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Learn preferences from explicit user feedback."""
        try:
            with self.learning_lock:
                user_id = feedback_data.get("user_id", "default_user")
                feedback_type = feedback_data.get("feedback_type")
                preference_category = feedback_data.get("category")
                preference_value = feedback_data.get("value")

                if user_id not in self.user_profiles:
                    self._create_user_profile(user_id)

                profile = self.user_profiles[user_id]

                # Create or update preference based on feedback
                pref_id = f"{preference_category}_{hash(str(preference_value))}"

                if pref_id in profile.preferences:
                    preference = profile.preferences[pref_id]

                    # Update based on feedback type
                    if feedback_type == "positive":
                        preference.strength = min(1.0, preference.strength + 0.2)
                        preference.confidence = min(1.0, preference.confidence + 0.1)
                    elif feedback_type == "negative":
                        preference.strength = max(0.1, preference.strength - 0.3)
                        preference.confidence = max(0.1, preference.confidence - 0.1)

                    preference.evidence_count += 1
                    preference.last_reinforced = datetime.now()

                else:
                    # Create new preference from feedback
                    strength = 0.8 if feedback_type == "positive" else 0.2

                    preference = UserPreference(
                        preference_id=pref_id,
                        category=PreferenceCategory(preference_category),
                        name=f"User feedback: {preference_category}",
                        value=preference_value,
                        strength=strength,
                        confidence=0.7,
                        evidence_count=1,
                        last_reinforced=datetime.now(),
                        created_at=datetime.now(),
                        context_conditions=feedback_data.get("context", {}),
                    )

                    profile.preferences[pref_id] = preference

                return True

        except Exception as e:
            logger.error(f"Error learning from feedback: {e}")
            return False

    def get_user_preferences(self, user_id: str = "default_user", category: Optional[str] = None) -> Dict[str, Any]:
        """Get user preferences, optionally filtered by category."""
        try:
            if user_id not in self.user_profiles:
                return {}

            profile = self.user_profiles[user_id]
            preferences = {}

            for pref_id, pref in profile.preferences.items():
                if pref.confidence >= self.confidence_threshold:
                    if category is None or pref.category.value == category:
                        preferences[pref_id] = {
                            "category": pref.category.value,
                            "name": pref.name,
                            "value": pref.value,
                            "strength": pref.strength,
                            "confidence": pref.confidence,
                            "evidence_count": pref.evidence_count,
                            "last_reinforced": pref.last_reinforced.isoformat(),
                        }

            return preferences

        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}

    def _create_user_profile(self, user_id: str):
        """Create a new user behavior profile."""
        profile = UserBehaviorProfile(profile_id=f"profile_{user_id}_{int(time.time())}", user_id=user_id, preferences={}, activity_history=[], created_at=datetime.now(), last_updated=datetime.now())

        self.user_profiles[user_id] = profile
        logger.info(f"Created user profile for: {user_id}")

    def _extract_preferences_from_action(self, action_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract implicit preferences from user actions."""
        preferences = []

        action_type = action_data.get("action_type")
        context = action_data.get("context", {})
        outcome = action_data.get("outcome", {})

        # Extract timing preferences
        if "timestamp" in action_data:
            timestamp = datetime.fromisoformat(action_data["timestamp"])
            hour = timestamp.hour

            preferences.append({"category": PreferenceCategory.TIMING, "name": "preferred_work_hours", "value": hour, "strength": 0.3})

        # Extract workflow preferences
        if action_type and outcome.get("success", False):
            preferences.append({"category": PreferenceCategory.WORKFLOW, "name": f"successful_{action_type}", "value": context, "strength": 0.5})

        return preferences

    def _update_preference(self, profile: UserBehaviorProfile, pref_data: Dict[str, Any]):
        """Update a preference in the user profile."""
        category = pref_data["category"]
        name = pref_data["name"]
        value = pref_data["value"]

        pref_id = f"{category.value}_{name}_{hash(str(value))}"

        if pref_id in profile.preferences:
            # Update existing preference
            preference = profile.preferences[pref_id]
            preference.strength = min(1.0, preference.strength + self.learning_rate)
            preference.confidence = min(1.0, preference.confidence + 0.05)
            preference.evidence_count += 1
            preference.last_reinforced = datetime.now()

        else:
            # Create new preference
            preference = UserPreference(
                preference_id=pref_id,
                category=category,
                name=name,
                value=value,
                strength=pref_data.get("strength", 0.5),
                confidence=0.5,
                evidence_count=1,
                last_reinforced=datetime.now(),
                created_at=datetime.now(),
            )

            profile.preferences[pref_id] = preference

    def process(self, input_data: Any) -> ExecutionResult:
        """Process input through the preference learner."""
        try:
            if isinstance(input_data, dict):
                command = input_data.get("command")

                if command == "learn_action":
                    action_data = input_data.get("action_data", {})
                    success = self.learn_from_user_action(action_data)
                    return ExecutionResult(success=success, message="Learned from user action" if success else "Failed to learn from action", data={})

                elif command == "learn_feedback":
                    feedback_data = input_data.get("feedback_data", {})
                    success = self.learn_from_feedback(feedback_data)
                    return ExecutionResult(success=success, message="Learned from feedback" if success else "Failed to learn from feedback", data={})

                elif command == "get_preferences":
                    user_id = input_data.get("user_id", "default_user")
                    category = input_data.get("category")
                    preferences = self.get_user_preferences(user_id, category)
                    return ExecutionResult(success=True, message=f"Retrieved {len(preferences)} preferences", data={"preferences": preferences})

            return ExecutionResult(success=False, message="Invalid input for UserPreferenceLearner", data={})

        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return ExecutionResult(success=False, message=f"Processing error: {str(e)}", data={})

    def cleanup(self):
        """Clean up resources."""
        logger.info("UserPreferenceLearner cleanup completed")

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass
