import logging
import tkinter as tk
from tkinter import messagebox
import os
import copy
from typing import Optional, Dict, Any, List, Callable

import customtkinter as ctk

from mark_i.ui.gui.app_controller import AppController
from mark_i.ui.gui.panels.visual_log_panel import VisualLogPanel
from mark_i.ui.gui.gui_utils import create_clickable_list_item
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.main_app_window")


class MainAppWindow(ctk.CTk):
    """
    The main application window (the View) for the Mark-I GUI.
    As of v14.0.0, this is the "Command & Control" interface for the proactive,
    self-improving Genesis Core.
    """

    def __init__(self, initial_profile_path: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Initializing MainAppWindow (View)...")
        self.title("Mark-I: The Genesis Core")
        self.geometry("1200x750")
        self.minsize(900, 600)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.controller = AppController(self)

        # --- UI Widget Attributes ---
        self.knowledge_objectives_frame: Optional[ctk.CTkScrollableFrame] = None
        self.knowledge_strategies_frame: Optional[ctk.CTkFrame] = None
        self.interactive_command_entry: Optional[ctk.CTkEntry] = None
        self.btn_execute_command: Optional[ctk.CTkButton] = None
        self.label_interactive_command_status: Optional[ctk.CTkLabel] = None
        self.btn_toggle_proactive: Optional[ctk.CTkButton] = None
        self.label_proactive_status: Optional[ctk.CTkLabel] = None
        self.btn_toggle_learning: Optional[ctk.CTkButton] = None
        self.btn_manage_knowledge: Optional[ctk.CTkButton] = None
        self.label_knowledge_status: Optional[ctk.CTkLabel] = None
        self.visual_log_panel: Optional[VisualLogPanel] = None
        self.label_gemini_api_key_status: Optional[ctk.CTkLabel] = None

        self._setup_ui_layout_and_menu()
        self.controller.initialize_app(initial_profile_path=None)
        self.protocol("WM_DELETE_WINDOW", self.controller.on_close_window)
        logger.info("MainAppWindow (View) v14.0.0 initialization complete.")

    def _setup_ui_layout_and_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Manage Knowledge...", command=self.controller.manage_knowledge)
        file_menu.add_command(label="Reload Knowledge Base", command=self.controller.reload_knowledge_base)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.controller.on_close_window)

        self.grid_columnconfigure(0, weight=2, minsize=300)
        self.grid_columnconfigure(1, weight=5, minsize=500)
        self.grid_rowconfigure(0, weight=1)

        self.knowledge_panel = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray20"))
        self.knowledge_panel.grid(row=0, column=0, sticky="nsew")
        self._setup_knowledge_panel_content()

        self.interaction_panel = ctk.CTkFrame(self, corner_radius=0)
        self.interaction_panel.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
        self._setup_interaction_panel_content()

    def _setup_knowledge_panel_content(self):
        self.knowledge_panel.grid_columnconfigure(0, weight=1)
        self.knowledge_panel.grid_rowconfigure(1, weight=3)
        self.knowledge_panel.grid_rowconfigure(3, weight=2)

        ctk.CTkLabel(self.knowledge_panel, text="AI Memory (Objectives)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.knowledge_objectives_frame = ctk.CTkScrollableFrame(self.knowledge_panel, fg_color=("gray95", "gray22"))
        self.knowledge_objectives_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        ctk.CTkLabel(self.knowledge_panel, text="Strategies for Selected Objective", font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")
        self.knowledge_strategies_frame = ctk.CTkScrollableFrame(self.knowledge_panel, fg_color=("gray95", "gray22"))
        self.knowledge_strategies_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(5, 10))

    def _setup_interaction_panel_content(self):
        self.interaction_panel.grid_columnconfigure(0, weight=1)
        self.interaction_panel.grid_rowconfigure(1, weight=1)

        cmd_frame = ctk.CTkFrame(self.interaction_panel)
        cmd_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        cmd_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(cmd_frame, text="Interactive Command", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 2), sticky="w")

        self.interactive_command_entry = ctk.CTkEntry(cmd_frame, placeholder_text="Type your goal for Mark-I to execute...")
        self.interactive_command_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.interactive_command_entry.bind("<Return>", lambda e: self.controller.execute_interactive_command())

        self.btn_execute_command = ctk.CTkButton(cmd_frame, text="Execute Goal", command=self.controller.execute_interactive_command)
        self.btn_execute_command.grid(row=1, column=1, padx=(0, 10), pady=5)

        self.label_interactive_command_status = ctk.CTkLabel(cmd_frame, text="Status: Ready", anchor="w", text_color="gray")
        self.label_interactive_command_status.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")

        tab_view = ctk.CTkTabview(self.interaction_panel)
        tab_view.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        log_tab = tab_view.add("Visual Execution Log")
        proactive_tab = tab_view.add("Proactive Cores")
        settings_tab = tab_view.add("Global Settings")

        log_tab.grid_rowconfigure(0, weight=1)
        log_tab.grid_columnconfigure(0, weight=1)
        self.visual_log_panel = VisualLogPanel(log_tab, fg_color="transparent")
        self.visual_log_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        proactive_tab.grid_columnconfigure(0, weight=1)
        agency_frame = ctk.CTkFrame(proactive_tab, border_width=1)
        agency_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        agency_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(agency_frame, text="Proactive Agency Core", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 2), sticky="w")
        self.btn_toggle_proactive = ctk.CTkButton(agency_frame, text="Start Proactive AI", command=self.controller.toggle_proactive_agency)
        self.btn_toggle_proactive.grid(row=1, column=0, padx=10, pady=(5, 10))
        self.label_proactive_status = ctk.CTkLabel(agency_frame, text="Status: Inactive", anchor="w")
        self.label_proactive_status.grid(row=1, column=1, padx=10, pady=(5, 10), sticky="ew")

        knowledge_frame = ctk.CTkFrame(proactive_tab, border_width=1)
        knowledge_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        knowledge_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(knowledge_frame, text="Knowledge Discovery Core", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(5, 2), sticky="w")
        self.btn_toggle_learning = ctk.CTkButton(knowledge_frame, text="Start Learning", command=self.controller.toggle_knowledge_discovery)
        self.btn_toggle_learning.grid(row=1, column=0, padx=10, pady=(5, 10))
        self.btn_manage_knowledge = ctk.CTkButton(knowledge_frame, text="Manage Knowledge", command=self.controller.manage_knowledge)
        self.btn_manage_knowledge.grid(row=1, column=1, padx=5, pady=(5, 10))
        self.label_knowledge_status = ctk.CTkLabel(knowledge_frame, text="Status: Ready to learn.", anchor="w")
        self.label_knowledge_status.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 5), sticky="ew")

        settings_tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(settings_tab, text="Gemini API Key Status:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.label_gemini_api_key_status = ctk.CTkLabel(settings_tab, text="Checking...", anchor="w")
        self.label_gemini_api_key_status.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def populate_knowledge_objectives(self, objectives: List[Dict[str, Any]]):
        if not self.knowledge_objectives_frame:
            return
        for widget in self.knowledge_objectives_frame.winfo_children():
            widget.destroy()
        for objective in sorted(objectives, key=lambda o: o.get("objective_name", "")):
            obj_name = objective.get("objective_name", "Unnamed Objective")
            create_clickable_list_item(self.knowledge_objectives_frame, obj_name, lambda name=obj_name: self.controller.on_objective_selected(name))

    def display_strategies_for_objective(self, objective: Optional[Dict[str, Any]]):
        if not self.knowledge_strategies_frame:
            return
        for widget in self.knowledge_strategies_frame.winfo_children():
            widget.destroy()
        if not objective or not objective.get("strategies"):
            ctk.CTkLabel(self.knowledge_strategies_frame, text="No strategies found.").pack(padx=5, pady=5)
            return
        for strategy in sorted(objective["strategies"], key=lambda s: s.get("success_rate", 0), reverse=True):
            strat_name = strategy.get("strategy_name", "Unnamed Strategy")
            success_rate = strategy.get("success_rate", 0.0)
            display_text = f"{strat_name} (Success Rate: {success_rate:.2%})"
            item_frame = ctk.CTkFrame(self.knowledge_strategies_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=1, padx=1)
            ctk.CTkLabel(item_frame, text=display_text, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

    def update_proactive_status(self, text: str):
        if self.label_proactive_status:
            self.label_proactive_status.configure(text=f"Status: {text}")

    def update_interactive_command_status(self, text: str):
        if self.label_interactive_command_status:
            self.label_interactive_command_status.configure(text=f"Status: {text}")

    def update_knowledge_status(self, text: str):
        if self.label_knowledge_status:
            self.label_knowledge_status.configure(text=f"Status: {text}")

    def start_log_polling(self):
        self.controller.process_log_queue()
