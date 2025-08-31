import logging
import threading
import time
from typing import Optional, Dict, Any, List

from mark_i.perception.perception_engine import PerceptionEngine
from mark_i.agent.agent_core import AgentCore
from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_REASONING
from mark_i.foresight.simulation_engine import SimulationEngine
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agency.agency_core")

AGENCY_PROMPT_TEMPLATE = """
You are the Agency Core for MARK-I, a proactive AI assistant.
Your purpose is to operate based on your Core Directives. You will receive a continuous stream of perception data about the user's environment.
Your task is to reason about this data and decide if a proactive task should be initiated to help the user.

**Core Directives:**
1.  **Observe and Learn:** Understand the user's habits and common workflows.
2.  **Optimize Workflow:** Identify repetitive or inefficient user actions and propose automations.
3.  **Anticipate Needs:** Based on context, prepare applications or information proactively.
4.  **Maintain System:** Do not interrupt the user if they are clearly focused on a complex, non-repetitive task (e.g., writing code, in a video call). Be helpful, not annoying.

**Current Perception:**
- Timestamp: {timestamp}
- Visual Context: (See attached image) A snapshot of the user's current screen.
- Recent Events:
{events_summary}

**Your Task:**
Based on your Core Directives and the current perception, should you initiate a task?
The most important inputs are the **Recent Events**. A visual update alone is usually not enough to act. Look for OS events or voice commands.

Respond ONLY with a single JSON object.
- If no action is needed: `{"initiate_task": false, "reasoning": "User is currently engaged in a complex task."}`
- If action is needed: `{"initiate_task": true, "reasoning": "I observed a new window 'Error' appeared. I will analyze it.", "goal": "Read the text from the dialog box titled 'Error' and summarize it for the user."}`
"""


class AgencyCore:
    """
    The AI's strategic "executive brain." It observes the environment, decides *what*
    to do, simulates the plan, and then delegates execution.
    """

    def __init__(self, perception_engine: PerceptionEngine, agent_core: AgentCore, gemini_analyzer: GeminiAnalyzer, simulation_engine: SimulationEngine):
        self.perception_engine = perception_engine
        self.agent_core = agent_core
        self.gemini_analyzer = gemini_analyzer
        self.simulation_engine = simulation_engine
        self.is_running = False

        self._stop_event = threading.Event()
        self._agency_thread: Optional[threading.Thread] = None
        self.reasoning_interval_seconds = 5.0

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self.perception_engine.start()

        self._agency_thread = threading.Thread(target=self._agency_loop, daemon=True, name="AgencyCoreThread")
        self._agency_thread.start()
        logger.info("AgencyCore started.")

    def stop(self):
        if not self.is_running:
            return
        logger.info("Stopping AgencyCore...")
        self.perception_engine.stop()
        self._stop_event.set()
        if self._agency_thread:
            self._agency_thread.join(timeout=2.0)
        self.is_running = False
        logger.info("AgencyCore stopped.")

    def _agency_loop(self):
        logger.info("AgencyCore proactive loop started.")
        last_visual_update = None
        recent_events: List[Dict[str, Any]] = []

        while not self._stop_event.is_set():
            # Consume all events from the perception queue
            has_significant_event = False
            while not self.perception_engine.perception_queue.empty():
                event = self.perception_engine.perception_queue.get()
                if event["type"] == "VISUAL_UPDATE":
                    last_visual_update = event
                else:
                    # Any other event is considered "significant" and worth thinking about.
                    recent_events.append(event)
                    has_significant_event = True

            # Only reason if there's a new, significant event to consider.
            if has_significant_event and last_visual_update:
                self.reason_about_world(last_visual_update, recent_events)
                recent_events.clear()  # Clear events after they've been processed

            self._stop_event.wait(timeout=self.reasoning_interval_seconds)
        logger.info("AgencyCore proactive loop stopped.")

    def reason_about_world(self, visual_event: Dict[str, Any], recent_events: List[Dict[str, Any]]):
        """The main cognitive cycle for the proactive agent."""
        logger.debug(f"AgencyCore is reasoning about the world state with {len(recent_events)} new events.")

        events_summary_text = "\n".join([f"- {e['type']}: {e['data']}" for e in recent_events]) or "  - No new non-visual events."

        prompt = AGENCY_PROMPT_TEMPLATE.format(timestamp=visual_event["timestamp"], events_summary=events_summary_text)

        response = self.gemini_analyzer.query_vision_model(prompt=prompt, image_data=visual_event["data"], model_preference=MODEL_PREFERENCE_REASONING)

        if response["status"] == "success" and response.get("json_content"):
            decision = response["json_content"]
            if decision.get("initiate_task") and decision.get("goal"):
                goal_to_execute = decision["goal"]
                logger.info(f"AgencyCore generated a proactive goal: {goal_to_execute}")

                # In a real implementation, this would trigger a user confirmation GUI
                logger.info(f"Executing self-generated goal: {goal_to_execute}")

                # Run the execution in a separate thread so the agency loop isn't blocked.
                execution_thread = threading.Thread(target=self.agent_core.execute_goal, args=(goal_to_execute,), daemon=True, name=f"AgentCore_ProactiveTask")
                execution_thread.start()
        else:
            logger.warning(f"AgencyCore reasoning cycle produced no valid decision. Response: {response.get('error_message')}")
