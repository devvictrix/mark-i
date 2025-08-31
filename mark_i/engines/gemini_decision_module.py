import logging
import json
import time
from typing import Dict, Any, Optional, List, Tuple, Callable
import os

import numpy as np

from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_REASONING, MODEL_PREFERENCE_FAST
from mark_i.engines.action_executor import ActionExecutor
from mark_i.core.config_manager import ConfigManager

from mark_i.engines.primitive_executors import (
    PrimitiveSubActionExecutorBase,
    ClickDescribedElementExecutor,
    TypeInDescribedFieldExecutor,
    PressKeySimpleExecutor,
    PressHotkeyExecutor,
    CheckVisualStateExecutor,
    OpenApplicationExecutor,
    PrimitiveSubActionExecuteResult,
)

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.gemini_decision_module")

PREDEFINED_ALLOWED_SUB_ACTIONS: Dict[str, Dict[str, Any]] = {
    "CLICK_DESCRIBED_ELEMENT": {"description": "Clicks an element described textually.", "executor_class": ClickDescribedElementExecutor},
    "TYPE_IN_DESCRIBED_FIELD": {"description": "Types text into an element described textually.", "executor_class": TypeInDescribedFieldExecutor},
    "PRESS_KEY_SIMPLE": {"description": "Presses a single standard keyboard key.", "executor_class": PressKeySimpleExecutor},
    "PRESS_HOTKEY": {"description": "Presses a combination of keys (e.g., Ctrl+S).", "executor_class": PressHotkeyExecutor},
    "CHECK_VISUAL_STATE": {"description": "Checks if a visual condition is met.", "executor_class": CheckVisualStateExecutor},
    "OPEN_APPLICATION": {"description": "Opens an application using the start menu.", "executor_class": OpenApplicationExecutor},
}


class GeminiDecisionModule:
    def __init__(
        self,
        gemini_analyzer: GeminiAnalyzer,
        action_executor: ActionExecutor,
        config_manager: ConfigManager,
    ):
        if not isinstance(gemini_analyzer, GeminiAnalyzer) or not gemini_analyzer.client_initialized:
            raise ValueError("Valid, initialized GeminiAnalyzer instance required for GeminiDecisionModule.")
        self.gemini_analyzer = gemini_analyzer
        if not isinstance(action_executor, ActionExecutor):
            raise ValueError("ActionExecutor instance is required.")
        self.action_executor = action_executor
        if not isinstance(config_manager, ConfigManager):
            raise ValueError("ConfigManager instance is required.")
        self.config_manager = config_manager
        self._primitive_executors: Dict[str, PrimitiveSubActionExecutorBase] = self._initialize_primitive_executors()
        self._executed_steps_log_during_task: List[str] = []
        logger.info("GeminiDecisionModule (NLU Task Orchestrator & Goal Executor) initialized.")

    def _initialize_primitive_executors(self) -> Dict[str, PrimitiveSubActionExecutorBase]:
        executors: Dict[str, PrimitiveSubActionExecutorBase] = {}
        shared_dependencies = {
            "action_executor_instance": self.action_executor,
            "gemini_analyzer_instance": self.gemini_analyzer,
            "target_refiner_func": self._refine_target_description_to_bbox,
        }
        for action_type, meta in PREDEFINED_ALLOWED_SUB_ACTIONS.items():
            executor_class = meta.get("executor_class")
            if executor_class:
                executors[action_type] = executor_class(**shared_dependencies)
        return executors

    def _construct_nlu_parse_prompt(self, natural_language_command: str) -> str:
        allowed_verbs = list(PREDEFINED_ALLOWED_SUB_ACTIONS.keys())
        nlu_schema_description = f"""
You are an NLU parser for a desktop automation tool. Convert the user's command into a structured JSON plan.
The `intent_verb` in your response MUST be one of the following allowed values: {json.dumps(allowed_verbs)}

The response JSON MUST have a top-level key "parsed_task" with a "command_type" and instruction details.
- "command_type": "SINGLE_INSTRUCTION", "SEQUENTIAL_INSTRUCTIONS", or "CONDITIONAL_INSTRUCTION".
- "instruction_details": Contains "intent_verb", "target_description", and "parameters".
  - For "OPEN_APPLICATION", "target_description" is the app name.
  - For "TYPE_IN_DESCRIBED_FIELD", "target_description" is the field, "parameters.text_to_type" is the text.
  - For "CLICK_DESCRIBED_ELEMENT", "target_description" is the element.
  - For "PRESS_KEY_SIMPLE", "parameters.key_name" is the single key.
  - For "PRESS_HOTKEY", "parameters.hotkey_combination" is the key combo string (e.g., "ctrl+s").
  - For "CHECK_VISUAL_STATE", "target_description" is the condition to check.
"""
        return f'{nlu_schema_description}\n\nUser Command to Parse: "{natural_language_command}"\n\nProvide your parsed JSON output now:'

    def _map_nlu_intent_to_allowed_sub_action(self, nlu_intent_verb: Optional[str]) -> Optional[str]:
        if nlu_intent_verb in PREDEFINED_ALLOWED_SUB_ACTIONS:
            return nlu_intent_verb
        logger.warning(f"NLU Intent verb '{nlu_intent_verb}' is not in the set of predefined sub-action types.")
        return None

    def _refine_target_description_to_bbox(self, target_description: str, context_image_np: np.ndarray, context_image_region_name: str, task_rule_name_for_log: str) -> Optional[Dict[str, Any]]:
        log_prefix = f"R '{task_rule_name_for_log}', NLU Task TargetRefine"
        prompt = (
            f"In the image of region '{context_image_region_name}', find the element best described as: \"{target_description}\".\n" f'Respond ONLY with JSON: {{"found": true, "box": [x,y,w,h]}}.'
        )
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=context_image_np, model_preference=MODEL_PREFERENCE_FAST)
        if response["status"] == "success" and response["json_content"]:
            data = response["json_content"]
            if data.get("found") and isinstance(data.get("box"), list) and len(data["box"]) == 4:
                box = [int(round(n)) for n in data["box"]]
                return {"value": {"box": box, "found": True, "element_label": target_description}, "_source_region_for_capture_": context_image_region_name}
        return None

    def _execute_primitive_sub_action(
        self, step_instruction_details: Dict, current_visual_context_images: Dict, primary_context_region_name: str, task_rule_name_for_log: str, task_parameters_from_rule: Dict
    ) -> PrimitiveSubActionExecuteResult:
        intent_verb = step_instruction_details.get("intent_verb")
        log_prefix_base = f"R '{task_rule_name_for_log}', NLU SubStep"
        primitive_action_type = self._map_nlu_intent_to_allowed_sub_action(intent_verb)
        if not primitive_action_type:
            logger.error(f"{log_prefix_base}: Could not map NLU intent '{intent_verb}' to primitive. Step failed.")
            return PrimitiveSubActionExecuteResult(success=False)
        executor = self._primitive_executors.get(primitive_action_type)
        if not executor:
            logger.error(f"{log_prefix_base}: No executor for primitive type '{primitive_action_type}'. Step failed.")
            return PrimitiveSubActionExecuteResult(success=False)
        return executor.execute(step_instruction_details, current_visual_context_images, primary_context_region_name, task_rule_name_for_log, task_parameters_from_rule, log_prefix_base)

    def _handle_single_instruction_node(self, instruction_details: Dict, current_images: Dict, primary_rgn_name: str, task_rule_name: str, task_parameters: Dict, branch_prefix: str) -> bool:
        exec_result = self._execute_primitive_sub_action(instruction_details, current_images, primary_rgn_name, f"{task_rule_name}_{branch_prefix}Single", task_parameters)
        return exec_result.success

    def _handle_sequential_instructions_node(self, steps_list: List[Dict], current_images: Dict, primary_rgn_name: str, task_rule_name: str, task_parameters: Dict, branch_prefix: str) -> bool:
        for i, step_item_data in enumerate(steps_list):
            if not isinstance(step_item_data, dict) or "instruction_details" not in step_item_data:
                return False
            exec_result = self._execute_primitive_sub_action(step_item_data["instruction_details"], current_images, primary_rgn_name, f"{task_rule_name}_{branch_prefix}SeqStep{i+1}", task_parameters)
            if not exec_result.success:
                return False
            time.sleep(float(task_parameters.get("delay_between_nlu_steps_sec", 0.3)))
        return True

    def _handle_conditional_instruction_node(
        self, cond_desc: str, then_node: Dict, else_node: Optional[Dict], current_images: Dict, primary_rgn_name: str, task_rule_name: str, task_parameters: Dict, depth: int, branch_prefix: str
    ) -> bool:
        eval_instr = {"intent_verb": "CHECK_VISUAL_STATE", "target_description": cond_desc, "parameters": {"condition_description": cond_desc}}
        condition_exec_result = self._execute_primitive_sub_action(eval_instr, current_images, primary_rgn_name, f"{task_rule_name}_{branch_prefix}IF_Check", task_parameters)
        if not condition_exec_result.success:
            return False

        target_branch = then_node if condition_exec_result.boolean_eval_result else else_node
        if target_branch:
            new_prefix = f"{branch_prefix}THEN." if condition_exec_result.boolean_eval_result else f"{branch_prefix}ELSE."
            return self._recursive_execute_plan_node(target_branch, current_images, primary_rgn_name, depth + 1, new_prefix, task_rule_name, task_parameters)
        return True

    def _recursive_execute_plan_node(self, plan_node_data: Dict, current_images: Dict, primary_rgn_name: str, depth: int, branch_prefix: str, task_rule_name: str, task_parameters: Dict) -> bool:
        if depth > task_parameters.get("max_recursion_depth_nlu", 5):
            return False
        node_type = plan_node_data.get("command_type")
        if node_type == "SINGLE_INSTRUCTION":
            return self._handle_single_instruction_node(plan_node_data.get("instruction_details", {}), current_images, primary_rgn_name, task_rule_name, task_parameters, branch_prefix)
        elif node_type == "SEQUENTIAL_INSTRUCTIONS":
            return self._handle_sequential_instructions_node(plan_node_data.get("steps", []), current_images, primary_rgn_name, task_rule_name, task_parameters, branch_prefix)
        elif node_type == "CONDITIONAL_INSTRUCTION":
            return self._handle_conditional_instruction_node(
                plan_node_data.get("condition_description", ""),
                plan_node_data.get("then_branch", {}),
                plan_node_data.get("else_branch"),
                current_images,
                primary_rgn_name,
                task_rule_name,
                task_parameters,
                depth,
                branch_prefix,
            )
        return False

    def execute_nlu_task(self, task_rule_name: str, natural_language_command: str, initial_context_images: Dict[str, np.ndarray], task_parameters: Dict[str, Any]) -> Dict[str, Any]:
        overall_task_result = {"status": "failure", "message": "NLU task initiated."}
        log_prefix_task = f"R '{task_rule_name}', NLU Task"
        logger.info(f"{log_prefix_task}: Starting execution for command: '{natural_language_command}'")

        nlu_parse_prompt = self._construct_nlu_parse_prompt(natural_language_command)
        nlu_context_image = next(iter(initial_context_images.values()), None)
        nlu_response = self.gemini_analyzer.query_vision_model(prompt=nlu_parse_prompt, image_data=nlu_context_image, model_preference=MODEL_PREFERENCE_REASONING)

        if nlu_response["status"] != "success" or not nlu_response["json_content"]:
            overall_task_result["message"] = f"NLU parsing query failed: {nlu_response.get('error_message', 'No JSON')}"
            return overall_task_result

        try:
            parsed_task_plan = nlu_response["json_content"]["parsed_task"]
        except (KeyError, TypeError):
            overall_task_result["message"] = "Error processing NLU JSON response structure."
            return overall_task_result

        primary_rgn_name = list(initial_context_images.keys())[0] if initial_context_images else ""
        if not primary_rgn_name:
            overall_task_result["message"] = "No primary context image available for execution."
            return overall_task_result

        final_success = self._recursive_execute_plan_node(parsed_task_plan, initial_context_images, primary_rgn_name, 0, "", task_rule_name, task_parameters)

        overall_task_result["status"] = "success" if final_success else "failure"
        overall_task_result["message"] = "NLU task executed all steps successfully." if final_success else "NLU task failed at one or more steps."
        logger.info(f"{log_prefix_task}: Final status: {overall_task_result['status']}. Msg: {overall_task_result['message']}")
        return overall_task_result