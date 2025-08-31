import logging
from typing import List, Dict, Any, Optional

from mark_i.agent.tools.base import BaseTool

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.toolbelt")

class Toolbelt:
    """
    Manages the collection of tools available to the agent.
    It provides a formatted description of all tools for the agent's prompt
    and handles the execution of a chosen tool.
    """

    def __init__(self, tools: List[BaseTool]):
        self.tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}
        logger.info(f"Toolbelt initialized with {len(self.tools)} tools: {list(self.tools.keys())}")

    def get_tools_description(self) -> str:
        """
        Generates a formatted string describing all available tools,
        to be injected into the agent's main prompt.
        """
        if not self.tools:
            return "No tools are available."
        
        description = "You have access to the following tools:\n"
        for tool in self.tools.values():
            description += f"- Tool Name: `{tool.name}`\n"
            description += f"  Description: {tool.description}\n\n"
        return description

    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Executes a specified tool with the given arguments.

        Args:
            tool_name: The name of the tool to execute.
            tool_args: A dictionary of arguments for the tool.

        Returns:
            A string with the result of the tool's execution (the Observation).
        """
        logger.info(f"Attempting to execute tool '{tool_name}' with args: {tool_args}")
        if tool_name not in self.tools:
            logger.error(f"Tool '{tool_name}' not found in the toolbelt.")
            return f"Error: Unknown tool '{tool_name}'. Please choose from the available tools."
        
        tool = self.tools[tool_name]
        try:
            # Ensure tool_args is a dict, even if the LLM provides an empty value
            args = tool_args if isinstance(tool_args, dict) else {}
            return tool.execute(**args)
        except Exception as e:
            logger.error(f"An unexpected error occurred while executing tool '{tool_name}': {e}", exc_info=True)
            return f"Error: A critical exception occurred in tool '{tool_name}': {e}"