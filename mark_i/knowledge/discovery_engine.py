import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, List
import copy

import numpy as np

from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.knowledge.knowledge_base import KnowledgeBase

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.knowledge.discovery_engine")

KNOWLEDGE_DISCOVERY_MODEL = "gemini-1.5-flash-latest"
KNOWLEDGE_REFINE_MODEL = "gemini-1.5-flash-latest"

KNOWLEDGE_DISCOVERY_PROMPT = """
You are a proactive knowledge discovery agent for the Mark-I visual automation tool. Your goal is to analyze screenshots and identify key, reusable pieces of information.

Analyze the provided screenshot and identify the following:
1.  **Application Icons/Logos:** (e.g., Chrome, Slack, VS Code, LINE).
2.  **Common UI Elements:** (e.g., a "User Profile" avatar, a main "File" menu).
3.  **Labeled Data Fields:** (e.g., "First Name:", "Email Address:", "Username:").

Respond ONLY with a single JSON object with a top-level key "discovered_elements".
The value of "discovered_elements" must be an array of objects.
Each object must have the following structure:
  - "type": (String, Required) One of: "application_icon", "ui_element", "data_field".
  - "name_suggestion": (String, Required) A concise, snake_case name for the item (e.g., "chrome_taskbar_icon", "first_name_field").
  - "description": (String, Required) A human-readable description of the identified item (e.g., "The Google Chrome icon on the taskbar.", "The input field labeled 'First Name'.").
"""


class KnowledgeDiscoveryEngine:
    """
    Proactively observes the user's screen to identify and suggest potential
    additions to the KnowledgeBase. This is the core of the v9.0.0 feature set.
    """

    def __init__(
        self,
        capture_engine: CaptureEngine,
        gemini_analyzer: GeminiAnalyzer,
        knowledge_base: KnowledgeBase,
        proposal_callback: Callable[[List[Dict[str, Any]]], None],
    ):
        self.capture_engine = capture_engine
        self.gemini_analyzer = gemini_analyzer
        self.knowledge_base = knowledge_base
        self.proposal_callback = proposal_callback

        self.discovery_interval_seconds: float = 30.0
        self.is_running: bool = False

        self._stop_event = threading.Event()
        self._discovery_thread: Optional[threading.Thread] = None
        logger.info("KnowledgeDiscoveryEngine initialized.")

    def start(self):
        if self._discovery_thread and self._discovery_thread.is_alive():
            logger.warning("KnowledgeDiscoveryEngine is already running.")
            return
        self._stop_event.clear()
        self.is_running = True
        self._discovery_thread = threading.Thread(target=self.run_discovery_loop, daemon=True)
        self._discovery_thread.name = "KnowledgeDiscoveryThread"
        logger.info(f"Starting KnowledgeDiscoveryEngine thread. Interval: {self.discovery_interval_seconds}s.")
        self._discovery_thread.start()

    def stop(self):
        if not self._discovery_thread or not self._discovery_thread.is_alive():
            logger.info("KnowledgeDiscoveryEngine not running.")
            return
        logger.info("Attempting to stop KnowledgeDiscoveryEngine thread...")
        self._stop_event.set()
        self._discovery_thread.join(timeout=self.discovery_interval_seconds + 5.0)
        if self._discovery_thread.is_alive():
            logger.warning("KnowledgeDiscoveryEngine thread did not stop in time.")
        else:
            logger.info("KnowledgeDiscoveryEngine thread successfully stopped.")
        self.is_running = False
        self._discovery_thread = None

    def run_discovery_loop(self):
        logger.info("Knowledge discovery loop started.")
        while not self._stop_event.is_set():
            try:
                screenshot = self._observe()
                if screenshot is not None:
                    knowledge_candidates = self._analyze_for_knowledge(screenshot)
                    if knowledge_candidates:
                        logger.info(f"Discovered {len(knowledge_candidates)} potential knowledge items.")
                        self.proposal_callback(knowledge_candidates)
            except Exception as e:
                logger.critical("Critical unhandled error in discovery loop.", exc_info=True)
                time.sleep(self.discovery_interval_seconds)
            self._stop_event.wait(timeout=self.discovery_interval_seconds)
        logger.info("Knowledge discovery loop has been stopped.")

    def _observe(self) -> Optional[np.ndarray]:
        logger.debug("KnowledgeDiscoveryEngine: [Observe] phase.")
        try:
            return self.capture_engine.capture_region(
                {"name": "knowledge_discovery_capture", "x": 0, "y": 0, "width": self.capture_engine.get_primary_screen_width(), "height": self.capture_engine.get_primary_screen_height()}
            )
        except Exception as e:
            logger.error(f"KnowledgeDiscoveryEngine: [Observe] phase failed: {e}", exc_info=True)
        return None

    def _refine_element_location(self, screenshot: np.ndarray, element_description: str) -> Optional[List[int]]:
        """Makes a focused AI call to get the bounding box for a single described element."""
        log_prefix = f"KD.Refine(Elem: '{element_description[:30]}...')"
        prompt = (
            f'In the provided image, find the precise bounding box for the element best described as: "{element_description}".\n'
            f'Respond ONLY with JSON: {{"found": true, "box": [x,y,w,h]}}. Coords must be integers. Ensure width and height are positive.\n'
            f'If not found, respond with {{"found": false, "box": null}}.'
        )
        # --- FIX APPLIED HERE ---
        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=screenshot, model_preference=[KNOWLEDGE_REFINE_MODEL])
        if response["status"] == "success" and response.get("json_content"):
            data = response["json_content"]
            if data.get("found") and isinstance(data.get("box"), list) and len(data["box"]) == 4:
                logger.debug(f"{log_prefix} Refined to box: {data['box']}")
                return [int(c) for c in data["box"]]
        logger.warning(f"{log_prefix} Could not refine location.")
        return None

    def _analyze_for_knowledge(self, screenshot: np.ndarray) -> Optional[List[Dict[str, Any]]]:
        logger.debug("KnowledgeDiscoveryEngine: [Analyze for Knowledge] phase.")
        # --- FIX APPLIED HERE ---
        response = self.gemini_analyzer.query_vision_model(prompt=KNOWLEDGE_DISCOVERY_PROMPT, image_data=screenshot, model_preference=[KNOWLEDGE_DISCOVERY_MODEL])
        if response["status"] != "success" or not response.get("json_content"):
            logger.warning(f"[Analyze] Initial knowledge identification query failed. Status: {response['status']}")
            return None

        content = response["json_content"]
        described_elements = content.get("discovered_elements")
        if not isinstance(described_elements, list):
            logger.warning("[Analyze] AI response did not contain a valid 'discovered_elements' list.")
            return None

        logger.info(f"[Analyze] Identified {len(described_elements)} potential elements. Now refining locations.")

        final_candidates = []
        for element in described_elements:
            description = element.get("description")
            if not description:
                continue

            time.sleep(1.0)  # Respect API rate limits for sequential calls

            bbox = self._refine_element_location(screenshot, description)
            if bbox:
                element_with_box = copy.deepcopy(element)
                element_with_box["bounding_box"] = bbox
                final_candidates.append(element_with_box)

        return final_candidates if final_candidates else None
