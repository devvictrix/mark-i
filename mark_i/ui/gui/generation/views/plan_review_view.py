import logging
import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from mark_i.ui.gui.generation.wizard_state import WizardState
from mark_i.generation.strategy_planner import IntermediatePlan

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.generation.views.plan_review_view")


class PlanReviewView(ctk.CTkFrame):
    """
    UI View for the second page of the AI Profile Creator wizard:
    displaying the AI-generated intermediate plan for user review.
    """

    def __init__(self, master: Any, controller: Any, state: WizardState, on_state_change: Callable[[], None]):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.state = state
        self.on_state_change = on_state_change  # Callback to notify controller of state changes

        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)

        self._setup_ui()
        logger.debug("PlanReviewView UI setup complete.")

    def _setup_ui(self):
        ctk.CTkLabel(self, text="AI Profile Creator: Step 2 - Review Automation Plan", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 15), anchor="w")

        if self.state.intermediate_plan and len(self.state.intermediate_plan) > 0:
            ctk.CTkLabel(self, text="Gemini has proposed the following high-level steps to achieve your goal:", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(5, 5))

            plan_display_frame = ctk.CTkScrollableFrame(self, height=450, fg_color=("gray92", "gray28"))
            plan_display_frame.pack(fill="both", expand=True, pady=(0, 10))

            for i, step in enumerate(self.state.intermediate_plan):
                step_id = step.get("step_id", i + 1)
                desc = step.get("description", "N/A")
                hint = step.get("suggested_element_type_hint")
                inputs_needed = step.get("required_user_input_for_step", [])

                step_text = f"Step {step_id}: {desc}"
                details_parts = []
                if hint:
                    details_parts.append(f"Element Hint: '{hint}'")
                if inputs_needed:
                    details_parts.append(f"User Inputs Required: {', '.join(inputs_needed)}")
                if details_parts:
                    step_text += f"\n  ► AI Details: {'. '.join(details_parts)}"

                ctk.CTkLabel(plan_display_frame, text=step_text, wraplength=self.controller.winfo_width() - 120, anchor="w", justify="left", font=ctk.CTkFont(size=13)).pack(
                    fill="x", pady=(4, 6), padx=5
                )
        elif self.state.intermediate_plan is None:
            ctk.CTkLabel(self, text="Generating plan... Please wait or check previous step if an error occurred.", wraplength=self.controller.winfo_width() - 40).pack(pady=20)
        else:  # Empty plan
            ctk.CTkLabel(
                self,
                text="AI generated an empty plan. This might mean the goal was too vague, too complex for direct steps, or deemed unsafe. Please refine your goal on the previous page or consider creating the profile manually using the main editor.",
                wraplength=self.controller.winfo_width() - 40,
                justify="left",
            ).pack(pady=20)

        self.on_state_change()  # Notify controller of state change
