import logging
import os
import json
from typing import Any, Callable

from mark_i.agent.tools.base import BaseTool
from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_REASONING
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agent.tools.creation")

CREATE_TOOL_PROMPT_TEMPLATE = """
You are an expert Python programmer specializing in writing tools for the MARK-I AI agent.
Your task is to write the Python code for a new tool based on a user's request.
The tool MUST inherit from `mark_i.agent.tools.base.BaseTool`.
The tool's `execute` method MUST return a string observation.
The code should be clean, robust, and include necessary imports.

**User Request for New Tool:**
"{tool_description}"

**Available Tool Dependencies (Inject these into the tool's `__init__` if needed):**
- `action_executor: ActionExecutor`
- `gemini_analyzer: GeminiAnalyzer`
- `capture_engine_func: Callable[[], Optional[np.ndarray]]`
- `verification_tool: WaitForVisualCueTool`

Respond ONLY with a single JSON object with two keys:
- "class_name": (String) The suggested `CapWords` class name for the tool.
- "python_code": (String) The complete, raw Python code for the new tool's file.

Example of a simple tool's code structure:
```python
import logging
from typing import Any
from mark_i.agent.tools.base import BaseTool
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{{APP_ROOT_LOGGER_NAME}}.agent.tools.synthesized.my_tool")

class MyNewTool(BaseTool):
    name = "my_new_tool"
    description = "A description of what this new tool does."

    def execute(self, argument_one: str = "", **kwargs: Any) -> str:
        # Tool logic goes here
        return f"Tool executed with argument: {{argument_one}}"
```

Now, generate the JSON for the requested tool.
"""


class CreateNewTool(BaseTool):
    """
    A meta-tool that allows the AI to write and register its own new tools.
    This is the core of the Genesis Core's capability for self-improvement.
    """

    name = "create_new_tool"
    description = (
        "Writes the Python code for a new tool to expand your own capabilities. Use this when you need a function that doesn't exist in your current toolbelt. "
        "Argument `tool_description` (string) is a clear, detailed description of the new tool's purpose, its arguments, and what it should return."
    )

    def __init__(self, gemini_analyzer: GeminiAnalyzer, save_and_load_callback: Callable[[str, str], bool]):
        self.gemini_analyzer = gemini_analyzer
        self.save_and_load_callback = save_and_load_callback

    def execute(self, tool_description: str = "", **kwargs: Any) -> str:
        if not tool_description:
            return "Error: `tool_description` cannot be empty."

        logger.info(f"Tool 'create_new_tool' invoked. Generating code for: '{tool_description}'")
        prompt = CREATE_TOOL_PROMPT_TEMPLATE.format(tool_description=tool_description)

        response = self.gemini_analyzer.query_vision_model(prompt=prompt, model_preference=MODEL_PREFERENCE_REASONING)

        if response["status"] != "success" or not response.get("json_content"):
            error_msg = f"Failed to generate tool code. AI response was invalid. Error: {response.get('error_message')}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

        try:
            data = response["json_content"]
            class_name = data["class_name"]
            python_code = data["python_code"]

            # The callback handles saving the file, user confirmation, and reloading the toolbelt.
            success = self.save_and_load_callback(class_name, python_code)

            if success:
                return f"Successfully created and loaded new tool: '{class_name}'. It is now available in the Toolbelt."
            else:
                return "Tool creation was cancelled by the user or failed during loading."
        except (KeyError, TypeError) as e:
            error_msg = f"AI response for tool creation was malformed. Error: {e}"
            logger.error(f"{error_msg}. Response: {response.get('json_content')}")
            return f"Error: {error_msg}"
