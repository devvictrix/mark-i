"""
Profile Widgets

Embeddable widgets for the main MARK-I interface including status displays,
quick execute controls, and profile suggestions.
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Optional, Callable, Dict, Any
import logging
from datetime import datetime

from ..models.profile import AutomationProfile
from ..profile_manager import ProfileManager
from ..execution.execution_engine import ExecutionEngine, ExecutionState
from .task_suggestions import AITaskSuggestionEngine, TaskSuggestion


class ProfileStatusWidget(ctk.CTkFrame):
    """Widget showing current profile execution status"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.logger = logging.getLogger("mark_i.profiles.integration.status_widget")
        
        # Components
        self.execution_engine = ExecutionEngine()
        
        # State
        self.current_executions: Dict[str, Dict[str, Any]] = {}
        
        self._create_widgets()
        self._setup_layout()
        self._start_status_updates()
        
        self.logger.info("ProfileStatusWidget initialized")
    
    def _create_widgets(self):
        """Create status widgets"""
        # Header
        self.header_label = ctk.CTkLabel(
            self, text="Profile Status",
            font=("Arial", 12, "bold")
        )
        
        # Status indicators
        self.status_frame = ctk.CTkFrame(self)
        
        # Queue status
        self.queue_label = ctk.CTkLabel(
            self.status_frame, text="Queue: 0",
            font=("Arial", 10)
        )
        
        # Active executions
        self.active_label = ctk.CTkLabel(
            self.status_frame, text="Active: 0",
            font=("Arial", 10)
        )
        
        # Overall status indicator
        self.status_indicator = ctk.CTkLabel(
            self.status_frame, text="●",
            text_color="gray",
            font=("Arial", 14)
        )
        
        # Current execution info
        self.current_execution_label = ctk.CTkLabel(
            self, text="No active executions",
            font=("Arial", 9),
            text_color="gray"
        )
    
    def _setup_layout(self):
        """Setup widget layout"""
        self.header_label.pack(pady=(5, 2))
        
        self.status_frame.pack(fill="x", padx=5, pady=2)
        
        self.queue_label.pack(side="left", padx=2)
        self.active_label.pack(side="left", padx=2)
        self.status_indicator.pack(side="right", padx=2)
        
        self.current_execution_label.pack(pady=(2, 5))
    
    def _start_status_updates(self):
        """Start periodic status updates"""
        self._update_status()
        self.after(2000, self._start_status_updates)  # Update every 2 seconds
    
    def _update_status(self):
        """Update status display"""
        try:
            # Get queue status from execution engine
            queue_status = self.execution_engine.get_queue_status()
            
            # Update labels
            self.queue_label.configure(text=f"Queue: {queue_status['queue_length']}")
            self.active_label.configure(text=f"Active: {queue_status['active_executions']}")
            
            # Update status indicator
            if queue_status['active_executions'] > 0:
                self.status_indicator.configure(text_color="green")
                
                # Show current execution info
                active_profiles = queue_status.get('active_profiles', [])
                if active_profiles:
                    current = active_profiles[0]
                    self.current_execution_label.configure(
                        text=f"Running: {current['profile_name']}"
                    )
            elif queue_status['queue_length'] > 0:
                self.status_indicator.configure(text_color="yellow")
                self.current_execution_label.configure(text="Profiles queued")
            else:
                self.status_indicator.configure(text_color="gray")
                self.current_execution_label.configure(text="No active executions")
                
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")


class QuickExecuteWidget(ctk.CTkFrame):
    """Widget for quick profile execution"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.logger = logging.getLogger("mark_i.profiles.integration.quick_execute_widget")
        
        # Components
        self.profile_manager = ProfileManager()
        self.execution_engine = ExecutionEngine()
        
        # State
        self.selected_profile: Optional[AutomationProfile] = None
        
        # Callbacks
        self.on_profile_executed: Optional[Callable[[AutomationProfile], None]] = None
        
        self._create_widgets()
        self._setup_layout()
        self._load_profiles()
        
        self.logger.info("QuickExecuteWidget initialized")
    
    def _create_widgets(self):
        """Create quick execute widgets"""
        # Header
        self.header_label = ctk.CTkLabel(
            self, text="Quick Execute",
            font=("Arial", 12, "bold")
        )
        
        # Profile selection
        self.profile_combo = ctk.CTkComboBox(
            self, values=["Loading..."],
            command=self._on_profile_selected,
            width=200
        )
        
        # Execute button
        self.execute_btn = ctk.CTkButton(
            self, text="▶ Execute",
            command=self._execute_profile,
            width=100,
            state="disabled"
        )
        
        # Mode selection
        self.mode_combo = ctk.CTkComboBox(
            self, values=["Normal", "Debug", "Simulation"],
            width=100
        )
        self.mode_combo.set("Normal")
    
    def _setup_layout(self):
        """Setup widget layout"""
        self.header_label.pack(pady=(5, 2))
        self.profile_combo.pack(pady=2, padx=5, fill="x")
        
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(fill="x", padx=5, pady=2)
        
        self.mode_combo.pack(in_=controls_frame, side="left", padx=2)
        self.execute_btn.pack(in_=controls_frame, side="right", padx=2)
    
    def _load_profiles(self):
        """Load available profiles"""
        try:
            profiles = self.profile_manager.get_quick_execute_profiles()
            
            if profiles:
                profile_names = [profile.name for profile in profiles]
                self.profile_combo.configure(values=profile_names)
                self.profile_combo.set("Select Profile...")
            else:
                self.profile_combo.configure(values=["No profiles available"])
                self.profile_combo.set("No profiles available")
                
        except Exception as e:
            self.logger.error(f"Failed to load profiles: {e}")
            self.profile_combo.configure(values=["Error loading profiles"])
    
    def _on_profile_selected(self, profile_name: str):
        """Handle profile selection"""
        try:
            if profile_name in ["Select Profile...", "No profiles available", "Error loading profiles"]:
                self.selected_profile = None
                self.execute_btn.configure(state="disabled")
                return
            
            # Find selected profile
            self.selected_profile = self.profile_manager.get_profile_by_name(profile_name)
            
            if self.selected_profile:
                self.execute_btn.configure(state="normal")
            else:
                self.execute_btn.configure(state="disabled")
                
        except Exception as e:
            self.logger.error(f"Failed to handle profile selection: {e}")
    
    def _execute_profile(self):
        """Execute selected profile"""
        try:
            if not self.selected_profile:
                return
            
            # Get execution mode
            mode_map = {
                "Normal": "normal",
                "Debug": "debug", 
                "Simulation": "simulation"
            }
            mode_name = mode_map.get(self.mode_combo.get(), "normal")
            
            # Execute profile
            execution_id = self.execution_engine.execute_profile(
                self.selected_profile,
                mode=ExecutionMode(mode_name)
            )
            
            # Callback
            if self.on_profile_executed:
                self.on_profile_executed(self.selected_profile)
            
            self.logger.info(f"Quick executed profile: {self.selected_profile.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to execute profile: {e}")
    
    def refresh_profiles(self):
        """Refresh profile list"""
        self._load_profiles()


class TaskSuggestionsWidget(ctk.CTkFrame):
    """Widget showing AI-powered task suggestions"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.logger = logging.getLogger("mark_i.profiles.integration.suggestions_widget")
        
        # Components
        self.suggestion_engine = AITaskSuggestionEngine()
        
        # State
        self.suggestions: List[TaskSuggestion] = []
        self.current_suggestion_index = 0
        
        # Callbacks
        self.on_suggestion_accepted: Optional[Callable[[TaskSuggestion], None]] = None
        
        self._create_widgets()
        self._setup_layout()
        self._load_suggestions()
        
        self.logger.info("TaskSuggestionsWidget initialized")
    
    def _create_widgets(self):
        """Create suggestion widgets"""
        # Header
        self.header_label = ctk.CTkLabel(
            self, text="AI Suggestions",
            font=("Arial", 12, "bold")
        )
        
        # Suggestion display
        self.suggestion_frame = ctk.CTkFrame(self)
        
        self.suggestion_title = ctk.CTkLabel(
            self.suggestion_frame, text="No suggestions",
            font=("Arial", 11, "bold")
        )
        
        self.suggestion_description = ctk.CTkLabel(
            self.suggestion_frame, text="",
            font=("Arial", 9),
            wraplength=250
        )
        
        self.confidence_label = ctk.CTkLabel(
            self.suggestion_frame, text="",
            font=("Arial", 8),
            text_color="gray"
        )
        
        # Navigation and action buttons
        self.controls_frame = ctk.CTkFrame(self)
        
        self.prev_btn = ctk.CTkButton(
            self.controls_frame, text="◀",
            width=30, command=self._previous_suggestion
        )
        
        self.next_btn = ctk.CTkButton(
            self.controls_frame, text="▶",
            width=30, command=self._next_suggestion
        )
        
        self.accept_btn = ctk.CTkButton(
            self.controls_frame, text="Accept",
            width=60, command=self._accept_suggestion
        )
        
        self.dismiss_btn = ctk.CTkButton(
            self.controls_frame, text="Dismiss",
            width=60, command=self._dismiss_suggestion
        )
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self, text="🔄 Refresh",
            width=80, command=self._refresh_suggestions
        )
    
    def _setup_layout(self):
        """Setup widget layout"""
        self.header_label.pack(pady=(5, 2))
        
        self.suggestion_frame.pack(fill="x", padx=5, pady=2)
        
        self.suggestion_title.pack(pady=2)
        self.suggestion_description.pack(pady=2)
        self.confidence_label.pack(pady=2)
        
        self.controls_frame.pack(fill="x", padx=5, pady=2)
        
        self.prev_btn.pack(side="left", padx=1)
        self.next_btn.pack(side="left", padx=1)
        self.accept_btn.pack(side="right", padx=1)
        self.dismiss_btn.pack(side="right", padx=1)
        
        self.refresh_btn.pack(pady=(2, 5))
    
    def _load_suggestions(self):
        """Load AI suggestions"""
        try:
            self.suggestions = self.suggestion_engine.generate_suggestions()
            self.current_suggestion_index = 0
            self._update_suggestion_display()
            
        except Exception as e:
            self.logger.error(f"Failed to load suggestions: {e}")
    
    def _update_suggestion_display(self):
        """Update suggestion display"""
        if not self.suggestions:
            self.suggestion_title.configure(text="No suggestions")
            self.suggestion_description.configure(text="Check back later for AI-powered suggestions")
            self.confidence_label.configure(text="")
            self._update_button_states(False)
            return
        
        # Get current suggestion
        suggestion = self.suggestions[self.current_suggestion_index]
        
        # Update display
        self.suggestion_title.configure(text=suggestion.title)
        self.suggestion_description.configure(text=suggestion.description)
        self.confidence_label.configure(
            text=f"Confidence: {suggestion.confidence:.0%} | {self.current_suggestion_index + 1}/{len(self.suggestions)}"
        )
        
        self._update_button_states(True)
    
    def _update_button_states(self, has_suggestions: bool):
        """Update button states"""
        state = "normal" if has_suggestions else "disabled"
        
        self.prev_btn.configure(state=state)
        self.next_btn.configure(state=state)
        self.accept_btn.configure(state=state)
        self.dismiss_btn.configure(state=state)
    
    def _previous_suggestion(self):
        """Show previous suggestion"""
        if self.suggestions:
            self.current_suggestion_index = (self.current_suggestion_index - 1) % len(self.suggestions)
            self._update_suggestion_display()
    
    def _next_suggestion(self):
        """Show next suggestion"""
        if self.suggestions:
            self.current_suggestion_index = (self.current_suggestion_index + 1) % len(self.suggestions)
            self._update_suggestion_display()
    
    def _accept_suggestion(self):
        """Accept current suggestion"""
        if not self.suggestions:
            return
        
        suggestion = self.suggestions[self.current_suggestion_index]
        
        try:
            # Handle different suggestion types
            if suggestion.suggestion_type == "profile" and suggestion.profile_id:
                # Execute suggested profile
                profile = ProfileManager().get_profile(suggestion.profile_id)
                if profile:
                    self.execution_engine.execute_profile(profile)
            elif suggestion.suggestion_type == "template":
                # Create profile from template
                # This would open template creation dialog
                pass
            
            # Callback
            if self.on_suggestion_accepted:
                self.on_suggestion_accepted(suggestion)
            
            # Remove accepted suggestion
            self.suggestions.pop(self.current_suggestion_index)
            if self.current_suggestion_index >= len(self.suggestions):
                self.current_suggestion_index = 0
            
            self._update_suggestion_display()
            
        except Exception as e:
            self.logger.error(f"Failed to accept suggestion: {e}")
    
    def _dismiss_suggestion(self):
        """Dismiss current suggestion"""
        if not self.suggestions:
            return
        
        suggestion = self.suggestions[self.current_suggestion_index]
        
        # Dismiss from engine
        self.suggestion_engine.dismiss_suggestion(suggestion.suggestion_id)
        
        # Remove from local list
        self.suggestions.pop(self.current_suggestion_index)
        if self.current_suggestion_index >= len(self.suggestions):
            self.current_suggestion_index = 0
        
        self._update_suggestion_display()
    
    def _refresh_suggestions(self):
        """Refresh suggestions"""
        self._load_suggestions()


class ProfileQuickAccessPanel(ctk.CTkFrame):
    """Panel with quick access to profiles and execution controls"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.logger = logging.getLogger("mark_i.profiles.integration.quick_access_panel")
        
        # Components
        self.profile_manager = ProfileManager()
        
        # Callbacks
        self.on_profile_manager_requested: Optional[Callable[[], None]] = None
        self.on_profile_executed: Optional[Callable[[AutomationProfile], None]] = None
        
        self._create_widgets()
        self._setup_layout()
        
        self.logger.info("ProfileQuickAccessPanel initialized")
    
    def _create_widgets(self):
        """Create quick access widgets"""
        # Header
        self.header_label = ctk.CTkLabel(
            self, text="Profile Quick Access",
            font=("Arial", 14, "bold")
        )
        
        # Status widget
        self.status_widget = ProfileStatusWidget(self, height=80)
        
        # Quick execute widget
        self.quick_execute_widget = QuickExecuteWidget(self, height=100)
        self.quick_execute_widget.on_profile_executed = self._on_profile_executed
        
        # Suggestions widget
        self.suggestions_widget = TaskSuggestionsWidget(self, height=120)
        self.suggestions_widget.on_suggestion_accepted = self._on_suggestion_accepted
        
        # Action buttons
        self.actions_frame = ctk.CTkFrame(self)
        
        self.manage_profiles_btn = ctk.CTkButton(
            self.actions_frame, text="📋 Manage Profiles",
            command=self._open_profile_manager
        )
        
        self.create_profile_btn = ctk.CTkButton(
            self.actions_frame, text="➕ New Profile",
            command=self._create_new_profile
        )
    
    def _setup_layout(self):
        """Setup panel layout"""
        self.header_label.pack(pady=(10, 5))
        
        self.status_widget.pack(fill="x", padx=10, pady=5)
        self.quick_execute_widget.pack(fill="x", padx=10, pady=5)
        self.suggestions_widget.pack(fill="x", padx=10, pady=5)
        
        self.actions_frame.pack(fill="x", padx=10, pady=5)
        
        self.manage_profiles_btn.pack(side="left", padx=2)
        self.create_profile_btn.pack(side="right", padx=2)
    
    def _on_profile_executed(self, profile: AutomationProfile):
        """Handle profile execution"""
        if self.on_profile_executed:
            self.on_profile_executed(profile)
    
    def _on_suggestion_accepted(self, suggestion: TaskSuggestion):
        """Handle suggestion acceptance"""
        self.logger.info(f"Suggestion accepted: {suggestion.title}")
    
    def _open_profile_manager(self):
        """Open profile manager"""
        if self.on_profile_manager_requested:
            self.on_profile_manager_requested()
    
    def _create_new_profile(self):
        """Create new profile"""
        # This would trigger new profile creation
        if self.on_profile_manager_requested:
            self.on_profile_manager_requested()
    
    def refresh_all(self):
        """Refresh all widgets"""
        try:
            self.quick_execute_widget.refresh_profiles()
            self.suggestions_widget._refresh_suggestions()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh panel: {e}")


def create_profile_sidebar(parent) -> ProfileQuickAccessPanel:
    """Create a profile sidebar for the main MARK-I interface"""
    return ProfileQuickAccessPanel(parent, width=300)