"""
Core module for MARK-I hierarchical AI architecture.

This module provides the foundational components, interfaces, and configuration
management for the MARK-I system.
"""

# Core interfaces
from .interfaces import (
    # Base interfaces
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
    
    # Knowledge & memory interfaces
    IKnowledgeBase,
    IEnhancedSystemContext,
    
    # Interface layer
    ISymbiosisInterface,
    IEthicalReasoningEngine,
    
    # Extensibility interfaces
    IPlugin,
    IPluginManager,
    
    # Event system
    IEventBus,
    Event,
    
    # Data models
    Context,
    Action,
    Observation,
    Goal,
    ExecutionResult,
    Priority,
    CollaborationStyle,
)

# Architecture configuration
from .architecture_config import (
    ArchitectureConfig,
    ArchitectureConfigManager,
    ComponentConfig,
    AgencyCoreConfig,
    AgentCoreConfig,
    ToolSynthesisConfig,
    PerceptualFilterConfig,
    SelfCorrectionConfig,
    KnowledgeBaseConfig,
    PerceptionEngineConfig,
    ActionExecutorConfig,
    SymbiosisInterfaceConfig,
    EthicalReasoningConfig,
    SystemIntegrationConfig,
    ExtensibilityConfig,
    LogLevel,
    ProcessingMode,
    get_architecture_config,
    get_config_manager,
    update_architecture_config,
    get_component_config,
)

# Base component classes
from .base_component import BaseComponent, ObservableComponent, ProcessingComponent

# Logging setup (safe to import)
from .logging_setup import APP_ROOT_LOGGER_NAME

# Conditional imports for components that require environment setup
try:
    from .config_manager import ConfigManager, load_environment_variables
    from .env_validator import EnvConfig, load_and_validate_env
    _CORE_COMPONENTS_AVAILABLE = True
except ImportError:
    _CORE_COMPONENTS_AVAILABLE = False

# App config imports are optional and only loaded when needed
def get_app_config():
    """Lazy loader for app config to avoid import-time environment requirements."""
    try:
        from .app_config import (
            VALIDATED_CONFIG,
            GEMINI_MODELS_PRO,
            GEMINI_MODELS_FLASH,
            GEMINI_MODELS_NANO,
            MODEL_PREFERENCE_REASONING,
            MODEL_PREFERENCE_FAST,
        )
        return {
            'VALIDATED_CONFIG': VALIDATED_CONFIG,
            'GEMINI_MODELS_PRO': GEMINI_MODELS_PRO,
            'GEMINI_MODELS_FLASH': GEMINI_MODELS_FLASH,
            'GEMINI_MODELS_NANO': GEMINI_MODELS_NANO,
            'MODEL_PREFERENCE_REASONING': MODEL_PREFERENCE_REASONING,
            'MODEL_PREFERENCE_FAST': MODEL_PREFERENCE_FAST,
        }
    except Exception as e:
        raise ImportError(f"App config not available: {e}")

def get_env_validator():
    """Lazy loader for environment validator."""
    if _CORE_COMPONENTS_AVAILABLE:
        return EnvConfig, load_and_validate_env
    else:
        raise ImportError("Environment validator not available")

def get_config_manager():
    """Lazy loader for config manager."""
    if _CORE_COMPONENTS_AVAILABLE:
        return ConfigManager, load_environment_variables
    else:
        raise ImportError("Config manager not available")

__all__ = [
    # Interfaces
    'IComponent',
    'IConfigurable',
    'IObservable',
    'IAgencyCore',
    'IAgentCore',
    'IStrategicExecutor',
    'IProcessingEngine',
    'IToolSynthesisEngine',
    'IPerceptualFilter',
    'ISelfCorrectionEngine',
    'IPerceptionEngine',
    'ICaptureEngine',
    'IActionExecutor',
    'IToolbelt',
    'IWorldModel',
    'IKnowledgeBase',
    'IEnhancedSystemContext',
    'ISymbiosisInterface',
    'IEthicalReasoningEngine',
    'IPlugin',
    'IPluginManager',
    'IEventBus',
    
    # Data models
    'Event',
    'Context',
    'Action',
    'Observation',
    'Goal',
    'ExecutionResult',
    'Priority',
    'CollaborationStyle',
    
    # Architecture configuration
    'ArchitectureConfig',
    'ArchitectureConfigManager',
    'ComponentConfig',
    'AgencyCoreConfig',
    'AgentCoreConfig',
    'ToolSynthesisConfig',
    'PerceptualFilterConfig',
    'SelfCorrectionConfig',
    'KnowledgeBaseConfig',
    'PerceptionEngineConfig',
    'ActionExecutorConfig',
    'SymbiosisInterfaceConfig',
    'EthicalReasoningConfig',
    'SystemIntegrationConfig',
    'ExtensibilityConfig',
    'LogLevel',
    'ProcessingMode',
    'get_architecture_config',
    'get_config_manager',
    'update_architecture_config',
    'get_component_config',
    
    # Base component classes
    'BaseComponent',
    'ObservableComponent',
    'ProcessingComponent',
    
    # Logging
    'APP_ROOT_LOGGER_NAME',
    
    # Lazy loaders for optional components
    'get_app_config',
    'get_env_validator',
    'get_config_manager',
]