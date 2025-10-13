"""
World Model for MARK-I hierarchical AI architecture.

This module provides the WorldModel component that tracks world state and entities,
implementing the IWorldModel interface.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

import numpy as np

from mark_i.core.base_component import BaseComponent
from mark_i.core.interfaces import IWorldModel, Observation, Action
from mark_i.core.architecture_config import ComponentConfig


class WorldModel(BaseComponent, IWorldModel):
    """
    Manages world state tracking and entity modeling.
    
    Maintains a representation of the current environment state,
    tracks entities, and predicts state changes from actions.
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize the WorldModel."""
        super().__init__("world_model", config)
        
        # World state tracking
        self.current_state: Dict[str, Any] = {}
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.state_history: List[Dict[str, Any]] = []
        
        # Entity tracking
        self.entity_counter = 0
        self.entity_relationships: Dict[str, List[str]] = {}
        
        # State prediction
        self.action_effects: Dict[str, Dict[str, Any]] = {}
        
    def _initialize_component(self) -> bool:
        """Initialize the WorldModel component."""
        try:
            # Initialize default state
            self.current_state = {
                "timestamp": datetime.now().isoformat(),
                "screen_state": None,
                "active_applications": [],
                "user_activity": None,
                "system_metrics": {},
                "ui_elements": [],
                "focus_target": None,
            }
            
            self.logger.info("WorldModel initialized with default state")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WorldModel: {e}")
            return False
    
    def update_state(self, observation: Observation) -> None:
        """Update world state with new observation."""
        try:
            # Store previous state in history
            if self.current_state:
                self.state_history.append(self.current_state.copy())
                
                # Limit history size
                max_history = getattr(self.config, 'max_history_size', 100)
                if len(self.state_history) > max_history:
                    self.state_history = self.state_history[-max_history:]
            
            # Update current state based on observation
            self.current_state["timestamp"] = observation.timestamp.isoformat()
            self.current_state["last_observation_source"] = observation.source
            
            # Process observation data based on source
            if observation.source == "screen_capture":
                self._update_screen_state(observation.data)
            elif observation.source == "ui_analysis":
                self._update_ui_elements(observation.data)
            elif observation.source == "system_monitor":
                self._update_system_metrics(observation.data)
            elif observation.source == "user_activity":
                self._update_user_activity(observation.data)
            else:
                # Generic data update
                if isinstance(observation.data, dict):
                    self.current_state.update(observation.data)
            
            self.logger.debug(f"World state updated from {observation.source}")
            
            # Notify observers of state change
            self._notify_observers({
                'type': 'state_updated',
                'source': observation.source,
                'timestamp': observation.timestamp.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to update world state: {e}")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current world state."""
        return self.current_state.copy()
    
    def predict_state_change(self, action: Action) -> Dict[str, Any]:
        """Predict how an action will change the world state."""
        try:
            prediction = {
                "action": action.name,
                "parameters": action.parameters,
                "predicted_changes": {},
                "confidence": action.confidence,
                "timestamp": datetime.now().isoformat()
            }
            
            # Use learned action effects if available
            if action.name in self.action_effects:
                effects = self.action_effects[action.name]
                prediction["predicted_changes"] = effects.get("typical_changes", {})
                prediction["confidence"] *= effects.get("reliability", 1.0)
            
            # Action-specific predictions
            if action.name == "click":
                prediction["predicted_changes"].update(self._predict_click_effects(action))
            elif action.name == "type_text":
                prediction["predicted_changes"].update(self._predict_text_input_effects(action))
            elif action.name == "key_press":
                prediction["predicted_changes"].update(self._predict_key_press_effects(action))
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"Failed to predict state change: {e}")
            return {"error": str(e)}
    
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get all tracked entities in the world."""
        return list(self.entities.values())
    
    def add_entity(self, entity: Dict[str, Any]) -> None:
        """Add a new entity to track."""
        try:
            # Generate unique ID if not provided
            entity_id = entity.get("id")
            if not entity_id:
                self.entity_counter += 1
                entity_id = f"entity_{self.entity_counter}"
                entity["id"] = entity_id
            
            # Add metadata
            entity["created_at"] = datetime.now().isoformat()
            entity["last_updated"] = entity["created_at"]
            
            # Store entity
            self.entities[entity_id] = entity
            
            # Initialize relationships
            self.entity_relationships[entity_id] = []
            
            self.logger.debug(f"Added entity: {entity_id}")
            
            # Notify observers
            self._notify_observers({
                'type': 'entity_added',
                'entity_id': entity_id,
                'entity_type': entity.get('type', 'unknown')
            })
            
        except Exception as e:
            self.logger.error(f"Failed to add entity: {e}")
    
    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from tracking."""
        try:
            if entity_id in self.entities:
                # Remove entity
                entity = self.entities.pop(entity_id)
                
                # Remove relationships
                self.entity_relationships.pop(entity_id, None)
                
                # Remove references from other entities
                for other_id, relationships in self.entity_relationships.items():
                    if entity_id in relationships:
                        relationships.remove(entity_id)
                
                self.logger.debug(f"Removed entity: {entity_id}")
                
                # Notify observers
                self._notify_observers({
                    'type': 'entity_removed',
                    'entity_id': entity_id,
                    'entity_type': entity.get('type', 'unknown')
                })
            else:
                self.logger.warning(f"Entity {entity_id} not found for removal")
                
        except Exception as e:
            self.logger.error(f"Failed to remove entity {entity_id}: {e}")
    
    def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> None:
        """Update an existing entity."""
        try:
            if entity_id in self.entities:
                self.entities[entity_id].update(updates)
                self.entities[entity_id]["last_updated"] = datetime.now().isoformat()
                
                self.logger.debug(f"Updated entity: {entity_id}")
                
                # Notify observers
                self._notify_observers({
                    'type': 'entity_updated',
                    'entity_id': entity_id,
                    'updates': list(updates.keys())
                })
            else:
                self.logger.warning(f"Entity {entity_id} not found for update")
                
        except Exception as e:
            self.logger.error(f"Failed to update entity {entity_id}: {e}")
    
    def find_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Find entities by type."""
        return [entity for entity in self.entities.values() 
                if entity.get('type') == entity_type]
    
    def find_entities_by_property(self, property_name: str, property_value: Any) -> List[Dict[str, Any]]:
        """Find entities by property value."""
        return [entity for entity in self.entities.values() 
                if entity.get(property_name) == property_value]
    
    def add_entity_relationship(self, entity_id1: str, entity_id2: str, relationship_type: str = "related") -> None:
        """Add a relationship between two entities."""
        try:
            if entity_id1 in self.entities and entity_id2 in self.entities:
                # Add bidirectional relationship
                if entity_id2 not in self.entity_relationships.get(entity_id1, []):
                    self.entity_relationships.setdefault(entity_id1, []).append(entity_id2)
                if entity_id1 not in self.entity_relationships.get(entity_id2, []):
                    self.entity_relationships.setdefault(entity_id2, []).append(entity_id1)
                
                self.logger.debug(f"Added relationship: {entity_id1} <-> {entity_id2}")
            else:
                self.logger.warning(f"Cannot add relationship: one or both entities not found")
                
        except Exception as e:
            self.logger.error(f"Failed to add entity relationship: {e}")
    
    def get_entity_relationships(self, entity_id: str) -> List[str]:
        """Get relationships for an entity."""
        return self.entity_relationships.get(entity_id, [])
    
    def _update_screen_state(self, screen_data: Any) -> None:
        """Update screen state from observation."""
        if isinstance(screen_data, np.ndarray):
            self.current_state["screen_state"] = {
                "shape": screen_data.shape,
                "dtype": str(screen_data.dtype),
                "timestamp": datetime.now().isoformat()
            }
        else:
            self.current_state["screen_state"] = screen_data
    
    def _update_ui_elements(self, ui_data: Any) -> None:
        """Update UI elements from observation."""
        if isinstance(ui_data, list):
            self.current_state["ui_elements"] = ui_data
            
            # Update entities with UI elements
            for element in ui_data:
                if isinstance(element, dict) and element.get("found"):
                    element_id = f"ui_{element.get('type', 'unknown')}_{hash(str(element))}"
                    element["id"] = element_id
                    element["category"] = "ui_element"
                    self.entities[element_id] = element
    
    def _update_system_metrics(self, metrics_data: Any) -> None:
        """Update system metrics from observation."""
        if isinstance(metrics_data, dict):
            self.current_state["system_metrics"] = metrics_data
    
    def _update_user_activity(self, activity_data: Any) -> None:
        """Update user activity from observation."""
        self.current_state["user_activity"] = activity_data
    
    def _predict_click_effects(self, action: Action) -> Dict[str, Any]:
        """Predict effects of a click action."""
        effects = {}
        
        # Get click coordinates
        x = action.parameters.get("x")
        y = action.parameters.get("y")
        
        if x is not None and y is not None:
            # Find entities at click location
            clicked_entities = self._find_entities_at_location(x, y)
            
            if clicked_entities:
                effects["clicked_entities"] = [e.get("id") for e in clicked_entities]
                
                # Predict based on entity types
                for entity in clicked_entities:
                    entity_type = entity.get("type")
                    if entity_type == "button":
                        effects["expected_action"] = "button_activation"
                    elif entity_type == "text_field":
                        effects["expected_action"] = "text_field_focus"
                    elif entity_type == "link":
                        effects["expected_action"] = "navigation"
        
        return effects
    
    def _predict_text_input_effects(self, action: Action) -> Dict[str, Any]:
        """Predict effects of text input action."""
        text = action.parameters.get("text", "")
        
        return {
            "text_length": len(text),
            "expected_action": "text_input",
            "input_type": "keyboard"
        }
    
    def _predict_key_press_effects(self, action: Action) -> Dict[str, Any]:
        """Predict effects of key press action."""
        key = action.parameters.get("key", "")
        
        effects = {"key_pressed": key}
        
        # Special key predictions
        if key.lower() in ["enter", "return"]:
            effects["expected_action"] = "form_submission_or_confirmation"
        elif key.lower() == "escape":
            effects["expected_action"] = "cancel_or_close"
        elif key.lower() == "tab":
            effects["expected_action"] = "focus_change"
        elif "ctrl+" in key.lower():
            effects["expected_action"] = "shortcut_activation"
        
        return effects
    
    def _find_entities_at_location(self, x: int, y: int) -> List[Dict[str, Any]]:
        """Find entities at a specific screen location."""
        matching_entities = []
        
        for entity in self.entities.values():
            box = entity.get("box")
            if isinstance(box, list) and len(box) == 4:
                ex, ey, ew, eh = box
                if ex <= x <= ex + ew and ey <= y <= ey + eh:
                    matching_entities.append(entity)
        
        return matching_entities
    
    def learn_action_effects(self, action: Action, actual_effects: Dict[str, Any]) -> None:
        """Learn from actual action effects to improve predictions."""
        try:
            action_name = action.name
            
            if action_name not in self.action_effects:
                self.action_effects[action_name] = {
                    "typical_changes": {},
                    "reliability": 1.0,
                    "sample_count": 0
                }
            
            effects_data = self.action_effects[action_name]
            effects_data["sample_count"] += 1
            
            # Update typical changes (simple averaging for now)
            for key, value in actual_effects.items():
                if key in effects_data["typical_changes"]:
                    # Simple moving average
                    current = effects_data["typical_changes"][key]
                    if isinstance(current, (int, float)) and isinstance(value, (int, float)):
                        effects_data["typical_changes"][key] = (current + value) / 2
                else:
                    effects_data["typical_changes"][key] = value
            
            self.logger.debug(f"Learned effects for action {action_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn action effects: {e}")
    
    def get_state_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent state history."""
        return self.state_history[-limit:] if limit > 0 else self.state_history
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get WorldModel-specific status."""
        return {
            "total_entities": len(self.entities),
            "entity_types": self._get_entity_type_counts(),
            "state_history_size": len(self.state_history),
            "learned_actions": len(self.action_effects),
            "current_state_keys": list(self.current_state.keys()),
        }
    
    def _get_entity_type_counts(self) -> Dict[str, int]:
        """Get count of entities by type."""
        type_counts = {}
        
        for entity in self.entities.values():
            entity_type = entity.get('type', 'unknown')
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        return type_counts