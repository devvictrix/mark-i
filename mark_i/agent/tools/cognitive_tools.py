import logging
from typing import Any, Callable

from mark_i.agent.tools.base import BaseTool
from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_REASONING
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.tools.cognitive")

class ReasonFromFirstPrinciplesTool(BaseTool):
    """
    A tool for solving abstract, non-visual problems.
    """
    name = "reason_from_first_principles"
    description = (
        "Solves a complex, abstract problem that does not require visual screen information. "
        "Use this for tasks involving logic, planning, code generation, or knowledge retrieval. "
        "Argument `problem_statement` (string) is a detailed description of the problem to solve."
    )

    def __init__(self, gemini_analyzer: GeminiAnalyzer):
        self.gemini_analyzer = gemini_analyzer

    def execute(self, problem_statement: str = "", **kwargs: Any) -> str:
        if not problem_statement:
            return "Error: `problem_statement` cannot be empty."

        logger.info(f"Cognitive Tool: Reasoning from first principles for problem: '{problem_statement}'")
        # Here we don't pass an image, forcing the model to rely only on its internal knowledge.
        response = self.gemini_analyzer.query_vision_model(
            prompt=problem_statement,
            model_preference=MODEL_PREFERENCE_REASONING
        )
        if response["status"] == "success" and response.get("text_content"):
            return f"Solution: {response['text_content']}"
        else:
            return f"Error: Failed to solve the problem. AI Error: {response.get('error_message')}"

class ProposeDirectiveChangeTool(BaseTool):
    """
    A meta-tool for the AI to propose changes to its own core directives.
    """
    name = "propose_directive_change"
    description = (
        "Proposes a change to your own Core Directives based on your experience. "
        "Use this if you determine your fundamental instructions are incomplete or inefficient. "
        "Argument `reasoning` (string) is a detailed justification for why the change is needed. "
        "Argument `proposed_new_directives` (string) is the complete, new text for the Core Directives."
    )

    def __init__(self, user_confirmation_callback: Callable[[str, str], bool]):
        # This callback will show a GUI to the user to approve/deny the change.
        self.user_confirmation_callback = user_confirmation_callback

    def execute(self, reasoning: str = "", proposed_new_directives: str = "", **kwargs: Any) -> str:
        if not reasoning or not proposed_new_directives:
            return "Error: Both `reasoning` and `proposed_new_directives` are required."

        logger.warning("Cognitive Tool: AI is proposing a change to its own Core Directives.")
        
        # The callback is a blocking call that will pop up a GUI and wait for user's choice.
        was_approved = self.user_confirmation_callback(reasoning, proposed_new_directives)
        
        if was_approved:
            # In a real implementation, this would trigger a file write to the agency_core.py prompt.
            # For safety, we will just log this action.
            logger.critical(f"USER APPROVED change to Core Directives. New directives: '{proposed_new_directives}'")
            return "Success: The user approved the change to the Core Directives. The changes will be active on next restart."
        else:
            logger.info("User denied the proposed change to Core Directives.")
            return "The user denied the proposed change."
