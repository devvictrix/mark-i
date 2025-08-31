import logging
import time
from typing import Dict, Any, Optional, Callable, Tuple

import numpy as np
import abc
import pyautogui

from mark_i.engines.action_executor import ActionExecutor
from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_FAST
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.primitive_executors")


class PrimitiveSubActionExecuteResult:
    """Holds the result of a primitive sub-action execution."""
    def __init__(self, success: bool, boolean_eval_result: Optional[bool] = None):
        self.success = success
        self.boolean_eval_result = boolean_eval_result


class PrimitiveSubActionExecutorBase(abc.ABC):
    """
    Abstract base class for executing a specific type of primitive sub-action
    derived from an NLU-parsed plan.
    """

    def __init__(
        self,
        action_executor_instance: ActionExecutor,
        gemini_analyzer_instance: GeminiAnalyzer,
        target_refiner_func: Callable[[str, np.ndarray, str, str], Optional[Dict[str, Any]]],
    ):
        self.action_executor = action_executor_instance
        self.gemini_analyzer = gemini_analyzer_instance
        self._refine_target_description_to_bbox = target_refiner_func

    @abc.abstractmethod
    def execute(
        self,
        step_instruction_details: Dict[str, Any],
        current_visual_context_images: Dict[str, np.ndarray],
        primary_context_region_name: str,
        task_rule_name_for_log: str,
        task_parameters_from_rule: Dict[str, Any],
        log_prefix_base: str
    ) -> PrimitiveSubActionExecuteResult:
        pass

    def _confirm_action_if_needed(
        self,
        action_description_for_confirm: str,
        require_confirmation: bool,
        log_prefix: str
    ) -> bool:
        if require_confirmation:
            logger.info(f"{log_prefix}: USER CONFIRMATION REQUIRED for: {action_description_for_confirm} (Simulating 'Yes' for backend execution)")
        return True


class OpenApplicationExecutor(PrimitiveSubActionExecutorBase):
    """Primitive for opening an application via the start menu."""
    def execute(
        self, step_instruction_details: Dict, current_visual_context_images: Dict,
        primary_context_region_name: str, task_rule_name_for_log: str,
        task_parameters_from_rule: Dict, log_prefix_base: str
    ) -> PrimitiveSubActionExecuteResult:
        target_desc = step_instruction_details.get("target_description", "")
        app_name = target_desc.replace("the", "").replace("application", "").strip()
        log_prefix = f"{log_prefix_base} OPEN_APPLICATION"

        if not app_name:
            logger.error(f"{log_prefix}: 'target_description' did not contain a valid application name. Description was: '{target_desc}'")
            return PrimitiveSubActionExecuteResult(success=False)
        
        try:
            logger.info(f"{log_prefix}: Attempting to open application '{app_name}' via start menu.")
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.typewrite(app_name, interval=0.05)
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1.5)
            logger.info(f"{log_prefix}: Application '{app_name}' launched successfully via start menu sequence.")
            return PrimitiveSubActionExecuteResult(success=True)
        except Exception as e:
            logger.error(f"{log_prefix}: A pyautogui error occurred while trying to open application '{app_name}': {e}", exc_info=True)
            return PrimitiveSubActionExecuteResult(success=False)


class PressHotkeyExecutor(PrimitiveSubActionExecutorBase):
    """Primitive for pressing complex hotkey combinations."""
    def execute(
        self, step_instruction_details: Dict, current_visual_context_images: Dict,
        primary_context_region_name: str, task_rule_name_for_log: str,
        task_parameters_from_rule: Dict, log_prefix_base: str
    ) -> PrimitiveSubActionExecuteResult:
        hotkey_str = step_instruction_details.get("parameters", {}).get("hotkey_combination")
        log_prefix = f"{log_prefix_base} PRESS_HOTKEY"
        if not hotkey_str or not isinstance(hotkey_str, str):
            logger.error(f"{log_prefix}: 'hotkey_combination' missing or invalid.")
            return PrimitiveSubActionExecuteResult(success=False)
        
        try:
            self.action_executor.execute_action({"type": "press_key", "key": hotkey_str, "context": {"rule_name": f"{task_rule_name_for_log}_NLU_Hotkey"}})
            return PrimitiveSubActionExecuteResult(success=True)
        except Exception as e:
            logger.error(f"{log_prefix}: Error during execution: {e}", exc_info=True)
            return PrimitiveSubActionExecuteResult(success=False)

class ClickDescribedElementExecutor(PrimitiveSubActionExecutorBase):
    def execute(
        self, step_instruction_details: Dict, current_visual_context_images: Dict,
        primary_context_region_name: str, task_rule_name_for_log: str,
        task_parameters_from_rule: Dict, log_prefix_base: str
    ) -> PrimitiveSubActionExecuteResult:
        target_desc = step_instruction_details.get("target_description")
        params_from_nlu = step_instruction_details.get("parameters", {})
        log_prefix = f"{log_prefix_base} CLICK_DESCRIBED_ELEMENT"

        if not target_desc or not isinstance(target_desc, str):
            logger.error(f"{log_prefix}: 'target_description' missing or invalid: '{target_desc}'.")
            return PrimitiveSubActionExecuteResult(success=False)

        current_step_image_np = current_visual_context_images.get(primary_context_region_name)
        if current_step_image_np is None:
            logger.error(f"{log_prefix}: Primary context image for region '{primary_context_region_name}' is missing.")
            return PrimitiveSubActionExecuteResult(success=False)

        refined_target_data = self._refine_target_description_to_bbox(
            target_desc, current_step_image_np, primary_context_region_name, task_rule_name_for_log
        )
        if not refined_target_data:
            logger.error(f"{log_prefix}: Failed to refine target '{target_desc}'.")
            return PrimitiveSubActionExecuteResult(success=False)

        if not self._confirm_action_if_needed(f"Click on '{target_desc}'", task_parameters_from_rule.get("require_confirmation_per_step", True), log_prefix):
            return PrimitiveSubActionExecuteResult(success=True)

        temp_var_name = f"_nlu_click_target_{time.monotonic_ns()}"
        action_executor_spec = {
            "type": "click", "target_relation": "center_of_gemini_element", "gemini_element_variable": temp_var_name,
            "button": params_from_nlu.get("button", "left"), "clicks": int(params_from_nlu.get("clicks", 1)),
            "interval": float(params_from_nlu.get("interval", 0.0)),
            "pyautogui_pause_before": task_parameters_from_rule.get("pyautogui_pause_before", 0.1),
            "context": {
                "rule_name": f"{task_rule_name_for_log}_NLU_Click", 
                "variables": {temp_var_name: refined_target_data}, 
                "fullscreen_region_config": task_parameters_from_rule.get("fullscreen_region_config")
            }
        }
        try:
            self.action_executor.execute_action(action_executor_spec)
            return PrimitiveSubActionExecuteResult(success=True)
        except Exception as e:
            logger.error(f"{log_prefix}: Error during ActionExecutor execution for click: {e}", exc_info=True)
            return PrimitiveSubActionExecuteResult(success=False)


class TypeInDescribedFieldExecutor(PrimitiveSubActionExecutorBase):
    def execute(
        self, step_instruction_details: Dict, current_visual_context_images: Dict,
        primary_context_region_name: str, task_rule_name_for_log: str,
        task_parameters_from_rule: Dict, log_prefix_base: str
    ) -> PrimitiveSubActionExecuteResult:
        target_desc = step_instruction_details.get("target_description")
        params_from_nlu = step_instruction_details.get("parameters", {})
        text_to_type = params_from_nlu.get("text_to_type")
        log_prefix = f"{log_prefix_base} TYPE_IN_DESCRIBED_FIELD"

        if not target_desc or not isinstance(target_desc, str):
            logger.error(f"{log_prefix}: 'target_description' missing or invalid.")
            return PrimitiveSubActionExecuteResult(success=False)
        if not isinstance(text_to_type, str):
            logger.error(f"{log_prefix}: 'text_to_type' missing or invalid.")
            return PrimitiveSubActionExecuteResult(success=False)

        current_step_image_np = current_visual_context_images.get(primary_context_region_name)
        if current_step_image_np is None:
            logger.error(f"{log_prefix}: Primary context image missing.")
            return PrimitiveSubActionExecuteResult(success=False)

        refined_field_data = self._refine_target_description_to_bbox(target_desc, current_step_image_np, primary_context_region_name, task_rule_name_for_log)
        if not refined_field_data:
            logger.error(f"{log_prefix}: Failed to refine field target '{target_desc}'.")
            return PrimitiveSubActionExecuteResult(success=False)

        try:
            click_var_name = f"_nlu_type_field_target_{time.monotonic_ns()}"
            click_spec = {
                "type": "click", 
                "target_relation": "center_of_gemini_element", 
                "gemini_element_variable": click_var_name, 
                "context": {
                    "rule_name": f"{task_rule_name_for_log}_NLU_ClickField", 
                    "variables": {click_var_name: refined_field_data},
                    "fullscreen_region_config": task_parameters_from_rule.get("fullscreen_region_config")
                }
            }
            self.action_executor.execute_action(click_spec)
            time.sleep(0.2)

            type_spec = {"type": "type_text", "text": text_to_type, "context": {"rule_name": f"{task_rule_name_for_log}_NLU_TypeText"}}
            self.action_executor.execute_action(type_spec)
            return PrimitiveSubActionExecuteResult(success=True)
        except Exception as e:
            logger.error(f"{log_prefix}: Error during execution: {e}", exc_info=True)
            return PrimitiveSubActionExecuteResult(success=False)


class PressKeySimpleExecutor(PrimitiveSubActionExecutorBase):
    def execute(
        self, step_instruction_details: Dict, current_visual_context_images: Dict,
        primary_context_region_name: str, task_rule_name_for_log: str,
        task_parameters_from_rule: Dict, log_prefix_base: str
    ) -> PrimitiveSubActionExecuteResult:
        key_name = step_instruction_details.get("parameters", {}).get("key_name")
        log_prefix = f"{log_prefix_base} PRESS_KEY_SIMPLE"
        if not key_name or not isinstance(key_name, str):
            logger.error(f"{log_prefix}: 'key_name' missing or invalid.")
            return PrimitiveSubActionExecuteResult(success=False)
        
        try:
            self.action_executor.execute_action({"type": "press_key", "key": key_name, "context": {"rule_name": f"{task_rule_name_for_log}_NLU_PressKey"}})
            return PrimitiveSubActionExecuteResult(success=True)
        except Exception as e:
            logger.error(f"{log_prefix}: Error during execution: {e}", exc_info=True)
            return PrimitiveSubActionExecuteResult(success=False)


class CheckVisualStateExecutor(PrimitiveSubActionExecutorBase):
    def execute(
        self, step_instruction_details: Dict, current_visual_context_images: Dict,
        primary_context_region_name: str, task_rule_name_for_log: str,
        task_parameters_from_rule: Dict, log_prefix_base: str
    ) -> PrimitiveSubActionExecuteResult:
        condition_desc = step_instruction_details.get("parameters", {}).get("condition_description", step_instruction_details.get("target_description"))
        log_prefix = f"{log_prefix_base} CHECK_VISUAL_STATE"
        if not condition_desc or not isinstance(condition_desc, str):
            logger.error(f"{log_prefix}: 'condition_description' missing or invalid.")
            return PrimitiveSubActionExecuteResult(success=False, boolean_eval_result=False)
        
        current_step_image_np = current_visual_context_images.get(primary_context_region_name)
        if current_step_image_np is None:
            logger.error(f"{log_prefix}: Primary context image missing.")
            return PrimitiveSubActionExecuteResult(success=False, boolean_eval_result=False)
        
        check_prompt = f"Based on the provided image, is this condition true or false? Condition: \"{condition_desc}\". Respond only with 'true' or 'false'."
        response = self.gemini_analyzer.query_vision_model(prompt=check_prompt, image_data=current_step_image_np, model_preference=MODEL_PREFERENCE_FAST)
        
        if response["status"] == "success" and response["text_content"]:
            result_text = response["text_content"].strip().lower()
            if result_text == "true":
                return PrimitiveSubActionExecuteResult(success=True, boolean_eval_result=True)
            elif result_text == "false":
                return PrimitiveSubActionExecuteResult(success=True, boolean_eval_result=False)
            else:
                logger.warning(f"{log_prefix}: Ambiguous response '{result_text}'. Interpreting as FALSE.")
                return PrimitiveSubActionExecuteResult(success=True, boolean_eval_result=False)
        
        logger.error(f"{log_prefix}: Query failed. Status: {response['status']}")
        return PrimitiveSubActionExecuteResult(success=False, boolean_eval_result=False)