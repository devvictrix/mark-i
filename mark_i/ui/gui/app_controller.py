import logging
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import copy
import shutil
import threading
from typing import Optional, Dict, Any, List, Callable

import customtkinter as ctk

from mark_i.core.config_manager import ConfigManager, TEMPLATES_SUBDIR_NAME
from mark_i.ui.gui.region_selector import RegionSelectorWindow
from mark_i.ui.gui.gui_config import DEFAULT_PROFILE_STRUCTURE
from mark_i.ui.gui.generation.profile_creation_wizard import ProfileCreationWizardWindow
from mark_i.ui.gui.autonomy_confirmation_dialog import AutonomyConfirmationDialog
from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.engines.capture_engine import CaptureEngine
from mark_i.generation.strategy_planner import StrategyPlanner
from mark_i.engines.gemini_decision_module import GeminiDecisionModule
from mark_i.engines.action_executor import ActionExecutor
from mark_i.autonomy.engine import AutonomyEngine
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.app_controller")


class AppController:
    """
    Controller for the MainAppWindow. Manages application state, logic,
    and interactions between the view (MainAppWindow) and backend models/services.
    """

    def __init__(self, view: ctk.CTk):
        self.view = view
        self.config_manager = ConfigManager(None, create_if_missing=True)

        # --- State ---
        self.current_profile_path: Optional[str] = None
        self.profile_data: Dict[str, Any] = copy.deepcopy(DEFAULT_PROFILE_STRUCTURE)
        self._is_dirty: bool = False
        self.selected_region_index: Optional[int] = None
        self.selected_template_index: Optional[int] = None
        self.selected_rule_index: Optional[int] = None
        self.selected_sub_condition_index: Optional[int] = None
        self.selected_region_item_widget: Optional[ctk.CTkFrame] = None
        self.selected_template_item_widget: Optional[ctk.CTkFrame] = None
        self.selected_rule_item_widget: Optional[ctk.CTkFrame] = None

        # --- Shared Engines (Single Source of Truth) ---
        self.capture_engine: Optional[CaptureEngine] = None
        self.gemini_analyzer_instance: Optional[GeminiAnalyzer] = None
        self.strategy_planner: Optional[StrategyPlanner] = None
        self.gemini_decision_module: Optional[GeminiDecisionModule] = None
        self.action_executor: Optional[ActionExecutor] = None
        self.autonomy_engine: Optional[AutonomyEngine] = None

        self._autonomy_confirmation_result: Optional[bool] = None
        self._autonomy_confirmation_event = threading.Event()

    def initialize_app(self, initial_profile_path: Optional[str]):
        """Initializes engines, loads profile, and populates the view."""
        self._initialize_engines()
        if initial_profile_path:
            self.load_profile_from_path(initial_profile_path)
        else:
            self.new_profile(prompt_save=False)

    def _initialize_engines(self):
        """Instantiates all shared engine components."""
        logger.info("AppController: Initializing shared engines...")
        self.capture_engine = CaptureEngine()
        self.action_executor = ActionExecutor(self.config_manager)  # ActionExecutor needs a CM, but it's for region context not profile data

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            default_model = self.profile_data.get("settings", {}).get("gemini_default_model_name", "gemini-1.5-flash-latest")
            self.gemini_analyzer_instance = GeminiAnalyzer(api_key=gemini_api_key, default_model_name=default_model)
            if self.gemini_analyzer_instance.client_initialized:
                self.strategy_planner = StrategyPlanner(self.gemini_analyzer_instance)
                self.gemini_decision_module = GeminiDecisionModule(self.gemini_analyzer_instance, self.action_executor, self.config_manager)
            else:
                logger.error("AppController: GeminiAnalyzer failed to initialize.")
        else:
            logger.warning("AppController: GEMINI_API_KEY not found. AI-dependent engines not initialized.")

        self.view._populate_general_settings_fields()

    def check_gemini_api_key_status(self) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_analyzer_instance and self.gemini_analyzer_instance.client_initialized:
            return "OK (Client Initialized)"
        elif api_key:
            return "Key Found but Client NOT Initialized (Check logs)"
        return "NOT FOUND in .env (AI features disabled)"

    def set_dirty_status(self, is_now_dirty: bool):
        if self._is_dirty == is_now_dirty:
            return
        self._is_dirty = is_now_dirty
        self.update_window_title()

    def update_window_title(self):
        title = "Mark-I Profile Editor"
        if self.current_profile_path:
            title += f" - {os.path.basename(self.current_profile_path)}"
        else:
            title += " - New Profile"
        if self._is_dirty:
            title += "*"
        self.view.update_window_title(title)

    def new_profile(self, event=None, prompt_save=True):
        if prompt_save and self._is_dirty and not self._prompt_save_if_dirty():
            return
        self.current_profile_path = None
        self.profile_data = copy.deepcopy(DEFAULT_PROFILE_STRUCTURE)
        self.config_manager = ConfigManager(None, create_if_missing=True)
        self.config_manager.update_profile_data(self.profile_data)
        self.view._populate_ui_from_profile_data()
        self.set_dirty_status(False)

    def launch_ai_profile_creator_wizard(self, event=None):
        if not self.gemini_analyzer_instance or not self.gemini_analyzer_instance.client_initialized:
            messagebox.showerror("Gemini Not Ready", "Gemini API client is not initialized.", parent=self.view)
            return
        if self._is_dirty and not self._prompt_save_if_dirty():
            return
        wizard = ProfileCreationWizardWindow(master=self.view, main_app_instance=self.view)
        self.view.wait_window(wizard)
        if hasattr(wizard, "newly_saved_profile_path") and wizard.newly_saved_profile_path:
            self.load_profile_from_path(wizard.newly_saved_profile_path)

    def open_profile(self, event=None):
        if self._is_dirty and not self._prompt_save_if_dirty():
            return
        filepath = filedialog.askopenfilename(title="Open Profile", defaultextension=".json", filetypes=[("JSON files", "*.json")], parent=self.view)
        if filepath:
            self.load_profile_from_path(filepath)

    def load_profile_from_path(self, filepath: str):
        try:
            self.config_manager = ConfigManager(filepath, create_if_missing=False)
            self.profile_data = self.config_manager.get_profile_data()
            self.current_profile_path = self.config_manager.get_profile_path()
            self.view._populate_ui_from_profile_data()
            self.set_dirty_status(False)
        except (FileNotFoundError, ValueError, IOError) as e:
            messagebox.showerror("Load Error", f"Could not load profile: {filepath}\nError: {e}", parent=self.view)
            self.new_profile(prompt_save=False)

    def save_profile(self, event=None) -> bool:
        if not self.current_profile_path:
            return self.save_profile_as()
        if not self._update_profile_data_from_ui():
            return False
        self.config_manager.update_profile_data(self.profile_data)
        try:
            if self.config_manager.save_current_profile():
                self.set_dirty_status(False)
                return True
            messagebox.showerror("Save Error", f"Could not save profile to {self.current_profile_path}.", parent=self.view)
            return False
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving profile: {e}", parent=self.view)
            return False

    def save_profile_as(self, event=None) -> bool:
        if not self._update_profile_data_from_ui():
            return False
        initial_fn = os.path.basename(self.current_profile_path) if self.current_profile_path else "new_profile.json"
        default_dir = self.config_manager.profiles_base_dir if self.config_manager else os.getcwd()
        filepath = filedialog.asksaveasfilename(
            title="Save Profile As", defaultextension=".json", initialdir=default_dir, filetypes=[("JSON files", "*.json")], initialfile=initial_fn, parent=self.view
        )
        if filepath:
            self.current_profile_path = filepath
            self.config_manager = ConfigManager(self.current_profile_path, create_if_missing=True)
            self.config_manager.update_profile_data(self.profile_data)
            return self.save_profile()
        return False

    def on_close_window(self, event=None):
        if self.autonomy_engine and self.autonomy_engine.is_running:
            self.autonomy_engine.stop()
        if self._prompt_save_if_dirty():
            self.view.destroy()

    def on_item_selected(self, list_name: str, item_data: Dict, item_index: int, item_widget_frame: Optional[ctk.CTkFrame]):
        if not item_widget_frame or not item_widget_frame.winfo_exists():
            return
        list_map = {
            "region": (self.view.btn_remove_region, "selected_region_index"),
            "template": (self.view.btn_remove_template, "selected_template_index"),
            "rule": (self.view.btn_remove_rule, "selected_rule_index"),
        }
        for ln, (btn, idx_attr) in list_map.items():
            if ln != list_name:
                self.view.highlight_selected_list_item(ln, None)
                setattr(self, idx_attr, None)
                if btn and hasattr(btn, "configure"):
                    btn.configure(state="disabled")
        if list_name != "rule" and self.selected_rule_index is not None:
            self.selected_sub_condition_index = None
            if self.view.details_panel_instance and self.view.details_panel_instance.condition_editor_component_instance:
                self.view.details_panel_instance.condition_editor_component_instance._highlight_cec_sub_condition_item(None)
        if list_name in list_map:
            setattr(self, list_map[list_name][1], item_index)
            self.view.highlight_selected_list_item(list_name, item_widget_frame)
            if list_map[list_name][0]:
                list_map[list_name][0].configure(state="normal")
        if self.view.details_panel_instance:
            self.view.details_panel_instance.update_display(copy.deepcopy(item_data), list_name)

    def _prompt_save_if_dirty(self) -> bool:
        if not self._is_dirty:
            return True
        response = messagebox.askyesnocancel("Unsaved Changes", "Save before proceeding?", parent=self.view)
        if response is True:
            return self.save_profile()
        return response is False

    def _update_profile_data_from_ui(self) -> bool:
        ui_settings = self.view.get_general_settings_from_ui()
        if ui_settings is None:
            return False
        self.profile_data["profile_description"] = ui_settings["description"]
        self.profile_data.setdefault("settings", {}).update(ui_settings["settings"])
        return True

    def clear_selection_states_and_details_panel(self):
        self.selected_region_index, self.selected_template_index, self.selected_rule_index, self.selected_sub_condition_index = None, None, None, None
        if self.view.details_panel_instance:
            self.view.details_panel_instance.update_display(None, "none")

    def add_region(self):
        if not self.current_profile_path:
            if not messagebox.askokcancel("Save Required", "Save profile before adding regions?", parent=self.view) or not self.save_profile_as():
                return
        if self._is_dirty and not self._prompt_save_if_dirty():
            return
        selector = RegionSelectorWindow(master=self.view, config_manager_context=self.config_manager, existing_region_data=None)
        self.view.wait_window(selector)
        if hasattr(selector, "changes_made") and selector.changes_made and selector.saved_region_info:
            new_region_data = selector.saved_region_info
            if any(r.get("name") == new_region_data["name"] for r in self.profile_data.get("regions", [])):
                messagebox.showerror("Name Conflict", f"Region name '{new_region_data['name']}' already exists.", parent=self.view)
                return
            self.profile_data.setdefault("regions", []).append(new_region_data)
            self.set_dirty_status(True)
            self.view._populate_all_list_frames()

    def remove_selected_region(self):
        self._remove_selected_item("region", "regions", "selected_region_index", self.view.btn_remove_region, lambda item, idx: item.get("name", f"R_{idx}"))

    def remove_selected_template(self):
        self._remove_selected_item("template", "templates", "selected_template_index", self.view.btn_remove_template, lambda item, idx: f"{item.get('name')}({item.get('filename')})")

    def remove_selected_rule(self):
        self._remove_selected_item("rule", "rules", "selected_rule_index", self.view.btn_remove_rule, lambda item, idx: item.get("name", f"Rule{idx}"))

    def _remove_selected_item(self, list_name: str, p_key: str, idx_attr: str, btn: Optional[ctk.CTkButton], display_cb: Callable):
        idx = getattr(self, idx_attr, None)
        if idx is None or p_key not in self.profile_data:
            return
        item_list = self.profile_data[p_key]
        if 0 <= idx < len(item_list):
            removed = item_list.pop(idx)
            list_frame = getattr(self.view, f"{list_name}s_list_scroll_frame")
            if list_frame:
                self.view._populate_specific_list_frame(list_name, list_frame, item_list, display_cb, btn)
            self.set_dirty_status(True)
            setattr(self, idx_attr, None)
            if btn:
                btn.configure(state="disabled")
            if self.view.details_panel_instance:
                self.view.details_panel_instance.update_display(None, "none")
            if list_name == "template" and self.current_profile_path and removed.get("filename"):
                try:
                    tpl_path = self.config_manager.get_template_image_path(removed["filename"])
                    if tpl_path and os.path.exists(tpl_path):
                        os.remove(tpl_path)
                except Exception as e:
                    messagebox.showwarning("File Deletion Error", f"Could not delete image '{removed['filename']}':\n{e}", parent=self.view)

    def add_template(self):
        if not self.current_profile_path:
            if not messagebox.askokcancel("Save Required", "Save profile before adding templates?", parent=self.view) or not self.save_profile_as():
                return
        if self._is_dirty and not self._prompt_save_if_dirty():
            return
        img_path = filedialog.askopenfilename(title="Select Template Image", filetypes=[("Images", "*.png *.jpg *.jpeg")], parent=self.view)
        if not img_path:
            return
        name_dialog = ctk.CTkInputDialog(text="Enter unique name for template:", title="Template Name")
        tpl_name = name_dialog.get_input()
        if not tpl_name or not tpl_name.strip():
            return
        tpl_name = tpl_name.strip()
        if any(t.get("name") == tpl_name for t in self.profile_data.get("templates", [])):
            messagebox.showerror("Name Error", f"Template name '{tpl_name}' already exists.", parent=self.view)
            return

        profile_dir = os.path.dirname(self.current_profile_path)
        templates_dir = os.path.join(profile_dir, TEMPLATES_SUBDIR_NAME)
        try:
            os.makedirs(templates_dir, exist_ok=True)
            _base, ext = os.path.splitext(os.path.basename(img_path))
            sane_fn = "".join(c if c.isalnum() else "_" for c in tpl_name).lower()
            target_fn = f"{sane_fn}{ext or '.png'}"
            target_path = os.path.join(templates_dir, target_fn)
            count = 1
            while os.path.exists(target_path):
                target_fn = f"{sane_fn}_{count}{ext or '.png'}"
                target_path = os.path.join(templates_dir, target_fn)
                count += 1
            shutil.copy2(img_path, target_path)
            self.profile_data.setdefault("templates", []).append({"name": tpl_name, "filename": target_fn, "comment": ""})
            self.view._populate_all_list_frames()
            self.set_dirty_status(True)
        except Exception as e:
            messagebox.showerror("Add Template Error", f"Could not add template '{tpl_name}':\n{e}", parent=self.view)

    def add_new_rule(self):
        name_dialog = ctk.CTkInputDialog(text="Enter unique name for new rule:", title="New Rule Name")
        rule_name = name_dialog.get_input()
        if not rule_name or not rule_name.strip():
            return
        rule_name = rule_name.strip()
        if any(r.get("name") == rule_name for r in self.profile_data.get("rules", [])):
            messagebox.showerror("Name Error", f"Rule name '{rule_name}' already exists.", parent=self.view)
            return
        self.profile_data.setdefault("rules", []).append(
            {"name": rule_name, "region": "", "condition": {"type": "always_true"}, "action": {"type": "log_message", "message": f"Rule '{rule_name}' triggered."}, "comment": ""}
        )
        self.view._populate_all_list_frames()
        self.set_dirty_status(True)

    # --- Autonomy Engine Methods ---

    def update_autonomy_status(self, status: str):
        """Thread-safe method to update the GUI with the autonomy engine's status."""
        self.view.after(0, self.view.update_autonomy_status_label, status)

    def _show_autonomy_confirmation_dialog_and_wait(self, plan: IntermediatePlan) -> bool:
        """Creates dialog on main thread and blocks calling thread until result is set."""
        self._autonomy_confirmation_result = None
        self._autonomy_confirmation_event.clear()

        plan_text = "\n".join([f"{step.get('step_id', i+1)}. {step.get('description', 'N/A')}" for i, step in enumerate(plan)])

        # Schedule the dialog creation on the main GUI thread
        self.view.after(0, self._create_confirmation_dialog, plan_text)

        # Wait for the dialog to be closed and the result to be set
        self._autonomy_confirmation_event.wait()
        return self._autonomy_confirmation_result or False

    def _create_confirmation_dialog(self, plan_text: str):
        """This method is called by `after()` and runs on the main GUI thread."""
        dialog = AutonomyConfirmationDialog(self.view, plan_text, self._handle_confirmation_result)
        self.view.wait_window(dialog)
        # If the window is closed without a button press, the callback might not have been called
        if self._autonomy_confirmation_result is None:
            self._handle_confirmation_result(False)  # Default to False if window closed

    def _handle_confirmation_result(self, result: bool):
        """Callback from the dialog, sets the result and the event."""
        self._autonomy_confirmation_result = result
        self._autonomy_confirmation_event.set()

    def toggle_autonomy_engine(self):
        """Starts or stops the Autonomous Assistant engine."""
        if self.autonomy_engine and self.autonomy_engine.is_running:
            self.autonomy_engine.stop()
            self.view.btn_start_assistant.configure(text="Start Assistant")
            return

        if not all([self.capture_engine, self.gemini_analyzer_instance, self.strategy_planner, self.gemini_decision_module]):
            messagebox.showerror("Engines Not Ready", "One or more required AI engines are not initialized. Cannot start assistant.", parent=self.view)
            return

        self.autonomy_engine = AutonomyEngine(
            capture_engine=self.capture_engine,
            gemini_analyzer=self.gemini_analyzer_instance,
            strategy_planner=self.strategy_planner,
            gemini_decision_module=self.gemini_decision_module,
            status_update_callback=self.update_autonomy_status,
            confirmation_gui_callback=self._show_autonomy_confirmation_dialog_and_wait,
        )
        self.autonomy_engine.start()
        self.view.btn_start_assistant.configure(text="Stop Assistant")
