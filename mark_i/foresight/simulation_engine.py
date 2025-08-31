import logging
from typing import Optional, Dict, Any, List

import numpy as np

from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_REASONING
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.foresight.simulation_engine")

FORESIGHT_PROMPT_TEMPLATE = """
You are a Foresight Engine for the MARK-I AI agent, acting as a "Red Team" specialist.
Your goal is to perform a cognitive simulation of a proposed plan and identify potential risks, failures, and unintended consequences.

**Current Situation:**
- The AI is observing the screen shown in the attached image.
- The AI's overall goal is: "{user_goal}"

**Proposed Strategic Plan to Simulate:**
```json
{strategic_plan_json}
```

**Your Task:**
Analyze the plan in the context of the current screen. Predict the step-by-step outcome of executing this plan.
Focus on what could go wrong.

Respond ONLY with a single JSON object with the following structure:
{{
  "simulation_summary": "A high-level, step-by-step prediction of what will happen if this plan is executed.",
  "risk_analysis": {{
    "overall_confidence_score": float, // Your confidence (0.0 to 1.0) that this plan will succeed without issues.
    "potential_risks": [
      {{
        "step_index": int, // The 1-based index of the step where the risk might occur.
        "risk_description": "A clear description of the potential problem (e.g., 'The 'Save' button might be disabled until text is entered.').",
        "severity": "Low | Medium | High | Critical"
      }}
    ],
    "suggested_mitigation": "An optional, high-level suggestion to make the plan safer (e.g., 'Add a step to verify the 'Save' button is enabled before clicking.')."
  }}
}}

If there are no obvious risks, return an empty "potential_risks" array and a high confidence score.
"""

class SimulationEngine:
    """
    Performs a cognitive "dry run" of a strategic plan to identify potential
    risks and failure modes before execution.
    """
    def __init__(self, gemini_analyzer: GeminiAnalyzer):
        self.gemini_analyzer = gemini_analyzer
        logger.info("SimulationEngine (Foresight Core) initialized.")

    def simulate_plan(self, user_goal: str, strategic_plan: List[Dict[str, str]], visual_context: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Simulates a plan and returns a risk analysis.

        Args:
            user_goal: The original high-level user goal.
            strategic_plan: The list of tactical steps to be simulated.
            visual_context: The current screenshot of the desktop.

        Returns:
            A dictionary containing the simulation and risk analysis, or None on failure.
        """
        logger.info(f"Foresight Engine: Simulating {len(strategic_plan)}-step plan for goal: '{user_goal}'")

        prompt = FORESIGHT_PROMPT_TEMPLATE.format(
            user_goal=user_goal,
            strategic_plan_json=json.dumps(strategic_plan, indent=2)
        )

        response = self.gemini_analyzer.query_vision_model(
            prompt=prompt,
            image_data=visual_context,
            model_preference=MODEL_PREFERENCE_REASONING # Use a powerful model for this
        )

        if response["status"] == "success" and response.get("json_content"):
            logger.info("Foresight simulation successful.")
            return response["json_content"]
        else:
            logger.error(f"Foresight simulation failed. AI response was invalid. Error: {response.get('error_message')}")
            return None
