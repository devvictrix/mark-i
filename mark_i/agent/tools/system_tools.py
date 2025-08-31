import logging
import time
from typing import Any, Dict

import pyautogui

from mark_i.agent.tools.base import BaseTool
from mark_i.engines.action_executor import ActionExecutor, VALID_PYAUTOGUI_KEYS
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.tools.system")

class OpenApplicationTool(BaseTool):
    """A tool for opening applications via the start menu."""
    name = "open_application"
    description = (
        "Opens an application by simulating a search in the Windows/OS start menu. "
        "Use this as the first step for tasks involving an application that is not already open. "
        "Argument `app_name` (string) is the name of the application to open (e.g., 'Notepad', 'Google Chrome')."
    )

    def execute(self, app_name: str = "", **kwargs: Any) -> str:
        if not app_name or not isinstance(app_name, str):
            return "Error: `app_name` parameter must be a non-empty string."
        
        try:
            logger.info(f"Tool 'open_application' executing for app: '{app_name}'")
            pyautogui.press('win')
            time.sleep(0.6)
            pyautogui.typewrite(app_name, interval=0.05)
            time.sleep(0.6)
            pyautogui.press('enter')
            time.sleep(1.8) # Give app time to launch
            return f"Successfully executed sequence to open application '{app_name}'. The next observation will confirm if it opened correctly."
        except Exception as e:
            logger.error(f"Tool 'open_application' failed for '{app_name}': {e}", exc_info=True)
            return f"Error: A system error occurred while trying to open '{app_name}': {e}"

class PressHotkeyTool(BaseTool):
    """A tool for pressing hotkey combinations."""
    name = "press_hotkey"
    description = (
        "Presses a combination of keyboard keys simultaneously (a hotkey). "
        "Argument `hotkey_combination` (string) is the hotkey to press, with keys separated by '+' or ',' (e.g., 'ctrl+s', 'ctrl,shift,esc')."
    )

    def __init__(self, action_executor: ActionExecutor):
        self.action_executor = action_executor

    def execute(self, hotkey_combination: str = "", **kwargs: Any) -> str:
        if not hotkey_combination or not isinstance(hotkey_combination, str):
            return "Error: `hotkey_combination` parameter must be a non-empty string."
        
        try:
            logger.info(f"Tool 'press_hotkey' executing for combo: '{hotkey_combination}'")
            # We can reuse the action executor's press_key logic which now handles hotkeys
            self.action_executor.execute_action({
                "type": "press_key",
                "key": hotkey_combination,
                "context": {"rule_name": "AgentTool_PressHotkey"}
            })
            return f"Successfully pressed hotkey combination: '{hotkey_combination}'."
        except Exception as e:
            logger.error(f"Tool 'press_hotkey' failed for '{hotkey_combination}': {e}", exc_info=True)
            return f"Error: A system error occurred while pressing hotkey '{hotkey_combination}': {e}"