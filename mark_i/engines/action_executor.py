import logging
import time
from typing import Dict, Any, Optional, Union, Tuple

import pyautogui

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.action_executor")

VALID_PYAUTOGUI_KEYS = pyautogui.KEYBOARD_KEYS


class ActionExecutor:
    """
    Executes actions like mouse clicks and keyboard inputs based on action specifications.
    Handles parameter validation, type conversion, and calculates target coordinates.
    v10.0.5 Update: This class is now stateless and does not depend on a ConfigManager.
    All necessary region context must be provided in the action's 'context' dictionary.
    """

    def __init__(self):
        """Initializes the stateless ActionExecutor."""
        pyautogui.FAILSAFE = True
        # FIX: Introduce a small default pause between all PyAutoGUI actions for stability.
        pyautogui.PAUSE = 0.1
        logger.info(f"ActionExecutor initialized (stateless). PyAutoGUI FAILSAFE is ON. Global PAUSE set to {pyautogui.PAUSE}s.")

    def _validate_and_convert_numeric_param(
        self,
        value: Any,
        param_name: str,
        target_type: type,
        action_type_for_log: str,
        rule_name_for_log: str,
        default_val: Optional[Union[int, float]] = None,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
    ) -> Optional[Union[int, float]]:
        """Validates and converts a parameter to the target numeric type (int or float)."""
        log_prefix = f"R '{rule_name_for_log}', A '{action_type_for_log}', Prm '{param_name}'"
        original_value_for_log = value
        converted_value: Optional[Union[int, float]] = None

        if isinstance(value, (int, float)):
            converted_value = target_type(value)
        elif isinstance(value, str):
            try:
                stripped_value = value.strip()
                if not stripped_value and default_val is not None:
                    return default_val
                elif not stripped_value and default_val is None:
                    logger.error(f"{log_prefix}: Empty string for required numeric. Original: '{original_value_for_log}'.")
                    return None
                if target_type == int:
                    converted_value = int(float(stripped_value))
                elif target_type == float:
                    converted_value = float(stripped_value)
                else:
                    return None
            except ValueError:
                logger.error(f"{log_prefix}: Invalid numeric string '{original_value_for_log}'.")
                return None
        else:
            logger.error(f"{log_prefix}: Unexpected type '{type(value).__name__}'.")
            return None

        if converted_value is not None:
            if min_val is not None and converted_value < min_val:
                logger.warning(f"{log_prefix}: Value {converted_value} < min {min_val}. Using default.")
                return default_val
            if max_val is not None and converted_value > max_val:
                logger.warning(f"{log_prefix}: Value {converted_value} > max {max_val}. Using default.")
                return default_val
            return converted_value
        return None

    def _apply_coordinate_offset(self, relative_coords: Tuple[int, int], context: Dict[str, Any]) -> Tuple[int, int]:
        """
        Translates relative coordinates (from cropped context) to absolute screen coordinates.
        
        Args:
            relative_coords: (x, y) coordinates relative to cropped image or region
            context: Context dictionary containing coordinate_offset
            
        Returns:
            Absolute screen coordinates
        """
        try:
            # Check if focused context is being used
            if context.get("use_focused_context", False):
                offset = context.get("coordinate_offset", (0, 0))
                absolute_coords = (relative_coords[0] + offset[0], relative_coords[1] + offset[1])
                logger.debug(f"Applied coordinate offset {offset}: {relative_coords} -> {absolute_coords}")
                return absolute_coords
            else:
                # No offset needed for full-screen context
                return relative_coords
        except Exception as e:
            logger.warning(f"Error applying coordinate offset: {e}. Using original coordinates.")
            return relative_coords

    def _get_target_coords(self, action_spec: Dict[str, Any], context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        Calculates target (x, y) absolute screen coordinates.
        v10.0.5 Update: Relies on `context['region_configs']` instead of a ConfigManager.
        v18.0.0 Update: Applies coordinate offset for focused context execution.
        """
        target_relation = action_spec.get("target_relation")
        action_type_for_log = action_spec.get("type", "unknown_action")
        rule_name_for_log = context.get("rule_name", "UnknownRule_TaskStep")
        log_prefix = f"R '{rule_name_for_log}', A '{action_type_for_log}', TargetCoord"

        if target_relation == "absolute":
            x_abs = self._validate_and_convert_numeric_param(action_spec.get("x"), "x_abs", int, action_type_for_log, rule_name_for_log)
            y_abs = self._validate_and_convert_numeric_param(action_spec.get("y"), "y_abs", int, action_type_for_log, rule_name_for_log)
            if x_abs is not None and y_abs is not None:
                # Apply coordinate offset for focused context
                final_coords = self._apply_coordinate_offset((int(x_abs), int(y_abs)), context)
                return final_coords
            return None

        region_configs_from_context = context.get("region_configs", {})

        if target_relation in ["center_of_gemini_element", "top_left_of_gemini_element"]:
            gemini_var_name = action_spec.get("gemini_element_variable")
            if not gemini_var_name:
                return None
            wrapped_gemini_data = context.get("variables", {}).get(gemini_var_name)
            if not isinstance(wrapped_gemini_data, dict):
                return None

            element_data_value = wrapped_gemini_data.get("value", {})
            source_region_name = wrapped_gemini_data.get("_source_region_for_capture_")

            if not source_region_name or not element_data_value.get("found"):
                return None

            # CRITICAL CHANGE: Get region config from context, not ConfigManager.
            # For strategic execution, this might be a special "fullscreen" context.
            if source_region_name == "fullscreen":
                source_region_config = context.get("fullscreen_region_config")
            else:
                source_region_config = region_configs_from_context.get(source_region_name)

            if not source_region_config:
                logger.error(f"{log_prefix}: Source region '{source_region_name}' config not found in provided context.")
                return None

            base_x, base_y = source_region_config.get("x", 0), source_region_config.get("y", 0)
            box_rel = element_data_value.get("box")
            if not isinstance(box_rel, list) or len(box_rel) != 4:
                return None

            rel_x, rel_y, w, h = [int(c) for c in box_rel]
            if target_relation == "center_of_gemini_element":
                relative_coords = (int(base_x + rel_x + w // 2), int(base_y + rel_y + h // 2))
            else:  # top_left
                relative_coords = (int(base_x + rel_x), int(base_y + rel_y))
            
            # Apply coordinate offset for focused context
            final_coords = self._apply_coordinate_offset(relative_coords, context)
            return final_coords

        # Legacy relations (can be removed later or adapted to use context)
        # ...

        logger.error(f"{log_prefix}: Unknown or unsupported target_relation '{target_relation}'.")
        return None

    def execute_action(self, full_action_spec_with_context: Dict[str, Any]):
        action_spec_params = {k: v for k, v in full_action_spec_with_context.items() if k != "context"}
        context = full_action_spec_with_context.get("context", {})
        action_type = action_spec_params.get("type")
        rule_name = context.get("rule_name", "UnknownRuleOrTask")
        log_prefix = f"R '{rule_name}', Action '{action_type}'"

        pause_before = self._validate_and_convert_numeric_param(
            str(action_spec_params.get("pyautogui_pause_before", "0.0")), "pyautogui_pause_before", float, str(action_type), rule_name, 0.0, min_val=0.0
        )
        if pause_before and pause_before > 0:
            time.sleep(pause_before)

        logger.info(f"{log_prefix}: Executing. Params: {action_spec_params}")

        try:
            if action_type == "click":
                coords = self._get_target_coords(action_spec_params, context)
                if coords:
                    pyautogui.click(x=coords[0], y=coords[1], button=str(action_spec_params.get("button", "left")))
                else:
                    logger.error(f"{log_prefix}: Could not get coordinates. Click skipped.")
            elif action_type == "type_text":
                pyautogui.typewrite(str(action_spec_params.get("text", "")))
            elif action_type == "press_key":
                key_param = action_spec_params.get("key", "")
                # NEW: Handle hotkeys
                keys_to_press = [k.strip().lower() for k in key_param.replace("+", ",").split(",") if k.strip()]
                valid_keys = [k for k in keys_to_press if k in VALID_PYAUTOGUI_KEYS]
                if not valid_keys:
                    logger.error(f"{log_prefix}: All keys {keys_to_press} invalid. Skipped.")
                    return
                if len(valid_keys) > 1:
                    logger.info(f"{log_prefix}: Pressing hotkey: {valid_keys}")
                    pyautogui.hotkey(*valid_keys)
                else:
                    logger.info(f"{log_prefix}: Pressing single key: '{valid_keys[0]}'")
                    pyautogui.press(valid_keys[0])
            else:
                logger.error(f"{log_prefix}: Unknown action type '{action_type}'. Skipped.")
        except pyautogui.FailSafeException:
            logger.critical(f"{log_prefix}: PyAutoGUI FAILSAFE triggered!")
            raise
        except Exception as e:
            logger.exception(f"{log_prefix}: Unexpected error: {e}")
