import logging
import tkinter as tk
from tkinter import messagebox
import os
import copy
from typing import Optional, Dict, Any, List, Callable

import customtkinter as ctk

from mark_i.ui.gui.app_controller import AppController
from mark_i.ui.gui.panels.details_panel import DetailsPanel
from mark_i.ui.gui.gui_utils import validate_and_get_widget_value, create_clickable_list_item
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.main_app_window")


class MainAppWindow(ctk.CTk):
    """
    The main application window (the View) for the Mark-I GUI Profile Editor.
    This class is responsible for creating and laying out all UI widgets.
    It delegates all logic and event handling to its AppController instance.
    """

    def __init__(self, initial_profile_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Initializing MainAppWindow (View)...")
        self.title("Mark-I Profile Editor")
        self.geometry("1350x800")
        self.minsize(1000, 700)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # The controller holds all state and logic
        self.controller = AppController(self)

        # --- UI Widget Attributes ---
        self.details_panel_instance: Optional[DetailsPanel] = None
        self.entry_profile_desc: Optional[ctk.CTkEntry] = None
        self.entry_monitor_interval: Optional[ctk.CTkEntry] = None
        self.entry_dominant_k: Optional[ctk.CTkEntry] = None
        self.entry_tesseract_cmd: Optional[ctk.CTkEntry] = None
        self.entry_tesseract_config: Optional[ctk.CTkEntry] = None
        self.entry_gemini_default_model: Optional[ctk.CTkEntry] = None
        self.label_gemini_api_key_status: Optional[ctk.CTkLabel] = None
        self.label_current_profile_path: Optional[ctk.CTkLabel] = None
        self.regions_list_scroll_frame: Optional[ctk.CTkScrollableFrame] = None
        self.templates_list_scroll_frame: Optional[ctk.CTkScrollableFrame] = None
        self.rules_list_scroll_frame: Optional[ctk.CTkScrollableFrame] = None
        self.btn_remove_region: Optional[ctk.CTkButton] = None
        self.btn_remove_template: Optional[ctk.CTkButton] = None
        self.btn_remove_rule: Optional[ctk.CTkButton] = None
        self.btn_start_assistant: Optional[ctk.CTkButton] = None  # New
        self.label_assistant_status: Optional[ctk.CTkLabel] = None  # New

        # 1. Build the UI widgets
        self._setup_ui_layout_and_menu()

        # 2. Initialize the controller, which will load data and populate the UI
        self.controller.initialize_app(initial_profile_path)

        # 3. Set up protocol handlers
        self.protocol("WM_DELETE_WINDOW", self.controller.on_close_window)
        logger.info("MainAppWindow (View) initialization complete.")

    def _setup_ui_layout_and_menu(self):
        # Menu setup delegates commands to the controller
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Profile", command=self.controller.new_profile, accelerator="Ctrl+N")
        file_menu.add_command(label="New AI-Generated Profile...", command=self.controller.launch_ai_profile_creator_wizard, accelerator="Ctrl+G")
        file_menu.add_separator()
        file_menu.add_command(label="Open Profile...", command=self.controller.open_profile, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save Profile", command=self.controller.save_profile, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Profile As...", command=self.controller.save_profile_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.controller.on_close_window)

        self.bind_all("<Control-n>", self.controller.new_profile)
        self.bind_all("<Control-g>", self.controller.launch_ai_profile_creator_wizard)
        self.bind_all("<Control-o>", self.controller.open_profile)
        self.bind_all("<Control-s>", self.controller.save_profile)
        self.bind_all("<Control-S>", self.controller.save_profile_as)

        # Main layout grid
        self.grid_columnconfigure(0, weight=1, minsize=330)
        self.grid_columnconfigure(1, weight=2, minsize=380)
        self.grid_columnconfigure(2, weight=3, minsize=420)
        self.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray20"))
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 1), pady=0)
        self._setup_left_panel_content()

        self.center_panel = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray85", "gray17"))
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=(1, 1), pady=0)
        self._setup_center_panel_content()

        self.details_panel_instance = DetailsPanel(self, parent_app=self, corner_radius=0)
        self.details_panel_instance.grid(row=0, column=2, sticky="nsew", padx=(1, 0), pady=0)

    def _setup_left_panel_content(self):
        self.left_panel.grid_rowconfigure(0, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        tab_view = ctk.CTkTabview(self.left_panel)
        tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        settings_tab = tab_view.add("Settings")
        regions_tab = tab_view.add("Regions")
        templates_tab = tab_view.add("Templates")

        # Populate Settings Tab
        settings_tab.grid_columnconfigure(0, weight=1)
        pif_frame = ctk.CTkFrame(settings_tab, fg_color="transparent")
        pif_frame.grid(row=0, column=0, sticky="new", padx=5, pady=5)
        pif_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(pif_frame, text="Profile Path:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        self.label_current_profile_path = ctk.CTkLabel(pif_frame, text="...", anchor="w", wraplength=300, font=ctk.CTkFont(size=11))
        self.label_current_profile_path.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(pif_frame, text="Description:").grid(row=2, column=0, padx=5, pady=(5, 2), sticky="w")
        self.entry_profile_desc = ctk.CTkEntry(pif_frame)
        self.entry_profile_desc.grid(row=2, column=1, padx=5, pady=(5, 2), sticky="ew")
        self.entry_profile_desc.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))

        ctk.CTkLabel(pif_frame, text="Monitor Interval (s):").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.entry_monitor_interval = ctk.CTkEntry(pif_frame)
        self.entry_monitor_interval.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        self.entry_monitor_interval.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))

        ctk.CTkLabel(pif_frame, text="Dominant Colors (K):").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.entry_dominant_k = ctk.CTkEntry(pif_frame)
        self.entry_dominant_k.grid(row=4, column=1, padx=5, pady=2, sticky="ew")
        self.entry_dominant_k.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))

        ctk.CTkLabel(pif_frame, text="Tesseract CMD Path (Optional):").grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.entry_tesseract_cmd = ctk.CTkEntry(pif_frame)
        self.entry_tesseract_cmd.grid(row=5, column=1, padx=5, pady=2, sticky="ew")
        self.entry_tesseract_cmd.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))

        ctk.CTkLabel(pif_frame, text="Tesseract Config Str (Optional):").grid(row=6, column=0, padx=5, pady=2, sticky="w")
        self.entry_tesseract_config = ctk.CTkEntry(pif_frame)
        self.entry_tesseract_config.grid(row=6, column=1, padx=5, pady=2, sticky="ew")
        self.entry_tesseract_config.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))

        ctk.CTkLabel(pif_frame, text="Gemini Default Model:").grid(row=7, column=0, padx=5, pady=2, sticky="w")
        self.entry_gemini_default_model = ctk.CTkEntry(pif_frame)
        self.entry_gemini_default_model.grid(row=7, column=1, padx=5, pady=2, sticky="ew")
        self.entry_gemini_default_model.bind("<KeyRelease>", lambda e: self.controller.set_dirty_status(True))

        ctk.CTkLabel(pif_frame, text="Gemini API Key Status:").grid(row=8, column=0, padx=5, pady=2, sticky="w")
        self.label_gemini_api_key_status = ctk.CTkLabel(pif_frame, text="Checking...", anchor="w")
        self.label_gemini_api_key_status.grid(row=8, column=1, padx=5, pady=2, sticky="ew")

        # Populate Regions Tab
        regions_tab.grid_columnconfigure(0, weight=1)
        regions_tab.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(regions_tab, text="Screen Regions", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=5, sticky="w", padx=5)
        self.regions_list_scroll_frame = ctk.CTkScrollableFrame(regions_tab, fg_color=("gray95", "gray22"))
        self.regions_list_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        region_buttons_frame = ctk.CTkFrame(regions_tab, fg_color="transparent")
        region_buttons_frame.grid(row=2, column=0, pady=5, sticky="ew", padx=5)
        ctk.CTkButton(region_buttons_frame, text="Add Region", width=100, command=self.controller.add_region).pack(side="left", padx=(0, 5))
        self.btn_remove_region = ctk.CTkButton(region_buttons_frame, text="Remove Selected", width=120, command=self.controller.remove_selected_region, state="disabled")
        self.btn_remove_region.pack(side="left", padx=5)

        # Populate Templates Tab
        templates_tab.grid_columnconfigure(0, weight=1)
        templates_tab.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(templates_tab, text="Image Templates", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=5, sticky="w", padx=5)
        self.templates_list_scroll_frame = ctk.CTkScrollableFrame(templates_tab, fg_color=("gray95", "gray22"))
        self.templates_list_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        template_buttons_frame = ctk.CTkFrame(templates_tab, fg_color="transparent")
        template_buttons_frame.grid(row=2, column=0, pady=5, sticky="ew", padx=5)
        ctk.CTkButton(template_buttons_frame, text="Add Template", width=100, command=self.controller.add_template).pack(side="left", padx=(0, 5))
        self.btn_remove_template = ctk.CTkButton(template_buttons_frame, text="Remove Selected", width=120, command=self.controller.remove_selected_template, state="disabled")
        self.btn_remove_template.pack(side="left", padx=5)

        # --- NEW: Autonomous Assistant Control Frame ---
        assistant_frame = ctk.CTkFrame(self.left_panel, border_width=1)
        assistant_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        assistant_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(assistant_frame, text="Autonomous Assistant (v6)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 2), sticky="w")

        self.btn_start_assistant = ctk.CTkButton(assistant_frame, text="Start Assistant", command=self.controller.toggle_autonomy_engine)
        self.btn_start_assistant.grid(row=1, column=0, padx=10, pady=(5, 10))

        self.label_assistant_status = ctk.CTkLabel(assistant_frame, text="Status: Inactive", anchor="w")
        self.label_assistant_status.grid(row=1, column=1, padx=10, pady=(5, 10), sticky="ew")

    def _setup_center_panel_content(self):
        self.center_panel.grid_columnconfigure(0, weight=1)
        self.center_panel.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self.center_panel, text="Automation Rules", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.rules_list_scroll_frame = ctk.CTkScrollableFrame(self.center_panel, fg_color=("gray95", "gray22"))
        self.rules_list_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))
        rule_buttons_frame = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        rule_buttons_frame.grid(row=2, column=0, pady=(5, 10), padx=10, sticky="ew")
        ctk.CTkButton(rule_buttons_frame, text="Add New Rule", command=self.controller.add_new_rule).pack(side="left", padx=(0, 5))
        self.btn_remove_rule = ctk.CTkButton(rule_buttons_frame, text="Remove Selected Rule", command=self.controller.remove_selected_rule, state="disabled")
        self.btn_remove_rule.pack(side="left", padx=5)

    def update_window_title(self, new_title: str):
        self.title(new_title)

    def _populate_ui_from_profile_data(self):
        logger.debug("Populating UI from controller's profile_data...")
        if not all([self.label_current_profile_path, self.regions_list_scroll_frame, self.templates_list_scroll_frame, self.rules_list_scroll_frame]):
            logger.error("Core UI elements not initialized. Cannot populate UI.")
            return

        self._populate_profile_path_and_title()
        self._populate_general_settings_fields()
        self.controller.clear_selection_states_and_details_panel()
        self._populate_all_list_frames()
        logger.debug("UI population from profile_data complete.")

    def _populate_profile_path_and_title(self):
        if self.label_current_profile_path:
            path_text = self.controller.current_profile_path or "New Profile (unsaved)"
            self.label_current_profile_path.configure(text=f"Path: {path_text}")
        self.controller.update_window_title()

    def _populate_general_settings_fields(self):
        if not self.entry_profile_desc:
            return

        self.entry_profile_desc.delete(0, tk.END)
        self.entry_profile_desc.insert(0, self.controller.profile_data.get("profile_description", ""))

        settings = self.controller.profile_data.get("settings", {})
        self.entry_monitor_interval.delete(0, tk.END)
        self.entry_monitor_interval.insert(0, str(settings.get("monitoring_interval_seconds", 1.0)))
        self.entry_dominant_k.delete(0, tk.END)
        self.entry_dominant_k.insert(0, str(settings.get("analysis_dominant_colors_k", 3)))
        self.entry_tesseract_cmd.delete(0, tk.END)
        self.entry_tesseract_cmd.insert(0, str(settings.get("tesseract_cmd_path", "") or ""))
        self.entry_tesseract_config.delete(0, tk.END)
        self.entry_tesseract_config.insert(0, str(settings.get("tesseract_config_custom", "")))
        self.entry_gemini_default_model.delete(0, tk.END)
        self.entry_gemini_default_model.insert(0, str(settings.get("gemini_default_model_name", "gemini-1.5-flash-latest")))
        self.label_gemini_api_key_status.configure(text=self.controller.check_gemini_api_key_status())

    def _populate_all_list_frames(self):
        if self.regions_list_scroll_frame:
            self._populate_specific_list_frame(
                "region", self.regions_list_scroll_frame, self.controller.profile_data.get("regions", []), lambda item, idx: item.get("name", f"R_{idx}"), self.btn_remove_region
            )
        if self.templates_list_scroll_frame:
            self._populate_specific_list_frame(
                "template",
                self.templates_list_scroll_frame,
                self.controller.profile_data.get("templates", []),
                lambda item, idx: f"{item.get('name','T_')}({item.get('filename','F_')})",
                self.btn_remove_template,
            )
        if self.rules_list_scroll_frame:
            self._populate_specific_list_frame(
                "rule", self.rules_list_scroll_frame, self.controller.profile_data.get("rules", []), lambda item, idx: item.get("name", f"Rule_{idx}"), self.btn_remove_rule
            )

    def _populate_specific_list_frame(self, list_key: str, frame: ctk.CTkScrollableFrame, items: List[Dict], display_cb: Callable, button: Optional[ctk.CTkButton]):
        for w in frame.winfo_children():
            w.destroy()
        setattr(self.controller, f"selected_{list_key}_item_widget", None)
        if button and hasattr(button, "configure"):
            button.configure(state="disabled")

        for i, item_data in enumerate(items):
            txt = display_cb(item_data, i)
            item_frame_ref = {}
            item_ui_frame = create_clickable_list_item(
                frame, txt, lambda e=None, lk=list_key, d=copy.deepcopy(item_data), idx=i, ifr=item_frame_ref: self.controller.on_item_selected(lk, d, idx, ifr.get("frame"))
            )
            item_frame_ref["frame"] = item_ui_frame

    def get_general_settings_from_ui(self) -> Optional[Dict[str, Any]]:
        if not self.entry_profile_desc:
            return None
        settings_data = {}
        all_valid = True

        desc, desc_ok = validate_and_get_widget_value(self.entry_profile_desc, None, "Profile Description", str, "", required=False, allow_empty_string=True)
        settings_data["description"] = desc
        all_valid &= desc_ok

        settings = {}
        val, ok = validate_and_get_widget_value(self.entry_monitor_interval, None, "Monitoring Interval", float, 1.0, required=True, min_val=0.01)
        settings["monitoring_interval_seconds"] = val
        all_valid &= ok

        val, ok = validate_and_get_widget_value(self.entry_dominant_k, None, "Dominant K", int, 3, required=True, min_val=1, max_val=20)
        settings["analysis_dominant_colors_k"] = val
        all_valid &= ok

        val, ok = validate_and_get_widget_value(self.entry_tesseract_cmd, None, "Tesseract CMD Path", str, "", required=False, allow_empty_string=True)
        settings["tesseract_cmd_path"] = val if val else None
        all_valid &= ok

        val, ok = validate_and_get_widget_value(self.entry_tesseract_config, None, "Tesseract Config Str", str, "", required=False, allow_empty_string=True)
        settings["tesseract_config_custom"] = val
        all_valid &= ok

        val, ok = validate_and_get_widget_value(self.entry_gemini_default_model, None, "Gemini Default Model", str, "gemini-1.5-flash-latest", required=False, allow_empty_string=True)
        settings["gemini_default_model_name"] = val if val else "gemini-1.5-flash-latest"
        all_valid &= ok

        settings_data["settings"] = settings
        return settings_data if all_valid else None

    def highlight_selected_list_item(self, list_name_key: str, new_selected_widget_frame: Optional[ctk.CTkFrame]):
        attr_widget_name = f"selected_{list_name_key}_item_widget"
        old_widget = getattr(self.controller, attr_widget_name, None)
        if old_widget and isinstance(old_widget, ctk.CTkFrame) and old_widget.winfo_exists():
            old_widget.configure(fg_color="transparent")

        if new_selected_widget_frame and new_selected_widget_frame.winfo_exists():
            try:
                hl_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
                hl_color = hl_color[0] if isinstance(hl_color, tuple) and ctk.get_appearance_mode().lower() == "light" else (hl_color[1] if isinstance(hl_color, tuple) else hl_color)
            except (KeyError, TypeError, AttributeError):
                hl_color = "#3a7ebf"
            new_selected_widget_frame.configure(fg_color=hl_color)
            setattr(self.controller, attr_widget_name, new_selected_widget_frame)
        else:
            setattr(self.controller, attr_widget_name, None)

    def update_autonomy_status_label(self, text: str):
        """Updates the status label of the Autonomous Assistant."""
        if self.label_assistant_status:
            self.label_assistant_status.configure(text=f"Status: {text}")
