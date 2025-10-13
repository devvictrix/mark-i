"""
MARK-I: Advanced AI-powered visual automation agent.

MARK-I implements a sophisticated hierarchical AI architecture that combines strategic reasoning,
tactical execution, and specialized processing engines. The system operates as a symbiotic
intelligence platform that can proactively assist users, learn from experiences, and
continuously expand its capabilities through self-improvement mechanisms.

Architecture Overview:
- Agency Core: Strategic/proactive reasoning and opportunity detection
- Agent Core: Tactical execution using ReAct cognitive loops
- Processing Engines: Specialized engines for tool synthesis, perceptual filtering, etc.
- Action Layer: GUI interaction, tool management, and world state tracking
- Perception Layer: Multi-modal environmental sensing and visual processing
- Knowledge Layer: Learning, memory, and experience storage
- Interface Layer: Human-AI collaboration and communication

Version: 1.0.0
"""

# Core interfaces and base classes
from mark_i.core.interfaces import (
    # Core interfaces
    IComponent,
    IConfigurable,
    IObservable,
    
    # Cognitive layer interfaces
    IAgencyCore,
    IAgentCore,
    IStrategicExecutor,
    
    # Processing engine interfaces
    IProcessingEngine,
    IToolSynthesisEngine,
    IPerceptualFilter,
    ISelfCorrectionEngine,
    
    # Perception layer interfaces
    IPerceptionEngine,
    ICaptureEngine,
    
    # Action layer interfaces
    IActionExecutor,
    IToolbelt,
    IWorldModel,
    
    # Knowledge layer interfaces
    IKnowledgeBase,
    IEnhancedSystemContext,
    
    # Interface layer
    ISymbiosisInterface,
    IEthicalReasoningEngine,
    
    # Extensibility interfaces
    IPlugin,
    IPluginManager,
    IEventBus,
    
    # Data models
    Context,
    Action,
    Observation,
    Goal,
    ExecutionResult,
    Event,
    Priority,
    CollaborationStyle,
)

from mark_i.core.base_component import (
    BaseComponent,
    ObservableComponent,
    ProcessingComponent,
)

from mark_i.core.architecture_config import (
    ArchitectureConfig,
    ArchitectureConfigManager,
    # Note: get_architecture_config and related functions require environment setup
)

# Action layer components
from mark_i.action import (
    ActionExecutor,
    Toolbelt,
    WorldModel,
)

# Utility functions for safe configuration access
def get_architecture_config():
    """
    Get architecture configuration (requires environment setup).
    
    Raises:
        ImportError: If environment is not properly configured
    """
    try:
        from mark_i.core.architecture_config import get_architecture_config as _get_config
        return _get_config()
    except Exception as e:
        raise ImportError(f"Architecture config not available: {e}")

def get_app_config():
    """
    Get application configuration (requires environment setup).
    
    Raises:
        ImportError: If environment is not properly configured
    """
    from mark_i.core import get_app_config as _get_app_config
    return _get_app_config()

__version__ = "1.0.0"
__author__ = "MARK-I Development Team"

__all__ = [
    # Core interfaces
    "IComponent",
    "IConfigurable", 
    "IObservable",
    "IAgencyCore",
    "IAgentCore",
    "IStrategicExecutor",
    "IProcessingEngine",
    "IToolSynthesisEngine",
    "IPerceptualFilter",
    "ISelfCorrectionEngine",
    "IPerceptionEngine",
    "ICaptureEngine",
    "IActionExecutor",
    "IToolbelt",
    "IWorldModel",
    "IKnowledgeBase",
    "IEnhancedSystemContext",
    "ISymbiosisInterface",
    "IEthicalReasoningEngine",
    "IPlugin",
    "IPluginManager",
    "IEventBus",
    
    # Data models
    "Context",
    "Action",
    "Observation",
    "Goal",
    "ExecutionResult",
    "Event",
    "Priority",
    "CollaborationStyle",
    
    # Base components
    "BaseComponent",
    "ObservableComponent",
    "ProcessingComponent",
    
    # Configuration
    "ArchitectureConfig",
    "ArchitectureConfigManager",
    
    # Action layer
    "ActionExecutor",
    "Toolbelt",
    "WorldModel",
    
    # Utility functions
    "get_architecture_config",
    "get_app_config",
]