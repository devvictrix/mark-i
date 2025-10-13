import logging
import json
import os
import hashlib
import threading
from typing import Dict, Any, Optional, List, Tuple
import copy
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
from mark_i.core.interfaces import IKnowledgeBase, Context
from mark_i.core.base_component import BaseComponent
from mark_i.core.architecture_config import ComponentConfig

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.knowledge.knowledge_base")

DEFAULT_KNOWLEDGE_BASE_FILENAME = "knowledge_base.json"
MAX_STRATEGIES_PER_OBJECTIVE = 5  # Prevents knowledge base from growing indefinitely
MAX_EXPERIENCES = 10000  # Maximum number of experiences to store
SIMILARITY_THRESHOLD = 0.7  # Threshold for similarity matching


@dataclass
class Experience:
    """Represents a stored experience with context and outcomes."""
    experience_id: str
    context: Dict[str, Any]
    actions_taken: List[Dict[str, Any]]
    outcome: Dict[str, Any]
    success_metrics: Dict[str, float]
    lessons_learned: List[str]
    timestamp: datetime
    tags: List[str] = field(default_factory=list)
    similarity_vector: Optional[List[float]] = None


@dataclass
class ApplicationKnowledge:
    """Knowledge about a specific application."""
    app_name: str
    interface_patterns: Dict[str, Any]
    common_actions: List[Dict[str, Any]]
    success_rates: Dict[str, float]
    learned_shortcuts: Dict[str, str]
    ui_elements: Dict[str, Dict[str, Any]]
    last_updated: datetime
    usage_frequency: int = 0


@dataclass
class UserPreference:
    """Represents a learned user preference."""
    preference_id: str
    category: str  # "workflow", "interface", "timing", "communication", etc.
    preference_data: Dict[str, Any]
    confidence: float
    evidence_count: int
    last_updated: datetime


class KnowledgeBase(BaseComponent, IKnowledgeBase):
    """
    Enhanced knowledge base for learning and memory management.
    
    Provides experience storage, similarity-based retrieval, application learning,
    and user preference management with context indexing and pattern recognition.
    """

    def __init__(self, config: ComponentConfig, project_root: Optional[str] = None):
        super().__init__(config)
        
        # Configuration
        self.max_experiences = getattr(config, "max_experiences", MAX_EXPERIENCES)
        self.similarity_threshold = getattr(config, "similarity_threshold", SIMILARITY_THRESHOLD)
        self.knowledge_consolidation_interval = getattr(config, "knowledge_consolidation_interval", 100)
        self.user_preference_weight = getattr(config, "user_preference_weight", 0.8)
        self.application_learning = getattr(config, "application_learning", True)
        self.knowledge_graph_depth = getattr(config, "knowledge_graph_depth", 5)
        self.auto_cleanup = getattr(config, "auto_cleanup", True)
        
        # Storage setup
        if project_root:
            from mark_i.core.storage_manager import StorageManager
            storage_manager = StorageManager(project_root)
            knowledge_storage = storage_manager.get_storage_path("knowledge")
            self.kb_path = str(knowledge_storage / DEFAULT_KNOWLEDGE_BASE_FILENAME)
        else:
            # Fallback for testing or standalone usage
            self.kb_path = DEFAULT_KNOWLEDGE_BASE_FILENAME
        
        # Data structures
        self.knowledge_data: Dict[str, Any] = {}
        self.experiences: Dict[str, Experience] = {}
        self.application_knowledge: Dict[str, ApplicationKnowledge] = {}
        self.user_preferences: Dict[str, UserPreference] = {}
        
        # Threading and synchronization
        self.knowledge_lock = threading.Lock()
        self.experience_lock = threading.Lock()
        self.preference_lock = threading.Lock()
        
        # Context indexing
        self.context_index: Dict[str, List[str]] = defaultdict(list)  # context_key -> experience_ids
        self.tag_index: Dict[str, List[str]] = defaultdict(list)  # tag -> experience_ids
        
        # Performance tracking
        self.consolidation_counter = 0
        
        # Load existing knowledge
        self.load_knowledge()
        
        logger.info("Enhanced KnowledgeBase initialized with experience storage and retrieval capabilities")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this knowledge base."""
        return {
            "experience_storage": True,
            "similarity_retrieval": True,
            "application_learning": self.application_learning,
            "user_preference_learning": True,
            "knowledge_graph_organization": True,
            "context_indexing": True,
            "pattern_recognition": True,
            "max_experiences": self.max_experiences,
            "similarity_threshold": self.similarity_threshold,
            "knowledge_graph_depth": self.knowledge_graph_depth
        }

    def load_knowledge(self):
        logger.info(f"Attempting to load knowledge base from: {self.kb_path}")
        if not os.path.exists(self.kb_path):
            logger.warning(f"Knowledge base file not found at '{self.kb_path}'. Initializing with empty structure.")
            self.knowledge_data = {"aliases": {}, "perceptual_filters": {"ignore_list": []}, "user_data": {}, "objectives": []}
            return

        try:
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.knowledge_data = json.load(f)
            # Ensure top-level keys exist for robustness
            self.knowledge_data.setdefault("aliases", {})
            self.knowledge_data.setdefault("perceptual_filters", {"ignore_list": []})
            self.knowledge_data["perceptual_filters"].setdefault("ignore_list", [])
            self.knowledge_data.setdefault("user_data", {})
            self.knowledge_data.setdefault("objectives", [])
            logger.info("Knowledge base loaded and validated successfully.")
        except Exception as e:
            logger.error(f"Failed to read/parse knowledge base file '{self.kb_path}': {e}", exc_info=True)
            self.knowledge_data = {}
        
        # Load enhanced data structures
        self._load_experiences()
        self._load_application_knowledge()
        self._load_user_preferences()
        self._rebuild_indices()

    def get_full_knowledge_base(self) -> Dict[str, Any]:
        return copy.deepcopy(self.knowledge_data)

    def find_objective(self, objective_name_to_find: str) -> Optional[Dict[str, Any]]:
        objectives = self.knowledge_data.get("objectives", [])
        if not isinstance(objectives, list):
            return None
        for objective in objectives:
            if isinstance(objective, dict) and objective.get("objective_name") == objective_name_to_find:
                return copy.deepcopy(objective)
        return None

    def get_all_strategies_for_objective(self, objective_name: str) -> List[Dict[str, Any]]:
        """Returns all strategies for a given objective, sorted by success rate."""
        objective = self.find_objective(objective_name)
        if not objective or not isinstance(objective.get("strategies"), list):
            return []

        return sorted(objective["strategies"], key=lambda s: s.get("success_rate", 0.0), reverse=True)

    def save_knowledge_base(self) -> bool:
        logger.info(f"Saving updated knowledge base to: {self.kb_path}")
        try:
            with open(self.kb_path, "w", encoding="utf-8") as f:
                json.dump(self.knowledge_data, f, indent=2, ensure_ascii=False)
            logger.info("Knowledge base saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to save knowledge base file '{self.kb_path}': {e}", exc_info=True)
            return False

    def update_strategy_metadata(self, objective_name: str, strategy_name: str, updates: Dict[str, Any]) -> bool:
        objectives = self.knowledge_data.get("objectives", [])
        if not isinstance(objectives, list):
            return False

        for objective in objectives:
            if objective.get("objective_name") == objective_name:
                strategies = objective.get("strategies", [])
                if not isinstance(strategies, list):
                    break
                for strategy in strategies:
                    if strategy.get("strategy_name") == strategy_name:
                        strategy.update(updates)
                        logger.info(f"Updated metadata for Strategy '{strategy_name}' in Objective '{objective_name}' with: {updates}")
                        return self.save_knowledge_base()

        logger.warning(f"Cannot update strategy metadata: Strategy or Objective not found.")
        return False

    def save_strategy(self, objective_name: str, new_strategy: Dict[str, Any], goal_prompt_if_new: Optional[str] = None) -> bool:
        """
        Saves a strategy. If the objective doesn't exist, it's created.
        If a strategy with the same name exists, it's updated. Otherwise, it's appended.
        Prunes the list if it exceeds the maximum allowed strategies.
        """
        objectives = self.knowledge_data.setdefault("objectives", [])
        target_objective = None
        for obj in objectives:
            if obj.get("objective_name") == objective_name:
                target_objective = obj
                break

        if not target_objective:
            target_objective = {"objective_name": objective_name, "goal_prompt": goal_prompt_if_new or f"Goal for {objective_name}", "strategies": []}
            objectives.append(target_objective)

        strategies = target_objective.setdefault("strategies", [])

        # Check if a strategy with the same name already exists to update it
        found_existing = False
        for i, existing_strategy in enumerate(strategies):
            if existing_strategy.get("strategy_name") == new_strategy.get("strategy_name"):
                strategies[i] = new_strategy
                found_existing = True
                logger.info(f"Updated existing strategy '{new_strategy.get('strategy_name')}' for objective '{objective_name}'.")
                break

        if not found_existing:
            strategies.append(new_strategy)
            logger.info(f"Appended new strategy '{new_strategy.get('strategy_name')}' for objective '{objective_name}'.")

        # Prune old/low-performing strategies if list is too long
        if len(strategies) > MAX_STRATEGIES_PER_OBJECTIVE:
            logger.info(f"Strategy list for '{objective_name}' exceeds max of {MAX_STRATEGIES_PER_OBJECTIVE}. Pruning...")
            # Sort by success rate (desc) and then by last used (desc) to keep the best and most recent
            strategies.sort(key=lambda s: (s.get("success_rate", 0.0), s.get("last_used", "")), reverse=True)
            target_objective["strategies"] = strategies[:MAX_STRATEGIES_PER_OBJECTIVE]

        result = self.save_knowledge_base()
        if result:
            self.save_enhanced_knowledge()
        return result

    ## V18 OPTIMIZATION START ##
    def get_perceptual_ignore_list(self) -> List[str]:
        """Returns the list of item descriptions to be ignored during perception."""
        filters = self.knowledge_data.get("perceptual_filters", {})
        return filters.get("ignore_list", [])

    def add_to_perceptual_ignore_list(self, item_description: str) -> bool:
        """Adds a new item description to the perceptual ignore list and saves."""
        if not self._validate_ignore_description(item_description):
            return False

        item_description = item_description.strip()
        filters = self.knowledge_data.setdefault("perceptual_filters", {})
        ignore_list = filters.setdefault("ignore_list", [])

        if item_description not in ignore_list:
            ignore_list.append(item_description)
            logger.info(f"Added '{item_description}' to perceptual ignore list.")
            return self.save_knowledge_base()

        logger.debug(f"'{item_description}' already in perceptual ignore list.")
        return True  # It's already there, so the state is correct.

    def remove_from_perceptual_ignore_list(self, item_description: str) -> bool:
        """Removes an item description from the perceptual ignore list."""
        if not item_description or not isinstance(item_description, str):
            logger.warning("Invalid item description provided for removal.")
            return False

        filters = self.knowledge_data.get("perceptual_filters", {})
        ignore_list = filters.get("ignore_list", [])

        if item_description in ignore_list:
            ignore_list.remove(item_description)
            logger.info(f"Removed '{item_description}' from perceptual ignore list.")
            return self.save_knowledge_base()
        else:
            logger.warning(f"'{item_description}' not found in perceptual ignore list.")
            return False

    def get_perceptual_ignore_list_formatted(self) -> str:
        """Returns the ignore list formatted for inclusion in AI prompts."""
        ignore_list = self.get_perceptual_ignore_list()
        
        if not ignore_list:
            return "No items to ignore."
        
        # Format as numbered list for clarity in AI prompts
        formatted_items = []
        for i, item in enumerate(ignore_list, 1):
            formatted_items.append(f"{i}. {item}")
        
        return "\n".join(formatted_items)

    def clear_perceptual_ignore_list(self) -> bool:
        """Clears all items from the perceptual ignore list."""
        filters = self.knowledge_data.setdefault("perceptual_filters", {})
        ignore_list = filters.get("ignore_list", [])
        
        if ignore_list:
            item_count = len(ignore_list)
            filters["ignore_list"] = []
            logger.info(f"Cleared {item_count} items from perceptual ignore list.")
            return self.save_knowledge_base()
        else:
            logger.info("Perceptual ignore list was already empty.")
            return True
    
    # IKnowledgeBase interface implementation
    
    def store_experience(self, experience: Dict[str, Any]) -> None:
        """Store a new experience with context indexing."""
        try:
            with self.experience_lock:
                # Create experience ID
                experience_id = self._generate_experience_id(experience)
                
                # Create Experience object
                exp = Experience(
                    experience_id=experience_id,
                    context=experience.get("context", {}),
                    actions_taken=experience.get("actions_taken", []),
                    outcome=experience.get("outcome", {}),
                    success_metrics=experience.get("success_metrics", {}),
                    lessons_learned=experience.get("lessons_learned", []),
                    timestamp=datetime.now(),
                    tags=experience.get("tags", [])
                )
                
                # Generate similarity vector for efficient retrieval
                exp.similarity_vector = self._generate_similarity_vector(exp)
                
                # Store experience
                self.experiences[experience_id] = exp
                
                # Update indices
                self._update_context_index(exp)
                self._update_tag_index(exp)
                
                # Cleanup if needed
                if len(self.experiences) > self.max_experiences:
                    self._cleanup_old_experiences()
                
                # Periodic consolidation
                self.consolidation_counter += 1
                if self.consolidation_counter >= self.knowledge_consolidation_interval:
                    self._consolidate_knowledge()
                    self.consolidation_counter = 0
                
                logger.debug(f"Stored experience: {experience_id}")
                
        except Exception as e:
            logger.error(f"Error storing experience: {e}")
    
    def retrieve_similar_experiences(self, context: Context, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve similar experiences based on context."""
        try:
            with self.experience_lock:
                if not self.experiences:
                    return []
                
                # Create context vector for similarity comparison
                context_dict = {
                    "timestamp": context.timestamp.isoformat() if context.timestamp else "",
                    "active_applications": context.active_applications or [],
                    "user_activity": context.user_activity or "",
                    "system_state": context.system_state or {}
                }
                
                context_vector = self._generate_context_similarity_vector(context_dict)
                
                # Calculate similarities
                similarities = []
                for exp_id, experience in self.experiences.items():
                    if experience.similarity_vector:
                        similarity = self._calculate_similarity(context_vector, experience.similarity_vector)
                        if similarity >= self.similarity_threshold:
                            similarities.append((similarity, experience))
                
                # Sort by similarity and return top results
                similarities.sort(key=lambda x: x[0], reverse=True)
                
                results = []
                for similarity, experience in similarities[:limit]:
                    result = {
                        "experience_id": experience.experience_id,
                        "context": experience.context,
                        "actions_taken": experience.actions_taken,
                        "outcome": experience.outcome,
                        "success_metrics": experience.success_metrics,
                        "lessons_learned": experience.lessons_learned,
                        "timestamp": experience.timestamp.isoformat(),
                        "tags": experience.tags,
                        "similarity_score": similarity
                    }
                    results.append(result)
                
                logger.debug(f"Retrieved {len(results)} similar experiences")
                return results
                
        except Exception as e:
            logger.error(f"Error retrieving similar experiences: {e}")
            return []
    
    def update_application_knowledge(self, app_info: Dict[str, Any]) -> None:
        """Update knowledge about an application."""
        try:
            app_name = app_info.get("app_name", "unknown")
            
            with self.knowledge_lock:
                if app_name not in self.application_knowledge:
                    self.application_knowledge[app_name] = ApplicationKnowledge(
                        app_name=app_name,
                        interface_patterns={},
                        common_actions=[],
                        success_rates={},
                        learned_shortcuts={},
                        ui_elements={},
                        last_updated=datetime.now()
                    )
                
                app_knowledge = self.application_knowledge[app_name]
                
                # Update interface patterns
                if "interface_patterns" in app_info:
                    app_knowledge.interface_patterns.update(app_info["interface_patterns"])
                
                # Update common actions
                if "actions" in app_info:
                    for action in app_info["actions"]:
                        if action not in app_knowledge.common_actions:
                            app_knowledge.common_actions.append(action)
                
                # Update success rates
                if "success_rates" in app_info:
                    app_knowledge.success_rates.update(app_info["success_rates"])
                
                # Update shortcuts
                if "shortcuts" in app_info:
                    app_knowledge.learned_shortcuts.update(app_info["shortcuts"])
                
                # Update UI elements
                if "ui_elements" in app_info:
                    app_knowledge.ui_elements.update(app_info["ui_elements"])
                
                app_knowledge.last_updated = datetime.now()
                app_knowledge.usage_frequency += 1
                
                logger.debug(f"Updated application knowledge for: {app_name}")
                
        except Exception as e:
            logger.error(f"Error updating application knowledge: {e}")
    
    def learn_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """Learn and update user preferences."""
        try:
            with self.preference_lock:
                for category, pref_data in preferences.items():
                    preference_id = f"{category}_{hashlib.md5(str(pref_data).encode()).hexdigest()[:8]}"
                    
                    if preference_id in self.user_preferences:
                        # Update existing preference
                        pref = self.user_preferences[preference_id]
                        pref.preference_data.update(pref_data)
                        pref.evidence_count += 1
                        pref.confidence = min(1.0, pref.confidence + 0.1)
                        pref.last_updated = datetime.now()
                    else:
                        # Create new preference
                        self.user_preferences[preference_id] = UserPreference(
                            preference_id=preference_id,
                            category=category,
                            preference_data=pref_data,
                            confidence=0.5,
                            evidence_count=1,
                            last_updated=datetime.now()
                        )
                    
                    logger.debug(f"Learned user preference: {category}")
                
        except Exception as e:
            logger.error(f"Error learning user preferences: {e}")
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get current user preferences."""
        try:
            with self.preference_lock:
                preferences = {}
                for pref in self.user_preferences.values():
                    if pref.confidence >= 0.6:  # Only return confident preferences
                        if pref.category not in preferences:
                            preferences[pref.category] = []
                        
                        pref_info = {
                            "data": pref.preference_data,
                            "confidence": pref.confidence,
                            "evidence_count": pref.evidence_count,
                            "last_updated": pref.last_updated.isoformat()
                        }
                        preferences[pref.category].append(pref_info)
                
                # Sort by confidence within each category
                for category in preferences:
                    preferences[category].sort(key=lambda x: x["confidence"], reverse=True)
                
                return preferences
                
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    def organize_knowledge_graph(self) -> Dict[str, Any]:
        """Organize and return knowledge graph structure."""
        try:
            with self.knowledge_lock:
                graph = {
                    "nodes": {},
                    "edges": [],
                    "statistics": {
                        "total_experiences": len(self.experiences),
                        "total_applications": len(self.application_knowledge),
                        "total_preferences": len(self.user_preferences),
                        "knowledge_depth": self.knowledge_graph_depth
                    }
                }
                
                # Add application nodes
                for app_name, app_knowledge in self.application_knowledge.items():
                    graph["nodes"][f"app_{app_name}"] = {
                        "type": "application",
                        "name": app_name,
                        "usage_frequency": app_knowledge.usage_frequency,
                        "success_rates": app_knowledge.success_rates,
                        "last_updated": app_knowledge.last_updated.isoformat()
                    }
                
                # Add preference nodes
                for pref_id, preference in self.user_preferences.items():
                    if preference.confidence >= 0.7:  # Only include confident preferences
                        graph["nodes"][f"pref_{pref_id}"] = {
                            "type": "preference",
                            "category": preference.category,
                            "confidence": preference.confidence,
                            "evidence_count": preference.evidence_count
                        }
                
                # Add experience cluster nodes
                experience_clusters = self._cluster_experiences()
                for cluster_id, cluster_info in experience_clusters.items():
                    graph["nodes"][f"cluster_{cluster_id}"] = {
                        "type": "experience_cluster",
                        "size": cluster_info["size"],
                        "avg_success": cluster_info["avg_success"],
                        "common_tags": cluster_info["common_tags"]
                    }
                
                # Add edges based on relationships
                self._add_knowledge_graph_edges(graph)
                
                return graph
                
        except Exception as e:
            logger.error(f"Error organizing knowledge graph: {e}")
            return {"nodes": {}, "edges": [], "statistics": {}}
    
    # Helper methods for enhanced functionality
    
    def _generate_experience_id(self, experience: Dict[str, Any]) -> str:
        """Generate a unique ID for an experience."""
        content = f"{experience.get('context', {})}{experience.get('actions_taken', [])}{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_similarity_vector(self, experience: Experience) -> List[float]:
        """Generate a similarity vector for an experience."""
        try:
            # Create feature vector based on context and actions
            features = []
            
            # Context features
            context = experience.context
            features.extend([
                len(context.get("active_applications", [])),
                1.0 if context.get("user_activity") else 0.0,
                len(str(context.get("system_state", {}))),
                experience.timestamp.hour / 24.0,  # Time of day
                experience.timestamp.weekday() / 7.0  # Day of week
            ])
            
            # Action features
            actions = experience.actions_taken
            features.extend([
                len(actions),
                sum(1 for action in actions if action.get("success", False)) / max(1, len(actions)),
                len(set(action.get("type", "") for action in actions))
            ])
            
            # Outcome features
            outcome = experience.outcome
            features.extend([
                1.0 if outcome.get("success", False) else 0.0,
                len(outcome.get("errors", [])),
                outcome.get("duration", 0.0) / 3600.0  # Duration in hours
            ])
            
            # Normalize vector
            if features:
                magnitude = sum(f * f for f in features) ** 0.5
                if magnitude > 0:
                    features = [f / magnitude for f in features]
            
            return features
            
        except Exception as e:
            logger.error(f"Error generating similarity vector: {e}")
            return []
    
    def _generate_context_similarity_vector(self, context: Dict[str, Any]) -> List[float]:
        """Generate a similarity vector for a context."""
        try:
            features = []
            
            features.extend([
                len(context.get("active_applications", [])),
                1.0 if context.get("user_activity") else 0.0,
                len(str(context.get("system_state", {}))),
                datetime.now().hour / 24.0,
                datetime.now().weekday() / 7.0
            ])
            
            # Normalize
            if features:
                magnitude = sum(f * f for f in features) ** 0.5
                if magnitude > 0:
                    features = [f / magnitude for f in features]
            
            return features
            
        except Exception as e:
            logger.error(f"Error generating context similarity vector: {e}")
            return []
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            if not vec1 or not vec2 or len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def _update_context_index(self, experience: Experience):
        """Update context index for efficient retrieval."""
        try:
            context = experience.context
            
            # Index by active applications
            for app in context.get("active_applications", []):
                self.context_index[f"app_{app}"].append(experience.experience_id)
            
            # Index by user activity
            if context.get("user_activity"):
                self.context_index[f"activity_{context['user_activity']}"].append(experience.experience_id)
            
            # Index by time patterns
            hour = experience.timestamp.hour
            self.context_index[f"hour_{hour}"].append(experience.experience_id)
            
            weekday = experience.timestamp.weekday()
            self.context_index[f"weekday_{weekday}"].append(experience.experience_id)
            
        except Exception as e:
            logger.error(f"Error updating context index: {e}")
    
    def _update_tag_index(self, experience: Experience):
        """Update tag index for efficient retrieval."""
        try:
            for tag in experience.tags:
                self.tag_index[tag].append(experience.experience_id)
        except Exception as e:
            logger.error(f"Error updating tag index: {e}")
    
    def _cleanup_old_experiences(self):
        """Remove old experiences when limit is exceeded."""
        try:
            if len(self.experiences) <= self.max_experiences:
                return
            
            # Sort by timestamp and remove oldest
            sorted_experiences = sorted(
                self.experiences.items(),
                key=lambda x: x[1].timestamp
            )
            
            to_remove = len(self.experiences) - self.max_experiences
            for i in range(to_remove):
                exp_id, experience = sorted_experiences[i]
                del self.experiences[exp_id]
                
                # Clean up indices
                self._remove_from_indices(experience)
            
            logger.info(f"Cleaned up {to_remove} old experiences")
            
        except Exception as e:
            logger.error(f"Error cleaning up old experiences: {e}")
    
    def _remove_from_indices(self, experience: Experience):
        """Remove experience from all indices."""
        try:
            exp_id = experience.experience_id
            
            # Remove from context index
            for key, exp_list in self.context_index.items():
                if exp_id in exp_list:
                    exp_list.remove(exp_id)
            
            # Remove from tag index
            for tag in experience.tags:
                if exp_id in self.tag_index[tag]:
                    self.tag_index[tag].remove(exp_id)
            
        except Exception as e:
            logger.error(f"Error removing from indices: {e}")
    
    def _consolidate_knowledge(self):
        """Consolidate and optimize knowledge storage."""
        try:
            logger.info("Starting knowledge consolidation")
            
            # Clean up empty index entries
            self.context_index = {k: v for k, v in self.context_index.items() if v}
            self.tag_index = {k: v for k, v in self.tag_index.items() if v}
            
            # Update preference confidences based on recent evidence
            current_time = datetime.now()
            for preference in self.user_preferences.values():
                days_since_update = (current_time - preference.last_updated).days
                if days_since_update > 30:  # Decay confidence over time
                    preference.confidence = max(0.1, preference.confidence * 0.95)
            
            logger.info("Knowledge consolidation completed")
            
        except Exception as e:
            logger.error(f"Error during knowledge consolidation: {e}")
    
    def _cluster_experiences(self) -> Dict[str, Dict[str, Any]]:
        """Cluster similar experiences for knowledge graph."""
        try:
            clusters = {}
            processed = set()
            
            for exp_id, experience in self.experiences.items():
                if exp_id in processed:
                    continue
                
                # Find similar experiences
                similar_experiences = [experience]
                processed.add(exp_id)
                
                for other_id, other_exp in self.experiences.items():
                    if other_id != exp_id and other_id not in processed:
                        if (experience.similarity_vector and other_exp.similarity_vector and
                            self._calculate_similarity(experience.similarity_vector, other_exp.similarity_vector) > 0.8):
                            similar_experiences.append(other_exp)
                            processed.add(other_id)
                
                # Create cluster
                if len(similar_experiences) >= 2:
                    cluster_id = f"cluster_{len(clusters)}"
                    
                    # Calculate cluster statistics
                    total_success = sum(1 for exp in similar_experiences 
                                      if exp.outcome.get("success", False))
                    avg_success = total_success / len(similar_experiences)
                    
                    all_tags = []
                    for exp in similar_experiences:
                        all_tags.extend(exp.tags)
                    
                    common_tags = [tag for tag in set(all_tags) 
                                 if all_tags.count(tag) >= len(similar_experiences) // 2]
                    
                    clusters[cluster_id] = {
                        "size": len(similar_experiences),
                        "avg_success": avg_success,
                        "common_tags": common_tags
                    }
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering experiences: {e}")
            return {}
    
    def _add_knowledge_graph_edges(self, graph: Dict[str, Any]):
        """Add edges to the knowledge graph based on relationships."""
        try:
            # Add edges between applications and preferences
            for app_name in self.application_knowledge.keys():
                app_node = f"app_{app_name}"
                
                for pref_id, preference in self.user_preferences.items():
                    if preference.confidence >= 0.7:
                        pref_node = f"pref_{pref_id}"
                        
                        # Check if preference relates to this application
                        if (app_name.lower() in str(preference.preference_data).lower() or
                            any(app_name.lower() in tag.lower() for tag in preference.preference_data.get("tags", []))):
                            
                            graph["edges"].append({
                                "from": app_node,
                                "to": pref_node,
                                "type": "influences",
                                "weight": preference.confidence
                            })
            
        except Exception as e:
            logger.error(f"Error adding knowledge graph edges: {e}")
    
    def _load_experiences(self):
        """Load experiences from storage."""
        try:
            experiences_file = self.kb_path.replace(".json", "_experiences.json")
            if os.path.exists(experiences_file):
                with open(experiences_file, 'r') as f:
                    experiences_data = json.load(f)
                
                for exp_data in experiences_data:
                    experience = Experience(
                        experience_id=exp_data["experience_id"],
                        context=exp_data["context"],
                        actions_taken=exp_data["actions_taken"],
                        outcome=exp_data["outcome"],
                        success_metrics=exp_data["success_metrics"],
                        lessons_learned=exp_data["lessons_learned"],
                        timestamp=datetime.fromisoformat(exp_data["timestamp"]),
                        tags=exp_data.get("tags", []),
                        similarity_vector=exp_data.get("similarity_vector")
                    )
                    self.experiences[experience.experience_id] = experience
                
                logger.info(f"Loaded {len(experiences_data)} experiences")
        
        except Exception as e:
            logger.warning(f"Could not load experiences: {e}")
    
    def _load_application_knowledge(self):
        """Load application knowledge from storage."""
        try:
            apps_file = self.kb_path.replace(".json", "_applications.json")
            if os.path.exists(apps_file):
                with open(apps_file, 'r') as f:
                    apps_data = json.load(f)
                
                for app_data in apps_data:
                    app_knowledge = ApplicationKnowledge(
                        app_name=app_data["app_name"],
                        interface_patterns=app_data["interface_patterns"],
                        common_actions=app_data["common_actions"],
                        success_rates=app_data["success_rates"],
                        learned_shortcuts=app_data["learned_shortcuts"],
                        ui_elements=app_data["ui_elements"],
                        last_updated=datetime.fromisoformat(app_data["last_updated"]),
                        usage_frequency=app_data.get("usage_frequency", 0)
                    )
                    self.application_knowledge[app_knowledge.app_name] = app_knowledge
                
                logger.info(f"Loaded knowledge for {len(apps_data)} applications")
        
        except Exception as e:
            logger.warning(f"Could not load application knowledge: {e}")
    
    def _load_user_preferences(self):
        """Load user preferences from storage."""
        try:
            prefs_file = self.kb_path.replace(".json", "_preferences.json")
            if os.path.exists(prefs_file):
                with open(prefs_file, 'r') as f:
                    prefs_data = json.load(f)
                
                for pref_data in prefs_data:
                    preference = UserPreference(
                        preference_id=pref_data["preference_id"],
                        category=pref_data["category"],
                        preference_data=pref_data["preference_data"],
                        confidence=pref_data["confidence"],
                        evidence_count=pref_data["evidence_count"],
                        last_updated=datetime.fromisoformat(pref_data["last_updated"])
                    )
                    self.user_preferences[preference.preference_id] = preference
                
                logger.info(f"Loaded {len(prefs_data)} user preferences")
        
        except Exception as e:
            logger.warning(f"Could not load user preferences: {e}")
    
    def _rebuild_indices(self):
        """Rebuild context and tag indices."""
        try:
            self.context_index.clear()
            self.tag_index.clear()
            
            for experience in self.experiences.values():
                self._update_context_index(experience)
                self._update_tag_index(experience)
            
            logger.debug("Rebuilt knowledge indices")
        
        except Exception as e:
            logger.error(f"Error rebuilding indices: {e}")
    
    def save_enhanced_knowledge(self) -> bool:
        """Save enhanced knowledge structures."""
        try:
            # Save experiences
            experiences_file = self.kb_path.replace(".json", "_experiences.json")
            experiences_data = []
            for experience in self.experiences.values():
                exp_dict = {
                    "experience_id": experience.experience_id,
                    "context": experience.context,
                    "actions_taken": experience.actions_taken,
                    "outcome": experience.outcome,
                    "success_metrics": experience.success_metrics,
                    "lessons_learned": experience.lessons_learned,
                    "timestamp": experience.timestamp.isoformat(),
                    "tags": experience.tags,
                    "similarity_vector": experience.similarity_vector
                }
                experiences_data.append(exp_dict)
            
            with open(experiences_file, 'w') as f:
                json.dump(experiences_data, f, indent=2)
            
            # Save application knowledge
            apps_file = self.kb_path.replace(".json", "_applications.json")
            apps_data = []
            for app_knowledge in self.application_knowledge.values():
                app_dict = {
                    "app_name": app_knowledge.app_name,
                    "interface_patterns": app_knowledge.interface_patterns,
                    "common_actions": app_knowledge.common_actions,
                    "success_rates": app_knowledge.success_rates,
                    "learned_shortcuts": app_knowledge.learned_shortcuts,
                    "ui_elements": app_knowledge.ui_elements,
                    "last_updated": app_knowledge.last_updated.isoformat(),
                    "usage_frequency": app_knowledge.usage_frequency
                }
                apps_data.append(app_dict)
            
            with open(apps_file, 'w') as f:
                json.dump(apps_data, f, indent=2)
            
            # Save user preferences
            prefs_file = self.kb_path.replace(".json", "_preferences.json")
            prefs_data = []
            for preference in self.user_preferences.values():
                pref_dict = {
                    "preference_id": preference.preference_id,
                    "category": preference.category,
                    "preference_data": preference.preference_data,
                    "confidence": preference.confidence,
                    "evidence_count": preference.evidence_count,
                    "last_updated": preference.last_updated.isoformat()
                }
                prefs_data.append(pref_dict)
            
            with open(prefs_file, 'w') as f:
                json.dump(prefs_data, f, indent=2)
            
            logger.info("Enhanced knowledge structures saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving enhanced knowledge: {e}")
            return False

    def _validate_ignore_description(self, description: str) -> bool:
        """Validates that an ignore description is suitable for filtering."""
        if not description or not isinstance(description, str):
            return False
        
        stripped = description.strip()
        if len(stripped) < 3:
            logger.warning(f"Ignore description too short: '{description}'")
            return False
            
        if len(stripped) > 200:
            logger.warning(f"Ignore description too long: '{description}'")
            return False
            
        return True
