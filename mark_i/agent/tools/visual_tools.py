import logging
from typing import Any, Dict, Callable, Optional

import numpy as np

from mark_i.agent.tools.base import BaseTool
from mark_i.agent.tools.synchronization_tools import WaitForVisualCueTool
from mark_i.engines.action_executor import ActionExecutor
from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_FAST
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.tools.visual")


class ClickElementTool(BaseTool):
    """A tool for visually identifying and clicking a UI element, with closed-loop verification."""

    name = "click_element"
    description = (
        "Visually identifies a UI element and clicks it. Can optionally wait for a visual confirmation that the click had the desired effect. "
        "Argument `element_description` (string) is a clear description of the target element (e.g., 'the login button'). "
        "Argument `expected_outcome_description` (string, optional) is a description of the visual state the screen should be in *after* the click is successful (e.g., 'the user dashboard is visible'). If provided, the tool will wait and verify this outcome."
    )

    def __init__(self, action_executor: ActionExecutor, gemini_analyzer: GeminiAnalyzer, capture_engine_func: Callable[[], Optional[np.ndarray]], verification_tool: WaitForVisualCueTool):
        self.action_executor = action_executor
        self.gemini_analyzer = gemini_analyzer
        self.get_screenshot = capture_engine_func
        self.verification_tool = verification_tool

    def _refine_target_to_bbox(self, description: str, image: np.ndarray) -> Optional[Dict[str, Any]]:
        prompt = f'In the image, find the element best described as: "{description}". Respond ONLY with JSON: {{"found": true, "box": [x,y,w,h]}}.'
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=image, model_preference=MODEL_PREFERENCE_FAST)
        if response["status"] == "success" and response.get("json_content"):
            data = response["json_content"]
            if data.get("found") and isinstance(data.get("box"), list) and len(data["box"]) == 4:
                return {"value": {"box": data["box"], "found": True, "element_label": description}, "_source_region_for_capture_": "fullscreen"}
        return None

    def execute(self, element_description: str = "", expected_outcome_description: Optional[str] = None, **kwargs: Any) -> str:
        if not element_description:
            return "Error: `element_description` parameter is missing."

        screenshot = self.get_screenshot()
        if screenshot is None:
            return "Error: Could not capture screen to find element."

        refined_target = self._refine_target_to_bbox(element_description, screenshot)
        if not refined_target:
            return f"Error: Could not visually locate the element described as '{element_description}' on the screen."

        context = {
            "rule_name": "AgentTool_Click",
            "variables": {"agent_target": refined_target},
            "fullscreen_region_config": {"x": 0, "y": 0, "width": screenshot.shape, "height": screenshot.shape},
        }

        try:
            self.action_executor.execute_action({"type": "click", "target_relation": "center_of_gemini_element", "gemini_element_variable": "agent_target", "context": context})
            logger.info(f"Successfully performed physical click on element described as '{element_description}'.")
        except Exception as e:
            return f"Error: A system error occurred while trying to click '{element_description}': {e}"

        # --- Closed-Loop Verification Step ---
        if expected_outcome_description:
            logger.info(f"Performing closed-loop verification. Expecting to see: '{expected_outcome_description}'")
            verification_result = self.verification_tool.execute(cue_description=expected_outcome_description, timeout_seconds=7.0)
            if "Success" in verification_result:
                return f"Successfully clicked '{element_description}' and verified the outcome: '{expected_outcome_description}'."
            else:
                return f"Error: Clicked '{element_description}', but failed to verify the outcome. Verification tool reported: '{verification_result}'"
        
        return f"Successfully clicked the element described as '{element_description}' (no verification requested)."


class TypeTextTool(BaseTool):
    """A tool for typing text into the currently focused UI element."""

    name = "type_text"
    description = "Types a given string of text using the keyboard. This is used after clicking on a text field. " "Argument `text_to_type` (string) is the text that should be typed."

    def __init__(self, action_executor: ActionExecutor):
        self.action_executor = action_executor

    def execute(self, text_to_type: str = "", **kwargs: Any) -> str:
        if not isinstance(text_to_type, str):
            return "Error: `text_to_type` must be a string."

        try:
            self.action_executor.execute_action({"type": "type_text", "text": text_to_type, "context": {"rule_name": "AgentTool_TypeText"}})
            log_text = text_to_type[:30] + "..." if len(text_to_type) > 30 else text_to_type
            return f"Successfully typed the text: '{log_text}'."
        except Exception as e:
            return f"Error: A system error occurred while typing: {e}"
