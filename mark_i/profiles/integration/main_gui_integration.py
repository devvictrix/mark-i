"""
Main GUI Integration

Integration components for adding profile functionality to the main MARK-I GUI
including menu items, toolbar buttons, and quick access features.
"""

import logging
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable, List, Dict, Any

from ..profile_manager import ProfileManager
from ..models.profile import AutomationProfile
from ..ui.profile_manager_ui import ProfileManagerWindow
from ..ui.execution_monitor import ExecutionMonitorWindow, ExecutionControlWidget
from ..execution.execution_engine import ExecutionEngine, ExecutionMode


class ProfileMenuIntegration:
    """Integration component for adding profile menu to main MARK-I GUI"""
    
    def __init__(self, main_window, menu_bar):
        self.main_window = main_window
        self.menu_bar = menu_bar
        self.logger = logging.getLogger("mark_i.profiles.integration.menu")
        
        # Profile system components
        self.profile_manager = ProfileManager()
        self.execution_engine = ExecutionEngine()
        
        # UI windows
        self.profile_manager_window: Optional[ProfileManagerWindow] = None
        self.execution_monitor_window: Optional[ExecutionMonitorWindow] = None
        
        # Create profile menu
        self._create_profile_menu()
        
        self.logger.info("ProfileMenuIntegration initialized")
    
    def _create_profile_menu(self):
        """Create the profile menu in the main menu bar"""
        try:
            # Create Profiles menu
            self.profile_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="Profiles", menu=self.profile_menu)
            
            # Profile Management submenu
            self.profile_menu.add_command(
                label="Profile Manager...",
                command=self.open_profile_manager,
                accelerator="Ctrl+Shift+P"
            )
            
            self.profile_menu.add_command(
                label="New Profile...",
                command=self.create_new_profile,
                accelerator="Ctrl+Alt+N"
            )
            
            self.profile_menu.add_separator()
            
            # Quick Execute submenu
            self.quick_execute_menu = tk.Menu(self.profile_menu, tearoff=0)
            self.profile_menu.add_cascade(label="Quick Execute", menu=self.quick_execute_menu)
            
            # Execution Monitor
            self.profile_menu.add_command(
                label="Execution Monitor...",
                command=self.open_execution_monitor,
                accelerator="Ctrl+Shift+M"
            )
            
            self.profile_menu.add_separator()
            
            # Recent Profiles submenu
            self.recent_profiles_menu = tk.Menu(self.profile_menu, tearoff=0)
            self.profile_menu.add_cascade(label="Recent Profiles", menu=self.recent_profiles_menu)
            
            # Templates submenu
            self.templates_menu = tk.Menu(self.profile_menu, tearoff=0)
            self.profile_menu.add_cascade(label="Templates", menu=self.templates_menu)
            
            self.profile_menu.add_separator()
            
            # Import/Export
            self.profile_menu.add_command(
                label="Import Profile...",
                command=self.import_profile
            )
            
            self.profile_menu.add_command(
                label="Export Profile...",
                command=self.export_profile
            )
            
            # Populate dynamic menus
            self._populate_quick_execute_menu()
            self._populate_recent_profiles_menu()
            self._populate_templates_menu()
            
            # Bind keyboard shortcuts
            self._bind_keyboard_shortcuts()
            
        except Exception as e:
            self.logger.error(f"Failed to create profile menu: {e}")
    
    def _populate_quick_execute_menu(self):
        """Populate quick execute menu with available profiles"""
        try:
            # Clear existing items
            self.quick_execute_menu.delete(0, tk.END)
            
            # Get profiles for quick execute (favorites or recently used)
            profiles = self.profile_manager.get_quick_execute_profiles()
            
            if not profiles:
                self.quick_execute_menu.add_command(
                    label="No profiles available",
                    state="disabled"
                )
                return
            
            # Add profiles to menu
            for profile in profiles[:10]:  # Limit to 10 items
                self.quick_execute_menu.add_command(
                    label=profile.name,
                    command=lambda p=profile: self.quick_execute_profile(p)
                )
            
            if len(profiles) > 10:
                self.quick_execute_menu.add_separator()
                self.quick_execute_menu.add_command(
                    label="More profiles...",
                    command=self.open_profile_manager
                )
                
        except Exception as e:
            self.logger.error(f"Failed to populate quick execute menu: {e}")
    
    def _populate_recent_profiles_menu(self):
        """Populate recent profiles menu"""
        try:
            # Clear existing items
            self.recent_profiles_menu.delete(0, tk.END)
            
            # Get recent profiles
            recent_profiles = self.profile_manager.get_recent_profiles()
            
            if not recent_profiles:
                self.recent_profiles_menu.add_command(
                    label="No recent profiles",
                    state="disabled"
                )
                return
            
            # Add recent profiles
            for profile in recent_profiles[:10]:
                self.recent_profiles_menu.add_command(
                    label=profile.name,
                    command=lambda p=profile: self.open_profile_for_edit(p)
                )
            
            self.recent_profiles_menu.add_separator()
            self.recent_profiles_menu.add_command(
                label="Clear Recent",
                command=self.clear_recent_profiles
            )
            
        except Exception as e:
            self.logger.error(f"Failed to populate recent profiles menu: {e}")
    
    def _populate_templates_menu(self):
        """Populate templates menu"""
        try:
            # Clear existing items
            self.templates_menu.delete(0, tk.END)
            
            # Template categories
            categories = ["Email", "Web", "System"]
            
            for category in categories:
                category_menu = tk.Menu(self.templates_menu, tearoff=0)
                self.templates_menu.add_cascade(label=category, menu=category_menu)
                
                # Add template variants for category
                variants = self._get_template_variants(category.lower())
                for variant in variants:
                    category_menu.add_command(
                        label=variant.title(),
                        command=lambda c=category.lower(), v=variant: self.create_from_template(c, v)
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to populate templates menu: {e}")
    
    def _get_template_variants(self, category: str) -> List[str]:
        """Get template variants for category"""
        template_variants = {
            "email": ["outlook", "gmail", "thunderbird"],
            "web": ["chrome", "firefox", "edge"],
            "system": ["windows", "macos", "linux"]
        }
        return template_variants.get(category, [])
    
    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for profile actions"""
        try:
            # Profile Manager
            self.main_window.bind("<Control-Shift-P>", lambda e: self.open_profile_manager())
            
            # New Profile
            self.main_window.bind("<Control-Alt-n>", lambda e: self.create_new_profile())
            
            # Execution Monitor
            self.main_window.bind("<Control-Shift-M>", lambda e: self.open_execution_monitor())
            
            # Quick execute (F1-F10 for first 10 profiles)
            for i in range(1, 11):
                self.main_window.bind(f"<F{i}>", lambda e, idx=i-1: self.quick_execute_by_index(idx))
            
        except Exception as e:
            self.logger.error(f"Failed to bind keyboard shortcuts: {e}")
    
    # Menu action methods
    
    def open_profile_manager(self):
        """Open the profile manager window"""
        try:
            if self.profile_manager_window and self.profile_manager_window.winfo_exists():
                self.profile_manager_window.focus()
            else:
                self.profile_manager_window = ProfileManagerWindow(self.main_window)
                self.profile_manager_window.on_profile_executed = self.on_profile_executed
                
        except Exception as e:
            self.logger.error(f"Failed to open profile manager: {e}")
            messagebox.showerror("Error", f"Failed to open profile manager: {str(e)}")
    
    def create_new_profile(self):
        """Create a new profile"""
        try:
            # Open profile manager and trigger new profile creation
            self.open_profile_manager()
            if self.profile_manager_window:
                self.profile_manager_window.new_profile()
                
        except Exception as e:
            self.logger.error(f"Failed to create new profile: {e}")
            messagebox.showerror("Error", f"Failed to create new profile: {str(e)}")
    
    def open_execution_monitor(self):
        """Open the execution monitor window"""
        try:
            if self.execution_monitor_window and self.execution_monitor_window.winfo_exists():
                self.execution_monitor_window.focus()
            else:
                self.execution_monitor_window = ExecutionMonitorWindow(self.main_window)
                
        except Exception as e:
            self.logger.error(f"Failed to open execution monitor: {e}")
            messagebox.showerror("Error", f"Failed to open execution monitor: {str(e)}")
    
    def quick_execute_profile(self, profile: AutomationProfile):
        """Quick execute a profile"""
        try:
            # Execute profile with default settings
            execution_id = self.execution_engine.execute_profile(
                profile, 
                mode=ExecutionMode.NORMAL
            )
            
            # Show execution monitor
            self.open_execution_monitor()
            if self.execution_monitor_window:
                self.execution_monitor_window.load_profile(profile)
            
            self.logger.info(f"Quick executed profile: {profile.name} (ID: {execution_id})")
            
        except Exception as e:
            self.logger.error(f"Failed to quick execute profile: {e}")
            messagebox.showerror("Error", f"Failed to execute profile: {str(e)}")
    
    def quick_execute_by_index(self, index: int):
        """Quick execute profile by index (for keyboard shortcuts)"""
        try:
            profiles = self.profile_manager.get_quick_execute_profiles()
            if 0 <= index < len(profiles):
                self.quick_execute_profile(profiles[index])
                
        except Exception as e:
            self.logger.error(f"Failed to quick execute by index: {e}")
    
    def open_profile_for_edit(self, profile: AutomationProfile):
        """Open profile for editing"""
        try:
            self.open_profile_manager()
            # Would need to enhance ProfileManagerWindow to load specific profile
            
        except Exception as e:
            self.logger.error(f"Failed to open profile for edit: {e}")
    
    def import_profile(self):
        """Import a profile"""
        try:
            self.open_profile_manager()
            if self.profile_manager_window:
                self.profile_manager_window.import_profile()
                
        except Exception as e:
            self.logger.error(f"Failed to import profile: {e}")
    
    def export_profile(self):
        """Export a profile"""
        try:
            self.open_profile_manager()
            if self.profile_manager_window:
                self.profile_manager_window.export_selected()
                
        except Exception as e:
            self.logger.error(f"Failed to export profile: {e}")
    
    def create_from_template(self, category: str, variant: str):
        """Create profile from template"""
        try:
            self.open_profile_manager()
            if self.profile_manager_window:
                # Set template category and create
                self.profile_manager_window.template_category_combo.set(category)
                self.profile_manager_window._load_templates()
                # Would need to select specific variant and create
                
        except Exception as e:
            self.logger.error(f"Failed to create from template: {e}")
    
    def clear_recent_profiles(self):
        """Clear recent profiles list"""
        try:
            self.profile_manager.clear_recent_profiles()
            self._populate_recent_profiles_menu()
            
        except Exception as e:
            self.logger.error(f"Failed to clear recent profiles: {e}")
    
    def on_profile_executed(self, profile: AutomationProfile):
        """Handle profile execution from profile manager"""
        try:
            # Execute profile
            execution_id = self.execution_engine.execute_profile(profile)
            
            # Open execution monitor
            self.open_execution_monitor()
            if self.execution_monitor_window:
                self.execution_monitor_window.load_profile(profile)
            
        except Exception as e:
            self.logger.error(f"Failed to handle profile execution: {e}")
    
    def refresh_menus(self):
        """Refresh dynamic menu content"""
        try:
            self._populate_quick_execute_menu()
            self._populate_recent_profiles_menu()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh menus: {e}")


class ProfileToolbarIntegration:
    """Integration component for adding profile toolbar to main MARK-I GUI"""
    
    def __init__(self, main_window, toolbar_frame):
        self.main_window = main_window
        self.toolbar_frame = toolbar_frame
        self.logger = logging.getLogger("mark_i.profiles.integration.toolbar")
        
        # Profile system components
        self.profile_manager = ProfileManager()
        self.execution_engine = ExecutionEngine()
        
        # Menu integration (for shared functionality)
        self.menu_integration: Optional[ProfileMenuIntegration] = None
        
        # Create toolbar elements
        self._create_toolbar_elements()
        
        self.logger.info("ProfileToolbarIntegration initialized")
    
    def set_menu_integration(self, menu_integration: ProfileMenuIntegration):
        """Set reference to menu integration for shared functionality"""
        self.menu_integration = menu_integration
    
    def _create_toolbar_elements(self):
        """Create profile-related toolbar elements"""
        try:
            # Profile section separator
            separator = ctk.CTkFrame(self.toolbar_frame, width=2, height=30)
            separator.pack(side="left", padx=5, pady=5)
            
            # Profile Manager button
            self.profile_manager_btn = ctk.CTkButton(
                self.toolbar_frame,
                text="📋 Profiles",
                width=100,
                command=self.open_profile_manager
            )
            self.profile_manager_btn.pack(side="left", padx=2, pady=5)
            
            # Quick Execute dropdown
            self.quick_execute_combo = ctk.CTkComboBox(
                self.toolbar_frame,
                values=["Select Profile..."],
                command=self.on_quick_execute_selected,
                width=150
            )
            self.quick_execute_combo.pack(side="left", padx=2, pady=5)
            
            # Execute button
            self.execute_btn = ctk.CTkButton(
                self.toolbar_frame,
                text="▶ Execute",
                width=80,
                command=self.execute_selected_profile,
                state="disabled"
            )
            self.execute_btn.pack(side="left", padx=2, pady=5)
            
            # Execution Monitor button
            self.monitor_btn = ctk.CTkButton(
                self.toolbar_frame,
                text="📊 Monitor",
                width=90,
                command=self.open_execution_monitor
            )
            self.monitor_btn.pack(side="left", padx=2, pady=5)
            
            # Status indicator
            self.status_indicator = ctk.CTkLabel(
                self.toolbar_frame,
                text="●",
                text_color="gray",
                font=("Arial", 16)
            )
            self.status_indicator.pack(side="left", padx=5, pady=5)
            
            # Populate quick execute dropdown
            self._populate_quick_execute_dropdown()
            
        except Exception as e:
            self.logger.error(f"Failed to create toolbar elements: {e}")
    
    def _populate_quick_execute_dropdown(self):
        """Populate quick execute dropdown with profiles"""
        try:
            profiles = self.profile_manager.get_quick_execute_profiles()
            
            if profiles:
                profile_names = [profile.name for profile in profiles]
                self.quick_execute_combo.configure(values=["Select Profile..."] + profile_names)
            else:
                self.quick_execute_combo.configure(values=["No profiles available"])
                
        except Exception as e:
            self.logger.error(f"Failed to populate quick execute dropdown: {e}")
    
    def on_quick_execute_selected(self, profile_name: str):
        """Handle quick execute profile selection"""
        if profile_name == "Select Profile..." or profile_name == "No profiles available":
            self.execute_btn.configure(state="disabled")
            return
        
        self.execute_btn.configure(state="normal")
    
    def execute_selected_profile(self):
        """Execute the selected profile"""
        try:
            profile_name = self.quick_execute_combo.get()
            if profile_name in ["Select Profile...", "No profiles available"]:
                return
            
            # Find profile by name
            profile = self.profile_manager.get_profile_by_name(profile_name)
            if not profile:
                messagebox.showerror("Error", f"Profile '{profile_name}' not found")
                return
            
            # Execute profile
            if self.menu_integration:
                self.menu_integration.quick_execute_profile(profile)
            else:
                # Fallback execution
                execution_id = self.execution_engine.execute_profile(profile)
                self.logger.info(f"Executed profile: {profile_name} (ID: {execution_id})")
            
            # Update status indicator
            self.update_status_indicator("running")
            
        except Exception as e:
            self.logger.error(f"Failed to execute selected profile: {e}")
            messagebox.showerror("Error", f"Failed to execute profile: {str(e)}")
    
    def open_profile_manager(self):
        """Open profile manager"""
        if self.menu_integration:
            self.menu_integration.open_profile_manager()
    
    def open_execution_monitor(self):
        """Open execution monitor"""
        if self.menu_integration:
            self.menu_integration.open_execution_monitor()
    
    def update_status_indicator(self, status: str):
        """Update execution status indicator"""
        colors = {
            "idle": "gray",
            "running": "green",
            "paused": "yellow",
            "completed": "blue",
            "failed": "red",
            "cancelled": "orange"
        }
        
        color = colors.get(status, "gray")
        self.status_indicator.configure(text_color=color)
    
    def refresh_toolbar(self):
        """Refresh toolbar content"""
        try:
            self._populate_quick_execute_dropdown()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh toolbar: {e}")


def integrate_profiles_into_main_gui(main_window, menu_bar, toolbar_frame) -> Dict[str, Any]:
    """
    Main integration function to add profile functionality to MARK-I GUI
    
    Args:
        main_window: Main MARK-I window
        menu_bar: Main menu bar
        toolbar_frame: Main toolbar frame
        
    Returns:
        Dictionary with integration components
    """
    try:
        # Create integration components
        menu_integration = ProfileMenuIntegration(main_window, menu_bar)
        toolbar_integration = ProfileToolbarIntegration(main_window, toolbar_frame)
        
        # Link components
        toolbar_integration.set_menu_integration(menu_integration)
        
        # Return integration components for external access
        return {
            'menu_integration': menu_integration,
            'toolbar_integration': toolbar_integration,
            'refresh_ui': lambda: (
                menu_integration.refresh_menus(),
                toolbar_integration.refresh_toolbar()
            )
        }
        
    except Exception as e:
        logging.getLogger("mark_i.profiles.integration").error(f"Failed to integrate profiles: {e}")
        return {}