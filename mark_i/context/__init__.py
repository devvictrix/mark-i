"""
MARK-I Context Collection System

This module provides comprehensive system context awareness including:
- Hardware specifications and performance monitoring
- Application discovery and usage tracking
- Network connectivity and configuration
- UI context and window management
- User environment and behavior patterns
- Enhanced system context integration
- Environment monitoring and change detection
- Context-driven optimization and adaptation
"""

from .context_manager import ContextManager
from .collectors.base_collector import BaseCollector
from .ai_integration import AIContextProvider, get_ai_context_provider
from .enhanced_context_engine import EnhancedContextEngine
from .system_context_integration import SystemContextIntegration
from .environment_monitor import EnvironmentMonitor
from .context_driven_optimizer import ContextDrivenOptimizer
from .adaptive_decision_engine import AdaptiveDecisionEngine
from .context_history_tracker import ContextHistoryTracker

__all__ = [
    'ContextManager',
    'BaseCollector',
    'AIContextProvider',
    'get_ai_context_provider',
    'EnhancedContextEngine',
    'SystemContextIntegration',
    'EnvironmentMonitor',
    'ContextDrivenOptimizer',
    'AdaptiveDecisionEngine',
    'ContextHistoryTracker'
]