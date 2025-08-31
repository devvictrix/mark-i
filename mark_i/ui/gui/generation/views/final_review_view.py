import logging
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import json
import copy
from typing import Optional, Dict, Any, List, Union, Callable

import customtkinter as ctk

from mark_i.ui.gui.generation.wizard_state import WizardState
from mark_i.generation.profile_generator import ProfileGenerator

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.generation.views.final_review_view")


class FinalReviewView(ctk.CTkFrame):
    """
    UI View for the final page of the AI Profile Creator wizard:
    displaying the generated profile JSON for review and handling saving.
    """

    def __init__(self, master: Any, controller: Any, state: WizardState, profile_generator: ProfileGenerator, on_state_change: Callable[[], None]):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.state = state
        self.profile_generator = profile_generator
        self.on_state_change = on_state_change  # Callback to notify controller of state changes

        self.profile_filename_entry: Optional[ctk.CTkEntry] = None

        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)

        self._setup_ui()
        logger.debug("FinalReviewView UI setup complete.")

    def _setup_ui(self):
        ctk.CTkLabel(self, text="AI Profile Creator: Final Review & Save Profile", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 15), anchor="w")

        profile_summary_textbox = ctk.CTkTextbox(self, height=450, wrap="word", state="disabled", font=ctk.CTkFont(family="Courier New", size=11))
        profile_summary_textbox.pack(fill="both", expand=True, pady=(0, 10))

        # Ensure staged templates are added to the profile_generator before getting the final data
        # This is a critical step to include templates in the JSON preview
        for tpl_data in self.state.staged_templates_with_image_data:
            if "_image_data_np_for_save" in tpl_data:  # Only pass cleaned metadata to profile_generator.add_template_definition
                self.profile_generator.add_template_definition({k: v for k, v in tpl_data.items() if k != "_image_data_np_for_save"})

        data = self.profile_generator.get_generated_profile_data()
        if self.state.user_goal_text:
            data["profile_description"] = f"AI-Generated for goal: {self.state.user_goal_text[:120]}"

        try:
            text = json.dumps(data, indent=2)
            profile_summary_textbox.configure(state="normal")
            profile_summary_textbox.delete("0.0", "end")
            profile_summary_textbox.insert("0.0", text)
            profile_summary_textbox.configure(state="disabled")
        except Exception as e:
            profile_summary_textbox.configure(state="normal")
            profile_summary_textbox.delete("0.0", "end")
            profile_summary_textbox.insert("0.0", f"Error displaying profile: {e}")
            profile_summary_textbox.configure(state="disabled")
            logger.error(f"FinalReviewView: Error displaying generated profile JSON: {e}", exc_info=True)

        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(name_frame, text="Profile Filename:").pack(side="left", padx=(0, 5))

        self.profile_filename_entry = ctk.CTkEntry(name_frame, placeholder_text=self.state.generated_profile_name_base)
        self.profile_filename_entry.pack(side="left", expand=True, fill="x")
        self.profile_filename_entry.insert(0, self.state.generated_profile_name_base)
        self.profile_filename_entry.bind("<KeyRelease>", lambda e: self.on_state_change())  # Notify controller of state change

        self.on_state_change()  # Ensure navigation buttons reflect current state

    def save_generated_profile(self):
        """
        Called by the controller when the user clicks 'Save Profile & Close'.
        Handles saving the generated profile JSON and its associated template images.
        """
        logger.info("FinalReviewView: Save Profile button clicked.")
        filename_base_from_ui = self.profile_filename_entry.get().strip()
        if not filename_base_from_ui:
            messagebox.showerror("Filename Missing", "Please enter a filename for the profile.", parent=self.controller)
            return

        # Ensure the profile generator has the latest description
        self.profile_generator.generated_profile_data["profile_description"] = self.profile_generator.get_generated_profile_data().get("profile_description", self.state.generated_profile_name_base)

        # Use main_app_instance's config_manager to determine default save directory
        default_save_dir = self.controller.get_current_main_app_instance().config_manager.profiles_base_dir
        initial_filename_for_dialog = f"{filename_base_from_ui}.json"

        filepath_chosen_by_user = filedialog.asksaveasfilename(
            title="Save AI-Generated Profile As",
            initialdir=default_save_dir,
            initialfile=initial_filename_for_dialog,
            defaultextension=".json",
            filetypes=[("JSON Profile", "*.json"), ("All files", "*.*")],
            parent=self.controller,
        )

        if filepath_chosen_by_user:
            # Add staged templates from wizard_state to profile_generator for saving
            for tpl_data in self.state.staged_templates_with_image_data:
                self.profile_generator.add_template_definition(tpl_data)  # This will store the _image_data_np_for_save

            success = self.profile_generator.save_generated_profile(filepath_chosen_by_user)
            if success:
                messagebox.showinfo("Profile Saved", f"AI-Generated profile (and its templates) saved to:\n{filepath_chosen_by_user}", parent=self.controller)
                self.controller.newly_saved_profile_path = filepath_chosen_by_user
                if messagebox.askyesno("Open in Editor?", "Open the new profile in the main editor?", parent=self.controller):
                    self.controller.get_current_main_app_instance()._load_profile_from_path(filepath_chosen_by_user)
                self.controller._on_close_wizard(was_saved=True)
            else:
                messagebox.showerror("Save Failed", "Could not save profile or its templates. Please check logs for details.", parent=self.controller)
        else:
            logger.info("FinalReviewView: Profile save dialog cancelled by user.")

        self.on_state_change()  # Notify controller of state change
