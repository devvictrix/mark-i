import logging
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import copy
import shutil
import threading
import time
from typing import Optional, Dict, Any, List, Callable
from queue import Queue

import customtkinter as ctk
import numpy as np
from PIL import Image
import cv2

# Config and Engine Imports
from mark_i.core.config_manager import ConfigManager
from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.engines.action_executor import ActionExecutor
from mark_i.knowledge.knowledge_base import KnowledgeBase
from mark_i.knowledge.discovery_engine import KnowledgeDiscoveryEngine
from mark_i.agent.agent_core import AgentCore
from mark_i.agent.toolbelt import Toolbelt
from mark_i.agent.tools.system_tools import OpenApplicationTool, PressHotkeyTool
from mark_i.agent.tools.visual_tools import ClickElementTool, TypeTextTool
from mark_i.agent.tools.interactive_tools import AskUserTool
from mark_i.agent.tools.synchronization_tools import WaitForVisualCueTool
from mark_i.agent.tools.creation_tools import CreateNewTool
from mark_i.agent.tools.cognitive_tools import ReasonFromFirstPrinciplesTool, ProposeDirectiveChangeTool
from mark_i.perception.perception_engine import PerceptionEngine
from mark_i.agency.agency_core import AgencyCore
from mark_i.foresight.simulation_engine import SimulationEngine

# GUI Component Imports
from mark_i.ui.gui.autonomy_confirmation_dialog import AutonomyConfirmationDialog
from mark_i.ui.gui.knowledge_curator_window import KnowledgeCuratorWindow
from mark_i.ui.gui.logging_handler import GuiLoggingHandler
from mark_i.ui.gui.user_input_dialog import UserInputDialog
from mark_i.ui.gui.simple_eye_debug import SimpleEyeDebugWindow

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.app_controller")


class AppController:
    """
    Controller for the MainAppWindow v14+. Manages application state, logic,
    and the lifecycle of the top-level AI cores.
    """

    def __init__(self, view: ctk.CTk):
        self.view = view
        self.project_root = self._find_project_root()

        self.user_input_response: str = ""
        self.user_input_event = threading.Event()

        self.selected_objective_name: Optional[str] = None

        # --- Core Engines & Components ---
        self.capture_engine: Optional[CaptureEngine] = None
        self.gemini_analyzer_instance: Optional[GeminiAnalyzer] = None
        self.action_executor: Optional[ActionExecutor] = None
        self.knowledge_base: Optional[KnowledgeBase] = None
        self.toolbelt: Optional[Toolbelt] = None

        # --- High-Level AI Cores ---
        self.agent_core: Optional[AgentCore] = None  # The Tactical Core
        self.perception_engine: Optional[PerceptionEngine] = None  # The Senses
        self.simulation_engine: Optional[SimulationEngine] = None  # The Foresight Core
        self.agency_core: Optional[AgencyCore] = None  # The Proactive Core
        self.knowledge_discovery_engine: Optional[KnowledgeDiscoveryEngine] = None

        self.gui_log_queue = Queue()
        self._knowledge_discovery_cache: Dict[str, Any] = {}
        
        # Eye Debug Window
        self.eye_debug_window: Optional[SimpleEyeDebugWindow] = None

    def initialize_app(self, initial_profile_path: Optional[str]):
        """Initializes engines and populates the UI."""
        self._initialize_engines()
        self.reload_knowledge_base()
        self.view.start_log_polling()

    def _initialize_engines(self):
        """Instantiates all shared engine components and AI cores."""
        logger.info("AppController: Initializing all engines and AI cores...")

        self.capture_engine = CaptureEngine()
        self.action_executor = ActionExecutor()
        self.knowledge_base = KnowledgeBase(self.project_root)

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            self.gemini_analyzer_instance = GeminiAnalyzer(api_key=gemini_api_key)
            if self.gemini_analyzer_instance.client_initialized:

                def get_current_screenshot_for_tool() -> Optional[np.ndarray]:
                    if self.capture_engine:
                        return self.capture_engine.capture_region(
                            {"name": "tool_capture", "x": 0, "y": 0, "width": self.capture_engine.get_primary_screen_width(), "height": self.capture_engine.get_primary_screen_height()}
                        )
                    return None

                # Instantiate Tools
                wait_tool = WaitForVisualCueTool(self.gemini_analyzer_instance, get_current_screenshot_for_tool)
                click_tool = ClickElementTool(self.action_executor, self.gemini_analyzer_instance, get_current_screenshot_for_tool, wait_tool)

                # Placeholder callbacks for meta-tools
                def save_and_load_new_tool(class_name, code):
                    logger.warning(f"Tool Synthesis requested for {class_name}, but is not fully implemented.")
                    return False

                def confirm_directive_change(reason, new_directives):
                    logger.warning(f"Directive change proposed, but is not fully implemented.")
                    return False

                tools = [
                    OpenApplicationTool(),
                    PressHotkeyTool(self.action_executor),
                    click_tool,
                    TypeTextTool(self.action_executor),
                    AskUserTool(self.prompt_user_for_input),
                    wait_tool,
                    CreateNewTool(self.gemini_analyzer_instance, save_and_load_new_tool),
                    ReasonFromFirstPrinciplesTool(self.gemini_analyzer_instance),
                    ProposeDirectiveChangeTool(confirm_directive_change),
                ]
                self.toolbelt = Toolbelt(tools)

                # Instantiate AI Cores
                self.agent_core = AgentCore(
                    knowledge_base=self.knowledge_base,
                    capture_engine=self.capture_engine,
                    gemini_analyzer=self.gemini_analyzer_instance,
                    toolbelt=self.toolbelt,
                    status_update_callback=self._handle_agent_core_update,
                )
                self.perception_engine = PerceptionEngine(capture_engine=self.capture_engine)
                self.simulation_engine = SimulationEngine(gemini_analyzer=self.gemini_analyzer_instance)
                self.agency_core = AgencyCore(
                    perception_engine=self.perception_engine, agent_core=self.agent_core, gemini_analyzer=self.gemini_analyzer_instance, simulation_engine=self.simulation_engine
                )
            else:
                logger.error("AppController: GeminiAnalyzer failed to initialize.")
        else:
            logger.warning("AppController: GEMINI_API_KEY not found. AI will not function.")

        if self.view.label_gemini_api_key_status:
            self.view.label_gemini_api_key_status.configure(text=self.check_gemini_api_key_status())

    def _find_project_root(self) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

    def check_gemini_api_key_status(self) -> str:
        if self.gemini_analyzer_instance and self.gemini_analyzer_instance.client_initialized:
            return "OK (Client Initialized)"
        elif os.getenv("GEMINI_API_KEY"):
            return "Key Found but Client NOT Initialized"
        return "NOT FOUND in .env"

    def on_close_window(self, event=None):
        if self.agency_core and self.agency_core.is_running:
            self.agency_core.stop()
        if self.knowledge_discovery_engine and self.knowledge_discovery_engine.is_running:
            self.knowledge_discovery_engine.stop()
        self.view.destroy()

    def reload_knowledge_base(self):
        if not self.knowledge_base or not self.view.knowledge_objectives_frame:
            return
        self.knowledge_base.load_knowledge()
        objectives = self.knowledge_base.get_full_knowledge_base().get("objectives", [])
        self.view.populate_knowledge_objectives(objectives)
        self.on_objective_selected(None)

    def on_objective_selected(self, objective_name: Optional[str]):
        self.selected_objective_name = objective_name
        objective_data = None
        if self.knowledge_base and objective_name:
            objective_data = self.knowledge_base.find_objective(objective_name)
        self.view.display_strategies_for_objective(objective_data)

    def execute_interactive_command(self):
        command_text = self.view.interactive_command_entry.get().strip()
        if not command_text:
            return

        if not self.agent_core:
            messagebox.showerror("AI Engine Not Ready", "The Agent Core is not initialized.", parent=self.view)
            return

        self.view.btn_execute_command.configure(state="disabled")
        thread = threading.Thread(target=self._execute_interactive_command_in_thread, args=(command_text,))
        thread.daemon = True
        thread.start()

    def _execute_interactive_command_in_thread(self, command: str):
        if not self.agent_core:
            return
        result = self.agent_core.execute_goal(command)
        self.view.after(0, self.reload_knowledge_base)
        self.view.after(0, lambda: self.view.btn_execute_command.configure(state="normal"))

    def _handle_agent_core_update(self, update: Dict[str, Any]):
        if self.view and self.view.visual_log_panel:
            self.view.after(0, self.view.visual_log_panel.update_state, update)

        update_type = update.get("type")
        data = update.get("data", {})
        if update_type == "task_start":
            self.view.after(0, self.view.update_interactive_command_status, "Executing...")
        elif update_type == "task_end":
            final_status = f"Status: {data.get('status', 'unknown')}. {data.get('message', '')}"
            self.view.after(0, self.view.update_interactive_command_status, final_status)

    def process_log_queue(self):
        while not self.gui_log_queue.empty():
            try:
                self.view.visual_log_panel.add_log_message(self.gui_log_queue.get_nowait())
            except Exception:
                pass
        self.view.after(200, self.process_log_queue)

    def prompt_user_for_input(self, question: str) -> str:
        self.user_input_event.clear()
        self.view.after(0, self._show_user_input_dialog, question)
        self.user_input_event.wait()
        return self.user_input_response

    def _show_user_input_dialog(self, question: str):
        dialog = UserInputDialog(self.view, title="MARK-I Needs Input", prompt=question)
        self.user_input_response = dialog.get_input()
        self.user_input_event.set()

    def toggle_proactive_agency(self):
        if self.agency_core and self.agency_core.is_running:
            self.agency_core.stop()
            self.view.update_proactive_status("Inactive")
            self.view.btn_toggle_proactive.configure(text="Start Proactive AI")
            return
        if not self.agency_core:
            messagebox.showerror("Engines Not Ready", "The Agency Core is not initialized.", parent=self.view)
            return
        self.agency_core.start()
        self.view.update_proactive_status("Running...")
        self.view.btn_toggle_proactive.configure(text="Stop Proactive AI")

    def _handle_knowledge_proposals(self, candidates: List[Dict[str, Any]]):
        if not candidates or not self.capture_engine:
            return
        self._knowledge_discovery_cache = {
            "candidates": candidates,
            "screenshot": self.capture_engine.capture_region(
                {"name": "curation_capture", "x": 0, "y": 0, "width": self.capture_engine.get_primary_screen_width(), "height": self.capture_engine.get_primary_screen_height()}
            ),
        }
        self.view.after(0, self.view.update_knowledge_status, f"{len(candidates)} new items. Click 'Manage'.")

    def _save_confirmed_knowledge(self, confirmed_items: List[Dict[str, Any]]):
        if not self.knowledge_base:
            return
        kb_data = self.knowledge_base.get_full_knowledge_base()
        kb_data.setdefault("user_data", {})
        kb_data.setdefault("aliases", {})
        for item in confirmed_items:
            item_name = item.get("name")
            if not item_name:
                continue
            if item.get("type") == "data_field":
                kb_data["user_data"][item_name] = item.get("value")
            elif item.get("type") in ["application_icon", "ui_element"]:
                kb_data["aliases"][item_name] = item.get("description")
        if self.knowledge_base.save_knowledge_base():
            self.knowledge_base.load_knowledge()
            self.reload_knowledge_base()
            messagebox.showinfo("Knowledge Base Updated", f"{len(confirmed_items)} items saved.", parent=self.view)
        else:
            messagebox.showerror("Save Error", "Failed to save to knowledge_base.json.", parent=self.view)

    def manage_knowledge(self):
        if not self._knowledge_discovery_cache.get("candidates"):
            messagebox.showinfo("No New Knowledge", "No new items found yet. Let learning run.", parent=self.view)
            return
        screenshot_np = self._knowledge_discovery_cache.get("screenshot")
        if screenshot_np is None:
            return
        screenshot_pil = Image.fromarray(cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2RGB))
        curator = KnowledgeCuratorWindow(
            master=self.view, knowledge_candidates=self._knowledge_discovery_cache["candidates"], screenshot_pil=screenshot_pil, save_callback=self._save_confirmed_knowledge
        )
        self.view.wait_window(curator)
        self._knowledge_discovery_cache.clear()
        self.view.update_knowledge_status("Ready to learn.")

    def toggle_knowledge_discovery(self):
        if self.knowledge_discovery_engine and self.knowledge_discovery_engine.is_running:
            self.knowledge_discovery_engine.stop()
            self.view.update_knowledge_status("Inactive")
            self.view.btn_toggle_learning.configure(text="Start Learning")
            return
        if not all([self.capture_engine, self.gemini_analyzer_instance, self.knowledge_base]):
            return
        self.knowledge_discovery_engine = KnowledgeDiscoveryEngine(
            capture_engine=self.capture_engine, gemini_analyzer=self.gemini_analyzer_instance, knowledge_base=self.knowledge_base, proposal_callback=self._handle_knowledge_proposals
        )
        self.knowledge_discovery_engine.start()
        self.view.update_knowledge_status("Learning...")
        self.view.btn_toggle_learning.configure(text="Stop Learning")
    
    def open_eye_debug(self):
        """Open the Eye Debug window to show what MARK-I sees."""
        try:
            # Always create a new window to avoid threading issues
            self.eye_debug_window = SimpleEyeDebugWindow(parent=self.view)
            self.eye_debug_window.show()
            logger.info("Eye Debug window opened")
            
        except Exception as e:
            logger.error(f"Failed to open Eye Debug window: {e}")
            messagebox.showerror("Error", f"Failed to open Eye Debug window:\n{str(e)}", parent=self.view)
