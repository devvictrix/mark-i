import numpy as np
from PIL import Image
from typing import Optional, Dict, Any, List

from mark_i.generation.strategy_planner import IntermediatePlan, IntermediatePlanStep


class WizardState:
    """
    Manages the persistent state and data for the AI Profile Creation Wizard.
    This class decouples the wizard's data from its UI presentation.
    """

    def __init__(self):
        self.user_goal_text: str = ""
        self.current_full_context_pil: Optional[Image.Image] = None
        self.current_full_context_np: Optional[np.ndarray] = None  # BGR NumPy array

        self.intermediate_plan: Optional[IntermediatePlan] = None
        self.current_plan_step_index: int = -1  # -1 means no step selected, 0 is first step

        # Data for the profile being generated (accumulated)
        self.generated_profile_data: Dict[str, Any] = {}
        self.generated_profile_name_base: str = "ai_generated_profile"

        # --- Current Step Specific Data (for Region and Logic Definition Pages) ---
        self.current_step_data: Optional[IntermediatePlanStep] = None  # The IntermediatePlanStep being defined
        self.current_step_region_name: Optional[str] = None
        self.current_step_region_coords: Optional[Dict[str, int]] = None  # {"x": ..., "y": ..., "width": ..., "height": ...}
        self.current_step_region_image_np: Optional[np.ndarray] = None  # Cropped BGR image of the defined region
        self.current_step_region_image_pil_for_display: Optional[Image.Image] = None  # PIL version of cropped region image

        # AI suggestions for the current logic definition step
        self.ai_suggested_condition_for_step: Optional[Dict[str, Any]] = None
        self.ai_suggested_action_for_step: Optional[Dict[str, Any]] = None
        self.ai_element_to_refine_desc: Optional[str] = None  # Text description of element needing bbox refinement

        # Refinement candidates and user selection for actions
        self.ai_refined_element_candidates: List[Dict[str, Any]] = []  # [{"box": [x,y,w,h], "label_suggestion":"...", "confidence":...}]
        self.user_selected_candidate_box_index: Optional[int] = None
        self.user_confirmed_element_for_action: Optional[Dict[str, Any]] = None  # The wrapped element data for ActionExecutor
        self.current_step_temp_gemini_var_name: Optional[str] = None  # Temporary var name for Gemini element in action

        # Temporary storage for captured templates (image data + metadata)
        # This will be processed by ProfileGenerator.save_generated_profile()
        self.staged_templates_with_image_data: List[Dict[str, Any]] = []

    def reset_for_new_profile(self):
        """Resets all wizard state variables for starting a new profile generation."""
        self.__init__()  # Simple way to reset all fields to their initial state

    def get_current_plan_step(self) -> Optional[IntermediatePlanStep]:
        if self.intermediate_plan and 0 <= self.current_plan_step_index < len(self.intermediate_plan):
            return self.intermediate_plan[self.current_plan_step_index]
        return None

    def get_next_plan_step(self) -> Optional[IntermediatePlanStep]:
        if self.intermediate_plan and (self.current_plan_step_index + 1) < len(self.intermediate_plan):
            return self.intermediate_plan[self.current_plan_step_index + 1]
        return None

    def get_previous_plan_step(self) -> Optional[IntermediatePlanStep]:
        if self.intermediate_plan and (self.current_plan_step_index - 1) >= 0:
            return self.intermediate_plan[self.current_plan_step_index - 1]
        return None
