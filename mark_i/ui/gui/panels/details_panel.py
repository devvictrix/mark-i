import logging
import tkinter as tk
from tkinter import messagebox
import os
import copy
from typing import Optional, Dict, Any, List, Union, Callable

import customtkinter as ctk
from PIL import Image, UnidentifiedImageError, ImageFont

from mark_i.ui.gui.gui_config import (
    UI_PARAM_CONFIG,
    OPTIONS_CONST_MAP,
    MAX_PREVIEW_WIDTH,
    MAX_PREVIEW_HEIGHT,
    ACTION_TYPES,
)
from mark_i.ui.gui.gui_utils import validate_and_get_widget_value, Tooltip
from mark_i.ui.gui.panels.condition_editor_component import ConditionEditorComponent

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.panels.details_panel")


class DetailsPanel(ctk.CTkScrollableFrame):
    def __init__(self, master: Any, parent_app: Any, **kwargs):
        super().__init__(master, label_text="Selected Item Details", **kwargs)
        self.parent_app = parent_app
        self.controller = parent_app.controller

        self.detail_widgets: Dict[str, Union[ctk.CTkEntry, ctk.CTkOptionMenu, ctk.CTkCheckBox, ctk.CTkTextbox]] = {}
        self.detail_optionmenu_vars: Dict[str, Union[tk.StringVar, tk.BooleanVar]] = {}

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)
        self.content_frame.grid_columnconfigure(1, weight=1)

        self.label_placeholder = ctk.CTkLabel(
            self.content_frame,
            text="Select an item from the lists (Regions, Templates, Rules)\n to see or edit its details here.",
            wraplength=380,
            justify="center",
            font=ctk.CTkFont(size=14),
        )
        self.label_placeholder.pack(padx=20, pady=30, anchor="center", expand=True)

        self.template_preview_image_label: Optional[ctk.CTkLabel] = None
        self.action_params_frame: Optional[ctk.CTkFrame] = None
        self.condition_editor_component_instance: Optional[ConditionEditorComponent] = None
        logger.debug("DetailsPanel initialized.")

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.detail_widgets.clear()
        self.detail_optionmenu_vars.clear()
        self.template_preview_image_label = None
        self.action_params_frame = None
        if self.condition_editor_component_instance:
            self.condition_editor_component_instance.destroy()
            self.condition_editor_component_instance = None
        logger.debug("DetailsPanel content cleared.")

    def update_display(self, item_data: Optional[Dict[str, Any]], item_type: str):
        self.clear_content()
        if item_data is None or item_type == "none":
            self.label_placeholder = ctk.CTkLabel(self.content_frame, text="Select an item from the lists to see or edit its details.", wraplength=380, justify="center", font=ctk.CTkFont(size=14))
            self.label_placeholder.pack(padx=20, pady=30, anchor="center", expand=True)
            return
        logger.info(f"DetailsPanel: Updating display for item_type '{item_type}', name: '{item_data.get('name', 'N/A')}'")
        self.content_frame.grid_columnconfigure(1, weight=1)
        if item_type == "region":
            self._display_region_details(item_data)
        elif item_type == "template":
            self._display_template_details(item_data)
        elif item_type == "rule":
            self._display_rule_details(item_data)
        else:
            ctk.CTkLabel(self.content_frame, text=f"Cannot display details for unknown item type: '{item_type}'.", wraplength=380).pack(padx=10, pady=20, anchor="center", expand=True)

    def _display_region_details(self, region_data: Dict[str, Any]):
        logger.debug(f"Displaying region details for: {region_data.get('name', 'Unnamed Region')}")
        self.content_frame.grid_columnconfigure(1, weight=1)
        row_idx = 0
        ctk.CTkLabel(self.content_frame, text="Name:").grid(row=row_idx, column=0, padx=(10, 5), pady=5, sticky="w")
        name_e = ctk.CTkEntry(self.content_frame, placeholder_text="Unique region name")
        name_e.insert(0, str(region_data.get("name", "")))
        name_e.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        name_e.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))
        self.detail_widgets["name"] = name_e
        row_idx += 1
        coords_map = {"x": 0, "y": 0, "width": 100, "height": 100}
        for key, def_val in coords_map.items():
            ctk.CTkLabel(self.content_frame, text=f"{key.capitalize()}:").grid(row=row_idx, column=0, padx=(10, 5), pady=5, sticky="w")
            entry_c = ctk.CTkEntry(self.content_frame, placeholder_text=f"Enter {key}")
            entry_c.insert(0, str(region_data.get(key, def_val)))
            entry_c.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
            entry_c.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))
            self.detail_widgets[key] = entry_c
            row_idx += 1
        ctk.CTkLabel(self.content_frame, text="Comment:").grid(row=row_idx, column=0, padx=(10, 5), pady=5, sticky="nw")
        comment_tb = ctk.CTkTextbox(self.content_frame, height=60, wrap="word")
        comment_tb.insert("0.0", str(region_data.get("comment", "")))
        comment_tb.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        comment_tb.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))
        self.detail_widgets["comment"] = comment_tb
        row_idx += 1
        btn_fr = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_fr.grid(row=row_idx, column=0, columnspan=2, pady=(15, 10), padx=10, sticky="ew")
        btn_fr.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(btn_fr, text="Apply Region Changes", command=self.parent_app._apply_region_changes).grid(row=0, column=0, padx=(0, 5), sticky="e")
        ctk.CTkButton(btn_fr, text="Edit Coords (Selector)", command=self.parent_app._edit_region_coordinates_with_selector).grid(row=0, column=1, padx=(5, 0), sticky="w")

    def _display_template_details(self, template_data: Dict[str, Any]):
        logger.debug(f"Displaying template details for: {template_data.get('name', 'Unnamed Template')}")
        self.content_frame.grid_columnconfigure(1, weight=1)
        row_idx = 0
        ctk.CTkLabel(self.content_frame, text="Name:").grid(row=row_idx, column=0, padx=(10, 5), pady=5, sticky="w")
        name_e = ctk.CTkEntry(self.content_frame, placeholder_text="Unique template name")
        name_e.insert(0, str(template_data.get("name", "")))
        name_e.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        name_e.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))
        self.detail_widgets["template_name"] = name_e
        row_idx += 1
        ctk.CTkLabel(self.content_frame, text="Filename:").grid(row=row_idx, column=0, padx=(10, 5), pady=5, sticky="w")
        ctk.CTkLabel(self.content_frame, text=str(template_data.get("filename", "N/A")), anchor="w").grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1
        ctk.CTkLabel(self.content_frame, text="Comment:").grid(row=row_idx, column=0, padx=(10, 5), pady=5, sticky="nw")
        comment_tb = ctk.CTkTextbox(self.content_frame, height=60, wrap="word")
        comment_tb.insert("0.0", str(template_data.get("comment", "")))
        comment_tb.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        comment_tb.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))
        self.detail_widgets["comment"] = comment_tb
        row_idx += 1
        ctk.CTkLabel(self.content_frame, text="Preview:").grid(row=row_idx, column=0, padx=(10, 5), pady=5, sticky="nw")
        self.template_preview_image_label = ctk.CTkLabel(self.content_frame, text="Loading preview...", width=MAX_PREVIEW_WIDTH, height=MAX_PREVIEW_HEIGHT, anchor="w")
        self.template_preview_image_label.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")
        row_idx += 1
        self._update_template_preview_image(template_data.get("filename"))
        ctk.CTkButton(self.content_frame, text="Apply Template Changes", command=self.parent_app._apply_template_changes).grid(row=row_idx, column=0, columnspan=2, pady=(15, 10), padx=10)

    def _update_template_preview_image(self, filename: Optional[str]):
        if not self.template_preview_image_label:
            return
        if not filename or not self.controller.current_profile_path:
            self.template_preview_image_label.configure(image=None, text="No preview.")
            return
        template_path = self.controller.config_manager.get_template_image_path(filename)
        if template_path and os.path.exists(template_path):
            try:
                img = Image.open(template_path)
                img_copy = img.copy()
                img_copy.thumbnail((MAX_PREVIEW_WIDTH, MAX_PREVIEW_HEIGHT), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(img_copy.width, img_copy.height))
                self.template_preview_image_label.configure(image=ctk_img, text="")
            except UnidentifiedImageError:
                self.template_preview_image_label.configure(image=None, text=f"Error: Not an image\n{filename}")
            except Exception as e:
                self.template_preview_image_label.configure(image=None, text=f"Error loading preview:\n{filename}")
                logger.error(f"Err preview '{template_path}': {e}", exc_info=True)
        else:
            self.template_preview_image_label.configure(image=None, text=f"File not found:\n{filename}")
            logger.warning(f"Tpl img not found: {template_path}")

    def _display_rule_details(self, rule_data: Dict[str, Any]):
        logger.debug(f"DP: Displaying rule details for: {rule_data.get('name', 'Unnamed Rule')}")
        self.controller.selected_sub_condition_index = None
        self.content_frame.grid_columnconfigure(1, weight=1)
        current_master_row = 0

        ctk.CTkLabel(self.content_frame, text="Rule Name:").grid(row=current_master_row, column=0, sticky="w", padx=(10, 5), pady=2)
        name_e = ctk.CTkEntry(self.content_frame, placeholder_text="Unique rule name")
        name_e.insert(0, rule_data.get("name", ""))
        name_e.grid(row=current_master_row, column=1, sticky="ew", padx=5, pady=2)
        name_e.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))
        self.detail_widgets["rule_name"] = name_e
        current_master_row += 1

        ctk.CTkLabel(self.content_frame, text="Default Region:").grid(row=current_master_row, column=0, sticky="w", padx=(10, 5), pady=2)
        regions = [""] + [r.get("name", "") for r in self.controller.profile_data.get("regions", []) if r.get("name")]
        var_region = ctk.StringVar(value=str(rule_data.get("region", "")))
        menu_region = ctk.CTkOptionMenu(self.content_frame, variable=var_region, values=regions, command=lambda c: self.controller.set_dirty_status(True))
        menu_region.grid(row=current_master_row, column=1, sticky="ew", padx=5, pady=2)
        self.detail_optionmenu_vars["rule_region_var"] = var_region
        self.detail_widgets["rule_region"] = menu_region
        current_master_row += 1

        ctk.CTkLabel(self.content_frame, text="Comment (Rule):").grid(row=current_master_row, column=0, padx=(10, 5), pady=5, sticky="nw")
        rule_comment_tb = ctk.CTkTextbox(self.content_frame, height=40, wrap="word")
        rule_comment_tb.insert("0.0", str(rule_data.get("comment", "")))
        rule_comment_tb.grid(row=current_master_row, column=1, padx=5, pady=5, sticky="ew")
        rule_comment_tb.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))
        self.detail_widgets["rule_comment"] = rule_comment_tb
        current_master_row += 1

        cond_data_for_editor = copy.deepcopy(rule_data.get("condition", {"type": "always_true"}))
        self.condition_editor_component_instance = ConditionEditorComponent(
            master=self.content_frame, parent_panel=self, parent_app=self.parent_app, rule_name_for_context=rule_data.get("name", "UnnamedRule")
        )
        self.condition_editor_component_instance.grid(row=current_master_row, column=0, columnspan=2, sticky="new", pady=(10, 5), padx=0)
        current_master_row += 1
        self.condition_editor_component_instance.update_ui_with_condition_data(cond_data_for_editor)

        act_data = copy.deepcopy(rule_data.get("action", {"type": "log_message"}))
        act_outer_fr = ctk.CTkFrame(self.content_frame)
        act_outer_fr.grid(row=current_master_row, column=0, columnspan=2, sticky="new", pady=(10, 5), padx=5)
        act_outer_fr.grid_columnconfigure(0, weight=1)
        current_master_row += 1
        ctk.CTkLabel(act_outer_fr, text="ACTION TO PERFORM", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=0, pady=(0, 5))
        self.action_params_frame = ctk.CTkFrame(act_outer_fr, fg_color="transparent")
        self.action_params_frame.pack(fill="x", expand=True, padx=0, pady=(0, 5))
        self.action_params_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.action_params_frame, text="Action Type:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        init_act_type = str(act_data.get("type", "log_message"))
        var_act_type = ctk.StringVar(value=init_act_type)
        menu_act_type = ctk.CTkOptionMenu(self.action_params_frame, variable=var_act_type, values=ACTION_TYPES, command=lambda choice: self.parent_app._on_rule_part_type_change("action", choice))
        menu_act_type.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.detail_optionmenu_vars["action_type_var"] = var_act_type
        self.detail_widgets["action_type"] = menu_act_type
        self._render_dynamic_parameters("actions", init_act_type, act_data, self.action_params_frame, start_row=1, widget_prefix="act_")

        ctk.CTkButton(self.content_frame, text="Apply All Rule Changes", command=self.parent_app._apply_rule_changes, height=35, font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=current_master_row, column=0, columnspan=2, pady=(20, 10), padx=10, sticky="ew"
        )

    def _cec_render_sub_condition_params_editor(self, sub_cond_data: Dict[str, Any], index: int):
        if not self.condition_editor_component_instance or not self.condition_editor_component_instance.sub_condition_params_editor_frame:
            logger.error("DP: CEC or its sub_condition_params_editor_frame is None. Cannot render editor.")
            return
        target_editor_frame = self.condition_editor_component_instance.sub_condition_params_editor_frame
        for w in target_editor_frame.winfo_children():
            w.destroy()
        target_editor_frame.grid_columnconfigure(1, weight=1)
        current_type = str(sub_cond_data.get("type", "always_true"))
        ctk.CTkLabel(target_editor_frame, text=f"Editing Sub-Condition #{index+1} / Type:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(0, 5), pady=(5, 2), sticky="w")
        type_var = ctk.StringVar(value=current_type)
        type_menu = ctk.CTkOptionMenu(target_editor_frame, variable=type_var, values=CONDITION_TYPES, command=lambda choice: self.parent_app._on_rule_part_type_change("condition", choice))
        type_menu.grid(row=0, column=1, padx=5, pady=(5, 2), sticky="ew")
        self.detail_optionmenu_vars["subcond_condition_type_var"] = type_var
        self.detail_widgets["subcond_condition_type"] = type_menu
        self._render_dynamic_parameters("conditions", current_type, sub_cond_data, target_editor_frame, 1, "subcond_")
        logger.debug(f"DP: Rendered params for sub-condition #{index+1} (type: {current_type}) into CEC frame.")

    def _cec_convert_condition_structure(self):
        self.parent_app._convert_condition_structure()

    def _cec_add_sub_condition(self):
        self.parent_app._add_sub_condition_to_rule()

    def _cec_remove_selected_sub_condition(self):
        self.parent_app._remove_selected_sub_condition()

    def _cec_on_condition_type_change(self, part_key: str, new_type: str):
        self.parent_app._on_rule_part_type_change(part_key, new_type)

    def _create_param_label(self, parent: ctk.CTkFrame, text: str, row: int) -> ctk.CTkLabel:
        label = ctk.CTkLabel(parent, text=text)
        label.grid(row=row, column=0, padx=(0, 5), pady=2, sticky="nw" if "textbox" in text.lower() else "w")
        return label

    def _create_param_entry(self, parent: ctk.CTkFrame, p_def: Dict, value: Any, row: int) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(parent, placeholder_text=str(p_def.get("placeholder", "")))
        display_value = ", ".join(map(str, value)) if p_def["type"] == "list_str_csv" and isinstance(value, list) else str(value)
        entry.insert(0, display_value)
        entry.bind("<KeyRelease>", lambda e, dp=self: dp.controller.set_dirty_status(True))
        entry.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        return entry

    def _create_param_textbox(self, parent: ctk.CTkFrame, p_def: Dict, value: Any, row: int) -> ctk.CTkTextbox:
        textbox = ctk.CTkTextbox(parent, height=p_def.get("height", 60), wrap="word")
        textbox.insert("0.0", str(value))
        textbox.bind("<FocusOut>", lambda e, dp=self: dp.controller.set_dirty_status(True))
        textbox.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        return textbox

    def _create_param_optionmenu(
        self, parent: ctk.CTkFrame, p_def: Dict, value: Any, row: int, widget_full_key: str, current_pass_controlling_widgets: Dict, current_pass_param_widgets_and_defs: List
    ) -> ctk.CTkOptionMenu:
        options_list = []
        src_key = p_def.get("options_source") if p_def["widget"] == "optionmenu_dynamic" else p_def.get("options_const_key")
        if p_def["widget"] == "optionmenu_dynamic" and src_key == "regions":
            options_list = [""] + [r.get("name", "") for r in self.controller.profile_data.get("regions", []) if r.get("name")]
        elif p_def["widget"] == "optionmenu_dynamic" and src_key == "templates":
            options_list = [""] + [t.get("name", "") for t in self.controller.profile_data.get("templates", []) if t.get("name")]
        elif p_def["widget"] == "optionmenu_static" and src_key:
            options_list = OPTIONS_CONST_MAP.get(src_key, [])
        if not options_list:
            options_list = [str(p_def.get("default", ""))] if str(p_def.get("default", "")) else [""]
        str_current_val = str(value)
        final_current_val = (
            str_current_val if str_current_val in options_list else (str(p_def.get("default", "")) if str(p_def.get("default", "")) in options_list else (options_list[0] if options_list else ""))
        )
        tk_var = ctk.StringVar(value=final_current_val)
        option_menu = ctk.CTkOptionMenu(
            parent,
            variable=tk_var,
            values=options_list,
            command=lambda choice, p=p_def, cpw=current_pass_controlling_widgets, cppwd=current_pass_param_widgets_and_defs, wp=widget_full_key.split("_")[
                0
            ] + "_": self._update_conditional_visibility_dp(p, choice, cpw, cppwd, wp),
        )
        option_menu.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        self.detail_optionmenu_vars[f"{widget_full_key}_var"] = tk_var
        if any(opd.get("condition_show", {}).get("field") == p_def["id"] for opd in UI_PARAM_CONFIG.get(p_def["_param_group_key"], {}).get(p_def["_item_subtype"], []) if opd.get("condition_show")):
            self.detail_widgets[widget_full_key] = option_menu
        return option_menu

    def _create_param_checkbox(
        self, parent: ctk.CTkFrame, p_def: Dict, value: Any, row: int, widget_full_key: str, current_pass_controlling_widgets: Dict, current_pass_param_widgets_and_defs: List
    ) -> ctk.CTkCheckBox:
        tk_bool_var = tk.BooleanVar(value=bool(value))
        checkbox = ctk.CTkCheckBox(
            parent,
            text="",
            variable=tk_bool_var,
            command=lambda p=p_def, v=tk_bool_var, cpw=current_pass_controlling_widgets, cppwd=current_pass_param_widgets_and_defs, wp=widget_full_key.split("_")[
                0
            ] + "_": self._update_conditional_visibility_dp(p, v.get(), cpw, cppwd, wp),
        )
        checkbox.grid(row=row, column=1, padx=5, pady=2, sticky="ew")
        self.detail_optionmenu_vars[f"{widget_full_key}_var"] = tk_bool_var
        if any(opd.get("condition_show", {}).get("field") == p_def["id"] for opd in UI_PARAM_CONFIG.get(p_def["_param_group_key"], {}).get(p_def["_item_subtype"], []) if opd.get("condition_show")):
            self.detail_widgets[widget_full_key] = checkbox
        return checkbox

    def _render_dynamic_parameters(self, param_group_key: str, item_subtype: str, data_source: Dict[str, Any], parent_frame: ctk.CTkFrame, start_row: int, widget_prefix: str):
        current_pass_param_widgets_and_defs: List[Dict[str, Any]] = []
        current_pass_controlling_widgets: Dict[str, Union[ctk.CTkOptionMenu, ctk.CTkCheckBox]] = {}
        current_group = None

        for child_widget in list(parent_frame.winfo_children()):
            grid_info = child_widget.grid_info()
            if grid_info and grid_info.get("row", -1) >= start_row:
                widget_key_to_pop = next((wk for wk, w_instance in self.detail_widgets.items() if w_instance == child_widget and wk.startswith(widget_prefix)), None)
                if widget_key_to_pop:
                    self.detail_widgets.pop(widget_key_to_pop, None)
                    self.detail_optionmenu_vars.pop(f"{widget_key_to_pop}_var", None)
                child_widget.destroy()

        param_defs_for_subtype = UI_PARAM_CONFIG.get(param_group_key, {}).get(item_subtype, [])
        current_r = start_row
        if not param_defs_for_subtype and item_subtype not in ["always_true"]:
            ctk.CTkLabel(parent_frame, text=f"No parameters defined for '{item_subtype}'.", text_color="gray").grid(row=current_r, column=0, columnspan=2, pady=5)
            return

        for p_def_orig in param_defs_for_subtype:
            p_def = copy.deepcopy(p_def_orig)
            p_def["_param_group_key"] = param_group_key
            p_def["_item_subtype"] = item_subtype

            p_group = p_def.get("group")
            if p_group and p_group != current_group:
                ctk.CTkLabel(parent_frame, text=p_group.upper(), font=ctk.CTkFont(size=11, weight="bold", slant="italic")).grid(row=current_r, column=0, columnspan=2, sticky="w", pady=(8, 2))
                current_r += 1
                current_group = p_group

            p_id, lbl_txt, w_type, def_val, tooltip_text = p_def["id"], p_def["label"], p_def["widget"], p_def.get("default", ""), p_def.get("tooltip")
            current_value_for_param = data_source.get(p_id, def_val)
            widget_full_key = f"{widget_prefix}{p_id}"

            label_widget = self._create_param_label(parent_frame, lbl_txt, current_r)
            created_widget_instance: Optional[Union[ctk.CTkEntry, ctk.CTkTextbox, ctk.CTkOptionMenu, ctk.CTkCheckBox]] = None

            if w_type == "entry":
                created_widget_instance = self._create_param_entry(parent_frame, p_def, current_value_for_param, current_r)
            elif w_type == "textbox":
                created_widget_instance = self._create_param_textbox(parent_frame, p_def, current_value_for_param, current_r)
            elif w_type.startswith("optionmenu"):
                created_widget_instance = self._create_param_optionmenu(
                    parent_frame, p_def, current_value_for_param, current_r, widget_full_key, current_pass_controlling_widgets, current_pass_param_widgets_and_defs
                )
            elif w_type == "checkbox":
                created_widget_instance = self._create_param_checkbox(
                    parent_frame, p_def, current_value_for_param, current_r, widget_full_key, current_pass_controlling_widgets, current_pass_param_widgets_and_defs
                )

            if created_widget_instance:
                self.detail_widgets[widget_full_key] = created_widget_instance
                current_pass_param_widgets_and_defs.append({"widget": created_widget_instance, "label_widget": label_widget, "param_def": p_def})
                if tooltip_text:
                    Tooltip(label_widget, tooltip_text)
                    Tooltip(created_widget_instance, tooltip_text)
                current_r += 1
            else:
                label_widget.destroy()

        self._apply_all_conditional_visibility_dp(current_pass_param_widgets_and_defs, current_pass_controlling_widgets, widget_prefix)

    def _update_conditional_visibility_dp(self, changed_param_def_controller, new_value_of_controller, controlling_widgets_map, param_widgets_list, widget_prefix):
        self.controller.set_dirty_status(True)
        self._apply_all_conditional_visibility_dp(param_widgets_list, controlling_widgets_map, widget_prefix)

    def _apply_all_conditional_visibility_dp(self, param_widgets_and_defs_list, controlling_widgets_map, current_widget_prefix):
        if not param_widgets_and_defs_list:
            return
        for item in param_widgets_and_defs_list:
            widget_instance, label_widget_instance, param_definition = item["widget"], item["label_widget"], item["param_def"]
            visibility_config = param_definition.get("condition_show")
            should_be_visible = True
            if visibility_config:
                controlling_field_id = visibility_config.get("field")
                expected_values = visibility_config.get("values", [])
                controller_widget = controlling_widgets_map.get(controlling_field_id)
                current_val = None
                if isinstance(controller_widget, ctk.CTkOptionMenu):
                    var = self.detail_optionmenu_vars.get(f"{current_widget_prefix}{controlling_field_id}_var")
                    current_val = var.get() if var and isinstance(var, tk.StringVar) else None
                elif isinstance(controller_widget, ctk.CTkCheckBox):
                    var = self.detail_optionmenu_vars.get(f"{current_widget_prefix}{controlling_field_id}_var")
                    current_val = var.get() if var and isinstance(var, tk.BooleanVar) else None
                    expected_values = [bool(v) for v in expected_values if isinstance(v, (str, int, bool))]
                if current_val is None or current_val not in expected_values:
                    should_be_visible = False

            if widget_instance and widget_instance.winfo_exists():
                is_mapped = widget_instance.winfo_ismapped()
                if should_be_visible and not is_mapped:
                    widget_instance.grid()
                    if label_widget_instance and label_widget_instance.winfo_exists() and not label_widget_instance.winfo_ismapped():
                        label_widget_instance.grid()
                elif not should_be_visible and is_mapped:
                    widget_instance.grid_remove()
                    if label_widget_instance and label_widget_instance.winfo_exists() and label_widget_instance.winfo_ismapped():
                        label_widget_instance.grid_remove()

    def _get_basic_rule_attributes_from_ui(self, final_rule_data: Dict[str, Any]) -> bool:
        all_valid = True
        val, ok = validate_and_get_widget_value(self.detail_widgets.get("rule_name"), None, "Rule Name", str, "", True)
        final_rule_data["name"] = val
        all_valid &= ok
        var = self.detail_optionmenu_vars.get("rule_region_var")
        final_rule_data["region"] = var.get() if var else ""
        val, ok = validate_and_get_widget_value(self.detail_widgets.get("rule_comment"), None, "Rule Comment", str, "", False, True)
        final_rule_data["comment"] = val
        all_valid &= ok
        return all_valid

    def _get_condition_block_from_ui(self, final_rule_data: Dict[str, Any]) -> bool:
        all_valid = True
        is_compound = "logical_operator_var" in self.detail_optionmenu_vars
        if is_compound:
            var = self.detail_optionmenu_vars.get("logical_operator_var")
            op = var.get() if var else "AND"
            sub_conds_ui = []
            rule_model = self.controller.profile_data["rules"][self.controller.selected_rule_index]
            sub_conds_model = rule_model.get("condition", {}).get("sub_conditions", [])
            for i, item_model in enumerate(sub_conds_model):
                if i == self.controller.selected_sub_condition_index:
                    var = self.detail_optionmenu_vars.get("subcond_condition_type_var")
                    sub_type = var.get() if var else "always_true"
                    sub_params = self._get_parameters_for_block_from_ui("conditions", sub_type, "subcond_")
                    if sub_params is None:
                        all_valid = False
                        break
                    sub_conds_ui.append(sub_params)
                else:
                    sub_conds_ui.append(copy.deepcopy(item_model))
            if not all_valid:
                return False
            final_rule_data["condition"] = {"logical_operator": op, "sub_conditions": sub_conds_ui}
        else:
            var = self.detail_optionmenu_vars.get("condition_type_var")
            single_type = var.get() if var else "always_true"
            single_params = self._get_parameters_for_block_from_ui("conditions", single_type, "cond_")
            if single_params is None:
                all_valid = False
            else:
                final_rule_data["condition"] = single_params
        return all_valid

    def _get_action_block_from_ui(self, final_rule_data: Dict[str, Any]) -> bool:
        var = self.detail_optionmenu_vars.get("action_type_var")
        act_type = var.get() if var else "log_message"
        act_params = self._get_parameters_for_block_from_ui("actions", act_type, "act_")
        if act_params is None:
            return False
        final_rule_data["action"] = act_params
        return True

    def get_all_rule_data_from_ui(self) -> Optional[Dict[str, Any]]:
        if self.controller.selected_rule_index is None:
            return None
        if not (0 <= self.controller.selected_rule_index < len(self.controller.profile_data["rules"])):
            return None
        final_data = {"name": "", "region": "", "condition": {}, "action": {}, "comment": ""}
        if not self._get_basic_rule_attributes_from_ui(final_data):
            return None
        if not self._get_condition_block_from_ui(final_data):
            return None
        if not self._get_action_block_from_ui(final_data):
            return None
        return final_data

    def _get_parameters_for_block_from_ui(self, param_group_key: str, item_subtype: str, widget_prefix: str) -> Optional[Dict[str, Any]]:
        params: Dict[str, Any] = {"type": item_subtype}
        all_ok = True
        param_defs = UI_PARAM_CONFIG.get(param_group_key, {}).get(item_subtype, [])
        if not param_defs and item_subtype != "always_true":
            return params
        for p_def in param_defs:
            p_id, lbl, t_type, d_val, is_req = p_def["id"], p_def["label"].rstrip(":"), p_def["type"], p_def.get("default", ""), p_def.get("required", False)
            w_key = f"{widget_prefix}{p_id}"
            widget = self.detail_widgets.get(w_key)
            var = self.detail_optionmenu_vars.get(f"{w_key}_var")
            is_vis = widget.winfo_ismapped() if widget and widget.winfo_exists() else (var is not None)
            eff_req = is_req and is_vis
            if not is_vis and not eff_req:
                continue
            if widget is None and not isinstance(var, tk.BooleanVar):
                if eff_req:
                    logger.error(f"Widget for required param '{lbl}' not found.")
                    all_ok = False
                params[p_id] = d_val
                continue
            val_args = {"required": eff_req, "allow_empty_string": p_def.get("allow_empty_string", t_type == str), "min_val": p_def.get("min_val"), "max_val": p_def.get("max_val")}
            val, valid = validate_and_get_widget_value(widget, var, lbl, t_type, d_val, **val_args)
            if not valid:
                all_ok = False
                val = d_val
            if t_type == "list_str_csv":
                params[p_id] = [s.strip() for s in val.split(",")] if isinstance(val, str) and val.strip() else ([] if not d_val or not isinstance(d_val, list) else d_val)
            else:
                params[p_id] = val
            if p_id == "template_name" and param_group_key == "conditions":
                s_name = val
                params["template_filename"] = ""
                if s_name:
                    found = next((t for t in self.controller.profile_data.get("templates", []) if t.get("name") == s_name), None)
                    if found and found.get("filename"):
                        params["template_filename"] = found["filename"]
                    elif eff_req:
                        messagebox.showerror("Error", f"Filename for template '{s_name}' not found.")
                        all_ok = False
                elif eff_req:
                    messagebox.showerror("Error", f"'{lbl}' is required.")
                    all_ok = False
                if "template_name" in params:
                    del params["template_name"]
        if item_subtype == "always_true" and param_group_key == "conditions":
            region_pdef = next((pd for pd in UI_PARAM_CONFIG.get("conditions", {}).get("always_true", []) if pd["id"] == "region"), None)
            if region_pdef:
                val, _ = validate_and_get_widget_value(
                    self.detail_widgets.get(f"{widget_prefix}region"), self.detail_optionmenu_vars.get(f"{widget_prefix}region_var"), "Region", str, "", required=False
                )
                if val:
                    params["region"] = val
        return params if all_ok else None
