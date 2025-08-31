import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, List

import numpy as np
from google.api_core import exceptions as google_api_exceptions

from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.execution.strategic_executor import StrategicExecutor # UPDATED
from mark_i.engines.gemini_decision_module import GeminiDecisionModule

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.autonomy.engine")

ASSESS_PRIMARY_MODEL = "gemini-2.0-flash"
ASSESS_FALLBACK_MODEL = "gemini-1.5-flash-latest"


ASSESS_PROMPT = """
You are an expert AI assistant integrated into a visual desktop automation tool named Mark-I.
Your task is to analyze a full-screen screenshot and act as a proactive assistant.
Analyze the provided image and respond with a single JSON object.

Your analysis should answer these questions:
1.  What is the primary application in focus? What is the user likely doing? (e.g., "User is browsing a file explorer", "User is reading a web article").
2.  Is there a clear, actionable event or state that Mark-I could help with? (e.g., a completed download, an error message, a dialog box waiting for input).
3.  If a task is identified, what is a concise, actionable goal for Mark-I to perform? This goal will be fed into another AI to generate an execution plan.

Respond ONLY with a single JSON object with the following structure:
{
  "assessment": {
    "application_in_focus": "Name of the application or context (e.g., 'Windows File Explorer', 'Google Chrome - News Article', 'VS Code')",
    "user_activity_inference": "A brief description of the user's inferred activity."
  },
  "assistance_opportunity": {
    "task_identified": boolean, // true if a clear, actionable task is found, otherwise false
    "confidence_score": float, // Your confidence (0.0 to 1.0) that this is a useful, non-intrusive task to suggest
    "task_description": "A human-readable description of the situation and the proposed task. (e.g., 'A file download notification for 'report-final.pdf' is visible. Propose to move it to the Desktop.') Set to null if no task is identified.",
    "derived_goal_for_planner": "A clear, one-sentence command for the next AI agent to plan. (e.g., 'Move the downloaded file named report-final.pdf to the Desktop folder.') Set to null if no task is identified."
  }
}

Guidelines:
- Be conservative. Only identify tasks with high confidence (e.g., > 0.75). Avoid interrupting the user if they seem busy with a complex task (e.g., writing code, in a video call).
- Good tasks are simple, consequential actions: clearing notifications, moving a downloaded file, closing a completed installer, clicking "OK" on an informational dialog.
- If no clear task is available, set "task_identified" to false.
"""

class AutonomyEngine:
    """
    High-level meta-controller for proactive, autonomous operation (v6.0.0).
    v10.0.8 Update: Now uses StrategicExecutor for planning and execution.
    """

    def __init__(
        self,
        capture_engine: CaptureEngine,
        gemini_analyzer: GeminiAnalyzer,
        strategic_executor: StrategicExecutor, # UPDATED
        confirmation_gui_callback: Callable[[str], bool], # UPDATED to take simple string
    ):
        self.capture_engine = capture_engine
        self.gemini_analyzer = gemini_analyzer
        self.strategic_executor = strategic_executor # UPDATED
        self.confirmation_gui_callback = confirmation_gui_callback

        self.assessment_interval_seconds: float = 10.0
        self.is_running: bool = False

        self._stop_event = threading.Event()
        self._autonomy_thread: Optional[threading.Thread] = None
        logger.info("AutonomyEngine initialized.")

    def start(self):
        """Starts the autonomous operation loop in a separate thread."""
        if self._autonomy_thread and self._autonomy_thread.is_alive():
            logger.warning("AutonomyEngine is already running. Start command ignored.")
            return

        self._stop_event.clear()
        self.is_running = True
        self._autonomy_thread = threading.Thread(target=self.run_autonomy_loop, daemon=True)
        self._autonomy_thread.name = "AutonomyEngineThread"
        logger.info(f"Starting AutonomyEngine thread. Assessment interval: {self.assessment_interval_seconds}s.")
        self._autonomy_thread.start()

    def stop(self):
        """Signals the autonomous loop to stop and waits for the thread to join."""
        if not self._autonomy_thread or not self._autonomy_thread.is_alive():
            logger.info("AutonomyEngine is not running or already stopped.")
            return

        logger.info("Attempting to stop AutonomyEngine thread...")
        self._stop_event.set()
        join_timeout = self.assessment_interval_seconds + 5.0
        self._autonomy_thread.join(timeout=join_timeout)

        if self._autonomy_thread.is_alive():
            logger.warning(f"AutonomyEngine thread did not stop in {join_timeout:.1f}s.")
        else:
            logger.info("AutonomyEngine thread successfully stopped.")
        
        self.is_running = False
        self._autonomy_thread = None

    def run_autonomy_loop(self):
        """The main operational loop for the autonomous assistant."""
        logger.info("Autonomous loop started.")
        while not self._stop_event.is_set():
            try:
                full_screen_capture = self._observe()
                if full_screen_capture is not None:
                    assessed_task_goal = self._assess(full_screen_capture)
                    if assessed_task_goal:
                        self._execute(assessed_task_goal)
            except Exception as e:
                logger.critical("Critical unhandled error in autonomy loop.", exc_info=True)
                time.sleep(self.assessment_interval_seconds * 2)
            
            self._stop_event.wait(timeout=self.assessment_interval_seconds)
        logger.info("Autonomous loop has been stopped.")

    def _observe(self) -> Optional[np.ndarray]:
        """Captures the current state of the entire screen."""
        logger.debug("AutonomyEngine: [Observe] phase.")
        try:
            return self.capture_engine.capture_region(
                {"name": "autonomous_fullscreen_capture", "x": 0, "y": 0, "width": self.capture_engine.get_primary_screen_width(), "height": self.capture_engine.get_primary_screen_height()}
            )
        except Exception as e:
            logger.error(f"AutonomyEngine: [Observe] phase failed: {e}", exc_info=True)
            return None

    def _assess(self, screen_capture: np.ndarray) -> Optional[str]:
        """Uses Gemini to assess the screen capture for potential tasks."""
        logger.debug("AutonomyEngine: [Assess] phase.")
        try:
            response = self.gemini_analyzer.query_vision_model(
                prompt=ASSESS_PROMPT, image_data=screen_capture, model_name_override=ASSESS_PRIMARY_MODEL
            )
            # ... (fallback logic remains the same)

            if response["status"] == "success" and response["json_content"]:
                opportunity = response["json_content"].get("assistance_opportunity", {})
                if opportunity.get("task_identified") and opportunity.get("confidence_score", 0) > 0.75:
                    derived_goal = opportunity.get("derived_goal_for_planner")
                    if derived_goal:
                        logger.info(f"[Assess] Task identified. Goal: '{derived_goal}'.")
                        return str(derived_goal)
        except Exception as e:
            logger.error(f"AutonomyEngine: [Assess] phase failed with an exception: {e}", exc_info=True)
        return None

    def _execute(self, goal: str):
        """Manages the user confirmation and execution via StrategicExecutor."""
        logger.debug(f"AutonomyEngine: [Execute] phase for goal: '{goal}'")
        
        user_confirmed = self.confirmation_gui_callback(goal)
        
        if user_confirmed:
            logger.info(f"User confirmed autonomous action. Executing goal '{goal}' via StrategicExecutor...")
            try:
                # The StrategicExecutor runs in its own thread internally, no need to thread here.
                # It's already designed to be called from the GUI controller's thread.
                self.strategic_executor.execute_command(goal)
            except Exception as e:
                logger.error(f"AutonomyEngine: [Execute] phase failed: {e}", exc_info=True)
        else:
            logger.info("User denied autonomous action. Aborting execution.")