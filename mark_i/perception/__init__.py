"""
Perception module for MARK-I hierarchical AI architecture.

This module contains components for multi-modal environmental sensing and visual processing.
It provides the "Eye" functionality in the Eye-Brain-Hand paradigm, handling screen capture,
visual analysis, change detection, and perceptual filtering.
"""

from .perception_engine import PerceptionEngine

__all__ = ['PerceptionEngine']