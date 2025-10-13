"""
Action Executor for MARK-I hierarchical AI architecture.

This module provides the ActionExecutor component that handles GUI interactions
and action execution, implementing the IActionExecutor interface.
"""

import time
from typing import Dict, Any, Optional, Tuple

import pyautogui

from mark_i.core.base_component import BaseComponent
from mark_i.core.interfaces import IActionExecutor, ExecutionResult
from mark_i.core.architecture_config import ActionExecutorConfig


class ActionExecutor(BaseComponent, IActionExecutor):
    """
    Executes GUI actions like mouse clicks and keyboard inputs.
    
    Handles parameter validation, coordinate calculation, and provides
    safety mechanisms for GUI automation.
    """
    
    def __init__(self, config: Optional[ActionExecutorConfig] = None):
        """Initialize the ActionExecutor."""
        super().__init__("action_executor", config)
        
        # PyAutoGUI configuration
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = getattr(self.config, 'action_delay_ms', 50) / 1000.0
        
        self.valid_keys = pyautogui.KEYBOARD_KEYS
        
    def _initialize_component(self) -> bool:
        """Initialize the ActionExecutor component."""
        try:
            # Test PyAutoGUI functionality
            screen_size = pyautogui.size()
            self.logger.info(f"Screen size detected: {screen_size}")
            
            # Configure safety settings
            if hasattr(self.config, 'safety_checks') and self.config.safety_checks:
                self.logger.info("Safety checks enabled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ActionExecutor: {e}")
            return False
    
    def click(self, x: int, y: int, button: str = "left") -> ExecutionResult:
        """Perform a click action."""
        try:
            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                return ExecutionResult(
                    success=False,
                    message=f"Coordinates ({x}, {y}) are outside screen bounds ({screen_width}x{screen_height})"
                )
            
            # Validate button
            if button not in ["left", "right", "middle"]:
                return ExecutionResult(
                    success=False,
                    message=f"Invalid button: {button}. Must be 'left', 'right', or 'middle'"
                )
            
            # Perform click with safety checks
            if hasattr(self.config, 'verification_enabled') and self.config.verification_enabled:
                # Get current mouse position for verification
                original_pos = pyautogui.position()
            
            pyautogui.click(x=x, y=y, button=button)
            
            self.logger.debug(f"Clicked at ({x}, {y}) with {button} button")
            
            return ExecutionResult(
                success=True,
                message=f"Successfully clicked at ({x}, {y}) with {button} button",
                data={"x": x, "y": y, "button": button}
            )
            
        except pyautogui.FailSafeException:
            error_msg = "PyAutoGUI FAILSAFE triggered - mouse moved to corner"
            self.logger.critical(error_msg)
            return ExecutionResult(success=False, message=error_msg)
            
        except Exception as e:
            error_msg = f"Failed to perform click: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def type_text(self, text: str) -> ExecutionResult:
        """Type text."""
        try:
            if not isinstance(text, str):
                return ExecutionResult(
                    success=False,
                    message=f"Text must be a string, got {type(text)}"
                )
            
            pyautogui.typewrite(text)
            
            self.logger.debug(f"Typed text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            return ExecutionResult(
                success=True,
                message=f"Successfully typed {len(text)} characters",
                data={"text": text, "length": len(text)}
            )
            
        except pyautogui.FailSafeException:
            error_msg = "PyAutoGUI FAILSAFE triggered during text typing"
            self.logger.critical(error_msg)
            return ExecutionResult(success=False, message=error_msg)
            
        except Exception as e:
            error_msg = f"Failed to type text: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def key_press(self, key: str) -> ExecutionResult:
        """Press a key or key combination."""
        try:
            # Handle hotkey combinations (e.g., "ctrl+c", "alt+tab")
            if "+" in key:
                keys = [k.strip().lower() for k in key.split("+")]
                
                # Validate all keys
                invalid_keys = [k for k in keys if k not in self.valid_keys]
                if invalid_keys:
                    return ExecutionResult(
                        success=False,
                        message=f"Invalid keys: {invalid_keys}. Valid keys: {list(self.valid_keys)[:10]}..."
                    )
                
                pyautogui.hotkey(*keys)
                self.logger.debug(f"Pressed hotkey combination: {keys}")
                
                return ExecutionResult(
                    success=True,
                    message=f"Successfully pressed hotkey: {key}",
                    data={"keys": keys, "type": "hotkey"}
                )
            
            else:
                # Single key press
                key_lower = key.lower()
                if key_lower not in self.valid_keys:
                    return ExecutionResult(
                        success=False,
                        message=f"Invalid key: '{key}'. Valid keys: {list(self.valid_keys)[:10]}..."
                    )
                
                pyautogui.press(key_lower)
                self.logger.debug(f"Pressed key: '{key_lower}'")
                
                return ExecutionResult(
                    success=True,
                    message=f"Successfully pressed key: {key}",
                    data={"key": key_lower, "type": "single"}
                )
                
        except pyautogui.FailSafeException:
            error_msg = "PyAutoGUI FAILSAFE triggered during key press"
            self.logger.critical(error_msg)
            return ExecutionResult(success=False, message=error_msg)
            
        except Exception as e:
            error_msg = f"Failed to press key '{key}': {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> ExecutionResult:
        """Perform a drag action."""
        try:
            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            
            for name, x, y in [("start", start_x, start_y), ("end", end_x, end_y)]:
                if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                    return ExecutionResult(
                        success=False,
                        message=f"{name.capitalize()} coordinates ({x}, {y}) are outside screen bounds"
                    )
            
            # Perform drag
            pyautogui.drag(end_x - start_x, end_y - start_y, duration=0.5, button='left')
            
            self.logger.debug(f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
            return ExecutionResult(
                success=True,
                message=f"Successfully dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})",
                data={
                    "start_x": start_x, "start_y": start_y,
                    "end_x": end_x, "end_y": end_y,
                    "distance": ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
                }
            )
            
        except pyautogui.FailSafeException:
            error_msg = "PyAutoGUI FAILSAFE triggered during drag"
            self.logger.critical(error_msg)
            return ExecutionResult(success=False, message=error_msg)
            
        except Exception as e:
            error_msg = f"Failed to perform drag: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def scroll(self, x: int, y: int, direction: str, amount: int) -> ExecutionResult:
        """Perform a scroll action."""
        try:
            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                return ExecutionResult(
                    success=False,
                    message=f"Coordinates ({x}, {y}) are outside screen bounds"
                )
            
            # Validate direction and convert to scroll amount
            if direction.lower() == "up":
                scroll_amount = abs(amount)
            elif direction.lower() == "down":
                scroll_amount = -abs(amount)
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Invalid direction: '{direction}'. Must be 'up' or 'down'"
                )
            
            # Move to position and scroll
            pyautogui.moveTo(x, y)
            pyautogui.scroll(scroll_amount)
            
            self.logger.debug(f"Scrolled {direction} by {amount} at ({x}, {y})")
            
            return ExecutionResult(
                success=True,
                message=f"Successfully scrolled {direction} by {amount} at ({x}, {y})",
                data={"x": x, "y": y, "direction": direction, "amount": amount}
            )
            
        except pyautogui.FailSafeException:
            error_msg = "PyAutoGUI FAILSAFE triggered during scroll"
            self.logger.critical(error_msg)
            return ExecutionResult(success=False, message=error_msg)
            
        except Exception as e:
            error_msg = f"Failed to perform scroll: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def execute_complex_action(self, action_spec: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a complex action based on specification.
        
        This method provides compatibility with the existing action execution system
        while maintaining the new interface structure.
        """
        try:
            action_type = action_spec.get("type")
            
            if action_type == "click":
                # Handle coordinate calculation
                coords = self._get_target_coords(action_spec, context or {})
                if not coords:
                    return ExecutionResult(
                        success=False,
                        message="Could not determine target coordinates for click"
                    )
                
                button = action_spec.get("button", "left")
                return self.click(coords[0], coords[1], button)
                
            elif action_type == "type_text":
                text = action_spec.get("text", "")
                return self.type_text(text)
                
            elif action_type == "press_key":
                key = action_spec.get("key", "")
                return self.key_press(key)
                
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Unknown action type: {action_type}"
                )
                
        except Exception as e:
            error_msg = f"Failed to execute complex action: {e}"
            self.logger.error(error_msg)
            return ExecutionResult(success=False, message=error_msg)
    
    def _get_target_coords(self, action_spec: Dict[str, Any], context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Calculate target coordinates based on action specification and context."""
        try:
            target_relation = action_spec.get("target_relation")
            
            if target_relation == "absolute":
                x = action_spec.get("x")
                y = action_spec.get("y")
                if x is not None and y is not None:
                    return (int(x), int(y))
            
            elif target_relation in ["center_of_gemini_element", "top_left_of_gemini_element"]:
                # Handle Gemini element targeting
                gemini_var_name = action_spec.get("gemini_element_variable")
                if not gemini_var_name:
                    return None
                
                variables = context.get("variables", {})
                element_data = variables.get(gemini_var_name, {})
                
                if not isinstance(element_data, dict):
                    return None
                
                element_value = element_data.get("value", {})
                if not element_value.get("found"):
                    return None
                
                box = element_value.get("box")
                if not isinstance(box, list) or len(box) != 4:
                    return None
                
                x, y, w, h = [int(coord) for coord in box]
                
                if target_relation == "center_of_gemini_element":
                    return (x + w // 2, y + h // 2)
                else:  # top_left_of_gemini_element
                    return (x, y)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error calculating target coordinates: {e}")
            return None
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get ActionExecutor-specific status."""
        try:
            screen_size = pyautogui.size()
            mouse_pos = pyautogui.position()
            
            return {
                "screen_size": screen_size,
                "mouse_position": mouse_pos,
                "failsafe_enabled": pyautogui.FAILSAFE,
                "pause_duration": pyautogui.PAUSE,
                "safety_checks": getattr(self.config, 'safety_checks', False),
                "verification_enabled": getattr(self.config, 'verification_enabled', False),
            }
            
        except Exception as e:
            self.logger.error(f"Error getting ActionExecutor status: {e}")
            return {"error": str(e)}