import abc
from typing import Dict, Any, Optional

class BaseTool(abc.ABC):
    """
    Abstract base class for all tools available to the ReAct agent.
    Each tool must have a name, a description for the AI to understand its purpose,
    and an execute method.
    """
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The unique name of the tool (e.g., 'click_element')."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """
        A detailed description for the LLM to understand what the tool does,
        what its arguments are, and when to use it.
        """
        pass

    @abc.abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """
        Executes the tool with the given arguments.

        Args:
            **kwargs: The parameters for the tool, as decided by the agent.

        Returns:
            A string describing the outcome of the action (e.g., "Clicked button successfully.",
            "Error: Element not found."). This becomes the 'Observation' for the next step.
        """
        pass