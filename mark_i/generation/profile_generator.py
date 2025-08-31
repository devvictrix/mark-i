import logging
import json
import copy
import os
from typing import Dict, Any, Optional, List

import numpy as np
from PIL import Image
import cv2

from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.core.config_manager import ConfigManager, TEMPLATES_SUBDIR_NAME
from mark_i.generation.strategy_planner import IntermediatePlan, IntermediatePlanStep
from mark_i.ui.gui.gui_config import CONDITION_TYPES as ALL_CONDITION_TYPES_FROM_CONFIG, ACTION_TYPES as ALL_ACTION_TYPES_FROM_CONFIG


from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.generation.profile_generator")

DEFAULT_REGION_STRUCTURE_PG = {"name": "", "x": 10, "y": 10, "width": 200, "height": 150, "comment": "AI-suggested region placeholder"}
DEFAULT_CONDITION_STRUCTURE_PG = {"type": "always_true", "comment": "AI-suggested condition placeholder"}
DEFAULT_ACTION_STRUCTURE_PG = {"type": "log_message", "message": "AI-suggested action placeholder executed", "level": "INFO", "comment": "AI-suggested action placeholder"}
DEFAULT_RULE_STRUCTURE_PG = {"name": "", "region": "", "condition": {}, "action": {}, "comment": "AI-generated rule placeholder"}
DEFAULT_TEMPLATE_STRUCTURE_PG = {"name": "", "filename": "placeholder_template.png", "comment": "AI-suggested template placeholder - user must capture"}

DEFAULT_REGION_SUGGESTION_MODEL = "gemini-2.0-flash-lite"
DEFAULT_LOGIC_SUGGESTION_MODEL = "gemini-1.5-flash-latest"
DEFAULT_ELEMENT_REFINE_MODEL = "gemini-2.0-flash-lite"


class ProfileGenerator:
    """
    Takes an "intermediate_plan" and interactively guides the user (via GUI)
    to translate each plan step into Mark-I profile elements.
    Uses GeminiAnalyzer for AI-assisted suggestions for regions, conditions, actions,
    and refining element locations.
    Handles staging and saving of new template images.
    """

    def __init__(self, gemini_analyzer: GeminiAnalyzer, config_manager: ConfigManager):
        if not isinstance(gemini_analyzer, GeminiAnalyzer) or not gemini_analyzer.client_initialized:
            logger.critical("ProfileGenerator CRITICAL: Initialized with invalid/uninitialized GeminiAnalyzer. AI-assist will fail.")
            raise ValueError("Valid, initialized GeminiAnalyzer instance required for ProfileGenerator.")
        self.gemini_analyzer = gemini_analyzer

        if not isinstance(config_manager, ConfigManager):
            logger.critical("ProfileGenerator CRITICAL: Initialized without valid ConfigManager. Profile saving will fail.")
            raise ValueError("ConfigManager instance required for ProfileGenerator.")
        self.config_manager_for_generated_profile = config_manager

        self.intermediate_plan: Optional[IntermediatePlan] = None
        self.current_plan_step_index: int = -1
        self.generated_profile_data: Dict[str, Any] = {}
        self.current_full_visual_context_np: Optional[np.ndarray] = None

        logger.info("ProfileGenerator initialized with AI-assist capabilities.")

    def start_profile_generation(
        self,
        intermediate_plan: IntermediatePlan,
        profile_description: str = "AI-Generated Profile",
        initial_profile_settings: Optional[Dict[str, Any]] = None,
        initial_full_screen_context_np: Optional[np.ndarray] = None,
    ):
        if not isinstance(intermediate_plan, list):
            logger.warning("ProfileGenerator: Starting with an invalid intermediate plan.")
            self.intermediate_plan = []
        else:
            self.intermediate_plan = intermediate_plan

        self.current_plan_step_index = -1

        self.config_manager_for_generated_profile._initialize_default_profile_data()
        self.generated_profile_data = self.config_manager_for_generated_profile.get_profile_data()

        self.generated_profile_data["profile_description"] = profile_description
        if initial_profile_settings and isinstance(initial_profile_settings, dict):
            self.generated_profile_data["settings"].update(initial_profile_settings)

        self.generated_profile_data.setdefault("regions", [])
        self.generated_profile_data.setdefault("templates", [])
        self.generated_profile_data.setdefault("rules", [])

        if initial_full_screen_context_np is not None and isinstance(initial_full_screen_context_np, np.ndarray):
            self.current_full_visual_context_np = initial_full_screen_context_np
        else:
            self.current_full_visual_context_np = None

        logger.info(f"ProfileGenerator: New profile generation started. Plan has {len(self.intermediate_plan)} steps.")
        return True

    def set_current_visual_context(self, screen_capture_np: Optional[np.ndarray]):
        if screen_capture_np is not None and isinstance(screen_capture_np, np.ndarray):
            self.current_full_visual_context_np = screen_capture_np
        elif screen_capture_np is None:
            self.current_full_visual_context_np = None
        else:
            logger.warning("PG: Invalid visual context provided (not NumPy array or None).")

    def get_current_plan_step(self) -> Optional[IntermediatePlanStep]:
        if self.intermediate_plan and 0 <= self.current_plan_step_index < len(self.intermediate_plan):
            return self.intermediate_plan[self.current_plan_step_index]
        return None

    def advance_to_next_plan_step(self) -> Optional[IntermediatePlanStep]:
        if not self.intermediate_plan:
            return None
        if self.current_plan_step_index < len(self.intermediate_plan) - 1:
            self.current_plan_step_index += 1
            return self.intermediate_plan[self.current_plan_step_index]
        else:
            self.current_plan_step_index = len(self.intermediate_plan)
            return None

    def suggest_region_for_step(self, plan_step: IntermediatePlanStep) -> Optional[Dict[str, Any]]:
        log_prefix = f"PG.SuggestRegion (StepID: {plan_step.get('step_id', 'N/A')})"
        step_description = plan_step.get("description", "")
        if not self.gemini_analyzer or self.current_full_visual_context_np is None or not step_description:
            logger.error(f"{log_prefix}: Prerequisite missing (analyzer, context image, or step description).")
            return None

        prompt = (
            f"You are an AI assistant helping to define regions for visual automation. "
            f'The user is working on an automation step described as: "{step_description}".\n'
            f"Analyze the provided full screen image.\n"
            f"Identify the single most relevant rectangular region (bounding box) on this image for executing this task step.\n"
            f"Respond ONLY with a single JSON object with these keys:\n"
            f'  - "box": [x, y, width, height] (integers, relative to the top-left of the image).\n'
            f'  - "reasoning": "A brief explanation for your choice."\n'
            f'  - "suggested_region_name_hint": "A short, descriptive, snake_case name hint for this region".'
        )
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=self.current_full_visual_context_np, model_name_override=DEFAULT_REGION_SUGGESTION_MODEL)

        if response["status"] == "success" and response["json_content"]:
            try:
                content = response["json_content"]
                if isinstance(content, dict) and isinstance(content.get("box"), list) and len(content["box"]) == 4:
                    int_box = [int(round(n)) for n in content["box"]]
                    name_hint = "".join(c if c.isalnum() else "_" for c in str(content.get("suggested_region_name_hint", ""))).lower()
                    return {"box": int_box, "reasoning": str(content.get("reasoning", "")), "suggested_region_name_hint": name_hint}
            except Exception as e:
                logger.error(f"{log_prefix}: Error parsing suggestion JSON: {e}", exc_info=True)
        return None

    def suggest_logic_for_step(self, plan_step: IntermediatePlanStep, focused_region_image: np.ndarray, focused_region_name: str) -> Optional[Dict[str, Any]]:
        log_prefix = f"PG.SuggestLogic (StepID: {plan_step.get('step_id')}, Region: '{focused_region_name}')"
        step_description = plan_step.get("description", "")
        if not self.gemini_analyzer or focused_region_image is None or not step_description:
            logger.error(f"{log_prefix}: Prerequisite missing (analyzer, region image, or step description).")
            return None

        prompt = (
            f"You are an AI expert for the Mark-I visual automation tool.\n"
            f'Current Plan Step: "{step_description}" for region named "{focused_region_name}".\n'
            f"Suggest one Mark-I 'condition' object and one 'action' object to implement this step.\n"
            f"Valid condition types: {json.dumps(ALL_CONDITION_TYPES_FROM_CONFIG)}.\n"
            f"Valid action types: {json.dumps(ALL_ACTION_TYPES_FROM_CONFIG)}.\n"
            f"If interaction with a specific UI element is needed, the 'action' *MUST* include a 'target_description' field.\n"
            f"For parameters requiring user data, use placeholders like 'USER_INPUT_REQUIRED__param_name'.\n"
            f"Respond ONLY with a single JSON object with keys: \"suggested_condition\", \"suggested_action\", \"element_to_refine_description\", \"reasoning\"."
        )
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=focused_region_image, model_name_override=DEFAULT_LOGIC_SUGGESTION_MODEL)
        
        if response["status"] == "success" and response["json_content"]:
            try:
                content = response["json_content"]
                if isinstance(content, dict) and isinstance(content.get("suggested_condition"), dict) and isinstance(content.get("suggested_action"), dict):
                    return content
            except Exception as e:
                logger.error(f"{log_prefix}: Error parsing logic suggestion JSON: {e}", exc_info=True)
        return None

    def refine_element_location(self, element_description: str, focused_region_image: np.ndarray, focused_region_name: str) -> Optional[List[Dict[str, Any]]]:
        log_prefix = f"PG.RefineElement (Elem: '{element_description[:30]}...')"
        if not self.gemini_analyzer or focused_region_image is None or not element_description:
            logger.error(f"{log_prefix}: Prerequisite missing (analyzer, region image, or element description).")
            return None

        prompt = (
            f"In the image of region '{focused_region_name}', identify all elements matching: \"{element_description}\".\n"
            f'Output ONLY JSON: {{"elements": [{{"found": true, "box": [x,y,w,h], "label_suggestion":"...", "confidence_score": 0.0_to_1.0}}]}}.'
        )
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=focused_region_image, model_name_override=DEFAULT_ELEMENT_REFINE_MODEL)
        
        if response["status"] == "success" and response["json_content"]:
            try:
                content = response["json_content"]
                if isinstance(content, dict) and isinstance(content.get("elements"), list):
                    return [
                        {"box": [int(round(n)) for n in elem.get("box", [])], "label_suggestion": elem.get("label_suggestion"), "confidence": elem.get("confidence_score")}
                        for elem in content["elements"] if elem.get("found") and isinstance(elem.get("box"), list) and len(elem["box"]) == 4
                    ]
            except Exception as e:
                logger.error(f"{log_prefix}: Error parsing refinement JSON: {e}", exc_info=True)
        return None

    def add_region_definition(self, region_data: Dict[str, Any]) -> bool:
        if not (isinstance(region_data, dict) and region_data.get("name") and all(k in region_data for k in ["x", "y", "width", "height"])):
            return False
        existing = self.generated_profile_data.setdefault("regions", [])
        self.generated_profile_data["regions"] = [r for r in existing if r.get("name") != region_data["name"]]
        self.generated_profile_data["regions"].append({**copy.deepcopy(DEFAULT_REGION_STRUCTURE_PG), **region_data})
        return True

    def add_template_definition(self, template_data: Dict[str, Any]) -> bool:
        if not (isinstance(template_data, dict) and template_data.get("name") and template_data.get("filename")):
            return False
        self.generated_profile_data.setdefault("templates", []).append({**copy.deepcopy(DEFAULT_TEMPLATE_STRUCTURE_PG), **template_data})
        return True

    def add_rule_definition(self, rule_data: Dict[str, Any]) -> bool:
        if not (isinstance(rule_data, dict) and rule_data.get("name")):
            return False
        existing = self.generated_profile_data.setdefault("rules", [])
        self.generated_profile_data["rules"] = [r for r in existing if r.get("name") != rule_data["name"]]
        self.generated_profile_data["rules"].append({**copy.deepcopy(DEFAULT_RULE_STRUCTURE_PG), **rule_data})
        return True

    def get_generated_profile_data(self) -> Dict[str, Any]:
        profile_copy = copy.deepcopy(self.generated_profile_data)
        if "templates" in profile_copy and isinstance(profile_copy["templates"], list):
            for tpl in profile_copy["templates"]:
                if isinstance(tpl, dict):
                    tpl.pop("_image_data_np_for_save", None)
        return profile_copy

    def save_generated_profile(self, filepath_to_save: str) -> bool:
        if not self.generated_profile_data or not filepath_to_save:
            return False

        profile_data_for_json = self.get_generated_profile_data()
        staged_templates = [tpl for tpl in self.generated_profile_data.get("templates", []) if "_image_data_np_for_save" in tpl]

        self.config_manager_for_generated_profile.update_profile_data(profile_data_for_json)
        if not self.config_manager_for_generated_profile.save_current_profile(filepath_to_save):
            return False
        
        profile_base_dir = self.config_manager_for_generated_profile.get_profile_base_path()
        if not profile_base_dir: return False
        
        templates_target_dir = os.path.join(profile_base_dir, TEMPLATES_SUBDIR_NAME)
        os.makedirs(templates_target_dir, exist_ok=True)
        
        for tpl_data in staged_templates:
            try:
                cv2.imwrite(os.path.join(templates_target_dir, tpl_data["filename"]), tpl_data["_image_data_np_for_save"])
            except Exception as e:
                logger.error(f"Failed to save template image '{tpl_data['filename']}': {e}", exc_info=True)
        return True