"""
MARK-I Integration Components

Integration components for connecting the profile system to the main MARK-I interface.
"""

from .main_gui_integration import ProfileMenuIntegration, ProfileToolbarIntegration
from .quick_launch import QuickLaunchManager, ProfileShortcuts
from .task_suggestions import AITaskSuggestionEngine
from .profile_widgets import ProfileStatusWidget, QuickExecuteWidget

__all__ = [
    'ProfileMenuIntegration',
    'ProfileToolbarIntegration', 
    'QuickLaunchManager',
    'ProfileShortcuts',
    'AITaskSuggestionEngine',
    'ProfileStatusWidget',
    'QuickExecuteWidget'
]