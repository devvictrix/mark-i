import logging
from typing import Dict, List, Any, Optional  # Added this line

# Use __name__ for module-level logger for better organization if this module grows.
# For now, simple print or direct APP_ROOT_LOGGER_NAME if complex logging needed here.
# logger = logging.getLogger(__name__)
# from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
# logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.gui_config")

# --- Constants ---
DEFAULT_PROFILE_STRUCTURE: Dict[str, Any] = {  # Added type hint
    "profile_description": "New Profile",
    "settings": {
        "monitoring_interval_seconds": 1.0,
        "analysis_dominant_colors_k": 3,
        "tesseract_cmd_path": None,  # Optional path to tesseract executable
        "tesseract_config_custom": "",  # Custom tesseract config string, e.g., "--psm 6"
        "gemini_default_model_name": "gemini-1.5-flash-latest",  # Default model for Gemini features
    },
    "regions": [],
    "templates": [],
    "rules": [],
}

MAX_PREVIEW_WIDTH: int = 200  # Max width for template image previews in GUI
MAX_PREVIEW_HEIGHT: int = 150  # Max height for template image previews in GUI

# --- Wizard and Generation View Constants (NEW - Moved from profile_creation_wizard.py) ---
WIZARD_SCREENSHOT_PREVIEW_MAX_WIDTH = 600
WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT = 380
CANDIDATE_BOX_COLORS = ["#FF00FF", "#00FFFF", "#FFFF00", "#F08080", "#90EE90", "#ADD8E6", "#FFC0CB", "#E6E6FA"]
SELECTED_CANDIDATE_BOX_COLOR = "lime green"
FONT_PATH_PRIMARY = "arial.ttf"
FONT_PATH_FALLBACK = "DejaVuSans.ttf"


# --- Dropdown Options ---
CONDITION_TYPES: List[str] = [
    "pixel_color",
    "average_color_is",
    "template_match_found",
    "ocr_contains_text",
    "dominant_color_matches",
    "gemini_vision_query",  # AI-powered visual question answering
    "always_true",  # For unconditional rule execution or testing
]

ACTION_TYPES: List[str] = ["click", "type_text", "press_key", "log_message", "gemini_perform_task"]  # AI-driven task execution (goal-based and NLU-based)

LOGICAL_OPERATORS: List[str] = ["AND", "OR"]  # For compound conditions

CLICK_TARGET_RELATIONS: List[str] = [
    "center_of_region",
    "center_of_last_match",
    "absolute",
    "relative_to_region",
    "center_of_gemini_element",  # Target center of Gemini-identified bounding box
    "top_left_of_gemini_element",  # Target top-left of Gemini-identified bounding box
]

CLICK_BUTTONS: List[str] = ["left", "middle", "right", "primary", "secondary"]  # PyAutoGUI valid button names

LOG_LEVELS: List[str] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]  # For log_message action

# For 'gemini_perform_task' action's 'allowed_actions_override' parameter.
# These should match the keys in GeminiDecisionModule.PREDEFINED_ALLOWED_SUB_ACTIONS.
# This list is for UI presentation (e.g., tooltips, validation hints).
# The actual enforcement happens in GeminiDecisionModule.
GEMINI_TASK_ALLOWED_PRIMITIVE_ACTIONS_FOR_UI_HINT: List[str] = [
    "CLICK_DESCRIBED_ELEMENT",
    "TYPE_IN_DESCRIBED_FIELD",
    "PRESS_KEY_SIMPLE",
    "CHECK_VISUAL_STATE",
    # "WAIT_SHORT" # Add if/when implemented
]

# --- Data-driven UI Parameter Configuration ---
# This dictionary defines the parameters for each condition and action type,
# driving how the DetailsPanel in the GUI dynamically renders input fields.
#
# Structure for each parameter definition:
# {
#   "id": "internal_parameter_name",                 // Key used in JSON profile
#   "label": "User-Friendly Label:",                 // Text shown in GUI
#   "widget": "entry" | "textbox" | "optionmenu_static" | "optionmenu_dynamic" | "checkbox",
#   "type": python_type | "bgr_string" | "list_str_csv", // Expected data type for validation
#   "group": "Group Header Name",                    // (NEW) Optional header for visual grouping
#   "default": default_value,                        // Default value for this parameter
#   "required": True | False,                        // Is this parameter mandatory?
#   "placeholder": "Hint text for entry/textbox",    // Optional
#   "allow_empty_string": True | False,              // For string types, if "" is a valid value (even if required)
#   "min_val": number, "max_val": number,            // For numeric types
#   "options_source": "regions" | "templates",      // For optionmenu_dynamic
#   "options_const_key": "KEY_IN_OPTIONS_CONST_MAP", // For optionmenu_static
#   "height": number,                                // For CTkTextbox height
#   "condition_show": {                             // Optional: for conditional visibility
#       "field_id_prefix": "act_" | "cond_" | "subcond_", // Prefix of the CONTROLLING widget's ID
#       "field": "controlling_parameter_id",         // ID of the CONTROLLING parameter
#       "values": ["value1", "value2"]               // Show this param IF controller's value is one of these
#   }
# }
UI_PARAM_CONFIG: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "conditions": {
        "pixel_color": [
            {"id": "relative_x", "label": "Relative X:", "widget": "entry", "type": int, "default": 0, "required": True, "placeholder": "0", "group": "Targeting"},
            {"id": "relative_y", "label": "Relative Y:", "widget": "entry", "type": int, "default": 0, "required": True, "placeholder": "0", "group": "Targeting"},
            {
                "id": "expected_bgr",
                "label": "Expected BGR:",
                "widget": "entry",
                "type": "bgr_string",
                "default": "0,0,0",
                "required": True,
                "placeholder": "B,G,R e.g., 255,0,128",
                "group": "Color Matching",
            },
            {
                "id": "tolerance",
                "label": "Tolerance (0-255):",
                "widget": "entry",
                "type": int,
                "default": 0,
                "required": True,
                "min_val": 0,
                "max_val": 255,
                "placeholder": "0",
                "group": "Color Matching",
            },
            {"id": "region", "label": "Target Region (Override):", "widget": "optionmenu_dynamic", "options_source": "regions", "type": str, "default": "", "required": False, "group": "Scope"},
        ],
        "average_color_is": [
            {
                "id": "expected_bgr",
                "label": "Expected Avg BGR:",
                "widget": "entry",
                "type": "bgr_string",
                "default": "128,128,128",
                "required": True,
                "placeholder": "B,G,R",
                "group": "Color Matching",
            },
            {
                "id": "tolerance",
                "label": "Tolerance (0-255):",
                "widget": "entry",
                "type": int,
                "default": 10,
                "required": True,
                "min_val": 0,
                "max_val": 255,
                "placeholder": "10",
                "group": "Color Matching",
            },
            {"id": "region", "label": "Target Region (Override):", "widget": "optionmenu_dynamic", "options_source": "regions", "type": str, "default": "", "required": False, "group": "Scope"},
        ],
        "template_match_found": [
            {"id": "template_name", "label": "Template Name:", "widget": "optionmenu_dynamic", "options_source": "templates", "type": str, "default": "", "required": True, "group": "Template"},
            {
                "id": "min_confidence",
                "label": "Min Confidence (0.0-1.0):",
                "widget": "entry",
                "type": float,
                "default": 0.8,
                "required": True,
                "min_val": 0.0,
                "max_val": 1.0,
                "placeholder": "0.8",
                "group": "Matching Parameters",
            },
            {
                "id": "capture_as",
                "label": "Capture Match As:",
                "widget": "entry",
                "type": str,
                "default": "",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "Optional variable name",
                "group": "Output",
            },
            {"id": "region", "label": "Target Region (Override):", "widget": "optionmenu_dynamic", "options_source": "regions", "type": str, "default": "", "required": False, "group": "Scope"},
        ],
        "ocr_contains_text": [
            {
                "id": "text_to_find",
                "label": "Text to Find (CSV for OR):",
                "widget": "entry",
                "type": "list_str_csv",
                "default": [],
                "required": True,
                "placeholder": "keyword1,another keyword",
                "group": "Text Matching",
            },
            {"id": "case_sensitive", "label": "Case Sensitive Search", "widget": "checkbox", "type": bool, "default": False, "required": False, "group": "Text Matching"},
            {
                "id": "min_ocr_confidence",
                "label": "Min OCR Confidence (0-100, Optional):",
                "widget": "entry",
                "type": float,
                "default": 70.0,
                "required": False,
                "allow_empty_string": True,
                "min_val": 0.0,
                "max_val": 100.0,
                "placeholder": "e.g., 70.0",
                "group": "OCR Parameters",
            },
            {
                "id": "capture_as",
                "label": "Capture Full OCR Text As:",
                "widget": "entry",
                "type": str,
                "default": "",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "Optional variable name",
                "group": "Output",
            },
            {"id": "region", "label": "Target Region (Override):", "widget": "optionmenu_dynamic", "options_source": "regions", "type": str, "default": "", "required": False, "group": "Scope"},
        ],
        "dominant_color_matches": [
            {"id": "expected_bgr", "label": "Expected Dom. BGR:", "widget": "entry", "type": "bgr_string", "default": "0,0,255", "required": True, "placeholder": "B,G,R", "group": "Color Matching"},
            {
                "id": "tolerance",
                "label": "Tolerance (0-255):",
                "widget": "entry",
                "type": int,
                "default": 10,
                "required": True,
                "min_val": 0,
                "max_val": 255,
                "placeholder": "10",
                "group": "Color Matching",
            },
            {
                "id": "check_top_n_dominant",
                "label": "Check Top N Colors:",
                "widget": "entry",
                "type": int,
                "default": 1,
                "required": True,
                "min_val": 1,
                "placeholder": "1 to K (from settings)",
                "group": "Analysis Parameters",
            },
            {
                "id": "min_percentage",
                "label": "Min % Occurrence (0-100):",
                "widget": "entry",
                "type": float,
                "default": 5.0,
                "required": False,
                "min_val": 0.0,
                "max_val": 100.0,
                "placeholder": "5.0",
                "group": "Analysis Parameters",
            },
            {"id": "region", "label": "Target Region (Override):", "widget": "optionmenu_dynamic", "options_source": "regions", "type": str, "default": "", "required": False, "group": "Scope"},
        ],
        "gemini_vision_query": [
            {
                "id": "prompt",
                "label": "Gemini Vision Prompt:",
                "widget": "textbox",
                "type": str,
                "default": "Describe this image in detail.",
                "required": True,
                "placeholder": "e.g., Is there a login button visible? If so, describe it.",
                "height": 100,
                "group": "AI Prompt",
            },
            {
                "id": "expected_response_contains",
                "label": "Response Contains (CSV for OR, Optional):",
                "widget": "entry",
                "type": "list_str_csv",
                "default": [],
                "required": False,
                "allow_empty_string": True,
                "placeholder": "keyword1,keyword2",
                "group": "Validation",
            },
            {"id": "case_sensitive_response_check", "label": "Case Sensitive (for 'Contains')", "widget": "checkbox", "type": bool, "default": False, "required": False, "group": "Validation"},
            {
                "id": "expected_response_json_path",
                "label": "JSON Path in Response (Dot Notation, Optional):",
                "widget": "entry",
                "type": str,
                "default": "",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "e.g., data.items.0.name",
                "group": "Validation",
            },
            {
                "id": "expected_json_value",
                "label": "Expected JSON Value (String, Optional):",
                "widget": "entry",
                "type": str,
                "default": "",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "Value at JSON path",
                "group": "Validation",
            },
            {
                "id": "capture_as",
                "label": "Capture Gemini Response As:",
                "widget": "entry",
                "type": str,
                "default": "",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "Optional variable name",
                "group": "Output",
            },
            {
                "id": "model_name",
                "label": "Gemini Model (Override Profile Default, Optional):",
                "widget": "entry",
                "type": str,
                "default": "",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "e.g., gemini-1.5-flash-latest",
                "group": "AI Configuration",
            },
            {"id": "region", "label": "Target Region (Override):", "widget": "optionmenu_dynamic", "options_source": "regions", "type": str, "default": "", "required": False, "group": "Scope"},
        ],
        "always_true": [
            {
                "id": "region",
                "label": "Context Region (Optional Override):",
                "widget": "optionmenu_dynamic",
                "options_source": "regions",
                "type": str,
                "default": "",
                "required": False,
                "placeholder": "Usually not needed for always_true",
                "group": "Scope",
            }
        ],
    },
    "actions": {
        "click": [
            {
                "id": "target_relation",
                "label": "Target Relation:",
                "widget": "optionmenu_static",
                "options_const_key": "CLICK_TARGET_RELATIONS",
                "type": str,
                "default": "center_of_region",
                "required": True,
                "group": "Targeting",
            },
            {
                "id": "target_region",
                "label": "Target Region (if relation needs it):",
                "widget": "optionmenu_dynamic",
                "options_source": "regions",
                "type": str,
                "default": "",
                "required": False,
                "condition_show": {"field_id_prefix": "act_", "field": "target_relation", "values": ["center_of_region", "relative_to_region"]},
                "group": "Targeting",
            },
            {
                "id": "x",
                "label": "X Coord/Offset (if relation needs it):",
                "widget": "entry",
                "type": str,
                "default": "0",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "Abs/Rel X or {var}",
                "condition_show": {"field_id_prefix": "act_", "field": "target_relation", "values": ["absolute", "relative_to_region"]},
                "group": "Targeting",
            },
            {
                "id": "y",
                "label": "Y Coord/Offset (if relation needs it):",
                "widget": "entry",
                "type": str,
                "default": "0",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "Abs/Rel Y or {var}",
                "condition_show": {"field_id_prefix": "act_", "field": "target_relation", "values": ["absolute", "relative_to_region"]},
                "group": "Targeting",
            },
            {
                "id": "gemini_element_variable",
                "label": "Gemini Element Variable (if relation needs it):",
                "widget": "entry",
                "type": str,
                "default": "",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "e.g., captured_button_data",
                "condition_show": {"field_id_prefix": "act_", "field": "target_relation", "values": ["center_of_gemini_element", "top_left_of_gemini_element"]},
                "group": "Targeting",
            },
            {
                "id": "button",
                "label": "Mouse Button:",
                "widget": "optionmenu_static",
                "options_const_key": "CLICK_BUTTONS",
                "type": str,
                "default": "left",
                "required": True,
                "group": "Click Properties",
            },
            {
                "id": "clicks",
                "label": "Number of Clicks:",
                "widget": "entry",
                "type": str,
                "default": "1",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "1 or {var}",
                "group": "Click Properties",
            },
            {
                "id": "interval",
                "label": "Interval Betw. Clicks (s):",
                "widget": "entry",
                "type": str,
                "default": "0.0",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "0.0 or {var}",
                "group": "Click Properties",
            },
            {
                "id": "pyautogui_pause_before",
                "label": "Pause Before Action (s):",
                "widget": "entry",
                "type": str,
                "default": "0.0",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "0.0 or {var}",
                "group": "Timing",
            },
        ],
        "type_text": [
            {
                "id": "text",
                "label": "Text to Type:",
                "widget": "textbox",
                "type": str,
                "default": "",
                "required": True,
                "allow_empty_string": True,
                "placeholder": "Enter text here or use {variable}",
                "height": 80,
                "group": "Content",
            },
            {
                "id": "interval",
                "label": "Interval Betw. Keystrokes (s):",
                "widget": "entry",
                "type": str,
                "default": "0.0",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "0.0 or {var}",
                "group": "Typing Properties",
            },
            {
                "id": "pyautogui_pause_before",
                "label": "Pause Before Action (s):",
                "widget": "entry",
                "type": str,
                "default": "0.0",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "0.0 or {var}",
                "group": "Timing",
            },
        ],
        "press_key": [
            {
                "id": "key",
                "label": "Key(s) to Press (CSV for hotkey):",
                "widget": "entry",
                "type": str,
                "default": "enter",
                "required": True,
                "placeholder": "e.g., enter OR ctrl,alt,delete OR {my_key_var}",
                "group": "Key Input",
            },
            {
                "id": "pyautogui_pause_before",
                "label": "Pause Before Action (s):",
                "widget": "entry",
                "type": str,
                "default": "0.0",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "0.0 or {var}",
                "group": "Timing",
            },
        ],
        "log_message": [
            {
                "id": "message",
                "label": "Log Message:",
                "widget": "textbox",
                "type": str,
                "default": "Rule triggered log message.",
                "required": True,
                "allow_empty_string": True,
                "placeholder": "Your log message or {variable}",
                "height": 80,
                "group": "Content",
            },
            {"id": "level", "label": "Log Level:", "widget": "optionmenu_static", "options_const_key": "LOG_LEVELS", "type": str, "default": "INFO", "required": True, "group": "Content"},
        ],
        "gemini_perform_task": [
            {
                "id": "natural_language_command",
                "label": "Natural Language Command for Gemini:",
                "widget": "textbox",
                "type": str,
                "default": "Example: Click the 'Next' button if it is visible.",
                "required": True,
                "height": 100,
                "placeholder": "Describe the task for Gemini...",
                "group": "AI Command",
            },
            {
                "id": "goal_prompt",
                "label": "Simple Goal Prompt (Legacy - Optional):",
                "widget": "textbox",
                "type": str,
                "default": "",
                "required": False,
                "allow_empty_string": True,
                "height": 60,
                "placeholder": "If NLU command is empty, use this simple goal.",
                "group": "AI Command",
            },
            {
                "id": "context_region_names",
                "label": "Context Regions (CSV, Optional):",
                "widget": "entry",
                "type": "list_str_csv",
                "default": [],
                "required": False,
                "allow_empty_string": True,
                "placeholder": "region1,main_screen (uses rule default if empty)",
                "group": "AI Context",
            },
            {
                "id": "allowed_actions_override",
                "label": "Allowed Sub-Actions by Gemini (CSV, Optional):",
                "widget": "entry",
                "type": "list_str_csv",
                "default": [],
                "required": False,
                "allow_empty_string": True,
                "placeholder": "e.g., CLICK_DESCRIBED_ELEMENT (see docs)",
                "group": "AI Configuration",
            },
            {"id": "require_confirmation_per_step", "label": "Confirm Each AI-Decided Step", "widget": "checkbox", "type": bool, "default": True, "required": False, "group": "AI Configuration"},
            {
                "id": "max_steps",
                "label": "Max NLU Task Steps:",
                "widget": "entry",
                "type": int,
                "default": 5,
                "required": False,
                "min_val": 1,
                "max_val": 25,
                "placeholder": "5",
                "group": "AI Configuration",
            },
            {
                "id": "pyautogui_pause_before",
                "label": "Pause Before Task Start (s):",
                "widget": "entry",
                "type": str,
                "default": "0.1",
                "required": False,
                "allow_empty_string": True,
                "placeholder": "0.1 or {var}",
                "group": "Timing",
            },
        ],
    },
}

# Mapping for static optionmenu sources
OPTIONS_CONST_MAP: Dict[str, List[str]] = {
    "CLICK_TARGET_RELATIONS": CLICK_TARGET_RELATIONS,
    "CLICK_BUTTONS": CLICK_BUTTONS,
    "LOG_LEVELS": LOG_LEVELS,
    "LOGICAL_OPERATORS": LOGICAL_OPERATORS,  # Added for consistency if needed, though usually hardcoded in UI
    "GEMINI_TASK_ALLOWED_ACTION_TYPES_FOR_UI": GEMINI_TASK_ALLOWED_PRIMITIVE_ACTIONS_FOR_UI_HINT,
}
