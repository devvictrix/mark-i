import logging
import json
import os
from typing import Dict, Any, Optional, List
import copy
from datetime import datetime, timezone

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.knowledge.knowledge_base")

DEFAULT_KNOWLEDGE_BASE_FILENAME = "knowledge_base.json"
MAX_STRATEGIES_PER_OBJECTIVE = 5  # Prevents knowledge base from growing indefinitely


class KnowledgeBase:
    """
    Manages loading, accessing, and saving the user's knowledge base.
    v18.0 Update: Now manages perceptual filters.
    """

    def __init__(self, project_root: str):
        self.kb_path = os.path.join(project_root, DEFAULT_KNOWLEDGE_BASE_FILENAME)
        self.knowledge_data: Dict[str, Any] = {}
        self.load_knowledge()

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

        return self.save_knowledge_base()

    ## V18 OPTIMIZATION START ##
    def get_perceptual_ignore_list(self) -> List[str]:
        """Returns the list of item descriptions to be ignored during perception."""
        filters = self.knowledge_data.get("perceptual_filters", {})
        return filters.get("ignore_list", [])

    def add_to_perceptual_ignore_list(self, item_description: str) -> bool:
        """Adds a new item description to the perceptual ignore list and saves."""
        if not item_description or not isinstance(item_description, str):
            return False

        filters = self.knowledge_data.setdefault("perceptual_filters", {})
        ignore_list = filters.setdefault("ignore_list", [])

        if item_description not in ignore_list:
            ignore_list.append(item_description)
            logger.info(f"Added '{item_description}' to perceptual ignore list.")
            return self.save_knowledge_base()

        logger.debug(f"'{item_description}' already in perceptual ignore list.")
        return True  # It's already there, so the state is correct.
