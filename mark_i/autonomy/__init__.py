"""
Autonomy module for MARK-I hierarchical AI architecture.

This module contains the autonomous operation engine that coordinates
between different cognitive layers and manages system-wide autonomous behavior.
"""

from .engine import AutonomyEngine
from .self_correction_engine import SelfCorrectionEngine

__all__ = ['AutonomyEngine', 'SelfCorrectionEngine']