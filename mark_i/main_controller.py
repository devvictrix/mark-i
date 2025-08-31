import logging
import threading
import time
from typing import Dict, Any, Optional, Set
import os

from mark_i.core.config_manager import ConfigManager
from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.analysis_engine import AnalysisEngine
from mark_i.engines.rules_engine import RulesEngine
from mark_i.engines.action_executor import ActionExecutor
from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.engines.gemini_decision_module import GeminiDecisionModule

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

# Default logger if none is provided
default_logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.main_controller")


class MainController:
    """
    Orchestrates the main bot operation loop: Capture -> Analyze (selectively) -> Evaluate Rules -> Act.
    Runs the monitoring loop in a separate thread.
    """

    def __init__(self, profile_name_or_path: str, custom_logger: Optional[logging.Logger] = None):
        """
        Initializes the MainController.

        Args:
            profile_name_or_path: The name or path of the profile to load.
            custom_logger: An optional, pre-configured logger instance to use.
                           If None, it uses the default module logger.
        """
        self.logger = custom_logger or default_logger
        self.logger.info(f"Initializing MainController with profile: '{profile_name_or_path}'")

        try:
            self.config_manager = ConfigManager(profile_name_or_path)
        except (FileNotFoundError, ValueError, IOError) as e:
            self.logger.critical(f"MainController: Failed to load profile '{profile_name_or_path}': {e}", exc_info=True)
            raise

        profile_data = self.config_manager.get_profile_data()
        settings = profile_data.get("settings", {})
        
        ocr_command = settings.get("tesseract_cmd_path")
        ocr_config = settings.get("tesseract_config_custom", "")
        self.dominant_colors_k = settings.get("analysis_dominant_colors_k", 3)
        if not isinstance(self.dominant_colors_k, int) or self.dominant_colors_k <= 0:
            self.logger.warning(f"Invalid 'analysis_dominant_colors_k' ({self.dominant_colors_k}). Defaulting to 3.")
            self.dominant_colors_k = 3

        self.capture_engine = CaptureEngine()
        self.analysis_engine = AnalysisEngine(ocr_command=ocr_command, ocr_config=ocr_config)
        # v10.0.6 FIX: ActionExecutor is now stateless and takes no arguments.
        self.action_executor = ActionExecutor()

        self.gemini_decision_module: Optional[GeminiDecisionModule] = None
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            gemini_analyzer_for_gdm = GeminiAnalyzer(api_key=gemini_api_key, default_model_name=self.config_manager.get_setting("gemini_default_model_name", "gemini-1.5-flash-latest"))
            if gemini_analyzer_for_gdm.client_initialized:
                self.gemini_decision_module = GeminiDecisionModule(
                    gemini_analyzer=gemini_analyzer_for_gdm, action_executor=self.action_executor, config_manager=self.config_manager
                )
            else:
                self.logger.warning("MainController: GeminiAnalyzer for GeminiDecisionModule failed initialization.")
        else:
            self.logger.warning("MainController: GEMINI_API_KEY not found. 'gemini_perform_task' actions may fail.")

        self.rules_engine = RulesEngine(self.config_manager, self.analysis_engine, self.action_executor, gemini_decision_module=self.gemini_decision_module)

        self.monitoring_interval = settings.get("monitoring_interval_seconds", 1.0)
        if not isinstance(self.monitoring_interval, (int, float)) or self.monitoring_interval <= 0:
            self.logger.warning(f"Invalid 'monitoring_interval_seconds' ({self.monitoring_interval}). Defaulting to 1.0s.")
            self.monitoring_interval = 1.0

        self.regions_to_monitor = profile_data.get("regions", [])
        if not self.regions_to_monitor:
            self.logger.warning(f"Profile '{profile_name_or_path}' has no regions defined.")

        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self.logger.info(f"MainController initialized successfully for profile: '{self.config_manager.get_profile_path()}'.")

    def _perform_monitoring_cycle(self):
        if not self.regions_to_monitor:
            self.logger.debug("No regions configured to monitor. Skipping cycle.")
            return

        all_region_data: Dict[str, Dict[str, Any]] = {}
        self.logger.info(f"----- Starting new monitoring cycle -----")

        for region_spec in self.regions_to_monitor:
            region_name = region_spec.get("name")
            if not region_name:
                self.logger.warning(f"Skipping region due to missing name: {region_spec}")
                continue
            
            captured_image_bgr = self.capture_engine.capture_region(region_spec)
            region_data_packet: Dict[str, Any] = {"image": captured_image_bgr}

            if captured_image_bgr is not None:
                required_analyses: Set[str] = self.rules_engine.get_analysis_requirements_for_region(region_name)
                if "average_color" in required_analyses:
                    region_data_packet["average_color"] = self.analysis_engine.analyze_average_color(captured_image_bgr, region_name)
                if "ocr" in required_analyses:
                    region_data_packet["ocr_analysis_result"] = self.analysis_engine.ocr_extract_text(captured_image_bgr, region_name)
                if "dominant_color" in required_analyses:
                    region_data_packet["dominant_colors_result"] = self.analysis_engine.analyze_dominant_colors(captured_image_bgr, self.dominant_colors_k, region_name)
            else:
                self.logger.warning(f"Image capture failed for region '{region_name}'.")

            all_region_data[region_name] = region_data_packet

        if all_region_data:
            self.rules_engine.evaluate_rules(all_region_data)

        self.logger.info("----- Monitoring cycle finished -----")

    def run_monitoring_loop(self):
        profile_display_name = os.path.basename(self.config_manager.get_profile_path() or "UnspecifiedProfile")
        self.logger.info(f"Monitoring loop started for profile '{profile_display_name}'.")
        try:
            while not self._stop_event.is_set():
                cycle_start_time = time.perf_counter()
                self._perform_monitoring_cycle()
                elapsed_time = time.perf_counter() - cycle_start_time
                wait_time = self.monitoring_interval - elapsed_time
                if wait_time > 0:
                    self._stop_event.wait(timeout=wait_time)
        except Exception as e:
            self.logger.critical("Critical error in monitoring loop. Terminating.", exc_info=True)
        finally:
            self.logger.info(f"Monitoring loop for '{profile_display_name}' stopped.")

    def start(self):
        if self._monitor_thread and self._monitor_thread.is_alive():
            self.logger.warning("Monitoring loop already running.")
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self.run_monitoring_loop, daemon=True)
        self._monitor_thread.name = f"MonitoringThread-{os.path.basename(self.config_manager.get_profile_path() or 'NewProfile')}"
        self._monitor_thread.start()

    def stop(self):
        if not self._monitor_thread or not self._monitor_thread.is_alive():
            self.logger.info("Monitoring loop not running or already stopped.")
            return

        self.logger.info(f"Attempting to stop monitoring thread...")
        self._stop_event.set()
        self._monitor_thread.join(timeout=self.monitoring_interval + 5.0)

        if self._monitor_thread.is_alive():
            self.logger.warning("Monitoring thread did not stop in time.")
        else:
            self.logger.info("Monitoring thread successfully stopped.")
        self._monitor_thread = None