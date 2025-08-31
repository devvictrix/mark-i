import logging
import json
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone

import numpy as np

from mark_i.knowledge.knowledge_base import KnowledgeBase
from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.engines.gemini_decision_module import GeminiDecisionModule
from mark_i.generation.strategy_planner import IntermediatePlan

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.execution.strategic_executor")

OBJECTIVE_MATCHING_MODEL = "gemini-1.5-flash-latest"
STRATEGIC_PLANNING_MODEL = "gemini-1.5-pro-latest"
STRATEGIC_CORRECTION_MODEL = "gemini-1.5-pro-latest"
CONTEXTUAL_STRATEGY_SELECTION_MODEL = "gemini-1.5-flash-latest"
VERIFICATION_MODEL = "gemini-1.5-flash-latest"

SUCCESS_LEARNING_RATE = 0.1
FAILURE_DECAY_RATE = 0.75
NEW_STRATEGY_DEFAULT_SUCCESS_RATE = 0.9

OBJECTIVE_MATCHING_PROMPT = """
You are a command matching system. Find the best 'Objective' match for the user's command.
Respond ONLY with the exact `objective_name` from the list. If no objective is a clear match, respond with `None`.

**Available Objectives:**
```json
{objectives_json}
```

User Command: "{user_command}"
"""

CONTEXTUAL_STRATEGY_SELECTION_PROMPT = """
You are a strategic decision-making AI. Your goal is to select the best strategy to execute based on the current visual context of the screen.

**User Goal:** "{user_command}"

**Available Strategies (proven to work in the past):**
```json
{strategies_summary_json}
```

**Your Task:**
Analyze the attached screenshot. Based on what you currently see on the screen, which of the available strategies is the most appropriate and efficient to use right now? For example, a hotkey-based strategy is better if the main application window is in focus, while a menu-clicking strategy might be better if a dialog box is open.

Respond ONLY with a single JSON object containing the `strategy_name` of your chosen strategy.
Example: `{{"chosen_strategy_name": "Standard Report Strategy v2"}}`
"""

STRATEGIC_PLANNER_PROMPT_TEMPLATE = """
You are the strategic execution core for Mark-I, a visual automation AI.
You have access to a user-provided Knowledge Base and have been given a direct command from the user.
Your primary task is to create a high-level, multi-step strategic plan to accomplish the command.

CRITICAL CONTEXT: Your Knowledge Base
```json
{knowledge_base_json}
```

User Command: "{user_command}"
Your Task:
Based on the user command and knowledge base, generate a sequence of logical, high-level sub-goals. Each sub-goal should be a clear, tactical command that can be handed off to another AI agent (the GeminiDecisionModule) that can see the screen and execute simple actions.
 - If the command involves an application, the first step should ALWAYS be to ensure that application is open and active.
 - For each tactical goal, you MUST also provide an `expected_outcome_description`. This is a clear, verifiable visual state that should exist *after* the tactic is performed.
 - Use information from the knowledge base to resolve aliases (e.g., "my wife" -> "Big Boss").

Respond ONLY with a single JSON object with the following structure:
{{
  "strategic_plan": [
    {{
      "tactical_goal": "Your first sub-goal here.",
      "expected_outcome_description": "A description of what the screen should look like after this step."
    }},
    {{
      "tactical_goal": "Your second sub-goal here.",
      "expected_outcome_description": "The expected visual state after the second step."
    }}
  ]
}}
"""

STRATEGIC_CORRECTION_PROMPT_TEMPLATE = """
You are a strategic self-correction core for Mark-I, a visual automation AI.
An automation plan has failed. Your task is to analyze the failure context and generate a NEW, corrected strategic plan to achieve the original user goal from the current screen state.

**Original User Goal:** "{user_command}"

**Original Plan (Remaining Steps):**
```json
{original_plan_json}
```

**FAILURE ANALYSIS:**
- **Failed Tactic:** "{failed_tactic}"
- **Expected Outcome:** "{expected_outcome}"
- **Current Screen State:** (See attached image) The expected outcome was NOT met. The image shows the screen *after* the failed action.

**Your Task:**
Analyze the current screen state in the attached image. Based on what you see, create a brand-new sequence of tactical goals to recover from this failure and successfully complete the original user goal. The new plan might involve closing an unexpected dialog, retrying the failed step differently, or taking an entirely new approach.

Respond ONLY with a single JSON object with the same structure as before:
{{
  "strategic_plan": [
    {{
      "tactical_goal": "Your first RECOVERY sub-goal here.",
      "expected_outcome_description": "The expected visual state after this recovery step."
    }},
    {{
      "tactical_goal": "Your next sub-goal...",
      "expected_outcome_description": "..."
    }}
  ]
}}
"""


class StrategicExecutor:
    """
    Orchestrates complex commands using the OST pattern.
    v14.1 Update: Manages multiple strategies per objective and performs
    contextual selection before execution.
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        capture_engine: CaptureEngine,
        gemini_analyzer: GeminiAnalyzer,
        gemini_decision_module: GeminiDecisionModule,
        status_update_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.knowledge_base = knowledge_base
        self.capture_engine = capture_engine
        self.gemini_analyzer = gemini_analyzer
        self.gemini_decision_module = gemini_decision_module
        self.status_update_callback = status_update_callback
        self.knowledge_data: Dict[str, Any] = {}
        logger.info("StrategicExecutor initialized.")

    def _send_status_update(self, update_type: str, data: Dict[str, Any]):
        """Safely sends a status update to the GUI via the callback."""
        if self.status_update_callback:
            try:
                self.status_update_callback({"type": update_type, "data": data})
            except Exception as e:
                logger.error(f"Error in StrategicExecutor status_update_callback: {e}", exc_info=True)

    def _match_command_to_objective(self, command: str) -> Optional[str]:
        """Uses a fast AI model to match a user command to a known Objective."""
        objectives = self.knowledge_data.get("objectives", [])
        if not objectives:
            return None
        objectives_for_prompt = [{"objective_name": o.get("objective_name"), "goal_prompt": o.get("goal_prompt")} for o in objectives]
        prompt = OBJECTIVE_MATCHING_PROMPT.format(objectives_json=json.dumps(objectives_for_prompt, indent=2), user_command=command)
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, model_preference=[OBJECTIVE_MATCHING_MODEL])
        if response["status"] == "success" and response["text_content"]:
            matched_name = response["text_content"].strip()
            if matched_name != "None" and any(o.get("objective_name") == matched_name for o in objectives):
                logger.info(f"Command successfully matched to existing Objective: '{matched_name}'")
                return matched_name
        return None

    def _select_best_strategy_contextually(self, user_command: str, strategies: List[Dict[str, Any]], visual_context: np.ndarray) -> Optional[Dict[str, Any]]:
        """Uses AI to choose the best strategy from a list based on visual context."""
        if not strategies:
            return None
        if len(strategies) == 1:
            logger.info("Only one strategy available, selecting it by default.")
            return strategies

        logger.info(f"Performing contextual selection from {len(strategies)} available strategies.")
        self._send_status_update("strategy_select_start", {"strategy_count": len(strategies)})

        strategies_summary = [{"strategy_name": s.get("strategy_name"), "first_step": s.get("steps", [{}]).get("tactical_goal", "N/A")} for s in strategies]

        prompt = CONTEXTUAL_STRATEGY_SELECTION_PROMPT.format(user_command=user_command, strategies_summary_json=json.dumps(strategies_summary, indent=2))

        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=visual_context, model_preference=[CONTEXTUAL_STRATEGY_SELECTION_MODEL])

        if response["status"] == "success" and response.get("json_content"):
            chosen_name = response["json_content"].get("chosen_strategy_name")
            for strategy in strategies:
                if strategy.get("strategy_name") == chosen_name:
                    logger.info(f"AI contextually selected strategy: '{chosen_name}'")
                    self._send_status_update("strategy_select_success", {"chosen_strategy": chosen_name})
                    return strategy

        logger.warning("Contextual strategy selection failed or returned invalid choice. Falling back to the highest-rated strategy.")
        best_strategy = strategies  # List is pre-sorted
        self._send_status_update("strategy_select_fallback", {"chosen_strategy": best_strategy.get("strategy_name")})
        return best_strategy

    def _generate_new_strategy_from_scratch(self, command: str) -> Optional[List[Dict[str, str]]]:
        """Generates a new strategy (list of tactical goals) when no existing one is found."""
        logger.info(f"No suitable existing strategy found. Generating a new one for command: '{command}'")
        kb_json_string = json.dumps(self.knowledge_base.get_full_knowledge_base(), indent=2)
        prompt = STRATEGIC_PLANNER_PROMPT_TEMPLATE.format(knowledge_base_json=kb_json_string, user_command=command)
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, model_preference=[STRATEGIC_PLANNING_MODEL])
        if response["status"] == "success" and response["json_content"]:
            plan_data = response["json_content"]
            if "strategic_plan" in plan_data and isinstance(plan_data["strategic_plan"], list):
                steps = [s for s in plan_data["strategic_plan"] if isinstance(s, dict) and "tactical_goal" in s and "expected_outcome_description" in s]
                if steps:
                    logger.info(f"Successfully generated a new {len(steps)}-step strategy from scratch.")
                    return steps
        logger.error(f"Failed to generate a valid new strategy. Status: {response['status']}")
        return None

    def _generate_self_correction_plan(self, user_command: str, remaining_plan: List[Dict[str, str]], failed_step: Dict[str, str], failure_screenshot: np.ndarray) -> Optional[List[Dict[str, str]]]:
        """Generates a new plan to recover from a failed tactic."""
        logger.warning("Initiating self-correction re-planning...")
        self._send_status_update("replan_start", {"reason": "Verification failed."})
        prompt = STRATEGIC_CORRECTION_PROMPT_TEMPLATE.format(
            user_command=user_command,
            original_plan_json=json.dumps(remaining_plan, indent=2),
            failed_tactic=failed_step.get("tactical_goal", "N/A"),
            expected_outcome=failed_step.get("expected_outcome_description", "N/A"),
        )
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=failure_screenshot, model_preference=[STRATEGIC_CORRECTION_MODEL])
        if response["status"] == "success" and response["json_content"]:
            plan_data = response["json_content"]
            if "strategic_plan" in plan_data and isinstance(plan_data["strategic_plan"], list):
                steps = [s for s in plan_data["strategic_plan"] if isinstance(s, dict) and "tactical_goal" in s and "expected_outcome_description" in s]
                if steps:
                    logger.info(f"Successfully generated a new {len(steps)}-step self-correction plan.")
                    self._send_status_update("replan_success", {"new_step_count": len(steps)})
                    return steps
        logger.error(f"Failed to generate a valid self-correction plan. Status: {response['status']}")
        self._send_status_update("replan_failure", {})
        return None

    def _verify_action_outcome(self, screenshot: np.ndarray, expected_outcome: str) -> bool:
        """Uses a fast vision model to verify if the post-action screenshot matches the expected outcome."""
        if not expected_outcome:
            logger.warning("No expected outcome provided for verification. Assuming success by default.")
            return True
        prompt = f"Based on the provided image, is this condition true or false? Condition: \"{expected_outcome}\". Respond ONLY with the single word 'true' or 'false'."
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=screenshot, model_preference=[VERIFICATION_MODEL])
        if response["status"] == "success" and response["text_content"]:
            result = response["text_content"].strip().lower()
            logger.info(f"Verification for '{expected_outcome}': AI responded '{result}'.")
            return result == "true"
        logger.warning(f"Verification query failed for outcome '{expected_outcome}'. Assuming failure. Status: {response['status']}")
        return False

    def execute_command(self, command: str) -> Dict[str, Any]:
        logger.info(f"--- Strategic Execution Started for command: '{command}' ---")
        self._send_status_update("task_start", {"command": command})
        self.knowledge_data = self.knowledge_base.get_full_knowledge_base()

        strategic_plan: Optional[List[Dict[str, str]]] = None
        objective_name_for_saving: Optional[str] = None
        strategy_used_for_saving: Optional[Dict[str, Any]] = None
        was_newly_generated = False
        final_result_status = "failure"
        final_result_message = "Task did not complete successfully."

        # Phase 1: Try to find and select an existing strategy
        matched_objective_name = self._match_command_to_objective(command)
        if matched_objective_name:
            objective_name_for_saving = matched_objective_name
            all_strategies = self.knowledge_base.get_all_strategies_for_objective(matched_objective_name)
            if all_strategies:
                current_screen_for_selection = self._capture_screen_for_execution()
                if current_screen_for_selection is not None:
                    best_strategy = self._select_best_strategy_contextually(command, all_strategies, current_screen_for_selection)
                    if best_strategy:
                        strategic_plan = best_strategy.get("steps")
                        strategy_used_for_saving = best_strategy
                        self._send_status_update("strategy_found", {"objective": matched_objective_name, "strategy": best_strategy.get("strategy_name")})

        # Phase 2: Fallback to generating a new strategy
        if not strategic_plan:
            was_newly_generated = True
            self._send_status_update("strategy_generate_start", {})
            plan_steps = self._generate_new_strategy_from_scratch(command)
            if plan_steps:
                strategic_plan = plan_steps
                if not objective_name_for_saving:
                    objective_name_for_saving = f"Objective: {command[:50]}"
                strategy_used_for_saving = {
                    "strategy_name": "Dynamically Generated Strategy v1",
                    "success_rate": NEW_STRATEGY_DEFAULT_SUCCESS_RATE,
                    "last_used": datetime.now(timezone.utc).isoformat(),
                    "steps": plan_steps,
                }
                self._send_status_update("strategy_generate_success", {"objective": objective_name_for_saving, "strategy": strategy_used_for_saving["strategy_name"]})

        if not strategic_plan:
            self._send_status_update("task_end", {"status": "failure", "message": "Could not find or generate a strategic plan."})
            return {"status": "failure", "message": "Could not find or generate a strategic plan."}

        # Phase 3: Execute the plan with self-correction loop
        current_step_index = 0
        max_correction_attempts = 2
        correction_attempts = 0
        while current_step_index < len(strategic_plan):
            step = strategic_plan[current_step_index]
            goal = step.get("tactical_goal")
            expected_outcome = step.get("expected_outcome_description")

            if not goal or not expected_outcome:
                current_step_index += 1
                continue

            self._send_status_update("tactic_start", {"tactic": goal, "step_index": current_step_index + 1, "total_steps": len(strategic_plan)})
            pre_action_screenshot = self._capture_screen_for_execution()
            if pre_action_screenshot is None:
                final_result_message = f"Pre-action screen capture failed for step {current_step_index + 1}."
                break

            self._send_status_update("tactic_before_image", {"image_np": pre_action_screenshot})

            fullscreen_context = {"fullscreen_region_config": {"x": 0, "y": 0, "width": self.capture_engine.get_primary_screen_width(), "height": self.capture_engine.get_primary_screen_height()}}
            tactical_result = self.gemini_decision_module.execute_nlu_task(
                task_rule_name=f"StrategicTask_Step{current_step_index + 1}",
                natural_language_command=goal,
                initial_context_images={"fullscreen": pre_action_screenshot},
                task_parameters={"context_region_names": ["fullscreen"], "require_confirmation_per_step": False, **fullscreen_context},
            )

            if tactical_result.get("status") != "success":
                final_result_message = f"Step {current_step_index + 1} ('{goal}') failed during execution: {tactical_result.get('message')}"
                break

            time.sleep(1.5)
            post_action_screenshot = self._capture_screen_for_execution()
            if post_action_screenshot is None:
                final_result_message = f"Post-action screen capture failed for step {current_step_index + 1}."
                break

            is_verified = self._verify_action_outcome(post_action_screenshot, expected_outcome)
            self._send_status_update("tactic_after_image", {"image_np": post_action_screenshot, "verified": is_verified})

            if not is_verified:
                logger.error(f"Verification failed for tactic: '{goal}'")
                correction_attempts += 1
                if correction_attempts > max_correction_attempts:
                    final_result_message = "Maximum self-correction attempts reached."
                    break

                remaining_plan = strategic_plan[current_step_index:]
                new_plan_steps = self._generate_self_correction_plan(command, remaining_plan, step, post_action_screenshot)

                if new_plan_steps:
                    was_newly_generated = True
                    strategic_plan = new_plan_steps
                    strategy_used_for_saving = {
                        "strategy_name": f"Self-Corrected Strategy v{correction_attempts}",
                        "success_rate": NEW_STRATEGY_DEFAULT_SUCCESS_RATE,
                        "last_used": datetime.now(timezone.utc).isoformat(),
                        "steps": new_plan_steps,
                    }
                    current_step_index = 0
                    continue
                else:
                    final_result_message = "Verification failed and could not generate a correction plan."
                    break

            current_step_index += 1

        if current_step_index == len(strategic_plan):
            final_result_status = "success"
            final_result_message = "All strategic steps completed and verified."

        # Phase 4: Strategy Refinement (Learning)
        if objective_name_for_saving and strategy_used_for_saving:
            if final_result_status == "success":
                if was_newly_generated:
                    logger.info(f"Saving newly generated successful strategy to Objective '{objective_name_for_saving}'.")
                    self.knowledge_base.save_strategy(objective_name_for_saving, strategy_used_for_saving, command)
                else:
                    old_rate = strategy_used_for_saving.get("success_rate", 0.5)
                    new_rate = old_rate + (1.0 - old_rate) * SUCCESS_LEARNING_RATE
                    self.knowledge_base.update_strategy_metadata(
                        objective_name_for_saving, strategy_used_for_saving["strategy_name"], {"success_rate": new_rate, "last_used": datetime.now(timezone.utc).isoformat()}
                    )
            elif not was_newly_generated:
                old_rate = strategy_used_for_saving.get("success_rate", 0.5)
                new_rate = old_rate * FAILURE_DECAY_RATE
                self.knowledge_base.update_strategy_metadata(objective_name_for_saving, strategy_used_for_saving["strategy_name"], {"success_rate": new_rate})

        logger.info(f"--- Strategic Execution Finished with status: {final_result_status} ---")
        self._send_status_update("task_end", {"status": final_result_status, "message": final_result_message})
        return {"status": final_result_status, "message": final_result_message}

    def _capture_screen_for_execution(self) -> Optional[np.ndarray]:
        if self.capture_engine:
            return self.capture_engine.capture_region(
                {"name": "strategic_step_capture", "x": 0, "y": 0, "width": self.capture_engine.get_primary_screen_width(), "height": self.capture_engine.get_primary_screen_height()}
            )
        return None
