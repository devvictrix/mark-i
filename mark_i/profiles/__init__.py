"""
MARK-I Profile Automation System

This module provides comprehensive automation profile management for MARK-I,
enabling users to create, manage, and execute intelligent automation workflows
through visual interfaces and rule-based systems.
"""

from .models.profile import AutomationProfile
from .models.region import Region
from .models.rule import Rule, Condition, Action
from .profile_manager import ProfileManager

__all__ = [
    'AutomationProfile',
    'Region', 
    'Rule',
    'Condition',
    'Action',
    'ProfileManager'
]