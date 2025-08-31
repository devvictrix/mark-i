import logging
from typing import Any, Callable

from mark_i.agent.tools.base import BaseTool
from mark_i.symbiosis.bci_engine import BCIEngine
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.tools.bci")


class ReceiveThoughtAsTextTool(BaseTool):
    name = "receive_thought_as_text"
    description = "Receives a command directly from the user's thoughts via the BCI engine. This is the primary input method in symbiotic mode."

    def __init__(self, bci_engine: BCIEngine):
        self.bci_engine = bci_engine

    def execute(self, **kwargs: Any) -> str:
        if not self.bci_engine.bci_event_queue.empty():
            event = self.bci_engine.bci_event_queue.get()
            if event["type"] == "THOUGHT_RECEIVED":
                return f"User thought received: '{event['data']}'"
        return "No new user thought was detected."


class ProjectDataToUserTool(BaseTool):
    name = "project_data_to_user"
    description = "Sends a piece of information (text or image) directly back to the user's mind's eye via the BCI engine."

    def __init__(self, bci_engine: BCIEngine):
        self.bci_engine = bci_engine

    def execute(self, data_to_project: str = "", **kwargs: Any) -> str:
        if not data_to_project:
            return "Error: `data_to_project` cannot be empty."

        success = self.bci_engine.send_data_to_user(data_to_project)
        return "Successfully projected data to user." if success else "Failed to project data to user."
