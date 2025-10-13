"""
Agent module for MARK-I hierarchical AI architecture.

This module contains the Agent Core implementation for tactical execution
using ReAct (Reason+Act+Observe) cognitive loops. The Agent Core handles
direct command execution, goal decomposition, and tool coordination.

Components:
- AgentCore: Legacy agent implementation
- EnhancedAgentCore: New interface-compliant agent with ReAct loops
- AdaptiveAgentCore: Enhanced agent with uncertainty handling and error recovery
- UncertaintyHandler: Comprehensive uncertainty detection and resolution
- ErrorRecoverySystem: Adaptive error recovery with learning capabilities
- Toolbelt: Tool management and execution
- WorldModel: World state tracking and modeling
"""

from .agent_core import AgentCore
from .enhanced_agent_core import EnhancedAgentCore
from .adaptive_agent_core import AdaptiveAgentCore
from .uncertainty_handler import UncertaintyHandler
from .error_recovery import ErrorRecoverySystem
from .toolbelt import Toolbelt
from .world_model import WorldModel

__all__ = [
    'AgentCore',
    'EnhancedAgentCore',
    'AdaptiveAgentCore',
    'UncertaintyHandler',
    'ErrorRecoverySystem',
    'Toolbelt',
    'WorldModel'
]