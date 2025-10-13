"""
Agency module for MARK-I hierarchical AI architecture.

This module contains the Agency Core implementation for strategic and proactive reasoning.
The Agency Core operates at the highest cognitive level, monitoring the environment,
identifying opportunities, and generating strategic suggestions.

Components:
- AgencyCore: Main proactive reasoning and opportunity detection
- StrategicPlanner: Goal decomposition and strategic planning
- PreferenceLearner: User preference learning and adaptation
"""

from .agency_core import AgencyCore
from .strategic_planner import StrategicPlanner
from .preference_learner import PreferenceLearner

__all__ = [
    'AgencyCore',
    'StrategicPlanner', 
    'PreferenceLearner'
]