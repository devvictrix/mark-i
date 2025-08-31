import logging
import json
from typing import Dict, Any, Optional, List, Callable

import numpy as np

from mark_i.knowledge.knowledge_base import KnowledgeBase
from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_REASONING
from mark_i.agent.toolbelt import Toolbelt
from mark_i.agent.world_model import WorldModel

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.agent_core")

REACT_PROMPT_TEMPLATE = """
You are Mark-I, an intelligent and autonomous AI agent that can control a computer desktop by seeing the screen and using a set of tools.

Your ultimate goal is: "{goal}"

You operate in a continuous loop of Thought -> Action -> Observation.
1.  **Thought:** You will receive a screenshot as the current 'Observation'. Your first step is to reason about the situation. Formulate a concise, high-level thought about what you should do *next* to progress towards the goal. Your thought process should be a "chain of thought," breaking down the problem.
2.  **Action:** Based on your thought, you must choose a single tool to execute from your `Toolbelt`. Your response must be a JSON object containing the chosen tool's name and its arguments.

**CRITICAL INSTRUCTIONS FOR ACCURACY:**
- **BE ROBUST:** Do not assume actions succeed instantly. UIs can be slow.
- **VERIFY YOUR ACTIONS:** When you click something, you should usually verify the result. Use the `expected_outcome_description` parameter in the `click_element` tool.
- **SYNCHRONIZE:** If you need to wait for something to load or a process to finish, use the `wait_for_visual_cue` tool instead of guessing with a fixed delay. A good pattern is: `click_element` -> `wait_for_visual_cue`.

**AVAILABLE TOOLS (`Toolbelt`):**
{tools_description}
- Tool Name: `finish_task`
  Description: Use this tool ONLY when you have visually verified that the user's final goal has been fully and successfully achieved. Argument `final_summary` (string) is a brief summary of what you accomplished.

**HISTORY (Previous steps in this task):**
{history}

**CURRENT OBSERVATION:**
(See the attached screenshot of the current desktop state.)

**YOUR TASK:**
Based on the goal, history, and the current screen observation, generate your next Thought and Action.
Your response MUST be a single, valid JSON object with two keys: "thought" and "action".
The "action" value must be another JSON object with "tool_name" and "tool_args" keys.

Example of a robust, two-step thought process:
Step 1 Thought: "The goal is to save the document. I see the 'File' menu. I will click it to open the menu options. I expect to see a 'Save As...' option appear afterwards."
Step 1 Action: `{{"tool_name": "click_element", "tool_args": {{"element_description": "the 'File' menu button", "expected_outcome_description": "A dropdown menu containing a 'Save As...' option is visible."}}}}`
---
Step 2 Thought: "My click was successful and I see the 'Save As...' option. Now I need to wait for the 'Save As' dialog to fully appear after I click it."
Step 2 Action: `{{"tool_name": "click_element", "tool_args": {{"element_description": "the 'Save As...' menu item", "expected_outcome_description": "A dialog box with the title 'Save As' is visible."}}}}`

Now, provide your JSON response for the next step.
"""


class AgentCore:
    """
    Implements the ReAct (Reason+Act) agent architecture.
    This is the central "brain" of the v11 Cognitive Core, replacing the
    previous StrategicExecutor.
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        capture_engine: CaptureEngine,
        gemini_analyzer: GeminiAnalyzer,
        toolbelt: Toolbelt,
        status_update_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.knowledge_base = knowledge_base
        self.capture_engine = capture_engine
        self.gemini_analyzer = gemini_analyzer
        self.toolbelt = toolbelt
        self.status_update_callback = status_update_callback
        logger.info("AgentCore (v11 Cognitive Core) initialized.")

    def _send_status_update(self, update_type: str, data: Dict[str, Any]):
        if self.status_update_callback:
            try:
                self.status_update_callback({"type": update_type, "data": data})
            except Exception as e:
                logger.error(f"Error in AgentCore status_update_callback: {e}", exc_info=True)

    def _capture_observation(self) -> Optional[np.ndarray]:
        if self.capture_engine:
            return self.capture_engine.capture_region(
                {"name": "agent_observation_capture", "x": 0, "y": 0, "width": self.capture_engine.get_primary_screen_width(), "height": self.capture_engine.get_primary_screen_height()}
            )
        return None

    def execute_goal(self, goal: str, max_steps: int = 15) -> Dict[str, Any]:
        logger.info(f"--- AgentCore Execution Started for goal: '{goal}' ---")
        self._send_status_update("task_start", {"command": goal})

        world_model = WorldModel(initial_goal=goal)
        tools_description = self.toolbelt.get_tools_description()

        for step in range(max_steps):
            logger.info(f"AgentCore: Starting ReAct Step {step + 1}/{max_steps}")

            history_for_prompt = world_model.format_history_for_prompt()
            prompt = REACT_PROMPT_TEMPLATE.format(goal=goal, tools_description=tools_description, history=history_for_prompt)

            observation_image = self._capture_observation()
            if observation_image is None:
                final_message = "Failed to capture screen observation."
                self._send_status_update("task_end", {"status": "failure", "message": final_message})
                return {"status": "failure", "message": final_message}

            self._send_status_update("tactic_before_image", {"image_np": observation_image})

            # v12.0.5 FIX: Use `model_preference` instead of `model_name_override`
            llm_response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=observation_image, model_preference=MODEL_PREFERENCE_REASONING)

            if llm_response["status"] != "success" or not llm_response.get("json_content"):
                final_message = f"AI reasoning failed. Status: {llm_response['status']}, Error: {llm_response.get('error_message')}"
                self._send_status_update("task_end", {"status": "failure", "message": final_message})
                return {"status": "failure", "message": final_message}

            try:
                parsed_response = llm_response["json_content"]
                thought = parsed_response.get("thought", "No thought provided.")
                action_data = parsed_response.get("action", {})
                tool_name = action_data.get("tool_name")
                tool_args = action_data.get("tool_args", {})
            except Exception as e:
                final_message = f"Failed to parse AI's thought/action response. Error: {e}"
                self._send_status_update("task_end", {"status": "failure", "message": final_message})
                return {"status": "failure", "message": final_message}

            self._send_status_update("agent_thought", {"thought": thought, "action": f"{tool_name}({tool_args})"})

            if tool_name == "finish_task":
                final_message = f"Task completed successfully. AI summary: {tool_args.get('final_summary', 'No summary.')}"
                self._send_status_update("task_end", {"status": "success", "message": final_message})
                return {"status": "success", "message": final_message}

            observation_result = self.toolbelt.execute_tool(tool_name, tool_args)
            world_model.add_entry(thought, f"{tool_name}({json.dumps(tool_args)})", observation_result)

            self._send_status_update("tactic_after_image", {"observation_text": observation_result})

        final_message = "Task failed: Maximum number of steps reached."
        self._send_status_update("task_end", {"status": "failure", "message": final_message})
        return {"status": "failure", "message": final_message}
