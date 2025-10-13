"""
Knowledge module for MARK-I hierarchical AI architecture.

This module contains knowledge management, discovery, and learning capabilities.
It provides persistent memory, experience storage, and knowledge graph organization.
"""

from .knowledge_base import KnowledgeBase
from .discovery_engine import KnowledgeDiscoveryEngine

__all__ = ['KnowledgeBase', 'KnowledgeDiscoveryEngine']