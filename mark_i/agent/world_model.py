import logging
from typing import List, Dict, Any, Tuple

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.world_model")

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