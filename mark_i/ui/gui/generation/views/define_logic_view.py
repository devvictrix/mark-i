import logging
import tkinter as tk
from tkinter import messagebox
import os
import json
import copy
import time
import threading
from typing import Optional, Dict, Any, List, Union, Callable, Tuple

import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont  # Added ImageFont
import cv2

from mark_i.ui.gui.generation.wizard_state import WizardState
from mark_i.generation.profile_generator import ProfileGenerator, DEFAULT_CONDITION_STRUCTURE_PG, DEFAULT_ACTION_STRUCTURE_PG

# This import is the fix for the NameError
from mark_i.generation.strategy_planner import IntermediatePlanStep
from mark_i.ui.gui.generation.sub_image_selector_window import SubImageSelectorWindow

from mark_i.ui.gui.gui_config import (
    CONDITION_TYPES,
    ACTION_TYPES,
    UI_PARAM_CONFIG,
    OPTIONS_CONST_MAP,
    WIZARD_SCREENSHOT_PREVIEW_MAX_WIDTH,
    WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT,
    CANDIDATE_BOX_COLORS,
    SELECTED_CANDIDATE_BOX_COLOR,
)
from mark_i.ui.gui.gui_utils import validate_and_get_widget_value


from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.generation.views.define_logic_view")

USER_INPUT_PLACEHOLDER_PREFIX = "USER_INPUT_REQUIRED__"


class DefineLogicView(ctk.CTkFrame):
    """
    UI View for the fourth page of the AI Profile Creator wizard:
    defining the condition and action logic for a specific plan step and region.
    Offers AI suggestions, element refinement, and template capture.
    """

    def __init__(
        self, master: Any, controller: Any, state: WizardState, profile_generator: ProfileGenerator, main_app_instance: Any, overlay_font: ImageFont.FreeTypeFont, on_state_change: Callable[[], None]
    ):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.state = state
        self.profile_generator = profile_generator
        self.main_app_instance = main_app_instance  # For access to main app's config manager, dirty status
        self.overlay_font = overlay_font
        self.on_state_change = on_state_change  # Callback to notify controller of state changes

        self.ui_step_logic_detail_widgets: Dict[str, Union[ctk.CTkEntry, ctk.CTkOptionMenu, ctk.CTkCheckBox, ctk.CTkTextbox]] = {}
        self.ui_step_logic_optionmenu_vars: Dict[str, Union[tk.StringVar, tk.BooleanVar]] = {}
        self.ui_step_logic_param_widgets_and_defs: List[Dict[str, Any]] = []  # For conditional visibility
        self.ui_step_logic_controlling_widgets: Dict[str, Union[ctk.CTkOptionMenu, ctk.CTkCheckBox]] = {}  # For conditional visibility
        self.ui_step_logic_widget_prefix: str = ""  # For conditional visibility

        self.pack(fill="both", expand=True, padx=5, pady=5)
        self.grid_columnconfigure(0, weight=3, minsize=400)
        self.grid_columnconfigure(1, weight=2, minsize=350)
        self.grid_rowconfigure(0, weight=1)

        self._setup_ui()
        self._load_current_step_state()  # Load relevant state after UI is built
        logger.debug("DefineLogicView UI setup complete.")

    def _setup_ui(self):
        if not self.state.current_step_data or not self.state.current_step_region_name or self.state.current_step_region_image_pil_for_display is None:
            ctk.CTkLabel(
                self,
                text="Error: Critical data missing (step, region name, or region image).\nPlease go back to define the region for this task step first.",
                wraplength=self.controller.winfo_width() - 30,
                justify="left",
            ).pack(pady=20)
            self.on_state_change()
            return  # Signal inability to proceed

        step_id = self.state.current_step_data.get("step_id", self.state.current_plan_step_index + 1)
        step_desc = self.state.current_step_data.get("description", "N/A")
        self.state.current_step_temp_gemini_var_name = f"_ai_gen_step{step_id}_elem"  # Temp var name for the current step

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        ctk.CTkLabel(header_frame, text=f"Step {step_id}.B: Define Logic for Region '{self.state.current_step_region_name}'", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", anchor="w")
        ctk.CTkLabel(self, text=f'Task: "{step_desc}"', wraplength=self.controller.winfo_width() - 20, justify="left").pack(anchor="w", pady=(0, 10), fill="x")

        main_logic_area = ctk.CTkFrame(self, fg_color="transparent")
        main_logic_area.grid(row=1, column=0, columnspan=2, sticky="nsew")  # Adjusted row
        main_logic_area.grid_columnconfigure(0, weight=3, minsize=400)
        main_logic_area.grid_columnconfigure(1, weight=2, minsize=350)
        main_logic_area.grid_rowconfigure(0, weight=1)

        visual_panel = ctk.CTkFrame(main_logic_area, fg_color=("gray90", "gray25"))
        visual_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        visual_panel.grid_rowconfigure(1, weight=1)
        visual_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(visual_panel, text=f"Context: Region '{self.state.current_step_region_name}' (Click image to select element)", font=ctk.CTkFont(size=12)).pack(pady=(5, 2), anchor="w", padx=5)
        self.step_logic_region_image_label = ctk.CTkLabel(visual_panel, text="Region image...", height=WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT - 70)
        self.step_logic_region_image_label.pack(fill="both", expand=True, padx=5, pady=5)
        self.step_logic_region_image_label.bind("<Button-1>", self._on_region_image_click_for_element_selection)

        element_interaction_frame = ctk.CTkFrame(visual_panel, fg_color="transparent")
        element_interaction_frame.pack(fill="x", pady=5, padx=5)
        self.element_refine_entry = ctk.CTkEntry(element_interaction_frame, placeholder_text="Element description (e.g., 'login button')")
        self.element_refine_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.element_refine_entry.bind("<KeyRelease>", lambda e: self.btn_refine_element.configure(state="normal" if self.element_refine_entry.get().strip() else "disabled"))
        self.btn_refine_element = ctk.CTkButton(element_interaction_frame, text="AI Find Element", command=self._handle_ai_refine_element_threaded, width=120, state="disabled")
        self.btn_refine_element.pack(side="left", padx=(0, 5))
        self.btn_capture_template_for_step = ctk.CTkButton(element_interaction_frame, text="Use Template Instead", command=self._handle_capture_template_for_step, width=160, state="normal")
        self.btn_capture_template_for_step.pack(side="left")

        params_panel_outer = ctk.CTkFrame(main_logic_area, fg_color="transparent")
        params_panel_outer.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        params_panel_outer.grid_rowconfigure(0, weight=1)
        params_panel_outer.grid_columnconfigure(0, weight=1)
        self.params_panel_scrollable = ctk.CTkScrollableFrame(params_panel_outer, label_text="Configure Step Logic (AI Suggested / Manual)")
        self.params_panel_scrollable.pack(fill="both", expand=True)
        self.params_panel_scrollable.grid_columnconfigure(1, weight=1)

        self.step_logic_condition_frame = ctk.CTkFrame(self.params_panel_scrollable, fg_color="transparent")
        self.step_logic_condition_frame.pack(fill="x", pady=(5, 15), padx=5)
        self.step_logic_condition_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.step_logic_condition_frame, text="STEP CONDITION:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        self.step_logic_action_frame = ctk.CTkFrame(self.params_panel_scrollable, fg_color="transparent")
        self.step_logic_action_frame.pack(fill="x", pady=(10, 5), padx=5)
        self.step_logic_action_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.step_logic_action_frame, text="STEP ACTION:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

    def _load_current_step_state(self):
        """Loads relevant state from WizardState and updates UI elements."""
        self._display_current_step_region_image_with_candidates(self.state.ai_refined_element_candidates, self.state.user_selected_candidate_box_index)

        if self.state.ai_element_to_refine_desc:
            self.element_refine_entry.delete(0, tk.END)
            self.element_refine_entry.insert(0, self.state.ai_element_to_refine_desc)
            self.btn_refine_element.configure(state="normal")
        else:
            self.element_refine_entry.delete(0, tk.END)
            self.btn_refine_element.configure(state="disabled")

        # Render the condition/action editors based on state.ai_suggested_... or defaults
        s_cond = self.state.ai_suggested_condition_for_step or copy.deepcopy(DEFAULT_CONDITION_STRUCTURE_PG)
        s_act = self.state.ai_suggested_action_for_step or copy.deepcopy(DEFAULT_ACTION_STRUCTURE_PG)

        self._render_step_logic_editors(s_cond, s_act, self.state.ai_element_to_refine_desc)

        if not self.state.ai_suggested_condition_for_step and not self.state.ai_suggested_action_for_step:
            # If no logic was previously loaded for this step, trigger AI suggestion
            self.after(100, self._trigger_ai_logic_suggestion_for_step_threaded)

        self.on_state_change()  # Ensure navigation buttons reflect current state

    def _display_current_step_region_image_with_candidates(self, candidate_boxes: Optional[List[Dict[str, Any]]] = None, selected_box_idx: Optional[int] = None):
        if not hasattr(self, "step_logic_region_image_label") or not self.step_logic_region_image_label.winfo_exists():
            return
        if not self.state.current_step_region_image_pil_for_display:
            self.step_logic_region_image_label.configure(text="No image for current step's region.", image=None)
            return

        img_pil_to_draw_on = self.state.current_step_region_image_pil_for_display.copy()
        draw = ImageDraw.Draw(img_pil_to_draw_on, "RGBA")

        if candidate_boxes:
            for i, candidate in enumerate(candidate_boxes):
                box = candidate.get("box")
                if box and len(box) == 4:
                    color = SELECTED_CANDIDATE_BOX_COLOR if i == selected_box_idx else CANDIDATE_BOX_COLORS[i % len(CANDIDATE_BOX_COLORS)]
                    fill_color = color + "40" if i != selected_box_idx else None
                    x, y, w, h = box
                    draw.rectangle([x, y, x + w, y + h], outline=color, width=2, fill=fill_color)

                    if i == selected_box_idx:
                        cx, cy = x + w // 2, y + h // 2
                        draw.line([(cx - 6, cy), (cx + 6, cy)], fill=color, width=3)
                        draw.line([(cx, cy - 6), (cx, cy + 6)], fill=color, width=3)

                    label_text = str(i + 1)
                    text_x, text_y = x + 3, y + 1
                    try:
                        # Draw outline for text for better visibility
                        draw.text((text_x - 1, text_y - 1), label_text, font=self.overlay_font, fill="white")
                        draw.text((text_x + 1, text_y - 1), label_text, font=self.overlay_font, fill="white")
                        draw.text((text_x - 1, text_y + 1), label_text, font=self.overlay_font, fill="white")
                        draw.text((text_x + 1, text_y + 1), label_text, font=self.overlay_font, fill="white")
                        draw.text((text_x, text_y), label_text, font=self.overlay_font, fill=color)
                    except Exception:  # Fallback if font issues
                        draw.text((text_x, text_y), label_text, fill=color)

        max_w, max_h = WIZARD_SCREENSHOT_PREVIEW_MAX_WIDTH - 50, WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT - 50
        thumb = img_pil_to_draw_on.copy()
        thumb.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        dw, dh = thumb.size

        ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(dw, dh))
        self.step_logic_region_image_label.configure(image=ctk_img, text="", width=dw, height=dh)

        # Store scale factors for click event conversion
        self.step_logic_region_image_label.photo_image_scale_factor_x = self.state.current_step_region_image_pil_for_display.width / float(dw) if dw > 0 else 1.0
        self.step_logic_region_image_label.photo_image_scale_factor_y = self.state.current_step_region_image_pil_for_display.height / float(dh) if dh > 0 else 1.0

    def _on_region_image_click_for_element_selection(self, event):
        if not self.state.ai_refined_element_candidates or not hasattr(self.step_logic_region_image_label, "photo_image_scale_factor_x"):
            return

        scale_x = getattr(self.step_logic_region_image_label, "photo_image_scale_factor_x", 1.0)
        scale_y = getattr(self.step_logic_region_image_label, "photo_image_scale_factor_y", 1.0)
        click_x_orig, click_y_orig = int(event.x * scale_x), int(event.y * scale_y)

        newly_selected_idx = next(
            (
                i
                for i, c in enumerate(self.state.ai_refined_element_candidates)
                if c.get("box") and (c["box"][0] <= click_x_orig < c["box"][0] + c["box"][2]) and (c["box"][1] <= click_y_orig < c["box"][1] + c["box"][3])
            ),
            None,
        )

        if newly_selected_idx is not None and newly_selected_idx != self.state.user_selected_candidate_box_index:
            self.state.user_selected_candidate_box_index = newly_selected_idx
            self._display_current_step_region_image_with_candidates(self.state.ai_refined_element_candidates, self.state.user_selected_candidate_box_index)
            self._update_action_params_with_selected_element()
        elif newly_selected_idx is None and self.state.user_selected_candidate_box_index is not None:
            self.state.user_selected_candidate_box_index = None
            self._display_current_step_region_image_with_candidates(self.state.ai_refined_element_candidates, None)
            self._clear_action_target_params()

        self.on_state_change()  # Notify controller of state change

    def _update_action_params_with_selected_element(self):
        if (
            self.state.user_selected_candidate_box_index is None
            or not self.state.ai_refined_element_candidates
            or self.state.user_selected_candidate_box_index >= len(self.state.ai_refined_element_candidates)
        ):
            self.state.user_confirmed_element_for_action = None
            return

        sel_cand = self.state.ai_refined_element_candidates[self.state.user_selected_candidate_box_index]
        self.state.user_confirmed_element_for_action = {
            "value": {"box": sel_cand["box"], "found": True, "element_label": sel_cand.get("label_suggestion", self.state.ai_element_to_refine_desc or "AI Element")},
            "_source_region_for_capture_": self.state.current_step_region_name,
        }
        logger.info(
            f"DefineLogicView: Element confirmed for action: Label='{self.state.user_confirmed_element_for_action['value']['element_label']}', Box={self.state.user_confirmed_element_for_action['value']['box']} in region '{self.state.current_step_region_name}'"
        )

        act_type_var = self.ui_step_logic_optionmenu_vars.get("step_act_type_var")
        if act_type_var and isinstance(act_type_var, tk.StringVar):
            act_type_var.set("click")
            # Trigger a re-render of action parameters for 'click' type
            self._on_wizard_logic_type_change("action", "click")
            # Schedule setting click parameters shortly after the re-render completes
            self.after(50, self._set_click_action_params_for_selected_element)
        self.on_state_change()  # Notify controller of state change

    def _set_click_action_params_for_selected_element(self):
        # Set target_relation and gemini_element_variable in the UI
        rel_var = self.ui_step_logic_optionmenu_vars.get("step_act_target_relation_var")
        gem_var_entry = self.ui_step_logic_detail_widgets.get("step_act_gemini_element_variable")

        if rel_var and isinstance(rel_var, tk.StringVar):
            rel_var.set("center_of_gemini_element")
            # Manually trigger conditional visibility update for target_relation
            tr_pdef = next((p for p in UI_PARAM_CONFIG["actions"]["click"] if p["id"] == "target_relation"), None)
            if tr_pdef:
                self._update_step_logic_conditional_visibility(tr_pdef, "center_of_gemini_element")

        if gem_var_entry and isinstance(gem_var_entry, ctk.CTkEntry):
            gem_var_entry.delete(0, tk.END)
            gem_var_entry.insert(0, self.state.current_step_temp_gemini_var_name or "_wizard_sel_elem_")
        logger.debug(f"DefineLogicView: Click action UI params set for visually selected element (var: {self.state.current_step_temp_gemini_var_name}).")
        self.on_state_change()  # Notify controller of state change

    def _clear_action_target_params(self):
        self.state.user_confirmed_element_for_action = None
        act_type_var = self.ui_step_logic_optionmenu_vars.get("step_act_type_var")

        # Only clear target-specific parameters if the current action is still 'click'
        if act_type_var and isinstance(act_type_var, tk.StringVar) and act_type_var.get() == "click":
            rel_var = self.ui_step_logic_optionmenu_vars.get("step_act_target_relation_var")
            gem_var_entry = self.ui_step_logic_detail_widgets.get("step_act_gemini_element_variable")

            if rel_var:
                rel_var.set("center_of_region")  # Default back to center_of_region
            if gem_var_entry and isinstance(gem_var_entry, ctk.CTkEntry):
                gem_var_entry.delete(0, tk.END)

            # Manually trigger conditional visibility update for target_relation
            tr_pdef = next((p for p in UI_PARAM_CONFIG.get("actions", {}).get("click", []) if p["id"] == "target_relation"), None)
            if tr_pdef:
                self._update_step_logic_conditional_visibility(tr_pdef, "center_of_region")
        logger.debug("DefineLogicView: Cleared action target parameters in UI after deselecting element.")
        self.on_state_change()  # Notify controller of state change

    def _attempt_set_template_name_in_ui(self, template_name_to_set: str):
        widget_key = "step_cond_template_name"
        tk_var = self.ui_step_logic_optionmenu_vars.get(f"{widget_key}_var")
        widget = self.ui_step_logic_detail_widgets.get(widget_key)
        if tk_var and isinstance(tk_var, tk.StringVar) and widget and isinstance(widget, ctk.CTkOptionMenu):
            # Refresh options in case new template was added
            new_opts = [""] + [t.get("name", "") for t in self.profile_generator.generated_profile_data.get("templates", []) if t.get("name")]
            widget.configure(values=new_opts)
            if template_name_to_set in new_opts:
                tk_var.set(template_name_to_set)
            else:
                logger.warning(f"DefineLogicView: Newly added template '{template_name_to_set}' not found in dropdown options after repopulating. Options: {new_opts}")
        else:
            logger.warning(f"DefineLogicView: Could not find or set template_name dropdown for '{template_name_to_set}'.")
        self.on_state_change()  # Notify controller of state change

    def _set_click_action_params_for_template(self, template_name: str):
        target_relation_var = self.ui_step_logic_optionmenu_vars.get("step_act_target_relation_var")
        if target_relation_var and isinstance(target_relation_var, tk.StringVar):
            target_relation_var.set("center_of_last_match")
            # Manually trigger conditional visibility update
            tr_pdef = next((p for p in UI_PARAM_CONFIG.get("actions", {}).get("click", []) if p["id"] == "target_relation"), None)
            if tr_pdef:
                self._update_step_logic_conditional_visibility(tr_pdef, "center_of_last_match")
            logger.info(f"DefineLogicView: Action UI updated to target 'center_of_last_match' for template '{template_name}'.")

        # Ensure any gemini_element_variable is cleared
        gem_var_entry = self.ui_step_logic_detail_widgets.get("step_act_gemini_element_variable")
        if gem_var_entry and isinstance(gem_var_entry, ctk.CTkEntry):
            gem_var_entry.delete(0, tk.END)
        self.state.user_confirmed_element_for_action = None
        self.on_state_change()  # Notify controller of state change

    def _get_parameters_from_ui_wizard_scoped(self, param_group_key: str, item_subtype: str, widget_prefix: str) -> Optional[Dict[str, Any]]:
        params: Dict[str, Any] = {"type": item_subtype}
        all_ok = True
        param_defs = UI_PARAM_CONFIG.get(param_group_key, {}).get(item_subtype, [])
        if not param_defs and item_subtype != "always_true":
            return params

        for p_def in param_defs:
            p_id, lbl_err, target_type, def_val, is_req_def = p_def["id"], p_def["label"].rstrip(":"), p_def["type"], p_def.get("default", ""), p_def.get("required", False)
            w_key = f"{widget_prefix}{p_id}"
            widget = self.ui_step_logic_detail_widgets.get(w_key)
            tk_var = self.ui_step_logic_optionmenu_vars.get(f"{w_key}_var")

            is_vis = False
            if widget and widget.winfo_exists():
                is_vis = widget.winfo_ismapped()
            elif tk_var and isinstance(tk_var, tk.BooleanVar) and widget and widget.winfo_exists():
                is_vis = widget.winfo_ismapped()

            eff_req = is_req_def and is_vis

            if not is_vis and not eff_req:
                continue

            if widget is None and not isinstance(tk_var, tk.BooleanVar):
                if eff_req:
                    logger.error(f"DefineLogicView GetParams: UI Widget for required parameter '{lbl_err}' (ID: {p_id}) not found.")
                    all_ok = False
                params[p_id] = def_val
                continue

            val_args = {"required": eff_req, "allow_empty_string": p_def.get("allow_empty_string", target_type == str), "min_val": p_def.get("min_val"), "max_val": p_def.get("max_val")}
            val, valid = validate_and_get_widget_value(widget, tk_var, lbl_err, target_type, def_val, parent_widget_for_msgbox=self.controller, **val_args)  # Pass controller as parent

            if not valid:
                all_ok = False
                val = def_val

            if isinstance(val, str) and val.startswith(USER_INPUT_PLACEHOLDER_PREFIX):
                if eff_req:
                    messagebox.showerror("Input Required", f"Please provide a value for '{lbl_err}'. The placeholder '{val}' is not a valid input.", parent=self.controller)
                    all_ok = False
                    val = def_val
                elif p_def.get("allow_empty_string", False):
                    val = ""

            if target_type == "list_str_csv":
                params[p_id] = (
                    [s.strip() for s in val.split(",") if isinstance(val, str) and val.strip()]
                    if isinstance(val, str) and val.strip()
                    else ([] if not def_val or not isinstance(def_val, list) else def_val)
                )
            else:
                params[p_id] = val

            if p_id == "template_name" and param_group_key == "conditions":
                s_tpl_name = val
                params["template_filename"] = ""
                if s_tpl_name:
                    fname = next((t.get("filename", "") for t in self.profile_generator.generated_profile_data.get("templates", []) if t.get("name") == s_tpl_name), "")
                    params["template_filename"] = fname
                    if not fname and eff_req:
                        messagebox.showerror("Internal Error", f"Filename for selected template '{s_tpl_name}' could not be found in profile draft.", parent=self.controller)
                        all_ok = False
                elif eff_req:
                    messagebox.showerror("Input Error", f"'{lbl_err}' (Template Name) is required for template_match_found condition.", parent=self.controller)
                    all_ok = False
                if "template_name" in params:
                    del params["template_name"]

        if item_subtype == "always_true" and param_group_key == "conditions":
            # For always_true condition, we still allow an optional region override
            region_pdef_always_true = next((pd for pd in UI_PARAM_CONFIG.get("conditions", {}).get("always_true", []) if pd["id"] == "region"), None)
            if region_pdef_always_true:
                region_val_at, _ = validate_and_get_widget_value(
                    self.ui_step_logic_detail_widgets.get(f"{widget_prefix}region"),
                    self.ui_step_logic_optionmenu_vars.get(f"{widget_prefix}region_var"),
                    "Region (for always_true)",
                    str,
                    "",
                    required=False,
                    parent_widget_for_msgbox=self.controller,
                )
                if region_val_at:
                    params["region"] = region_val_at

        return params if all_ok else None

    def _get_current_step_logic_from_ui(self) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        log_prefix = f"DefineLogicView.GetStepLogicUI (StepID: {self.state.current_step_data.get('step_id') if self.state.current_step_data else 'N/A'})"
        cond_type_var = self.ui_step_logic_optionmenu_vars.get("step_cond_type_var")
        act_type_var = self.ui_step_logic_optionmenu_vars.get("step_act_type_var")
        if not cond_type_var or not act_type_var:
            logger.error(f"{log_prefix}: Crit err: Cond/Act type UI selectors MIA.")
            return None

        cond_type = cond_type_var.get()
        act_type = act_type_var.get()
        condition_params = self._get_parameters_from_ui_wizard_scoped("conditions", cond_type, "step_cond_")
        if condition_params is None:
            logger.error(f"{log_prefix}: Validation failed for Condition parameters of type '{cond_type}'.")
            return None

        action_params = self._get_parameters_from_ui_wizard_scoped("actions", act_type, "step_act_")
        if action_params is None:
            logger.error(f"{log_prefix}: Validation failed for Action parameters of type '{act_type}'.")
            return None

        # Special handling for converting AI-selected Gemini element click to absolute coordinates
        if self.state.user_confirmed_element_for_action and action_params.get("type") == "click" and action_params.get("gemini_element_variable") == self.state.current_step_temp_gemini_var_name:

            box_data = self.state.user_confirmed_element_for_action["value"]["box"]
            source_region_name_for_conversion = self.state.user_confirmed_element_for_action["_source_region_for_capture_"]

            # Retrieve the region config from the profile *being generated* (profile_generator_cm)
            source_region_config_from_draft = next(
                (r_cfg for r_cfg in self.profile_generator.generated_profile_data.get("regions", []) if r_cfg.get("name") == source_region_name_for_conversion), None
            )

            if source_region_config_from_draft:
                abs_screen_region_x = source_region_config_from_draft.get("x", 0)
                abs_screen_region_y = source_region_config_from_draft.get("y", 0)

                click_target_relation_in_ui_var = self.ui_step_logic_optionmenu_vars.get("step_act_target_relation_var")
                click_target_relation_in_ui = click_target_relation_in_ui_var.get() if click_target_relation_in_ui_var else "center_of_gemini_element"

                # Calculate absolute click coordinates based on target_relation (center or top-left)
                if "center" in click_target_relation_in_ui.lower():
                    abs_click_x = abs_screen_region_x + box_data[0] + (box_data[2] // 2)
                    abs_click_y = abs_screen_region_y + box_data[1] + (box_data[3] // 2)
                else:  # top_left_of_gemini_element
                    abs_click_x = abs_screen_region_x + box_data[0]
                    abs_click_y = abs_screen_region_y + box_data[1]

                # Overwrite action parameters to use absolute coordinates
                action_params["target_relation"] = "absolute"
                action_params["x"] = str(abs_click_x)
                action_params["y"] = str(abs_click_y)
                action_params.pop("gemini_element_variable", None)
                action_params.pop("target_region", None)  # Remove obsolete params
                logger.info(f"{log_prefix}: Converted Gemini elem click (var: {self.state.current_step_temp_gemini_var_name}) to absolute ({abs_click_x},{abs_click_y}).")
            else:
                logger.error(f"{log_prefix}: Cannot find source region '{source_region_name_for_conversion}' to convert Gemini click to absolute. Action may fail.")
                messagebox.showerror(
                    "Internal Error",
                    f"Source region '{source_region_name_for_conversion}' (for element click) not found in generated profile draft. Cannot accurately set absolute coordinates for AI-identified element.",
                    parent=self.controller,
                )
                return None

        return condition_params, action_params

    def confirm_and_add_logic_to_profile(self) -> bool:
        """
        Called by the controller when the user clicks 'Next' on this page.
        Validates UI inputs, assembles the rule, and adds it to the profile being generated.
        """
        logic_tuple = self._get_current_step_logic_from_ui()
        if not logic_tuple:
            return False  # Validation failed in _get_current_step_logic_from_ui, message already shown.

        confirmed_condition, confirmed_action = logic_tuple
        current_step = self.state.current_step_data

        if current_step and self.state.current_step_region_name:
            sanitized_desc = current_step.get("description", "Task")[:15].replace(" ", "_").replace("'", "")
            base_rule_name = f"Rule_Step{current_step.get('step_id')}_{sanitized_desc}"
            rule_name_to_add = base_rule_name
            count = 1
            # Ensure rule name is unique in the profile being generated
            while any(r.get("name") == rule_name_to_add for r in self.profile_generator.generated_profile_data.get("rules", [])):
                rule_name_to_add = f"{base_rule_name}_{count}"
                count += 1

            rule_to_add = {
                "name": rule_name_to_add,
                "region": self.state.current_step_region_name,
                "condition": confirmed_condition,
                "action": confirmed_action,
                "comment": f"AI Generated for: {current_step.get('description')}",
            }

            if self.profile_generator.add_rule_definition(rule_to_add):
                logger.info(f"DefineLogicView: Rule '{rule_name_to_add}' added for step {current_step.get('step_id')}.")
                self.main_app_instance._set_dirty_status(True)  # Mark main app as dirty
                return True
            else:
                messagebox.showerror("Error", f"Failed to add rule for step {current_step.get('step_id')}.", parent=self.controller)
                return False
        else:
            messagebox.showerror("Internal Error", "Missing step data or region name when attempting to add rule. Please review previous steps.", parent=self.controller)
            return False

    # --- AI Triggering & Handling ---
    def _trigger_ai_logic_suggestion_for_step_threaded(self):
        if not self.state.current_step_data or self.state.current_step_region_image_np is None or not self.state.current_step_region_name:
            logger.warning("DefineLogicView: Cannot trigger AI logic suggestion: missing step data, region image, or region name. Rendering defaults.")
            self._render_step_logic_editors(copy.deepcopy(DEFAULT_CONDITION_STRUCTURE_PG), copy.deepcopy(DEFAULT_ACTION_STRUCTURE_PG), None)
            return

        self.controller._show_loading_overlay("AI suggesting logic...")
        self.btn_refine_element.configure(state="disabled")  # Disable while AI is busy
        self.btn_capture_template_for_step.configure(state="disabled")  # Disable template capture while AI is busy

        thread = threading.Thread(
            target=self._perform_ai_logic_suggestion_in_thread, args=(self.state.current_step_data, self.state.current_step_region_image_np, self.state.current_step_region_name)
        )
        thread.daemon = True
        thread.start()

    def _perform_ai_logic_suggestion_in_thread(self, plan_step_data: IntermediatePlanStep, region_image_np: np.ndarray, region_name: str):
        suggestion_result = None
        error = None
        try:
            suggestion_result = self.profile_generator.suggest_logic_for_step(plan_step_data, region_image_np, region_name)
        except Exception as e:
            logger.error(f"DefineLogicView: Exception in AI logic suggestion thread: {e}", exc_info=True)
            error = e
        self.after(0, self._handle_ai_logic_suggestion_result, suggestion_result, error)

    def _handle_ai_logic_suggestion_result(self, suggestion_result: Optional[Dict[str, Any]], error: Optional[Exception]):
        self.controller._hide_loading_overlay()
        self.btn_refine_element.configure(state="normal" if self.element_refine_entry.get().strip() else "disabled")
        self.btn_capture_template_for_step.configure(state="normal")

        s_cond, s_act, el_ref_desc = copy.deepcopy(DEFAULT_CONDITION_STRUCTURE_PG), copy.deepcopy(DEFAULT_ACTION_STRUCTURE_PG), None

        if error:
            messagebox.showerror("AI Error", f"Error during AI logic suggestion: {error}.\nUsing default condition/action.", parent=self.controller)
        elif suggestion_result:
            s_cond = suggestion_result.get("suggested_condition", s_cond)
            s_act = suggestion_result.get("suggested_action", s_act)
            el_ref_desc = suggestion_result.get("element_to_refine_description")

            # Store suggestions in state for persistence across UI renders
            self.state.ai_suggested_condition_for_step = copy.deepcopy(s_cond)
            self.state.ai_suggested_action_for_step = copy.deepcopy(s_act)
            self.state.ai_element_to_refine_desc = el_ref_desc

            messagebox.showinfo(
                "AI Logic Suggestion",
                f"AI suggested a condition of type '{s_cond.get('type')}' and action '{s_act.get('type')}'.\nReasoning: {suggestion_result.get('reasoning', 'N/A')}",
                parent=self.controller,
            )
        else:
            messagebox.showwarning("AI Suggestion Failed", "AI could not suggest logic for this step. Please configure manually or use defaults.", parent=self.controller)
            # Clear any previous AI suggestions if a new attempt failed
            self.state.ai_suggested_condition_for_step = None
            self.state.ai_suggested_action_for_step = None
            self.state.ai_element_to_refine_desc = None

        self._render_step_logic_editors(s_cond, s_act, el_ref_desc)
        self.on_state_change()  # Notify controller of state change

    # --- Dynamic UI Rendering ---
    def _render_step_logic_editors(self, condition_data: Dict[str, Any], action_data: Dict[str, Any], element_to_refine_description: Optional[str]):
        # Render Condition UI
        cond_type = str(condition_data.get("type", "always_true"))
        cond_type_var = ctk.StringVar(value=cond_type)
        ctk.CTkLabel(self.step_logic_condition_frame, text="Type:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        cond_menu = ctk.CTkOptionMenu(self.step_logic_condition_frame, variable=cond_type_var, values=CONDITION_TYPES, command=lambda choice: self._on_wizard_logic_type_change("condition", choice))
        cond_menu.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.ui_step_logic_optionmenu_vars["step_cond_type_var"] = cond_type_var
        self.ui_step_logic_detail_widgets["step_cond_type"] = cond_menu
        self._render_dynamic_params_in_wizard_subframe("conditions", cond_type, condition_data, self.step_logic_condition_frame, 2, "step_cond_")

        # Render Action UI
        act_type = str(action_data.get("type", "log_message"))
        act_type_var = ctk.StringVar(value=act_type)
        ctk.CTkLabel(self.step_logic_action_frame, text="Type:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        act_menu = ctk.CTkOptionMenu(self.step_logic_action_frame, variable=act_type_var, values=ACTION_TYPES, command=lambda choice: self._on_wizard_logic_type_change("action", choice))
        act_menu.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.ui_step_logic_optionmenu_vars["step_act_type_var"] = act_type_var
        self.ui_step_logic_detail_widgets["step_act_type"] = act_menu
        self._render_dynamic_params_in_wizard_subframe("actions", act_type, action_data, self.step_logic_action_frame, 2, "step_act_")

        # Update element refinement entry field
        self.element_refine_entry.delete(0, tk.END)
        if element_to_refine_description:
            self.element_refine_entry.insert(0, element_to_refine_description)
            self.btn_refine_element.configure(state="normal")
        else:
            self.btn_refine_element.configure(state="disabled")

        self.on_state_change()  # Update navigation buttons

    def _on_wizard_logic_type_change(self, part_key: str, new_type: str):
        self.main_app_instance._set_dirty_status(True)  # Mark main app as dirty
        logger.debug(f"DefineLogicView: Logic part '{part_key}' type changed to '{new_type}'. Re-rendering params.")

        target_frame = self.step_logic_condition_frame if part_key == "condition" else self.step_logic_action_frame
        param_group_for_config = "conditions" if part_key == "condition" else "actions"
        widget_prefix = "step_cond_" if part_key == "condition" else "step_act_"

        default_data_for_new_type = {"type": new_type}
        new_type_param_defs = UI_PARAM_CONFIG.get(param_group_for_config, {}).get(new_type, [])

        # Preserve specific fields if they exist in the old data and are valid for the new type
        # For instance, if changing condition type, keep the 'region' if new type supports it
        if part_key == "condition":
            current_condition_data = self.state.ai_suggested_condition_for_step or {}
            region_widget = self.ui_step_logic_detail_widgets.get(f"{widget_prefix}region")
            region_var = self.ui_step_logic_optionmenu_vars.get(f"{widget_prefix}region_var")

            if region_widget and region_var and isinstance(region_var, tk.StringVar):
                current_region_val = region_var.get()
                if current_region_val and any(pdef.get("id") == "region" for pdef in new_type_param_defs):
                    default_data_for_new_type["region"] = current_region_val

            # Preserve 'capture_as' if it exists and new type supports it
            if "capture_as" in current_condition_data and any(pdef.get("id") == "capture_as" for pdef in new_type_param_defs):
                default_data_for_new_type["capture_as"] = current_condition_data["capture_as"]

            self.state.ai_suggested_condition_for_step = default_data_for_new_type  # Update state

        elif part_key == "action":
            current_action_data = self.state.ai_suggested_action_for_step or {}
            # Preserve 'pyautogui_pause_before' if new type supports it
            if "pyautogui_pause_before" in current_action_data and any(pdef.get("id") == "pyautogui_pause_before" for pdef in new_type_param_defs):
                default_data_for_new_type["pyautogui_pause_before"] = current_action_data["pyautogui_pause_before"]
            self.state.ai_suggested_action_for_step = default_data_for_new_type  # Update state
            # When action type changes, clear any specific element selection as it might be irrelevant
            self._clear_action_target_params()

        self._render_dynamic_params_in_wizard_subframe(param_group_for_config, new_type, default_data_for_new_type, target_frame, 2, widget_prefix)
        self.on_state_change()  # Notify controller of state change

    def _render_dynamic_params_in_wizard_subframe(self, param_group_key: str, item_subtype: str, data_source: Dict[str, Any], parent_frame: ctk.CTkFrame, start_row: int, widget_prefix: str):
        # Clear previous dynamic widgets and their associated state
        for child_widget in list(parent_frame.winfo_children()):
            grid_info = child_widget.grid_info()
            if grid_info and grid_info.get("row", -1) >= start_row:
                widget_key_to_pop = None
                for wk, w_instance in list(self.ui_step_logic_detail_widgets.items()):  # Use list() to iterate over a copy
                    if w_instance == child_widget and wk.startswith(widget_prefix):
                        widget_key_to_pop = wk
                        break
                if widget_key_to_pop:
                    self.ui_step_logic_detail_widgets.pop(widget_key_to_pop, None)
                    self.ui_step_logic_optionmenu_vars.pop(f"{widget_key_to_pop}_var", None)
                child_widget.destroy()

        self.ui_step_logic_param_widgets_and_defs.clear()
        self.ui_step_logic_controlling_widgets.clear()
        self.ui_step_logic_widget_prefix = widget_prefix

        param_defs_for_subtype = UI_PARAM_CONFIG.get(param_group_key, {}).get(item_subtype, [])
        current_r = start_row

        if not param_defs_for_subtype and item_subtype not in ["always_true"]:
            ctk.CTkLabel(parent_frame, text=f"No params for '{item_subtype}'.", text_color="gray").grid(row=current_r, column=0, columnspan=2)
            return

        for p_def_orig in param_defs_for_subtype:
            p_def = copy.deepcopy(p_def_orig)  # Work with a copy to add internal keys
            p_def["_param_group_key"] = param_group_key
            p_def["_item_subtype"] = item_subtype

            p_id, lbl_txt, w_type, d_type, def_val = p_def["id"], p_def["label"], p_def["widget"], p_def["type"], p_def.get("default", "")
            current_value_for_param = data_source.get(p_id, def_val)
            widget_full_key = f"{widget_prefix}{p_id}"

            label_widget = ctk.CTkLabel(parent_frame, text=lbl_txt)
            created_widget_instance = None

            if w_type == "entry":
                entry = ctk.CTkEntry(parent_frame, placeholder_text=str(p_def.get("placeholder", "")))
                display_value = ", ".join(map(str, current_value_for_param)) if d_type == "list_str_csv" and isinstance(current_value_for_param, list) else str(current_value_for_param)
                entry.insert(0, display_value)
                entry.bind("<KeyRelease>", lambda e, dp_wp=widget_prefix: self.main_app_instance._set_dirty_status(True))
                created_widget_instance = entry
            elif w_type == "textbox":
                textbox = ctk.CTkTextbox(parent_frame, height=p_def.get("height", 60), wrap="word")
                textbox.insert("0.0", str(current_value_for_param))
                textbox.bind("<FocusOut>", lambda e, dp_wp=widget_prefix: self.main_app_instance._set_dirty_status(True))
                created_widget_instance = textbox
            elif w_type.startswith("optionmenu"):
                options_list = []
                src_key = p_def.get("options_source") if w_type == "optionmenu_dynamic" else p_def.get("options_const_key")

                # Dynamic options from currently generated profile data
                if w_type == "optionmenu_dynamic" and src_key == "regions":
                    options_list = [""] + [r.get("name", "") for r in self.profile_generator.generated_profile_data.get("regions", []) if r.get("name")]
                elif w_type == "optionmenu_dynamic" and src_key == "templates":
                    options_list = [""] + [t.get("name", "") for t in self.profile_generator.generated_profile_data.get("templates", []) if t.get("name")]
                # Static options
                elif w_type == "optionmenu_static" and src_key:
                    options_list = OPTIONS_CONST_MAP.get(src_key, [])

                if not options_list:
                    options_list = [str(def_val)] if str(def_val) else [""]  # Ensure at least one option

                str_current_val = str(current_value_for_param)
                final_current_val_for_menu = str_current_val if str_current_val in options_list else (str(def_val) if str(def_val) in options_list else (options_list[0] if options_list else ""))

                tk_var = ctk.StringVar(value=final_current_val_for_menu)
                option_menu = ctk.CTkOptionMenu(
                    parent_frame, variable=tk_var, values=options_list, command=lambda choice, p=p_def, wp=widget_prefix: self._update_step_logic_conditional_visibility(p, choice)
                )
                self.ui_step_logic_optionmenu_vars[f"{widget_full_key}_var"] = tk_var
                created_widget_instance = option_menu

                if any(other_pdef.get("condition_show", {}).get("field") == p_id for other_pdef in param_defs_for_subtype if other_pdef.get("condition_show")):
                    self.ui_step_logic_controlling_widgets[p_id] = created_widget_instance
            elif w_type == "checkbox":
                tk_bool_var = tk.BooleanVar(value=bool(current_value_for_param))
                checkbox = ctk.CTkCheckBox(
                    parent_frame, text="", variable=tk_bool_var, command=lambda p=p_def, v=tk_bool_var, wp=widget_prefix: self._update_step_logic_conditional_visibility(p, v.get())
                )
                self.ui_step_logic_optionmenu_vars[f"{widget_full_key}_var"] = tk_bool_var
                created_widget_instance = checkbox

                if any(other_pdef.get("condition_show", {}).get("field") == p_id for other_pdef in param_defs_for_subtype if other_pdef.get("condition_show")):
                    self.ui_step_logic_controlling_widgets[p_id] = created_widget_instance

            if created_widget_instance:
                self.ui_step_logic_detail_widgets[widget_full_key] = created_widget_instance
                label_widget.grid(row=current_r, column=0, padx=(0, 5), pady=2, sticky="nw" if w_type == "textbox" else "w")
                created_widget_instance.grid(row=current_r, column=1, padx=5, pady=2, sticky="ew")
                self.ui_step_logic_param_widgets_and_defs.append({"widget": created_widget_instance, "label_widget": label_widget, "param_def": p_def})
                current_r += 1
            else:
                label_widget.destroy()

        self._apply_step_logic_conditional_visibility()  # Apply initial visibility after all widgets are created

    def _update_step_logic_conditional_visibility(self, changed_param_def_controller: Dict[str, Any], new_value_of_controller: Any):
        self.main_app_instance._set_dirty_status(True)  # Mark main app as dirty
        logger.debug(
            f"DefineLogicView: Controller '{changed_param_def_controller.get('id')}' for prefix '{self.ui_step_logic_widget_prefix}' changed to '{new_value_of_controller}'. Re-evaluating visibility."
        )
        self._apply_step_logic_conditional_visibility()
        self.on_state_change()  # Notify controller of state change

    def _apply_step_logic_conditional_visibility(self):
        if not hasattr(self, "ui_step_logic_param_widgets_and_defs") or not hasattr(self, "ui_step_logic_controlling_widgets") or not hasattr(self, "ui_step_logic_widget_prefix"):
            return

        for item in self.ui_step_logic_param_widgets_and_defs:
            widget_instance, label_widget_instance, param_definition = item["widget"], item["label_widget"], item["param_def"]
            visibility_config = param_definition.get("condition_show")
            should_be_visible = True

            if visibility_config:
                controlling_field_id = visibility_config.get("field")
                expected_values_for_visibility = visibility_config.get("values", [])
                controller_widget_instance = self.ui_step_logic_controlling_widgets.get(controlling_field_id)
                current_controller_value = None

                if isinstance(controller_widget_instance, ctk.CTkOptionMenu):
                    tk_var_for_controller = self.ui_step_logic_optionmenu_vars.get(f"{self.ui_step_logic_widget_prefix}{controlling_field_id}_var")
                    current_controller_value = tk_var_for_controller.get() if tk_var_for_controller else None
                elif isinstance(controller_widget_instance, ctk.CTkCheckBox):
                    tk_var_for_controller = self.ui_step_logic_optionmenu_vars.get(f"{self.ui_step_logic_widget_prefix}{controlling_field_id}_var")
                    current_controller_value = tk_var_for_controller.get() if tk_var_for_controller else None
                    expected_values_for_visibility = [bool(v) for v in expected_values_for_visibility if isinstance(v, (str, int, bool))]  # Cast expected values to bool
                elif isinstance(controller_widget_instance, ctk.CTkEntry):
                    current_controller_value = controller_widget_instance.get()

                if current_controller_value is None or current_controller_value not in expected_values_for_visibility:
                    should_be_visible = False

            if widget_instance and widget_instance.winfo_exists():
                is_currently_mapped = widget_instance.winfo_ismapped()
                if should_be_visible and not is_currently_mapped:
                    widget_instance.grid()
                    # Also grid the label if it exists and is currently unmapped
                    _ = label_widget_instance.grid() if label_widget_instance and label_widget_instance.winfo_exists() and not label_widget_instance.winfo_ismapped() else None
                elif not should_be_visible and is_currently_mapped:
                    widget_instance.grid_remove()
                    # Also grid_remove the label if it exists and is currently mapped
                    _ = label_widget_instance.grid_remove() if label_widget_instance and label_widget_instance.winfo_exists() and label_widget_instance.winfo_ismapped() else None

    # --- AI Refinement and Template Capture ---
    def _handle_ai_refine_element_threaded(self):
        element_desc_to_refine = self.element_refine_entry.get().strip()
        if not element_desc_to_refine:
            messagebox.showwarning("Input Missing", "Enter element description to find.", parent=self.controller)
            return
        if not self.state.current_step_region_image_np or not self.state.current_step_region_name:
            messagebox.showerror("Error", "Region image or name is missing for refinement context.", parent=self.controller)
            return

        self.state.ai_element_to_refine_desc = element_desc_to_refine
        self.controller._show_loading_overlay(f"AI refining '{element_desc_to_refine[:30]}...'")
        self.btn_refine_element.configure(state="disabled")  # Disable button during AI call

        thread = threading.Thread(target=self._perform_ai_refine_element_in_thread, args=(element_desc_to_refine, self.state.current_step_region_image_np, self.state.current_step_region_name))
        thread.daemon = True
        thread.start()

    def _perform_ai_refine_element_in_thread(self, element_desc: str, region_image_np: np.ndarray, region_name: str):
        candidates = None
        error = None
        try:
            candidates = self.profile_generator.refine_element_location(element_desc, region_image_np, region_name, task_rule_name_for_log="AI_Gen_Wizard_Refine")
        except Exception as e:
            logger.error(f"DefineLogicView: Exception in AI refine element thread: {e}", exc_info=True)
            error = e
        self.after(0, self._handle_ai_refine_element_result, candidates, error)

    def _handle_ai_refine_element_result(self, candidates: Optional[List[Dict[str, Any]]], error: Optional[Exception]):
        self.controller._hide_loading_overlay()
        self.btn_refine_element.configure(state="normal" if self.element_refine_entry.get().strip() else "disabled")  # Re-enable if text is present

        if error:
            messagebox.showerror("AI Error", f"Error during AI element refinement: {error}", parent=self.controller)
            self.state.ai_refined_element_candidates = []  # Clear candidates on error
        else:
            self.state.ai_refined_element_candidates = candidates if candidates else []

        self.state.user_selected_candidate_box_index = None  # Reset selection
        self._clear_action_target_params()  # Clear action params related to previous selection

        if self.state.ai_refined_element_candidates:
            self._display_current_step_region_image_with_candidates(self.state.ai_refined_element_candidates, None)
            messagebox.showinfo(
                "AI Element Candidates", f"AI found {len(self.state.ai_refined_element_candidates)} candidate(s). Click one on the image to select for action.", parent=self.controller
            )
        else:
            self._display_current_step_region_image_with_candidates(None, None)  # Clear overlays
            messagebox.showwarning("AI Refinement", "AI could not find matching elements, or refinement failed.", parent=self.controller)

        self.on_state_change()  # Notify controller of state change

    def _handle_capture_template_for_step(self):
        if not self.state.current_step_region_image_pil_for_display or not self.state.current_step_region_name:
            messagebox.showerror("Error", "Region image not available for template capture.", parent=self.controller)
            return

        element_desc_for_template = self.state.ai_element_to_refine_desc or (self.state.current_step_data.get("description", "step_element")[:20] if self.state.current_step_data else "step_element")

        # Generate a suggested unique template name
        default_template_name_base = f"tpl_{self.state.current_step_region_name}_{element_desc_for_template.replace(' ','_').lower()}"
        sane_default_template_name_base = "".join(c if c.isalnum() else "_" for c in default_template_name_base)
        sane_default_template_name_base = sane_default_template_name_base[:40] if len(sane_default_template_name_base) > 40 else sane_default_template_name_base

        count = 0
        suggested_tpl_name = sane_default_template_name_base
        # Check against already staged templates and existing templates in the draft profile
        while any(t.get("name") == suggested_tpl_name for t in self.profile_generator.generated_profile_data.get("templates", [])) or any(
            t.get("name") == suggested_tpl_name for t in self.state.staged_templates_with_image_data
        ):
            count += 1
            suggested_tpl_name = f"{sane_default_template_name_base}_{count}"

        template_name_dialog = ctk.CTkInputDialog(text=f"Enter unique name for this new template:", title="New Template Name", entry_text=suggested_tpl_name)
        template_name_input = template_name_dialog.get_input()

        if not template_name_input or not template_name_input.strip():
            logger.info("DefineLogicView: Template capture cancelled: No name provided.")
            return
        template_name = template_name_input.strip()

        # Final check for uniqueness after user input
        if any(t.get("name") == template_name for t in self.profile_generator.generated_profile_data.get("templates", [])) or any(
            t.get("name") == template_name for t in self.state.staged_templates_with_image_data
        ):
            messagebox.showerror("Name Conflict", f"A template named '{template_name}' already exists in this draft. Please choose a unique name.", parent=self.controller)
            return

        logger.info(f"DefineLogicView: Initiating template capture from region '{self.state.current_step_region_name}' for template '{template_name}'")

        self.controller.attributes("-alpha", 0.5)  # Temporarily dim wizard window
        sub_selector = SubImageSelectorWindow(
            master=self.controller, image_to_select_from_pil=self.state.current_step_region_image_pil_for_display, title=f"Select Area for Template '{template_name}'"
        )
        self.controller.wait_window(sub_selector)
        self.controller.attributes("-alpha", 1.0)  # Restore wizard window alpha

        selected_template_coords_xywh = sub_selector.get_selected_coords()
        if selected_template_coords_xywh:
            x_rel, y_rel, w_rel, h_rel = selected_template_coords_xywh
            if self.state.current_step_region_image_np is not None and w_rel > 0 and h_rel > 0:
                template_image_np_bgr = self.state.current_step_region_image_np[y_rel : y_rel + h_rel, x_rel : x_rel + w_rel]

                # Generate a unique filename for the template
                sane_filename_base_for_file = "".join(c if c.isalnum() else "_" for c in template_name).lower()
                template_filename_base = f"{sane_filename_base_for_file}.png"

                existing_filenames_in_draft = [tpl.get("filename") for tpl in self.profile_generator.generated_profile_data.get("templates", [])] + [
                    tpl.get("filename") for tpl in self.state.staged_templates_with_image_data
                ]

                final_template_filename = template_filename_base
                fn_count = 1
                while final_template_filename in existing_filenames_in_draft:
                    final_template_filename = f"{sane_filename_base_for_file}_{fn_count}.png"
                    fn_count += 1

                template_metadata = {
                    "name": template_name,
                    "filename": final_template_filename,
                    "comment": f"Template for '{element_desc_for_template}' in region '{self.state.current_step_region_name}'. User captured.",
                    "_image_data_np_for_save": template_image_np_bgr,  # Staged for later saving
                }

                self.state.staged_templates_with_image_data.append(template_metadata)  # Stage in WizardState
                logger.info(f"DefineLogicView: Template '{template_name}' (filename: {final_template_filename}) metadata and image data staged for profile.")

                # Update UI to reflect template capture in suggested condition/action
                cond_type_var = self.ui_step_logic_optionmenu_vars.get("step_cond_type_var")
                if cond_type_var:
                    cond_type_var.set("template_match_found")
                    self._on_wizard_logic_type_change("condition", "template_match_found")
                self.after(50, lambda: self._attempt_set_template_name_in_ui(template_name))

                act_type_var = self.ui_step_logic_optionmenu_vars.get("step_act_type_var")
                if act_type_var:
                    act_type_var.set("click")
                    self._on_wizard_logic_type_change("action", "click")
                self.after(100, lambda: self._set_click_action_params_for_template(template_name))

                messagebox.showinfo("Template Staged", f"Template '{template_name}' (filename '{final_template_filename}') captured.\nIt will be saved with the profile.", parent=self.controller)
            else:
                messagebox.showerror("Template Capture Error", "Could not capture a valid template image from the selection. Selected area might be invalid.", parent=self.controller)
        else:
            logger.info("DefineLogicView: Template capture from sub-image selector cancelled by user.")

        self.on_state_change()  # Notify controller of state change
