import logging
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import json
import copy
import time
import threading
from typing import Optional, Dict, Any, List, Union, Callable, Tuple

import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk, ImageDraw, UnidentifiedImageError, ImageFont, ImageGrab

from mark_i.generation.strategy_planner import StrategyPlanner, IntermediatePlan, IntermediatePlanStep
from mark_i.generation.profile_generator import ProfileGenerator, DEFAULT_CONDITION_STRUCTURE_PG, DEFAULT_ACTION_STRUCTURE_PG
from mark_i.ui.gui.generation.wizard_state import WizardState  # New: Import WizardState
from mark_i.ui.gui.generation.sub_image_selector_window import SubImageSelectorWindow
from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.core.config_manager import ConfigManager, TEMPLATES_SUBDIR_NAME
from mark_i.engines.capture_engine import CaptureEngine

# Importing view classes (will be created next)
from mark_i.ui.gui.generation.views.goal_input_view import GoalInputView
from mark_i.ui.gui.generation.views.plan_review_view import PlanReviewView
from mark_i.ui.gui.generation.views.define_region_view import DefineRegionView
from mark_i.ui.gui.generation.views.define_logic_view import DefineLogicView
from mark_i.ui.gui.generation.views.final_review_view import FinalReviewView

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

# Import constants from the new central location
from mark_i.ui.gui.gui_config import FONT_PATH_PRIMARY, FONT_PATH_FALLBACK

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.generation.profile_creation_wizard")

# Page Constants (renamed for clarity with new structure)
WIZARD_PAGE_GOAL_INPUT = 0
WIZARD_PAGE_PLAN_REVIEW = 1
WIZARD_PAGE_DEFINE_REGION = 2
WIZARD_PAGE_DEFINE_LOGIC = 3
WIZARD_PAGE_FINAL_REVIEW_SAVE = 4


class ProfileCreationWizardWindow(ctk.CTkToplevel):
    """
    The main controller window for the AI-assisted profile creation wizard.
    It orchestrates the flow between different wizard pages (views), manages
    the overall wizard state (WizardState), and interacts with backend services
    (StrategyPlanner, ProfileGenerator). It is responsible for threading AI calls
    to maintain GUI responsiveness.
    """

    def __init__(self, master: Any, main_app_instance: Any):  # main_app_instance is MainAppWindow
        super().__init__(master)
        self.main_app_instance = main_app_instance
        self.title("AI Profile Creator Wizard")
        self.transient(master)
        self.grab_set()
        self.attributes("-topmost", True)
        self.geometry("1100x850")
        self.minsize(950, 750)
        self.protocol("WM_DELETE_WINDOW", self._on_close_wizard)
        self.user_cancelled_wizard = False
        self.newly_saved_profile_path: Optional[str] = None

        # --- Backend Components Initialization ---
        if (
            not hasattr(self.main_app_instance, "gemini_analyzer_instance")
            or not self.main_app_instance.gemini_analyzer_instance
            or not self.main_app_instance.gemini_analyzer_instance.client_initialized
        ):
            logger.critical("ProfileCreationWizard: GeminiAnalyzer not available or not initialized in MainApp. Cannot proceed.")
            messagebox.showerror(
                "Critical API Error", "Gemini API client is not properly initialized.\nPlease ensure your GEMINI_API_KEY is correctly set in .env and the application was restarted.", parent=self
            )
            self.after(100, self.destroy)
            return

        self.gemini_analyzer_instance: GeminiAnalyzer = self.main_app_instance.gemini_analyzer_instance
        self.strategy_planner = StrategyPlanner(gemini_analyzer=self.gemini_analyzer_instance)
        # ConfigManager for the *profile being generated*, not the app's main CM
        self.profile_generator_cm = ConfigManager(None, create_if_missing=True)
        self.profile_generator = ProfileGenerator(gemini_analyzer=self.gemini_analyzer_instance, config_manager=self.profile_generator_cm)
        self.capture_engine = CaptureEngine()

        # --- Wizard State Management ---
        self.state = WizardState()
        self.current_page_view: Optional[ctk.CTkFrame] = None  # Holds the currently displayed page frame

        # UI Frames & Controls
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        self.navigation_frame = ctk.CTkFrame(self, height=60, fg_color=("gray80", "gray20"), corner_radius=0)
        self.navigation_frame.pack(fill="x", side="bottom", padx=0, pady=0)
        self.navigation_frame.grid_columnconfigure(0, weight=1)
        self.navigation_frame.grid_columnconfigure(4, weight=1)
        self.btn_cancel = ctk.CTkButton(self.navigation_frame, text="Cancel & Close Wizard", command=self._on_close_wizard, width=180, fg_color="firebrick1", hover_color="firebrick3")
        self.btn_cancel.grid(row=0, column=1, padx=(20, 5), pady=10, sticky="w")
        self.btn_next = ctk.CTkButton(self.navigation_frame, text="Next >", command=self._go_to_next_page, width=140, font=ctk.CTkFont(weight="bold"))
        self.btn_next.grid(row=0, column=3, padx=(5, 20), pady=10, sticky="e")
        self.btn_previous = ctk.CTkButton(self.navigation_frame, text="< Previous Step", command=self._go_to_previous_page, width=140)
        self.btn_previous.grid(row=0, column=2, padx=5, pady=10, sticky="e")

        self.loading_overlay = ctk.CTkFrame(self, fg_color=("black", "black"), corner_radius=0)
        self.loading_label_overlay = ctk.CTkLabel(self.loading_overlay, text="AI is thinking...", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
        self.loading_label_overlay.pack(expand=True)

        try:
            self.overlay_font = ImageFont.truetype(FONT_PATH_PRIMARY, 11)
        except IOError:
            try:
                self.overlay_font = ImageFont.truetype(FONT_PATH_FALLBACK, 11)
            except IOError:
                self.overlay_font = ImageFont.load_default()
                logger.warning("Arial/DejaVuSans fonts not found for image overlays, using PIL default.")

        self._show_page(WIZARD_PAGE_GOAL_INPUT)  # Start at the first page
        logger.info("ProfileCreationWizardWindow initialized and Goal Input page shown.")
        self.after(150, self._center_window)

    def _show_loading_overlay(self, message="AI is thinking..."):
        self.loading_label_overlay.configure(text=message)
        self.loading_overlay.place(in_=self.main_content_frame, relx=0, rely=0, relwidth=1, relheight=1)
        self.loading_overlay.lift()
        self.update_idletasks()

    def _hide_loading_overlay(self):
        self.loading_overlay.place_forget()

    def _center_window(self):
        self.update_idletasks()
        master = self.master
        if master and master.winfo_exists():
            x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{max(0,x)}+{max(0,y)}")
        else:
            self.geometry(f"+{(self.winfo_screenwidth()-self.winfo_width())//2}+{(self.winfo_screenheight()-self.winfo_height())//2}")
        self.lift()
        self.focus_force()

    def _clear_main_content_frame(self):
        if self.current_page_view:
            self.current_page_view.destroy()
            self.current_page_view = None

    def _update_navigation_buttons_state(self):
        self.btn_previous.configure(state="disabled")
        self.btn_next.configure(state="normal")  # Default to normal, then disable if conditions not met

        if self.state.current_page_index == WIZARD_PAGE_GOAL_INPUT:
            self.btn_next.configure(text="Generate Plan >")
        elif self.state.current_page_index == WIZARD_PAGE_PLAN_REVIEW:
            self.btn_previous.configure(state="normal")
            can_proceed_plan_review = bool(self.state.intermediate_plan and len(self.state.intermediate_plan) > 0)
            self.btn_next.configure(text="Start Building Profile >", state="normal" if can_proceed_plan_review else "disabled")
        elif self.state.current_page_index == WIZARD_PAGE_DEFINE_REGION:
            self.btn_previous.configure(state="normal")
            can_proceed_define_region = bool(self.state.current_step_region_name and self.state.current_step_region_coords)
            self.btn_next.configure(text="Confirm Region & Define Logic >", state="normal" if can_proceed_define_region else "disabled")
        elif self.state.current_page_index == WIZARD_PAGE_DEFINE_LOGIC:
            self.btn_previous.configure(state="normal")
            is_last_step_in_plan = (self.state.current_plan_step_index >= len(self.state.intermediate_plan or []) - 1) if self.state.intermediate_plan else True
            self.btn_next.configure(text="Finish & Review Profile >" if is_last_step_in_plan else "Confirm Logic & Next Step >")
        elif self.state.current_page_index == WIZARD_PAGE_FINAL_REVIEW_SAVE:
            self.btn_previous.configure(state="normal")
            self.btn_next.configure(text="Save Profile & Close")

    def _show_page(self, page_index: int):
        self._clear_main_content_frame()
        self.state.current_page_index = page_index

        # Instantiate the correct view based on the page index
        if page_index == WIZARD_PAGE_GOAL_INPUT:
            self.current_page_view = GoalInputView(
                master=self.main_content_frame, controller=self, state=self.state, on_generate_plan=self._handle_generate_plan_request, on_state_change=self._update_navigation_buttons_state
            )
        elif page_index == WIZARD_PAGE_PLAN_REVIEW:
            self.current_page_view = PlanReviewView(master=self.main_content_frame, controller=self, state=self.state, on_state_change=self._update_navigation_buttons_state)
        elif page_index == WIZARD_PAGE_DEFINE_REGION:
            self.current_page_view = DefineRegionView(
                master=self.main_content_frame, controller=self, state=self.state, capture_engine=self.capture_engine, on_state_change=self._update_navigation_buttons_state
            )
        elif page_index == WIZARD_PAGE_DEFINE_LOGIC:
            self.current_page_view = DefineLogicView(
                master=self.main_content_frame,
                controller=self,
                state=self.state,
                profile_generator=self.profile_generator,
                main_app_instance=self.main_app_instance,  # For dirty status and existing templates/regions
                overlay_font=self.overlay_font,  # Pass font for overlays
                on_state_change=self._update_navigation_buttons_state,
            )
        elif page_index == WIZARD_PAGE_FINAL_REVIEW_SAVE:
            self.current_page_view = FinalReviewView(
                master=self.main_content_frame, controller=self, state=self.state, profile_generator=self.profile_generator, on_state_change=self._update_navigation_buttons_state
            )
        else:
            ctk.CTkLabel(self.main_content_frame, text=f"Error: Unknown page index {page_index}").pack()
            self.current_page_view = None

        if self.current_page_view:
            self.current_page_view.grid(row=0, column=0, sticky="nsew")  # All views fill the content frame
            self.current_page_view.lift()
            self.current_page_view.focus_set()

        self._update_navigation_buttons_state()
        logger.debug(f"Wizard page changed to index {page_index}.")

    def _on_close_wizard(self, event=None, was_saved=False):
        if not was_saved and messagebox.askokcancel("Cancel Profile Generation?", "Discard this profile and close wizard?", parent=self, icon=messagebox.WARNING):
            logger.info("AI Profile Wizard cancelled (unsaved).")
            self.user_cancelled_wizard = True
            self.destroy()
        elif was_saved:
            logger.info("AI Profile Wizard closing (saved).")
            self.destroy()

    # --- Navigation Logic (Controller) ---
    def _go_to_next_page(self):
        logger.debug(f"Next button clicked. Current page index: {self.state.current_page_index}")

        if self.state.current_page_index == WIZARD_PAGE_GOAL_INPUT:
            # GoalInputView handles getting user_goal_text and context_np
            # It will call _handle_generate_plan_request on success
            if isinstance(self.current_page_view, GoalInputView):
                self.current_page_view.trigger_generate_plan()
            return

        elif self.state.current_page_index == WIZARD_PAGE_PLAN_REVIEW:
            if not self.state.intermediate_plan:
                messagebox.showerror("Error", "No plan available to proceed.", parent=self)
                return
            if self.profile_generator.advance_to_next_plan_step():
                self.state.current_plan_step_index = self.profile_generator.current_plan_step_index
                self.state.current_step_data = self.profile_generator.get_current_plan_step()
                self._reset_step_specific_state_for_new_step()
                self._show_page(WIZARD_PAGE_DEFINE_REGION)
            else:
                # Reached end of plan or plan was empty. Go to final review.
                self.state.current_page_index = WIZARD_PAGE_FINAL_REVIEW_SAVE
                self._show_page(WIZARD_PAGE_FINAL_REVIEW_SAVE)
            return

        elif self.state.current_page_index == WIZARD_PAGE_DEFINE_REGION:
            if isinstance(self.current_page_view, DefineRegionView) and self.current_page_view.confirm_and_add_region_to_profile():
                self._show_page(WIZARD_PAGE_DEFINE_LOGIC)
            return

        elif self.state.current_page_index == WIZARD_PAGE_DEFINE_LOGIC:
            if isinstance(self.current_page_view, DefineLogicView):
                logic_added_successfully = self.current_page_view.confirm_and_add_logic_to_profile()
                if logic_added_successfully:
                    if self.profile_generator.advance_to_next_plan_step():
                        self.state.current_plan_step_index = self.profile_generator.current_plan_step_index
                        self.state.current_step_data = self.profile_generator.get_current_plan_step()
                        self._reset_step_specific_state_for_new_step()  # Reset for next region/logic step
                        self._show_page(WIZARD_PAGE_DEFINE_REGION)  # Next step starts with region definition
                    else:
                        # Reached end of plan. Go to final review.
                        self.state.current_page_index = WIZARD_PAGE_FINAL_REVIEW_SAVE
                        self._show_page(WIZARD_PAGE_FINAL_REVIEW_SAVE)
            return

        elif self.state.current_page_index == WIZARD_PAGE_FINAL_REVIEW_SAVE:
            if isinstance(self.current_page_view, FinalReviewView):
                self.current_page_view.save_generated_profile()
            return

        logger.error(f"Unhandled next page transition from index {self.state.current_page_index}")

    def _go_to_previous_page(self):
        logger.debug(f"Previous button clicked. Current page: {self.state.current_page_index}")

        if self.state.current_page_index == WIZARD_PAGE_GOAL_INPUT:
            pass  # No previous page from here
        elif self.state.current_page_index == WIZARD_PAGE_PLAN_REVIEW:
            self._reset_for_plan_regeneration()
            self._show_page(WIZARD_PAGE_GOAL_INPUT)
        elif self.state.current_page_index == WIZARD_PAGE_DEFINE_REGION:
            if self.profile_generator.current_plan_step_index == 0:
                self.profile_generator.current_plan_step_index = -1  # Back to before first step
                self.state.current_plan_step_index = -1
                self.state.current_step_data = None
                self._reset_step_specific_state_for_new_step()
                self._show_page(WIZARD_PAGE_PLAN_REVIEW)
            elif self.profile_generator.current_plan_step_index > 0:
                self.profile_generator.current_plan_step_index -= 1  # Go back to previous step
                self.state.current_plan_step_index = self.profile_generator.current_plan_step_index
                self.state.current_step_data = self.profile_generator.get_current_plan_step()
                self._reset_step_specific_state_for_new_step()  # Load previous step's saved state
                self._show_page(WIZARD_PAGE_DEFINE_LOGIC)  # Previous step would have been defining logic
            else:  # Should not happen, implies plan_step_index < 0 but not at start
                self._show_page(WIZARD_PAGE_PLAN_REVIEW)
        elif self.state.current_page_index == WIZARD_PAGE_DEFINE_LOGIC:
            self._show_page(WIZARD_PAGE_DEFINE_REGION)  # Go back to define region for current step
        elif self.state.current_page_index == WIZARD_PAGE_FINAL_REVIEW_SAVE:
            if self.state.intermediate_plan and len(self.state.intermediate_plan) > 0:
                # Go back to the last step's logic page
                self.state.current_plan_step_index = len(self.state.intermediate_plan) - 1
                self.state.current_step_data = self.profile_generator.get_current_plan_step()
                self._reset_step_specific_state_for_new_step()  # Load previous step's saved state
                self._show_page(WIZARD_PAGE_DEFINE_LOGIC)
            else:  # If plan was empty, go back to goal input
                self._show_page(WIZARD_PAGE_GOAL_INPUT)

        logger.error(f"Unhandled previous page transition from index {self.state.current_page_index}")

    def _reset_for_plan_regeneration(self):
        """Resets relevant state when going back to the Goal Input page to regenerate the plan."""
        self.state.intermediate_plan = None
        self.state.current_plan_step_index = -1
        self.state.generated_profile_data.clear()
        self.state.staged_templates_with_image_data.clear()
        # Ensure profile generator's internal state is also reset for new generation
        self.profile_generator.start_profile_generation(intermediate_plan=[], profile_description="AI-Generated Profile (Reset)")
        # Other state is handled by _reset_step_specific_state_for_new_step

    def _reset_step_specific_state_for_new_step(self):
        """Resets all step-specific temporary UI data in WizardState."""
        self.state.current_step_region_name = None
        self.state.current_step_region_coords = None
        self.state.current_step_region_image_np = None
        self.state.current_step_region_image_pil_for_display = None
        self.state.ai_suggested_condition_for_step = None
        self.state.ai_suggested_action_for_step = None
        self.state.ai_element_to_refine_desc = None
        self.state.ai_refined_element_candidates = []
        self.state.user_selected_candidate_box_index = None
        self.state.user_confirmed_element_for_action = None
        self.state.current_step_temp_gemini_var_name = None

        if self.state.current_step_data:
            step_id_from_plan = self.state.current_step_data.get("step_id", self.state.current_plan_step_index + 1)
            logger.info(f"Wizard: Reset step-specific state for new plan step ID {step_id_from_plan}.")

            # Attempt to load previously saved elements for this step if they exist in generated_profile_data
            potential_rule_name_prefix = f"Rule_Step{step_id_from_plan}"
            found_rule_for_step = next((r for r in self.profile_generator_cm.get_profile_data().get("rules", []) if r.get("name", "").startswith(potential_rule_name_prefix)), None)

            if found_rule_for_step:
                self.state.ai_suggested_condition_for_step = copy.deepcopy(found_rule_for_step.get("condition"))
                self.state.ai_suggested_action_for_step = copy.deepcopy(found_rule_for_step.get("action"))
                self.state.ai_element_to_refine_desc = self.state.ai_suggested_action_for_step.get("target_description") if self.state.ai_suggested_action_for_step else None

                self.state.current_step_region_name = found_rule_for_step.get("region")
                if self.state.current_step_region_name:
                    region_cfg = next((r for r in self.profile_generator_cm.get_profile_data().get("regions", []) if r.get("name") == self.state.current_step_region_name), None)
                    if region_cfg:
                        self.state.current_step_region_coords = {k: region_cfg[k] for k in ["x", "y", "width", "height"]}
                        if self.state.current_full_context_np is not None:
                            x, y, w, h = (
                                self.state.current_step_region_coords["x"],
                                self.state.current_step_region_coords["y"],
                                self.state.current_step_region_coords["width"],
                                self.state.current_step_region_coords["height"],
                            )
                            img_h_f, img_w_f = self.state.current_full_context_np.shape[:2]
                            x_c, y_c = max(0, x), max(0, y)
                            x2_c, y2_c = min(img_w_f, x + w), min(img_h_f, y + h)
                            w_c, h_c = x2_c - x_c, y2_c - y_c
                            if w_c > 0 and h_c > 0:
                                self.state.current_step_region_image_np = self.state.current_full_context_np[y_c:y2_c, x_c:x2_c]
                                self.state.current_step_region_image_pil_for_display = Image.fromarray(cv2.cvtColor(self.state.current_step_region_image_np, cv2.COLOR_BGR2RGB))
                            else:
                                logger.warning(
                                    f"Failed to crop valid region image for '{self.state.current_step_region_name}' on reload. Coords: {self.state.current_step_region_coords}, Clamped: {w_c}x{h_c}"
                                )
            logger.debug(f"Wizard: State reloaded for step {step_id_from_plan}. Region '{self.state.current_step_region_name}' rule logic loaded: {found_rule_for_step is not None}")

    # --- Callbacks from Views (Controller methods) ---
    def _handle_generate_plan_request(self, user_goal: str, context_np: Optional[np.ndarray]):
        """Callback from GoalInputView to initiate plan generation."""
        logger.info(f"User requested AI plan generation for goal: '{user_goal[:50]}...'")
        self.state.user_goal_text = user_goal
        self.state.current_full_context_np = context_np
        self.profile_generator.set_current_visual_context(context_np)

        if not self.state.user_goal_text:
            messagebox.showerror("Input Error", "Please describe your automation goal.", parent=self)
            return
        self._show_loading_overlay("AI generating plan...")
        self.btn_next.configure(state="disabled")

        thread = threading.Thread(target=self._perform_generate_plan_in_thread, args=(self.state.user_goal_text, self.state.current_full_context_np))
        thread.daemon = True
        thread.start()

    def _perform_generate_plan_in_thread(self, user_goal: str, context_np: Optional[np.ndarray]):
        plan = None
        error = None
        try:
            plan = self.strategy_planner.generate_intermediate_plan(user_goal, context_np)
        except Exception as e:
            logger.error(f"Exception in AI generate plan thread: {e}", exc_info=True)
            error = e
        self.after(0, self._handle_generate_plan_result, plan, error)

    def _handle_generate_plan_result(self, plan: Optional[IntermediatePlan], error: Optional[Exception]):
        self._hide_loading_overlay()
        self.btn_next.configure(state="normal")
        if error:
            messagebox.showerror("AI Plan Error", f"Error during AI plan generation: {error}", parent=self)
            return

        self.state.intermediate_plan = plan
        if self.state.intermediate_plan is not None and len(self.state.intermediate_plan) > 0:
            self.profile_generator.start_profile_generation(
                self.state.intermediate_plan, f"AI-Gen for: {self.state.user_goal_text[:70]}", initial_full_screen_context_np=self.state.current_full_context_np
            )
            # Initializing profile_generator clears its internal profile_data. Re-get it for state.
            self.state.generated_profile_data = self.profile_generator.get_generated_profile_data()
            self.state.current_page_index = WIZARD_PAGE_PLAN_REVIEW
            self._show_page(WIZARD_PAGE_PLAN_REVIEW)
        elif self.state.intermediate_plan is not None and len(self.state.intermediate_plan) == 0:
            messagebox.showinfo(
                "AI Plan", "AI generated an empty plan. This might mean the goal was too vague or complex. You can refine your goal or proceed to build manually if desired.", parent=self
            )
            self.profile_generator.start_profile_generation(
                self.state.intermediate_plan, f"AI-Gen for: {self.state.user_goal_text[:70]}", initial_full_screen_context_np=self.state.current_full_context_np
            )
            self.state.generated_profile_data = self.profile_generator.get_generated_profile_data()
            self.state.current_page_index = WIZARD_PAGE_PLAN_REVIEW
            self._show_page(WIZARD_PAGE_PLAN_REVIEW)
        else:  # Plan is None (failed to generate)
            messagebox.showerror("AI Plan Failed", "Could not generate a plan. Try rephrasing your goal or check application logs.", parent=self)
            self.state.current_page_index = WIZARD_PAGE_GOAL_INPUT
            self._show_page(WIZARD_PAGE_GOAL_INPUT)

    # --- Utility methods for views to call the controller ---
    def get_current_main_app_instance(self):
        return self.main_app_instance

    def get_profile_generator(self):
        return self.profile_generator

    def get_capture_engine(self):
        return self.capture_engine

    def get_overlay_font(self):
        return self.overlay_font

    def update_navigation_buttons(self):
        self._update_navigation_buttons_state()
