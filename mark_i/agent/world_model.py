import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.world_model")

# Entity analysis prompt template with perceptual filtering
ENTITY_ANALYSIS_PROMPT_WITH_FILTERING = """
Analyze the provided screenshot and identify all interactive UI elements, buttons, text fields, and other interface components.

IMPORTANT: Ignore any elements that match these descriptions:
{ignore_list_formatted}

For each relevant element you find, provide:
1. Element type (button, text_field, label, etc.)
2. Descriptive text or label
3. Approximate bounding box coordinates
4. Current state (enabled/disabled, focused/unfocused, etc.)

Do not include any elements that match the ignore list descriptions above.

Respond with a JSON array of detected elements in this format:
[
  {{
    "type": "button",
    "text": "Login",
    "box": [x, y, width, height],
    "state": "enabled",
    "found": true
  }}
]
"""

# Standard entity analysis prompt (without filtering)
ENTITY_ANALYSIS_PROMPT = """
Analyze the provided screenshot and identify all interactive UI elements, buttons, text fields, and other interface components.

For each element you find, provide:
1. Element type (button, text_field, label, etc.)
2. Descriptive text or label
3. Approximate bounding box coordinates
4. Current state (enabled/disabled, focused/unfocused, etc.)

Respond with a JSON array of detected elements in this format:
[
  {{
    "type": "button",
    "text": "Login",
    "box": [x, y, width, height],
    "state": "enabled",
    "found": true
  }}
]
"""

class WorldModel:
    """
    Manages the agent's short-term memory for a single task.
    v12 Update: Now includes a structured list of perceived UI entities and a
    high-level list of "Intentions".
    """

    def __init__(self, initial_goal: str):
        self.goal = initial_goal
        self.intentions: List[str] = []
        self.current_intention_index: int = 0
        
        # The history is a list of (Thought, Action, Observation) tuples
        self.history: List[Tuple[str, str, str]] = []
        
        # v12: The structured understanding of the current screen
        self.entities: List[Dict[str, Any]] = []
        
        logger.info(f"WorldModel initialized for goal: '{initial_goal}'")

    def get_current_intention(self) -> str:
        """Returns the current high-level intention the agent is focused on."""
        if self.intentions and 0 <= self.current_intention_index < len(self.intentions):
            return self.intentions[self.current_intention_index]
        return self.goal # Fallback to the main goal if no intentions are set

    def advance_to_next_intention(self) -> bool:
        """
        Advances the focus to the next intention in the list.
        Returns True if successful, False if it was the last intention.
        """
        if self.current_intention_index < len(self.intentions) - 1:
            self.current_intention_index += 1
            # Clear history when moving to a new intention to keep prompts focused
            self.history.clear() 
            logger.info(f"Advanced to next intention ({self.current_intention_index + 1}/{len(self.intentions)}): '{self.get_current_intention()}'")
            return True
        logger.info("Reached the final intention.")
        return False

    def add_entry(self, thought: str, action: str, observation: str):
        """Adds a new Thought-Action-Observation cycle to the history."""
        if not all(isinstance(arg, str) for arg in [thought, action, observation]):
            logger.warning("Attempted to add non-string entry to WorldModel history. Entry skipped.")
            return
            
        self.history.append((thought, action, observation))
        logger.debug(f"WorldModel entry added. Thought: {thought[:50]}... Action: {action[:50]}...")

    def format_history_for_prompt(self) -> str:
        """
        Formats the entire history for the current intention into a single string
        for injection into the main ReAct prompt.
        """
        if not self.history:
            return "This is the first step for the current intention. Begin by analyzing the observation and forming a thought."

        formatted_string = ""
        for thought, action, observation in self.history:
            formatted_string += f"Thought: {thought}\n"
            formatted_string += f"Action: {action}\n"
            formatted_string += f"Observation: {observation}\n"
        
        return formatted_string

    def get_full_transcript(self) -> str:
        """Returns a human-readable transcript of the entire task execution."""
        transcript = f"Overall Goal: {self.goal}\n"
        transcript += "====================\n"
        transcript += "Intentions:\n"
        for i, intention in enumerate(self.intentions):
            transcript += f"  {i+1}. {intention}\n"
        transcript += "====================\n\n"
        
        # Note: This part would need to be enhanced if we want to show history for *all* intentions,
        # as the history is currently cleared between intentions.
        transcript += f"Executing Intention #{self.current_intention_index + 1}: {self.get_current_intention()}\n"
        transcript += "--------------------\n"
        for i, (thought, action, observation) in enumerate(self.history):
            transcript += f"Step {i+1}\n"
            transcript += f"Thought: {thought}\n"
            transcript += f"Action: {action}\n"
            transcript += f"Observation: {observation}\n"
            transcript += "--------------------\n"
        return transcript

    def update_entities(self, screenshot: np.ndarray, ignore_list: Optional[List[str]] = None, gemini_analyzer=None) -> List[Dict[str, Any]]:
        """
        Updates the current understanding of UI entities, applying perceptual filtering.
        
        Args:
            screenshot: Current screen capture as numpy array
            ignore_list: List of element descriptions to ignore during analysis
            gemini_analyzer: GeminiAnalyzer instance for vision analysis
            
        Returns:
            Filtered list of detected entities
        """
        if gemini_analyzer is None:
            logger.warning("No GeminiAnalyzer provided to update_entities. Returning empty entity list.")
            return []
            
        try:
            # Choose prompt based on whether we have an ignore list
            if ignore_list and len(ignore_list) > 0:
                # Format ignore list for the prompt
                ignore_list_formatted = "\n".join([f"- {item}" for item in ignore_list])
                prompt = ENTITY_ANALYSIS_PROMPT_WITH_FILTERING.format(ignore_list_formatted=ignore_list_formatted)
                logger.info(f"Analyzing entities with {len(ignore_list)} items in ignore list")
            else:
                prompt = ENTITY_ANALYSIS_PROMPT
                logger.info("Analyzing entities without filtering")
            
            # Query the vision model
            from mark_i.core.app_config import MODEL_PREFERENCE_FAST
            response = gemini_analyzer.query_vision_model(
                prompt=prompt,
                image_data=screenshot,
                model_preference=MODEL_PREFERENCE_FAST
            )
            
            if response["status"] == "success" and response.get("json_content"):
                entities = response["json_content"]
                if isinstance(entities, list):
                    # Filter out invalid entities
                    valid_entities = []
                    for entity in entities:
                        if isinstance(entity, dict) and entity.get("found", False):
                            valid_entities.append(entity)
                    
                    self.entities = valid_entities
                    logger.info(f"Updated WorldModel with {len(valid_entities)} entities")
                    
                    if ignore_list:
                        filtered_count = len(entities) - len(valid_entities)
                        logger.info(f"Perceptual filtering removed {filtered_count} entities")
                    
                    return valid_entities
                else:
                    logger.warning("Entity analysis returned non-list result")
                    return []
            else:
                logger.warning(f"Entity analysis failed: {response.get('error_message', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error updating entities: {e}", exc_info=True)
            return []