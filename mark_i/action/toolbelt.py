"""
Toolbelt for MARK-I hierarchical AI architecture.

This module provides the Toolbelt component that manages tools and their execution,
implementing the IToolbelt interface.
"""

import importlib
import inspect
from typing import Dict, Any, List, Optional, Type

from mark_i.core.base_component import BaseComponent
from mark_i.core.interfaces import IToolbelt
from mark_i.core.architecture_config import ComponentConfig


class Toolbelt(BaseComponent, IToolbelt):
    """
    Manages the collection of tools available to the agent.
    
    Provides tool discovery, registration, execution, and management
    capabilities for the MARK-I system.
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize the Toolbelt."""
        super().__init__("toolbelt", config)
        
        self.tools: Dict[str, Any] = {}
        self.tool_descriptions: Dict[str, str] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
    
    def _initialize_component(self) -> bool:
        """Initialize the Toolbelt component."""
        try:
            # Load default tools
            self._load_default_tools()
            
            self.logger.info(f"Toolbelt initialized with {len(self.tools)} tools")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Toolbelt: {e}")
            return False
    
    def _load_default_tools(self) -> None:
        """Load default tools from the tools directory."""
        try:
            # Import and register built-in tools
            from mark_i.agent.tools import base
            
            # This is a placeholder - in a full implementation, we would
            # dynamically discover and load tools from the tools directory
            self.logger.debug("Default tools loading completed")
            
        except Exception as e:
            self.logger.warning(f"Could not load default tools: {e}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self.tools.keys())
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with given parameters."""
        try:
            if tool_name not in self.tools:
                error_msg = f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
            
            tool = self.tools[tool_name]
            
            # Ensure parameters is a dict
            if not isinstance(parameters, dict):
                parameters = {}
            
            self.logger.info(f"Executing tool '{tool_name}' with parameters: {parameters}")
            
            # Execute the tool
            if hasattr(tool, 'execute'):
                result = tool.execute(**parameters)
            elif callable(tool):
                result = tool(**parameters)
            else:
                result = str(tool)
            
            self.logger.debug(f"Tool '{tool_name}' executed successfully")
            return str(result)
            
        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {e}"
            self.logger.error(error_msg, exc_info=True)
            return f"Error: {error_msg}"
    
    def add_tool(self, tool_name: str, tool_implementation: Any) -> bool:
        """Add a new tool to the toolbelt."""
        try:
            if tool_name in self.tools:
                self.logger.warning(f"Tool '{tool_name}' already exists, replacing")
            
            # Validate tool implementation
            if not self._validate_tool(tool_implementation):
                self.logger.error(f"Invalid tool implementation for '{tool_name}'")
                return False
            
            # Register the tool
            self.tools[tool_name] = tool_implementation
            
            # Extract description and metadata
            description = self._extract_tool_description(tool_implementation)
            self.tool_descriptions[tool_name] = description
            
            metadata = self._extract_tool_metadata(tool_implementation)
            self.tool_metadata[tool_name] = metadata
            
            self.logger.info(f"Tool '{tool_name}' added successfully")
            self._notify_observers({
                'type': 'tool_added',
                'tool_name': tool_name,
                'description': description
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add tool '{tool_name}': {e}")
            return False
    
    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from the toolbelt."""
        try:
            if tool_name not in self.tools:
                self.logger.warning(f"Tool '{tool_name}' not found, cannot remove")
                return False
            
            # Remove tool and associated data
            del self.tools[tool_name]
            self.tool_descriptions.pop(tool_name, None)
            self.tool_metadata.pop(tool_name, None)
            
            self.logger.info(f"Tool '{tool_name}' removed successfully")
            self._notify_observers({
                'type': 'tool_removed',
                'tool_name': tool_name
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove tool '{tool_name}': {e}")
            return False
    
    def get_tool_description(self, tool_name: str) -> str:
        """Get description of a specific tool."""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        return self.tool_descriptions.get(tool_name, "No description available")
    
    def get_tools_description(self) -> str:
        """Get description of all available tools."""
        if not self.tools:
            return "No tools are available."
        
        description = "You have access to the following tools:\n\n"
        
        for tool_name in sorted(self.tools.keys()):
            tool_desc = self.tool_descriptions.get(tool_name, "No description available")
            metadata = self.tool_metadata.get(tool_name, {})
            
            description += f"- **{tool_name}**\n"
            description += f"  Description: {tool_desc}\n"
            
            # Add parameter information if available
            if 'parameters' in metadata:
                params = metadata['parameters']
                if params:
                    description += f"  Parameters: {', '.join(params)}\n"
            
            description += "\n"
        
        return description
    
    def _validate_tool(self, tool_implementation: Any) -> bool:
        """Validate that a tool implementation is valid."""
        try:
            # Check if it's callable or has an execute method
            if not (callable(tool_implementation) or hasattr(tool_implementation, 'execute')):
                return False
            
            # Additional validation could be added here
            return True
            
        except Exception as e:
            self.logger.error(f"Tool validation error: {e}")
            return False
    
    def _extract_tool_description(self, tool_implementation: Any) -> str:
        """Extract description from tool implementation."""
        try:
            # Try to get description from various sources
            if hasattr(tool_implementation, 'description'):
                return str(tool_implementation.description)
            elif hasattr(tool_implementation, '__doc__') and tool_implementation.__doc__:
                return tool_implementation.__doc__.strip()
            elif hasattr(tool_implementation, 'execute') and hasattr(tool_implementation.execute, '__doc__'):
                return tool_implementation.execute.__doc__.strip()
            else:
                return "No description available"
                
        except Exception as e:
            self.logger.warning(f"Could not extract tool description: {e}")
            return "Description extraction failed"
    
    def _extract_tool_metadata(self, tool_implementation: Any) -> Dict[str, Any]:
        """Extract metadata from tool implementation."""
        try:
            metadata = {}
            
            # Extract parameter information
            if hasattr(tool_implementation, 'execute'):
                sig = inspect.signature(tool_implementation.execute)
                parameters = [param for param in sig.parameters.keys() if param != 'self']
                metadata['parameters'] = parameters
            elif callable(tool_implementation):
                sig = inspect.signature(tool_implementation)
                parameters = list(sig.parameters.keys())
                metadata['parameters'] = parameters
            
            # Extract additional metadata if available
            if hasattr(tool_implementation, 'metadata'):
                metadata.update(tool_implementation.metadata)
            
            return metadata
            
        except Exception as e:
            self.logger.warning(f"Could not extract tool metadata: {e}")
            return {}
    
    def get_tool_metadata(self, tool_name: str) -> Dict[str, Any]:
        """Get metadata for a specific tool."""
        return self.tool_metadata.get(tool_name, {})
    
    def list_tools_by_category(self, category: str) -> List[str]:
        """List tools by category."""
        matching_tools = []
        
        for tool_name, metadata in self.tool_metadata.items():
            if metadata.get('category') == category:
                matching_tools.append(tool_name)
        
        return matching_tools
    
    def search_tools(self, query: str) -> List[str]:
        """Search for tools by name or description."""
        query_lower = query.lower()
        matching_tools = []
        
        for tool_name in self.tools.keys():
            # Search in name
            if query_lower in tool_name.lower():
                matching_tools.append(tool_name)
                continue
            
            # Search in description
            description = self.tool_descriptions.get(tool_name, "").lower()
            if query_lower in description:
                matching_tools.append(tool_name)
        
        return matching_tools
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Toolbelt-specific status."""
        return {
            "total_tools": len(self.tools),
            "available_tools": list(self.tools.keys()),
            "tool_categories": self._get_tool_categories(),
        }
    
    def _get_tool_categories(self) -> Dict[str, int]:
        """Get count of tools by category."""
        categories = {}
        
        for metadata in self.tool_metadata.values():
            category = metadata.get('category', 'uncategorized')
            categories[category] = categories.get(category, 0) + 1
        
        return categories