import logging
import time
from typing import Any, Callable, Optional

import numpy as np

from mark_i.agent.tools.base import BaseTool
from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_FAST
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.tools.synchronization")

class WaitForVisualCueTool(BaseTool):
    """
    A tool that intelligently waits for a specific visual cue to appear on the screen.
    This is critical for synchronizing the AI's actions with the application's state.
    """
    name = "wait_for_visual_cue"
    description = (
        "Pauses execution and repeatedly checks the screen until a specific visual cue is observed or a timeout is reached. "
        "Use this to wait for applications to load, progress bars to finish, or confirmation messages to appear. "
        "Argument `cue_description` (string) is a clear, textual description of the visual element or state to wait for (e.g., 'the main dashboard is visible', 'a dialog box with the text Save Complete'). "
        "Argument `timeout_seconds` (float, default: 10.0) is the maximum time to wait."
    )

    def __init__(self, gemini_analyzer: GeminiAnalyzer, capture_engine_func: Callable[[], Optional[np.ndarray]]):
        self.gemini_analyzer = gemini_analyzer
        self.get_screenshot = capture_engine_func
        self.check_interval_seconds = 0.75 # How often to check the screen

    def _check_for_cue(self, cue_description: str) -> bool:
        """Performs a single visual check for the cue."""
        screenshot = self.get_screenshot()
        if screenshot is None:
            logger.warning("WaitForVisualCueTool: Failed to capture screen during check.")
            return False

        prompt = f"Based on the provided image, is this condition true or false? Condition: \"{cue_description}\". Respond ONLY with the single word 'true' or 'false'."
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=screenshot, model_preference=MODEL_PREFERENCE_FAST)

        if response["status"] == "success" and response["text_content"]:
            return response["text_content"].strip().lower() == "true"
        
        logger.warning(f"WaitForVisualCueTool: AI check for cue '{cue_description}' failed. Status: {response['status']}")
        return False

    def execute(self, cue_description: str = "", timeout_seconds: float = 10.0, **kwargs: Any) -> str:
        if not cue_description:
            return "Error: `cue_description` parameter cannot be empty."
        
        start_time = time.time()
        logger.info(f"Tool 'wait_for_visual_cue' started. Waiting for '{cue_description}' for up to {timeout_seconds}s.")
        
        while time.time() - start_time < timeout_seconds:
            if self._check_for_cue(cue_description):
                logger.info(f"Tool 'wait_for_visual_cue': Cue '{cue_description}' was observed successfully.")
                return f"Success: The visual cue '{cue_description}' was observed."
            
            time.sleep(self.check_interval_seconds)

        logger.warning(f"Tool 'wait_for_visual_cue': Timed out after {timeout_seconds}s waiting for '{cue_description}'.")
        return f"Error: Timed out after {timeout_seconds} seconds. The visual cue '{cue_description}' was not observed."
