"""
Symbiosis module for MARK-I hierarchical AI architecture.

This module contains components for human-AI collaboration and symbiotic intelligence.
It provides natural communication interfaces, trust management, and collaborative
decision-making capabilities.
"""

from .bci_engine import BCIEngine
from .shared_cognitive_workspace import SharedCognitiveWorkspace
from .symbiosis_interface import SymbiosisInterface
from .adaptive_collaboration import AdaptiveCollaborationEngine

__all__ = ['BCIEngine', 'SharedCognitiveWorkspace', 'SymbiosisInterface', 'AdaptiveCollaborationEngine']