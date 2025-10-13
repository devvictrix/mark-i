"""
Architecture configuration management for MARK-I hierarchical AI system.

This module provides configuration management specifically for the core architecture
components, including cognitive layers, processing engines, and system-wide settings.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, asdict, field
from enum import Enum

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
from mark_i.core.interfaces import Priority, CollaborationStyle

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.core.architecture_config")


class LogLevel(Enum):
    """Logging levels for components."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProcessingMode(Enum):
    """Processing modes for different components."""
    FAST = "fast"
    BALANCED = "balanced"
    THOROUGH = "thorough"
    ADAPTIVE = "adaptive"


@dataclass
class ComponentConfig:
    """Base configuration for all components."""
    enabled: bool = True
    log_level: LogLevel = LogLevel.INFO
    max_retries: int = 3
    timeout_seconds: float = 30.0
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgencyCoreConfig(ComponentConfig):
    """Configuration for Agency Core (Strategic/Proactive)."""
    monitoring_interval_seconds: float = 5.0
    opportunity_threshold: float = 0.7
    suggestion_cooldown_seconds: float = 30.0
    max_concurrent_suggestions: int = 3
    learning_rate: float = 0.1
    strategic_planning_depth: int = 5
    proactive_mode: bool = True
    user_interruption_threshold: float = 0.8


@dataclass
class AgentCoreConfig(ComponentConfig):
    """Configuration for Agent Core (Tactical/Reactive)."""
    max_react_steps: int = 15
    uncertainty_threshold: float = 0.5
    action_confidence_threshold: float = 0.6
    observation_timeout_seconds: float = 10.0
    tool_selection_strategy: str = "confidence_based"
    error_recovery_attempts: int = 3
    context_window_size: int = 10
    adaptive_strategy_adjustment: bool = True


@dataclass
class ToolSynthesisConfig(ComponentConfig):
    """Configuration for Tool Synthesis Engine."""
    capability_gap_threshold: float = 0.8
    code_generation_model: str = "gemini-1.5-pro"
    security_validation_level: str = "strict"
    sandbox_timeout_seconds: float = 60.0
    max_tool_complexity: int = 100
    auto_integration: bool = False
    validation_tests_required: bool = True


@dataclass
class PerceptualFilterConfig(ComponentConfig):
    """Configuration for Perceptual Filter."""
    attention_window_size: int = 5
    focus_adaptation_rate: float = 0.2
    noise_threshold: float = 0.3
    processing_optimization: bool = True
    ignore_pattern_learning: bool = True
    context_awareness_depth: int = 3
    efficiency_target: float = 0.85


@dataclass
class SelfCorrectionConfig(ComponentConfig):
    """Configuration for Self-Correction Engine."""
    failure_detection_sensitivity: float = 0.7
    strategy_generation_count: int = 3
    viability_threshold: float = 0.6
    learning_integration: bool = True
    correction_history_size: int = 50
    adaptive_threshold_adjustment: bool = True


@dataclass
class KnowledgeBaseConfig(ComponentConfig):
    """Configuration for Knowledge Base."""
    max_experiences: int = 10000
    similarity_threshold: float = 0.75
    knowledge_consolidation_interval: int = 100
    user_preference_weight: float = 0.8
    application_learning: bool = True
    knowledge_graph_depth: int = 5
    auto_cleanup: bool = True
    backup_interval_hours: int = 24


@dataclass
class PerceptionEngineConfig(ComponentConfig):
    """Configuration for Perception Engine."""
    capture_interval_ms: int = 100
    change_detection_threshold: float = 0.1
    visual_analysis_depth: ProcessingMode = ProcessingMode.BALANCED
    text_extraction: bool = True
    multi_modal_fusion: bool = True
    preprocessing_enabled: bool = True


@dataclass
class ActionExecutorConfig(ComponentConfig):
    """Configuration for Action Executor."""
    action_delay_ms: int = 50
    verification_enabled: bool = True
    safety_checks: bool = True
    coordinate_precision: int = 1
    input_simulation_mode: str = "native"
    error_recovery: bool = True


@dataclass
class SymbiosisInterfaceConfig(ComponentConfig):
    """Configuration for Symbiosis Interface."""
    communication_style: CollaborationStyle = CollaborationStyle.COLLABORATIVE
    response_timeout_seconds: float = 30.0
    trust_decay_rate: float = 0.05
    autonomy_adjustment_rate: float = 0.1
    user_feedback_weight: float = 0.9
    clarification_threshold: float = 0.6
    permission_required_actions: List[str] = field(default_factory=lambda: ["system_modification", "file_deletion", "network_access"])


@dataclass
class EthicalReasoningConfig(ComponentConfig):
    """Configuration for Ethical Reasoning Engine."""
    risk_assessment_model: str = "conservative"
    ethical_framework: str = "utilitarian_with_constraints"
    user_safety_priority: float = 1.0
    alternative_generation_count: int = 3
    ethical_logging: bool = True
    guideline_update_frequency: str = "weekly"


@dataclass
class SystemIntegrationConfig(ComponentConfig):
    """Configuration for system-wide integration."""
    event_bus_enabled: bool = True
    inter_component_timeout: float = 5.0
    health_check_interval: int = 60
    performance_monitoring: bool = True
    auto_scaling: bool = False
    failover_enabled: bool = True
    coordination_strategy: str = "hierarchical"


@dataclass
class ExtensibilityConfig(ComponentConfig):
    """Configuration for extensibility framework."""
    plugin_system_enabled: bool = True
    plugin_security_level: str = "strict"
    plugin_timeout_seconds: float = 30.0
    max_concurrent_plugins: int = 10
    plugin_resource_limits: Dict[str, Any] = field(default_factory=lambda: {
        "memory_mb": 512,
        "cpu_percent": 10,
        "disk_mb": 100
    })
    auto_update_plugins: bool = False


@dataclass
class ArchitectureConfig:
    """Complete architecture configuration."""
    # Core cognitive components
    agency_core: AgencyCoreConfig = field(default_factory=AgencyCoreConfig)
    agent_core: AgentCoreConfig = field(default_factory=AgentCoreConfig)
    
    # Processing engines
    tool_synthesis: ToolSynthesisConfig = field(default_factory=ToolSynthesisConfig)
    perceptual_filter: PerceptualFilterConfig = field(default_factory=PerceptualFilterConfig)
    self_correction: SelfCorrectionConfig = field(default_factory=SelfCorrectionConfig)
    ethical_reasoning: EthicalReasoningConfig = field(default_factory=EthicalReasoningConfig)
    
    # Perception and action
    perception_engine: PerceptionEngineConfig = field(default_factory=PerceptionEngineConfig)
    action_executor: ActionExecutorConfig = field(default_factory=ActionExecutorConfig)
    
    # Knowledge and memory
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
    
    # Interface and collaboration
    symbiosis_interface: SymbiosisInterfaceConfig = field(default_factory=SymbiosisInterfaceConfig)
    
    # System-wide settings
    system_integration: SystemIntegrationConfig = field(default_factory=SystemIntegrationConfig)
    extensibility: ExtensibilityConfig = field(default_factory=ExtensibilityConfig)
    
    # Global settings
    global_log_level: LogLevel = LogLevel.INFO
    debug_mode: bool = False
    performance_profiling: bool = False
    telemetry_enabled: bool = True
    config_version: str = "1.0.0"


class ArchitectureConfigManager:
    """Manages architecture configuration loading, validation, and saving."""
    
    DEFAULT_CONFIG_FILENAME = "architecture_config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the architecture configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = ArchitectureConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Find project root
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        package_dir = os.path.dirname(current_file_dir)
        project_root = os.path.dirname(package_dir)
        
        # Create .kiro directory if it doesn't exist
        kiro_dir = os.path.join(project_root, ".kiro")
        os.makedirs(kiro_dir, exist_ok=True)
        
        return os.path.join(kiro_dir, self.DEFAULT_CONFIG_FILENAME)
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            logger.info(f"Configuration file not found at {self.config_path}. Using default configuration.")
            self._save_config()  # Save default config
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate and merge with defaults
            self.config = self._merge_with_defaults(config_data)
            logger.info(f"Architecture configuration loaded from {self.config_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {self.config_path}: {e}")
            logger.info("Using default configuration.")
        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            logger.info("Using default configuration.")
    
    def _merge_with_defaults(self, config_data: Dict[str, Any]) -> ArchitectureConfig:
        """Merge loaded configuration with defaults."""
        default_config = ArchitectureConfig()
        
        # Convert to dict for easier manipulation
        default_dict = asdict(default_config)
        
        # Recursively merge configurations
        merged_dict = self._deep_merge(default_dict, config_data)
        
        # Convert back to dataclass
        return self._dict_to_config(merged_dict)
    
    def _deep_merge(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries."""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> ArchitectureConfig:
        """Convert dictionary to ArchitectureConfig dataclass."""
        try:
            # Handle enum conversions
            if 'global_log_level' in config_dict:
                if isinstance(config_dict['global_log_level'], str):
                    config_dict['global_log_level'] = LogLevel(config_dict['global_log_level'])
            
            # Handle nested component configs
            component_configs = {
                'agency_core': AgencyCoreConfig,
                'agent_core': AgentCoreConfig,
                'tool_synthesis': ToolSynthesisConfig,
                'perceptual_filter': PerceptualFilterConfig,
                'self_correction': SelfCorrectionConfig,
                'ethical_reasoning': EthicalReasoningConfig,
                'perception_engine': PerceptionEngineConfig,
                'action_executor': ActionExecutorConfig,
                'knowledge_base': KnowledgeBaseConfig,
                'symbiosis_interface': SymbiosisInterfaceConfig,
                'system_integration': SystemIntegrationConfig,
                'extensibility': ExtensibilityConfig,
            }
            
            for component_name, config_class in component_configs.items():
                if component_name in config_dict and isinstance(config_dict[component_name], dict):
                    component_dict = config_dict[component_name]
                    
                    # Handle enum conversions for component configs
                    if 'log_level' in component_dict and isinstance(component_dict['log_level'], str):
                        component_dict['log_level'] = LogLevel(component_dict['log_level'])
                    
                    # Special handling for specific component enums
                    if component_name == 'perception_engine' and 'visual_analysis_depth' in component_dict:
                        if isinstance(component_dict['visual_analysis_depth'], str):
                            component_dict['visual_analysis_depth'] = ProcessingMode(component_dict['visual_analysis_depth'])
                    
                    if component_name == 'symbiosis_interface' and 'communication_style' in component_dict:
                        if isinstance(component_dict['communication_style'], str):
                            component_dict['communication_style'] = CollaborationStyle(component_dict['communication_style'])
                    
                    config_dict[component_name] = config_class(**component_dict)
            
            return ArchitectureConfig(**config_dict)
            
        except Exception as e:
            logger.error(f"Failed to convert dictionary to ArchitectureConfig: {e}")
            logger.info("Using default configuration.")
            return ArchitectureConfig()
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Convert to dictionary with enum handling
            config_dict = self._config_to_dict(self.config)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Architecture configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {self.config_path}: {e}")
    
    def _config_to_dict(self, config: ArchitectureConfig) -> Dict[str, Any]:
        """Convert ArchitectureConfig to dictionary with proper enum handling."""
        config_dict = asdict(config)
        
        # Convert enums to strings
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            else:
                return obj
        
        return convert_enums(config_dict)
    
    def get_config(self) -> ArchitectureConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        try:
            # Convert current config to dict
            current_dict = asdict(self.config)
            
            # Merge updates
            merged_dict = self._deep_merge(current_dict, updates)
            
            # Convert back to config
            self.config = self._dict_to_config(merged_dict)
            
            # Save updated config
            self._save_config()
            
            logger.info("Architecture configuration updated successfully.")
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
    
    def get_component_config(self, component_name: str) -> Optional[ComponentConfig]:
        """Get configuration for a specific component."""
        return getattr(self.config, component_name, None)
    
    def update_component_config(self, component_name: str, config_updates: Dict[str, Any]) -> None:
        """Update configuration for a specific component."""
        if not hasattr(self.config, component_name):
            logger.error(f"Unknown component: {component_name}")
            return
        
        try:
            current_component_config = getattr(self.config, component_name)
            current_dict = asdict(current_component_config)
            
            # Merge updates
            merged_dict = self._deep_merge(current_dict, config_updates)
            
            # Get the component config class
            config_class = type(current_component_config)
            
            # Handle enum conversions
            if 'log_level' in merged_dict and isinstance(merged_dict['log_level'], str):
                merged_dict['log_level'] = LogLevel(merged_dict['log_level'])
            
            # Create new config instance
            new_config = config_class(**merged_dict)
            
            # Update the main config
            setattr(self.config, component_name, new_config)
            
            # Save updated config
            self._save_config()
            
            logger.info(f"Configuration for {component_name} updated successfully.")
            
        except Exception as e:
            logger.error(f"Failed to update configuration for {component_name}: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return list of issues."""
        issues = []
        
        # Validate global settings
        if self.config.config_version != "1.0.0":
            issues.append(f"Unsupported config version: {self.config.config_version}")
        
        # Validate component configurations
        components = [
            ('agency_core', self.config.agency_core),
            ('agent_core', self.config.agent_core),
            ('tool_synthesis', self.config.tool_synthesis),
            ('perceptual_filter', self.config.perceptual_filter),
            ('self_correction', self.config.self_correction),
            ('ethical_reasoning', self.config.ethical_reasoning),
            ('perception_engine', self.config.perception_engine),
            ('action_executor', self.config.action_executor),
            ('knowledge_base', self.config.knowledge_base),
            ('symbiosis_interface', self.config.symbiosis_interface),
            ('system_integration', self.config.system_integration),
            ('extensibility', self.config.extensibility),
        ]
        
        for component_name, component_config in components:
            component_issues = self._validate_component_config(component_name, component_config)
            issues.extend(component_issues)
        
        return issues
    
    def _validate_component_config(self, component_name: str, config: ComponentConfig) -> List[str]:
        """Validate a specific component configuration."""
        issues = []
        
        # Common validations
        if config.timeout_seconds <= 0:
            issues.append(f"{component_name}: timeout_seconds must be positive")
        
        if config.max_retries < 0:
            issues.append(f"{component_name}: max_retries cannot be negative")
        
        # Component-specific validations
        if isinstance(config, AgencyCoreConfig):
            if config.monitoring_interval_seconds <= 0:
                issues.append(f"{component_name}: monitoring_interval_seconds must be positive")
            if not 0 <= config.opportunity_threshold <= 1:
                issues.append(f"{component_name}: opportunity_threshold must be between 0 and 1")
        
        elif isinstance(config, AgentCoreConfig):
            if config.max_react_steps <= 0:
                issues.append(f"{component_name}: max_react_steps must be positive")
            if not 0 <= config.uncertainty_threshold <= 1:
                issues.append(f"{component_name}: uncertainty_threshold must be between 0 and 1")
        
        elif isinstance(config, KnowledgeBaseConfig):
            if config.max_experiences <= 0:
                issues.append(f"{component_name}: max_experiences must be positive")
            if not 0 <= config.similarity_threshold <= 1:
                issues.append(f"{component_name}: similarity_threshold must be between 0 and 1")
        
        return issues
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = ArchitectureConfig()
        self._save_config()
        logger.info("Architecture configuration reset to defaults.")
    
    def export_config(self, export_path: str) -> None:
        """Export current configuration to a file."""
        try:
            config_dict = self._config_to_dict(self.config)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to {export_path}")
            
        except Exception as e:
            logger.error(f"Failed to export configuration to {export_path}: {e}")
    
    def import_config(self, import_path: str) -> None:
        """Import configuration from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.config = self._merge_with_defaults(config_data)
            self._save_config()
            
            logger.info(f"Configuration imported from {import_path}")
            
        except Exception as e:
            logger.error(f"Failed to import configuration from {import_path}: {e}")


# Global configuration manager instance
_config_manager: Optional[ArchitectureConfigManager] = None


def get_architecture_config() -> ArchitectureConfig:
    """Get the global architecture configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ArchitectureConfigManager()
    return _config_manager.get_config()


def get_config_manager() -> ArchitectureConfigManager:
    """Get the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ArchitectureConfigManager()
    return _config_manager


def update_architecture_config(updates: Dict[str, Any]) -> None:
    """Update the global architecture configuration."""
    get_config_manager().update_config(updates)


def get_component_config(component_name: str) -> Optional[ComponentConfig]:
    """Get configuration for a specific component."""
    return get_config_manager().get_component_config(component_name)