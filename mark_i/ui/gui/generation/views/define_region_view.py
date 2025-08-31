import logging
import tkinter as tk
from tkinter import messagebox
import time
import threading
from typing import Optional, Dict, Any, List, Callable

import customtkinter as ctk
import numpy as np
from PIL import Image, ImageDraw
import cv2

from mark_i.ui.gui.generation.wizard_state import WizardState
from mark_i.generation.profile_generator import ProfileGenerator
# This import is the fix for the NameError
from mark_i.generation.strategy_planner import IntermediatePlanStep
from mark_i.engines.capture_engine import CaptureEngine
from mark_i.ui.gui.region_selector import RegionSelectorWindow

# Import constants from the new central location
from mark_i.ui.gui.gui_config import WIZARD_SCREENSHOT_PREVIEW_MAX_WIDTH, WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT, SELECTED_CANDIDATE_BOX_COLOR

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.generation.views.define_region_view")

# Default structure for a new region definition in the context of the wizard.
# Moved here as it's primarily used in the UI for region creation.
DEFAULT_REGION_STRUCTURE = {"name": "", "x": 10, "y": 10, "width": 200, "height": 150, "comment": "AI-suggested region placeholder"}


class DefineRegionView(ctk.CTkFrame):
    """
    UI View for the third page of the AI Profile Creator wizard:
    defining a screen region for the current automation plan step.
    Offers AI suggestions and manual drawing.
    """

    def __init__(self, master: Any, controller: Any, state: WizardState, capture_engine: CaptureEngine, on_state_change: Callable[[], None]):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.state = state
        self.capture_engine = capture_engine
        self.on_state_change = on_state_change  # Callback to notify controller of state changes

        self.profile_generator: ProfileGenerator = self.controller.get_profile_generator()  # Get instance from controller

        self._temp_suggested_region_coords: Optional[Dict[str, int]] = None  # Temp to hold AI suggestion before user confirmation

        self.pack(fill="both", expand=True, padx=5, pady=5)
        self.grid_columnconfigure(0, weight=1)

        self._setup_ui()
        self._load_current_step_state()  # Load relevant state after UI is built
        logger.debug("DefineRegionView UI setup complete.")

    def _setup_ui(self):
        if not self.state.current_step_data:
            ctk.CTkLabel(self, text="Error: No current plan step data available. Please go back to Plan Review.").pack(pady=20)
            self.on_state_change()
            return

        step_id = self.state.current_step_data.get("step_id", self.state.current_plan_step_index + 1)
        step_desc = self.state.current_step_data.get("description", "N/A")

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header_frame, text=f"Step {step_id}.A: Define Region for Task", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", anchor="w")
        ctk.CTkLabel(self, text=f'Task: "{step_desc}"', wraplength=self.controller.winfo_width() - 20, justify="left", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=(0, 10), fill="x")

        self.region_step_context_display_label = ctk.CTkLabel(self, text="Loading screen context...", fg_color=("gray90", "gray25"), corner_radius=6)
        self.region_step_context_display_label.pack(fill="both", expand=True, pady=(0, 10))

        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(5, 10))
        self.btn_ai_suggest_region = ctk.CTkButton(controls_frame, text="AI Suggest Region", command=self._handle_ai_suggest_region_threaded, width=160)
        self.btn_ai_suggest_region.pack(side="left", padx=(0, 10))
        self.btn_draw_region_manually = ctk.CTkButton(controls_frame, text="Draw/Adjust Manually", command=self._handle_draw_region_manually, width=180)
        self.btn_draw_region_manually.pack(side="left", padx=5)

        name_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        name_frame.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(name_frame, text="Region Name:").pack(side="left")
        self.current_step_region_name_entry = ctk.CTkEntry(name_frame, placeholder_text=f"e.g., step{step_id}_target_area")
        self.current_step_region_name_entry.pack(side="left", fill="x", expand=True)
        self.current_step_region_name_entry.bind("<KeyRelease>", lambda e: self.on_state_change())  # Notify controller of changes to enable/disable Next button

    def _load_current_step_state(self):
        """Loads state from WizardState and updates UI elements."""
        overlay_to_draw = self.state.current_step_region_coords  # Initially, if a region was confirmed for this step
        overlay_color = SELECTED_CANDIDATE_BOX_COLOR

        if self.state.current_step_region_name:
            self.current_step_region_name_entry.delete(0, tk.END)
            self.current_step_region_name_entry.insert(0, self.state.current_step_region_name)

        # If AI had previously suggested something for this step (but not confirmed yet)
        # Note: current_step_region_coords in state is for *confirmed* region.
        # _temp_suggested_region_coords is purely for displaying a suggestion not yet accepted.
        # Currently, if a confirmed region exists, it takes precedence.

        self.display_current_full_context_with_optional_overlay(
            label_widget=self.region_step_context_display_label,
            overlay_box=[overlay_to_draw["x"], overlay_to_draw["y"], overlay_to_draw["width"], overlay_to_draw["height"]] if overlay_to_draw else None,
            box_color=overlay_color,
        )
        self.on_state_change()  # Ensure navigation buttons reflect current state

    def display_current_full_context_with_optional_overlay(self, label_widget: ctk.CTkLabel, overlay_box: Optional[List[int]] = None, box_color: str = "red"):
        """Displays the full screen context image with an optional overlay box."""
        if not label_widget or not label_widget.winfo_exists():
            return
        if not self.state.current_full_context_pil:
            label_widget.configure(text="No screen context image.", image=None)
            return

        img_display = self.state.current_full_context_pil.copy()
        if overlay_box and len(overlay_box) == 4:
            try:
                draw = ImageDraw.Draw(img_display, "RGBA")
                x, y, w, h = overlay_box
                fill = box_color + "50" if box_color != SELECTED_CANDIDATE_BOX_COLOR else None
                draw.rectangle([x, y, x + w, y + h], outline=box_color, width=3, fill=fill)
                if box_color == SELECTED_CANDIDATE_BOX_COLOR:
                    cx, cy = x + w // 2, y + h // 2
                    draw.line([(cx - 6, cy), (cx + 6, cy)], fill=box_color, width=2)
                    draw.line([(cx, cy - 6), (cx, cy + 6)], fill=box_color, width=2)
            except Exception as e:
                logger.error(f"Error drawing overlay {overlay_box}: {e}")

        max_w, max_h = WIZARD_SCREENSHOT_PREVIEW_MAX_WIDTH, WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT
        thumb = img_display.copy()
        thumb.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        dw, dh = thumb.size

        ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(dw, dh))
        label_widget.configure(image=ctk_img, text="", width=dw, height=dh)

    def _handle_ai_suggest_region_threaded(self):
        if not self.state.current_step_data:
            return
        logger.info(f"User req AI region suggestion for step: {self.state.current_step_data.get('description')}")
        self.controller._show_loading_overlay("AI suggesting region...")
        self.btn_ai_suggest_region.configure(state="disabled")
        self.btn_draw_region_manually.configure(state="disabled")

        thread = threading.Thread(target=self._perform_ai_suggest_region_in_thread, args=(self.state.current_step_data,))
        thread.daemon = True
        thread.start()

    def _perform_ai_suggest_region_in_thread(self, plan_step_data_for_thread: IntermediatePlanStep):
        suggestion = None
        error = None
        try:
            suggestion = self.profile_generator.suggest_region_for_step(plan_step_data_for_thread)
        except Exception as e:
            logger.error(f"Exception in AI suggest region thread: {e}", exc_info=True)
            error = e
        self.after(0, self._handle_ai_suggest_region_result, suggestion, error)

    def _handle_ai_suggest_region_result(self, suggestion: Optional[Dict[str, Any]], error: Optional[Exception]):
        self.controller._hide_loading_overlay()
        self.btn_ai_suggest_region.configure(state="normal")
        self.btn_draw_region_manually.configure(state="normal")
        if error:
            messagebox.showerror("AI Error", f"Error during AI region suggestion: {error}", parent=self.controller)
            self.display_current_full_context_with_optional_overlay(self.region_step_context_display_label)
            return

        if suggestion and suggestion.get("box"):
            box = suggestion["box"]
            name_hint = suggestion.get("suggested_region_name_hint", f"step{self.state.current_step_data.get('step_id','X')}_ai_region")

            # Store AI suggestion temporarily, but not directly in state.current_step_region_coords until confirmed.
            self._temp_suggested_region_coords = {"x": box[0], "y": box[1], "width": box[2], "height": box[3]}

            self.current_step_region_name_entry.delete(0, tk.END)
            self.current_step_region_name_entry.insert(0, name_hint)

            self.display_current_full_context_with_optional_overlay(self.region_step_context_display_label, box, "orange")
            messagebox.showinfo(
                "AI Suggestion",
                f"AI suggests highlighted region (named '{name_hint}').\nReasoning: {suggestion.get('reasoning', 'N/A')}\nAdjust name if needed, or draw manually, then 'Confirm Region'.",
                parent=self.controller,
            )

            # Update state with the suggestion, so controller can react. This is a temporary "unconfirmed" region.
            # The next button will be enabled based on if a region (confirmed or temp) AND a name exists.
            self.state.current_step_region_coords = self._temp_suggested_region_coords  # This is the key change for Next button logic
            self.state.current_step_region_name = name_hint  # Also update name in state
        else:
            self.display_current_full_context_with_optional_overlay(self.region_step_context_display_label)
            messagebox.showwarning("AI Suggestion Failed", "AI could not suggest a region. Please define it manually.", parent=self.controller)
            # Clear any temporary state if suggestion failed
            self._temp_suggested_region_coords = None
            self.state.current_step_region_coords = None
            self.state.current_step_region_name = ""
            self.current_step_region_name_entry.delete(0, tk.END)

        self.on_state_change()  # Notify controller of state change

    def _handle_draw_region_manually(self):
        if not self.state.current_step_data:
            return
        logger.info(f"User opted to draw region manually for: {self.state.current_step_data.get('description')}")

        # Temporarily hide wizard window during capture
        self.controller.attributes("-alpha", 0.0)
        self.controller.lower()
        self.controller.update_idletasks()
        time.sleep(0.2)  # Give window time to hide fully

        capture_pil_for_selector = self.state.current_full_context_pil
        if not capture_pil_for_selector:
            # Fallback to live capture if no initial context image was set in state
            temp_screen_np = self.capture_engine.capture_region({"name": "temp_fullscreen_selector", "x": 0, "y": 0, "width": self.winfo_screenwidth(), "height": self.winfo_screenheight()})
            capture_pil_for_selector = Image.fromarray(cv2.cvtColor(temp_screen_np, cv2.COLOR_BGR2RGB)) if temp_screen_np is not None else None

        self.controller.attributes("-alpha", 1.0)
        self.controller.lift()
        self.controller.focus_set()

        if not capture_pil_for_selector:
            messagebox.showerror("Capture Error", "Failed to get screen image for manual region selection.", parent=self.controller)
            return

        temp_cm = self.controller.profile_generator_cm  # Use the generator's CM for context
        step_id = self.state.current_step_data.get("step_id", self.state.current_plan_step_index + 1)

        initial_name_for_selector = (
            self.current_step_region_name_entry.get().strip()
            or self.state.current_step_region_name
            or (self._temp_suggested_region_coords and self.state.current_step_data.get("suggested_region_name_hint"))
            or f"step{step_id}_manual_region"
        )

        initial_coords_for_selector = self.state.current_step_region_coords or self._temp_suggested_region_coords or copy.deepcopy(DEFAULT_REGION_STRUCTURE)
        existing_data_for_selector = {"name": initial_name_for_selector, **initial_coords_for_selector}

        # Ensure all required coords are present for the selector, even if defaults
        for k_coord, def_coord in DEFAULT_REGION_STRUCTURE.items():
            if k_coord in ["x", "y", "width", "height"]:
                existing_data_for_selector.setdefault(k_coord, def_coord)

        selector = RegionSelectorWindow(master=self.controller, config_manager_context=temp_cm, existing_region_data=existing_data_for_selector, direct_image_input_pil=capture_pil_for_selector)
        self.controller.wait_window(selector)

        if hasattr(selector, "saved_region_info") and selector.saved_region_info:
            cr = selector.saved_region_info

            # Update WizardState with the confirmed region details
            self.state.current_step_region_name = cr["name"]
            self.state.current_step_region_coords = {k: cr[k] for k in ["x", "y", "width", "height"]}

            # Update the UI entry field
            self.current_step_region_name_entry.delete(0, tk.END)
            self.current_step_region_name_entry.insert(0, self.state.current_step_region_name)

            box_to_draw = [
                self.state.current_step_region_coords["x"],
                self.state.current_step_region_coords["y"],
                self.state.current_step_region_coords["width"],
                self.state.current_step_region_coords["height"],
            ]
            self.display_current_full_context_with_optional_overlay(self.region_step_context_display_label, box_to_draw, SELECTED_CANDIDATE_BOX_COLOR)
            logger.info(f"User manually defined/confirmed region '{self.state.current_step_region_name}' at {self.state.current_step_region_coords}")
        else:
            logger.info("Manual region definition cancelled or no region saved.")

        self.on_state_change()  # Notify controller of state change

    def confirm_and_add_region_to_profile(self) -> bool:
        """
        Called by the controller when the user clicks 'Next' on this page.
        Validates input, adds region to the profile being generated, and prepares
        the cropped region image for the next step.
        """
        region_name_from_ui = self.current_step_region_name_entry.get().strip()
        if not region_name_from_ui:
            messagebox.showerror("Input Error", "Region Name cannot be empty.", parent=self.controller)
            self.current_step_region_name_entry.focus()
            return False

        # We assume state.current_step_region_coords is populated either by AI suggestion or manual draw
        if not self.state.current_step_region_coords:
            messagebox.showerror("Error", "No region coordinates defined/confirmed for this step.", parent=self.controller)
            return False

        self.state.current_step_region_name = region_name_from_ui  # Final confirmed name

        # Check for name conflict in the profile currently being generated
        existing_regions_in_draft = self.profile_generator.generated_profile_data.get("regions", [])
        if any(r.get("name") == self.state.current_step_region_name for r in existing_regions_in_draft):
            if not messagebox.askyesno(
                "Name Conflict",
                f"A region named '{self.state.current_step_region_name}' already exists in the profile being generated. Its definition will be updated with the current coordinates if you proceed. Continue?",
                parent=self.controller,
            ):
                self.current_step_region_name_entry.focus()
                return False
            else:
                # Remove old entry if user confirms overwrite. ProfileGenerator.add_region_definition also handles this.
                self.profile_generator.generated_profile_data["regions"] = [r for r in existing_regions_in_draft if r.get("name") != self.state.current_step_region_name]

        step_desc = self.state.current_step_data.get("description", "N/A") if self.state.current_step_data else "N/A"
        region_data_to_add_to_pg = {"name": self.state.current_step_region_name, **self.state.current_step_region_coords, "comment": f"For AI Gen Step: {step_desc}"}

        if self.profile_generator.add_region_definition(region_data_to_add_to_pg):
            logger.info(f"DefineRegionView: Region '{region_data_to_add_to_pg['name']}' definition added/updated in draft profile.")

            # Prepare cropped image for the next (logic definition) step
            if self.state.current_full_context_np is not None and self.state.current_step_region_coords:
                x, y, w, h = (
                    self.state.current_step_region_coords["x"],
                    self.state.current_step_region_coords["y"],
                    self.state.current_step_region_coords["width"],
                    self.state.current_step_region_coords["height"],
                )
                img_h_full, img_w_full = self.state.current_full_context_np.shape[:2]
                x_clamped = max(0, x)
                y_clamped = max(0, y)
                x2_clamped = min(img_w_full, x + w)
                y2_clamped = min(img_h_full, y + h)
                w_clamped = x2_clamped - x_clamped
                h_clamped = y2_clamped - y_clamped

                if w_clamped > 0 and h_clamped > 0:
                    self.state.current_step_region_image_np = self.state.current_full_context_np[y_clamped:y2_clamped, x_clamped:x2_clamped]
                    self.state.current_step_region_image_pil_for_display = Image.fromarray(cv2.cvtColor(self.state.current_step_region_image_np, cv2.COLOR_BGR2RGB))
                    logger.info(
                        f"DefineRegionView: Cropped region image '{self.state.current_step_region_name}' (shape: {self.state.current_step_region_image_np.shape}) set for logic definition step."
                    )
                else:
                    self.state.current_step_region_image_np = None
                    self.state.current_step_region_image_pil_for_display = None
                    logger.error(
                        f"DefineRegionView: Failed to crop valid region image for '{self.state.current_step_region_name}'. Coords: {self.state.current_step_region_coords}, Clamped: {w_clamped}x{h_clamped}"
                    )
                    messagebox.showerror("Crop Error", "Defined region resulted in invalid crop. Please adjust region coordinates.", parent=self.controller)
                    return False
            else:
                self.state.current_step_region_image_np = None
                self.state.current_step_region_image_pil_for_display = None
                logger.warning("DefineRegionView: No full context image to crop from for current step's region.")

            self._temp_suggested_region_coords = None  # Clear temporary suggestion after confirmation
            self.on_state_change()  # Update navigation buttons
            return True
        return False