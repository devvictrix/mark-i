import logging
import threading
from typing import Any, Callable

from mark_i.agent.tools.base import BaseTool
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.tools.interactive")

class AskUserTool(BaseTool):
    """
    A tool that allows the agent to pause execution and ask the user for
    clarification or information. This is critical for resolving ambiguity.
    """
    name = "ask_user"
    description = (
        "Asks the human user for information when you are stuck or lack critical knowledge. "
        "Use this if you are uncertain about which element to interact with, or if you are missing "
        "information needed to proceed (e.g., a password, a filename, or which button to click). "
        "Argument `question` (string) is the clear, concise question you want to ask the user."
    )

    def __init__(self, user_prompt_callback: Callable[[str], str]):
        # This callback will be provided by the AppController to show a GUI dialog
        # and block the agent's thread until the user responds.
        self.user_prompt_callback = user_prompt_callback

    def execute(self, question: str = "", **kwargs: Any) -> str:
        """
        Executes the tool by invoking the callback to show a GUI prompt.

        Args:
            question: The question to display to the user in the prompt.

        Returns:
            A string containing the user's response, which becomes the next Observation.
        """
        if not question or not isinstance(question, str):
            error_msg = "Error: `question` parameter must be a non-empty string."
            logger.error(f"Tool 'ask_user' failed: {error_msg}")
            return error_msg
        
        logger.info(f"Tool 'ask_user' executing with question: '{question}'")
        
        try:
            # The callback is a blocking call that will wait for the user's input.
            user_response = self.user_prompt_callback(question)
            
            if user_response:
                logger.info(f"User responded to 'ask_user' prompt with: '{user_response}'")
                return f"The user responded: '{user_response}'"
            else:
                logger.warning("User cancelled or provided no response to 'ask_user' prompt.")
                return "The user cancelled or provided no response. The task may need to be re-evaluated or finished."
        except Exception as e:
            logger.error(f"Tool 'ask_user' failed with a system exception: {e}", exc_info=True)
            return f"Error: A system error occurred while trying to ask the user a question: {e}"