"""
Profile Editor Window

Main visual interface for creating and editing automation profiles.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Dict, Any, List
import logging

from ..models.profile import AutomationProfile
from ..models.region import Region
from ..models.rule import Rule, Condition, Action
from ..profile_manager import ProfileManager
from ..validation.profile_validator import ProfileValidator


class ProfileEditorWindow(ctk.CTkToplevel):
    """Main profile editor interface"""
    
    def __init__(self, parent=None, profile_manager: ProfileManager = None):
        super().__init__(parent)
        
        self.profile_manager = profile_manager or ProfileManager()
        self.validator = ProfileValidator()
        self.logger = logging.getLogger("mark_i.profiles.ui.editor")
        
        # Current profile being edited
        self.current_profile: Optional[AutomationProfile] = None
        self.is_modified = False
        
        # UI state
        self.selected_region: Optional[Region] = None
        self.selected_rule: Optional[Rule] = None
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
        self.logger.info("ProfileEditorWindow initialized")
    
    def _setup_window(self):
        """Configure the main window"""
        self.title("MARK-I Profile Editor")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)        

        # Create toolbar
        self._create_toolbar()
        
        # Create main content area with tabs
        self._create_tabview()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self):
        """Create the toolbar with main actions"""
        self.toolbar = ctk.CTkFrame(self.main_frame, height=50)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.toolbar.grid_columnconfigure(6, weight=1)  # Spacer
        
        # New profile button
        self.new_btn = ctk.CTkButton(
            self.toolbar, text="New", width=80,
            command=self.new_profile
        )
        self.new_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Open profile button
        self.open_btn = ctk.CTkButton(
            self.toolbar, text="Open", width=80,
            command=self.open_profile
        )
        self.open_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Save profile button
        self.save_btn = ctk.CTkButton(
            self.toolbar, text="Save", width=80,
            command=self.save_profile
        )
        self.save_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Validate button
        self.validate_btn = ctk.CTkButton(
            self.toolbar, text="Validate", width=80,
            command=self.validate_profile
        )
        self.validate_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Test button
        self.test_btn = ctk.CTkButton(
            self.toolbar, text="Test", width=80,
            command=self.test_profile
        )
        self.test_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            self.toolbar, text="Export", width=80,
            command=self.export_profile
        )
        self.export_btn.grid(row=0, column=5, padx=5, pady=5) 
   
    def _create_tabview(self):
        """Create the main tabbed interface"""
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Profile Info tab
        self.info_tab = self.tabview.add("Profile Info")
        self._create_info_tab()
        
        # Regions tab
        self.regions_tab = self.tabview.add("Regions")
        self._create_regions_tab()
        
        # Rules tab
        self.rules_tab = self.tabview.add("Rules")
        self._create_rules_tab()
        
        # Settings tab
        self.settings_tab = self.tabview.add("Settings")
        self._create_settings_tab()
    
    def _create_info_tab(self):
        """Create the profile information tab"""
        # Configure grid
        self.info_tab.grid_columnconfigure(1, weight=1)
        
        # Profile name
        ctk.CTkLabel(self.info_tab, text="Profile Name:").grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        self.name_entry = ctk.CTkEntry(self.info_tab, width=300)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.name_entry.bind("<KeyRelease>", self._on_profile_modified)
        
        # Description
        ctk.CTkLabel(self.info_tab, text="Description:").grid(
            row=1, column=0, sticky="nw", padx=10, pady=5
        )
        self.description_text = ctk.CTkTextbox(self.info_tab, height=100)
        self.description_text.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.description_text.bind("<KeyRelease>", self._on_profile_modified)
        
        # Category
        ctk.CTkLabel(self.info_tab, text="Category:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5
        )
        self.category_combo = ctk.CTkComboBox(
            self.info_tab, 
            values=["email", "web", "files", "templates", "custom"],
            command=self._on_profile_modified
        )
        self.category_combo.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Target Application
        ctk.CTkLabel(self.info_tab, text="Target Application:").grid(
            row=3, column=0, sticky="w", padx=10, pady=5
        )
        self.target_app_entry = ctk.CTkEntry(self.info_tab, width=300)
        self.target_app_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        self.target_app_entry.bind("<KeyRelease>", self._on_profile_modified)
        
        # Tags
        ctk.CTkLabel(self.info_tab, text="Tags (comma-separated):").grid(
            row=4, column=0, sticky="w", padx=10, pady=5
        )
        self.tags_entry = ctk.CTkEntry(self.info_tab, width=300)
        self.tags_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        self.tags_entry.bind("<KeyRelease>", self._on_profile_modified)  
  
    def _create_regions_tab(self):
        """Create the regions management tab"""
        # Configure grid
        self.regions_tab.grid_columnconfigure(1, weight=1)
        self.regions_tab.grid_rowconfigure(0, weight=1)
        
        # Regions list frame
        regions_list_frame = ctk.CTkFrame(self.regions_tab)
        regions_list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        regions_list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(regions_list_frame, text="Regions", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )
        
        # Regions listbox
        self.regions_listbox = tk.Listbox(regions_list_frame, height=15)
        self.regions_listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        self.regions_listbox.bind("<<ListboxSelect>>", self._on_region_selected)
        
        # Region buttons
        self.add_region_btn = ctk.CTkButton(
            regions_list_frame, text="Add Region", width=100,
            command=self.add_region
        )
        self.add_region_btn.grid(row=2, column=0, padx=5, pady=5)
        
        self.remove_region_btn = ctk.CTkButton(
            regions_list_frame, text="Remove", width=100,
            command=self.remove_region
        )
        self.remove_region_btn.grid(row=2, column=1, padx=5, pady=5)
        
        # Region properties frame
        self.region_props_frame = ctk.CTkFrame(self.regions_tab)
        self.region_props_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.region_props_frame.grid_columnconfigure(1, weight=1)
        
        self._create_region_properties()
    
    def _create_region_properties(self):
        """Create region properties editor"""
        ctk.CTkLabel(self.region_props_frame, text="Region Properties", 
                    font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Region name
        ctk.CTkLabel(self.region_props_frame, text="Name:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5
        )
        self.region_name_entry = ctk.CTkEntry(self.region_props_frame, width=200)
        self.region_name_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # Position and size
        ctk.CTkLabel(self.region_props_frame, text="X:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5
        )
        self.region_x_entry = ctk.CTkEntry(self.region_props_frame, width=100)
        self.region_x_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(self.region_props_frame, text="Y:").grid(
            row=3, column=0, sticky="w", padx=10, pady=5
        )
        self.region_y_entry = ctk.CTkEntry(self.region_props_frame, width=100)
        self.region_y_entry.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(self.region_props_frame, text="Width:").grid(
            row=4, column=0, sticky="w", padx=10, pady=5
        )
        self.region_width_entry = ctk.CTkEntry(self.region_props_frame, width=100)
        self.region_width_entry.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        ctk.CTkLabel(self.region_props_frame, text="Height:").grid(
            row=5, column=0, sticky="w", padx=10, pady=5
        )
        self.region_height_entry = ctk.CTkEntry(self.region_props_frame, width=100)
        self.region_height_entry.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        
        # Description
        ctk.CTkLabel(self.region_props_frame, text="Description:").grid(
            row=6, column=0, sticky="nw", padx=10, pady=5
        )
        self.region_desc_text = ctk.CTkTextbox(self.region_props_frame, height=80)
        self.region_desc_text.grid(row=6, column=1, sticky="ew", padx=10, pady=5)
        
        # OCR enabled checkbox
        self.region_ocr_var = ctk.BooleanVar()
        self.region_ocr_check = ctk.CTkCheckBox(
            self.region_props_frame, text="OCR Enabled", variable=self.region_ocr_var
        )
        self.region_ocr_check.grid(row=7, column=0, columnspan=2, padx=10, pady=5)
        
        # Update region button
        self.update_region_btn = ctk.CTkButton(
            self.region_props_frame, text="Update Region",
            command=self.update_region
        )
        self.update_region_btn.grid(row=8, column=0, columnspan=2, pady=10)    

    def _create_rules_tab(self):
        """Create the rules management tab"""
        # Configure grid
        self.rules_tab.grid_columnconfigure(1, weight=1)
        self.rules_tab.grid_rowconfigure(0, weight=1)
        
        # Rules list frame
        rules_list_frame = ctk.CTkFrame(self.rules_tab)
        rules_list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        rules_list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(rules_list_frame, text="Rules", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )
        
        # Rules listbox
        self.rules_listbox = tk.Listbox(rules_list_frame, height=15)
        self.rules_listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        self.rules_listbox.bind("<<ListboxSelect>>", self._on_rule_selected)
        
        # Rule buttons
        self.add_rule_btn = ctk.CTkButton(
            rules_list_frame, text="Add Rule", width=100,
            command=self.add_rule
        )
        self.add_rule_btn.grid(row=2, column=0, padx=5, pady=5)
        
        self.remove_rule_btn = ctk.CTkButton(
            rules_list_frame, text="Remove", width=100,
            command=self.remove_rule
        )
        self.remove_rule_btn.grid(row=2, column=1, padx=5, pady=5)
        
        # Rule properties frame
        self.rule_props_frame = ctk.CTkFrame(self.rules_tab)
        self.rule_props_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.rule_props_frame.grid_columnconfigure(1, weight=1)
        
        self._create_rule_properties()
    
    def _create_rule_properties(self):
        """Create rule properties editor"""
        ctk.CTkLabel(self.rule_props_frame, text="Rule Properties", 
                    font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Rule name
        ctk.CTkLabel(self.rule_props_frame, text="Name:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5
        )
        self.rule_name_entry = ctk.CTkEntry(self.rule_props_frame, width=200)
        self.rule_name_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # Description
        ctk.CTkLabel(self.rule_props_frame, text="Description:").grid(
            row=2, column=0, sticky="nw", padx=10, pady=5
        )
        self.rule_desc_text = ctk.CTkTextbox(self.rule_props_frame, height=60)
        self.rule_desc_text.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        # Priority
        ctk.CTkLabel(self.rule_props_frame, text="Priority:").grid(
            row=3, column=0, sticky="w", padx=10, pady=5
        )
        self.rule_priority_entry = ctk.CTkEntry(self.rule_props_frame, width=100)
        self.rule_priority_entry.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # Enabled checkbox
        self.rule_enabled_var = ctk.BooleanVar(value=True)
        self.rule_enabled_check = ctk.CTkCheckBox(
            self.rule_props_frame, text="Enabled", variable=self.rule_enabled_var
        )
        self.rule_enabled_check.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        
        # Logical operator
        ctk.CTkLabel(self.rule_props_frame, text="Logical Operator:").grid(
            row=5, column=0, sticky="w", padx=10, pady=5
        )
        self.rule_logic_combo = ctk.CTkComboBox(
            self.rule_props_frame, values=["AND", "OR"], width=100
        )
        self.rule_logic_combo.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        
        # Conditions section
        ctk.CTkLabel(self.rule_props_frame, text="Conditions:", 
                    font=("Arial", 14, "bold")).grid(row=6, column=0, columnspan=2, pady=(20, 5))
        
        self.conditions_text = ctk.CTkTextbox(self.rule_props_frame, height=100)
        self.conditions_text.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Actions section
        ctk.CTkLabel(self.rule_props_frame, text="Actions:", 
                    font=("Arial", 14, "bold")).grid(row=8, column=0, columnspan=2, pady=(20, 5))
        
        self.actions_text = ctk.CTkTextbox(self.rule_props_frame, height=100)
        self.actions_text.grid(row=9, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Update rule button
        self.update_rule_btn = ctk.CTkButton(
            self.rule_props_frame, text="Update Rule",
            command=self.update_rule
        )
        self.update_rule_btn.grid(row=10, column=0, columnspan=2, pady=10)   
 
    def _create_settings_tab(self):
        """Create the profile settings tab"""
        # Configure grid
        self.settings_tab.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.settings_tab, text="Profile Settings", 
                    font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Monitoring interval
        ctk.CTkLabel(self.settings_tab, text="Monitoring Interval (seconds):").grid(
            row=1, column=0, sticky="w", padx=10, pady=5
        )
        self.monitoring_interval_entry = ctk.CTkEntry(self.settings_tab, width=100)
        self.monitoring_interval_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Max execution time
        ctk.CTkLabel(self.settings_tab, text="Max Execution Time (seconds):").grid(
            row=2, column=0, sticky="w", padx=10, pady=5
        )
        self.max_exec_time_entry = ctk.CTkEntry(self.settings_tab, width=100)
        self.max_exec_time_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Template match threshold
        ctk.CTkLabel(self.settings_tab, text="Template Match Threshold:").grid(
            row=3, column=0, sticky="w", padx=10, pady=5
        )
        self.template_threshold_entry = ctk.CTkEntry(self.settings_tab, width=100)
        self.template_threshold_entry.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # OCR confidence threshold
        ctk.CTkLabel(self.settings_tab, text="OCR Confidence Threshold:").grid(
            row=4, column=0, sticky="w", padx=10, pady=5
        )
        self.ocr_threshold_entry = ctk.CTkEntry(self.settings_tab, width=100)
        self.ocr_threshold_entry.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        # Use Gemini analysis
        self.use_gemini_var = ctk.BooleanVar(value=True)
        self.use_gemini_check = ctk.CTkCheckBox(
            self.settings_tab, text="Use Gemini AI Analysis", variable=self.use_gemini_var
        )
        self.use_gemini_check.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        
        # Screenshot on error
        self.screenshot_error_var = ctk.BooleanVar(value=True)
        self.screenshot_error_check = ctk.CTkCheckBox(
            self.settings_tab, text="Screenshot on Error", variable=self.screenshot_error_var
        )
        self.screenshot_error_check.grid(row=6, column=0, columnspan=2, padx=10, pady=5)
    
    def _create_status_bar(self):
        """Create the status bar"""
        self.status_bar = ctk.CTkFrame(self.main_frame, height=30)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.status_bar.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready")
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.modified_label = ctk.CTkLabel(self.status_bar, text="")
        self.modified_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def _setup_layout(self):
        """Setup the layout and configure weights"""
        pass  # Already configured in individual methods
    
    def _bind_events(self):
        """Bind event handlers"""
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _on_profile_modified(self, event=None):
        """Handle profile modification"""
        self.is_modified = True
        self.modified_label.configure(text="Modified")
        self._update_window_title()
    
    def _update_window_title(self):
        """Update window title based on current profile"""
        title = "MARK-I Profile Editor"
        if self.current_profile:
            title += f" - {self.current_profile.name}"
            if self.is_modified:
                title += " *"
        self.title(title)
    
    def _update_status(self, message: str):
        """Update status bar message"""
        self.status_label.configure(text=message)
        self.after(3000, lambda: self.status_label.configure(text="Ready")) 
   
    # Profile Management Methods
    
    def new_profile(self):
        """Create a new profile"""
        if self.is_modified and not self._confirm_discard_changes():
            return
        
        # Create new profile dialog
        dialog = ProfileInfoDialog(self, "New Profile")
        if dialog.result:
            name, description, category, target_app = dialog.result
            try:
                self.current_profile = self.profile_manager.create_profile(
                    name, description, category, target_app
                )
                self._load_profile_to_ui()
                self.is_modified = False
                self._update_window_title()
                self._update_status(f"Created new profile: {name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create profile: {str(e)}")
    
    def open_profile(self):
        """Open an existing profile"""
        if self.is_modified and not self._confirm_discard_changes():
            return
        
        # Show profile selection dialog
        profiles = self.profile_manager.list_profiles()
        if not profiles:
            messagebox.showinfo("No Profiles", "No profiles found. Create a new profile first.")
            return
        
        dialog = ProfileSelectionDialog(self, profiles)
        if dialog.selected_profile:
            self.current_profile = dialog.selected_profile
            self._load_profile_to_ui()
            self.is_modified = False
            self._update_window_title()
            self._update_status(f"Opened profile: {self.current_profile.name}")
    
    def save_profile(self):
        """Save the current profile"""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "No profile to save. Create a new profile first.")
            return
        
        try:
            # Update profile from UI
            self._update_profile_from_ui()
            
            # Save profile
            if self.profile_manager.save_profile(self.current_profile):
                self.is_modified = False
                self.modified_label.configure(text="")
                self._update_window_title()
                self._update_status(f"Saved profile: {self.current_profile.name}")
            else:
                messagebox.showerror("Error", "Failed to save profile")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {str(e)}")
    
    def validate_profile(self):
        """Validate the current profile"""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "No profile to validate.")
            return
        
        try:
            # Update profile from UI first
            self._update_profile_from_ui()
            
            # Validate profile
            result = self.validator.validate_profile(self.current_profile)
            
            # Show validation results
            ValidationResultDialog(self, result)
            
            if result.is_valid:
                self._update_status("Profile validation passed")
            else:
                self._update_status(f"Profile validation failed: {len(result.errors)} errors")
                
        except Exception as e:
            messagebox.showerror("Error", f"Validation failed: {str(e)}")
    
    def test_profile(self):
        """Test the current profile"""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "No profile to test.")
            return
        
        # This would integrate with ProfileExecutor for testing
        messagebox.showinfo("Test Profile", "Profile testing not yet implemented")
    
    def export_profile(self):
        """Export the current profile"""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "No profile to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Profile",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self._update_profile_from_ui()
                if self.profile_manager.export_profile(self.current_profile.id, filename):
                    self._update_status(f"Exported profile to: {filename}")
                else:
                    messagebox.showerror("Error", "Failed to export profile")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def _confirm_discard_changes(self) -> bool:
        """Confirm discarding unsaved changes"""
        return messagebox.askyesno(
            "Unsaved Changes", 
            "You have unsaved changes. Discard them?"
        )
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_modified and not self._confirm_discard_changes():
            return
        self.destroy()   
 
    # UI Update Methods
    
    def _load_profile_to_ui(self):
        """Load current profile data into UI"""
        if not self.current_profile:
            return
        
        # Load profile info
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, self.current_profile.name)
        
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", self.current_profile.description)
        
        self.category_combo.set(self.current_profile.category)
        
        self.target_app_entry.delete(0, tk.END)
        self.target_app_entry.insert(0, self.current_profile.target_application)
        
        self.tags_entry.delete(0, tk.END)
        self.tags_entry.insert(0, ", ".join(self.current_profile.tags))
        
        # Load regions
        self._refresh_regions_list()
        
        # Load rules
        self._refresh_rules_list()
        
        # Load settings
        settings = self.current_profile.settings
        self.monitoring_interval_entry.delete(0, tk.END)
        self.monitoring_interval_entry.insert(0, str(settings.monitoring_interval_seconds))
        
        self.max_exec_time_entry.delete(0, tk.END)
        self.max_exec_time_entry.insert(0, str(settings.max_execution_time_seconds))
        
        self.template_threshold_entry.delete(0, tk.END)
        self.template_threshold_entry.insert(0, str(settings.template_match_threshold))
        
        self.ocr_threshold_entry.delete(0, tk.END)
        self.ocr_threshold_entry.insert(0, str(settings.ocr_confidence_threshold))
        
        self.use_gemini_var.set(settings.use_gemini_analysis)
        self.screenshot_error_var.set(settings.screenshot_on_error)
    
    def _update_profile_from_ui(self):
        """Update current profile from UI data"""
        if not self.current_profile:
            return
        
        # Update profile info
        self.current_profile.name = self.name_entry.get()
        self.current_profile.description = self.description_text.get("1.0", tk.END).strip()
        self.current_profile.category = self.category_combo.get()
        self.current_profile.target_application = self.target_app_entry.get()
        
        # Update tags
        tags_text = self.tags_entry.get().strip()
        if tags_text:
            self.current_profile.tags = [tag.strip() for tag in tags_text.split(",")]
        else:
            self.current_profile.tags = []
        
        # Update settings
        settings = self.current_profile.settings
        try:
            settings.monitoring_interval_seconds = float(self.monitoring_interval_entry.get())
            settings.max_execution_time_seconds = int(self.max_exec_time_entry.get())
            settings.template_match_threshold = float(self.template_threshold_entry.get())
            settings.ocr_confidence_threshold = int(self.ocr_threshold_entry.get())
            settings.use_gemini_analysis = self.use_gemini_var.get()
            settings.screenshot_on_error = self.screenshot_error_var.get()
        except ValueError as e:
            raise ValueError(f"Invalid settings value: {str(e)}")
    
    def _refresh_regions_list(self):
        """Refresh the regions listbox"""
        self.regions_listbox.delete(0, tk.END)
        if self.current_profile:
            for region in self.current_profile.regions:
                self.regions_listbox.insert(tk.END, f"{region.name} ({region.x}, {region.y})")
    
    def _refresh_rules_list(self):
        """Refresh the rules listbox"""
        self.rules_listbox.delete(0, tk.END)
        if self.current_profile:
            for rule in self.current_profile.rules:
                status = "✓" if rule.enabled else "✗"
                self.rules_listbox.insert(tk.END, f"{status} {rule.name} (P:{rule.priority})")
    
    def _on_region_selected(self, event):
        """Handle region selection"""
        selection = self.regions_listbox.curselection()
        if selection and self.current_profile:
            index = selection[0]
            self.selected_region = self.current_profile.regions[index]
            self._load_region_to_ui()
    
    def _on_rule_selected(self, event):
        """Handle rule selection"""
        selection = self.rules_listbox.curselection()
        if selection and self.current_profile:
            index = selection[0]
            self.selected_rule = self.current_profile.rules[index]
            self._load_rule_to_ui()
    
    def _load_region_to_ui(self):
        """Load selected region to UI"""
        if not self.selected_region:
            return
        
        region = self.selected_region
        self.region_name_entry.delete(0, tk.END)
        self.region_name_entry.insert(0, region.name)
        
        self.region_x_entry.delete(0, tk.END)
        self.region_x_entry.insert(0, str(region.x))
        
        self.region_y_entry.delete(0, tk.END)
        self.region_y_entry.insert(0, str(region.y))
        
        self.region_width_entry.delete(0, tk.END)
        self.region_width_entry.insert(0, str(region.width))
        
        self.region_height_entry.delete(0, tk.END)
        self.region_height_entry.insert(0, str(region.height))
        
        self.region_desc_text.delete("1.0", tk.END)
        self.region_desc_text.insert("1.0", region.description)
        
        self.region_ocr_var.set(region.ocr_enabled)
    
    def _load_rule_to_ui(self):
        """Load selected rule to UI"""
        if not self.selected_rule:
            return
        
        rule = self.selected_rule
        self.rule_name_entry.delete(0, tk.END)
        self.rule_name_entry.insert(0, rule.name)
        
        self.rule_desc_text.delete("1.0", tk.END)
        self.rule_desc_text.insert("1.0", rule.description)
        
        self.rule_priority_entry.delete(0, tk.END)
        self.rule_priority_entry.insert(0, str(rule.priority))
        
        self.rule_enabled_var.set(rule.enabled)
        self.rule_logic_combo.set(rule.logical_operator)
        
        # Load conditions
        conditions_text = "\n".join([
            f"{i+1}. {cond.type} on {cond.region}" 
            for i, cond in enumerate(rule.conditions)
        ])
        self.conditions_text.delete("1.0", tk.END)
        self.conditions_text.insert("1.0", conditions_text)
        
        # Load actions
        actions_text = "\n".join([
            f"{i+1}. {action.type}" + (f" on {action.region}" if action.region else "")
            for i, action in enumerate(rule.actions)
        ])
        self.actions_text.delete("1.0", tk.END)
        self.actions_text.insert("1.0", actions_text)    

    # Region Management Methods
    
    def add_region(self):
        """Add a new region"""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Create or open a profile first.")
            return
        
        dialog = RegionDialog(self, "Add Region")
        if dialog.result:
            try:
                region = Region(**dialog.result)
                self.current_profile.add_region(region)
                self._refresh_regions_list()
                self._on_profile_modified()
                self._update_status(f"Added region: {region.name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add region: {str(e)}")
    
    def remove_region(self):
        """Remove selected region"""
        if not self.selected_region:
            messagebox.showwarning("No Selection", "Select a region to remove.")
            return
        
        if messagebox.askyesno("Confirm", f"Remove region '{self.selected_region.name}'?"):
            self.current_profile.remove_region(self.selected_region.name)
            self.selected_region = None
            self._refresh_regions_list()
            self._clear_region_ui()
            self._on_profile_modified()
            self._update_status("Region removed")
    
    def update_region(self):
        """Update selected region from UI"""
        if not self.selected_region:
            messagebox.showwarning("No Selection", "Select a region to update.")
            return
        
        try:
            # Update region properties
            self.selected_region.name = self.region_name_entry.get()
            self.selected_region.x = int(self.region_x_entry.get())
            self.selected_region.y = int(self.region_y_entry.get())
            self.selected_region.width = int(self.region_width_entry.get())
            self.selected_region.height = int(self.region_height_entry.get())
            self.selected_region.description = self.region_desc_text.get("1.0", tk.END).strip()
            self.selected_region.ocr_enabled = self.region_ocr_var.get()
            
            self._refresh_regions_list()
            self._on_profile_modified()
            self._update_status(f"Updated region: {self.selected_region.name}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid region values: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update region: {str(e)}")
    
    def _clear_region_ui(self):
        """Clear region UI fields"""
        self.region_name_entry.delete(0, tk.END)
        self.region_x_entry.delete(0, tk.END)
        self.region_y_entry.delete(0, tk.END)
        self.region_width_entry.delete(0, tk.END)
        self.region_height_entry.delete(0, tk.END)
        self.region_desc_text.delete("1.0", tk.END)
        self.region_ocr_var.set(False)
    
    # Rule Management Methods
    
    def add_rule(self):
        """Add a new rule"""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Create or open a profile first.")
            return
        
        dialog = RuleDialog(self, "Add Rule", self.current_profile.get_region_names())
        if dialog.result:
            try:
                rule = Rule(**dialog.result)
                self.current_profile.add_rule(rule)
                self._refresh_rules_list()
                self._on_profile_modified()
                self._update_status(f"Added rule: {rule.name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add rule: {str(e)}")
    
    def remove_rule(self):
        """Remove selected rule"""
        if not self.selected_rule:
            messagebox.showwarning("No Selection", "Select a rule to remove.")
            return
        
        if messagebox.askyesno("Confirm", f"Remove rule '{self.selected_rule.name}'?"):
            self.current_profile.remove_rule(self.selected_rule.name)
            self.selected_rule = None
            self._refresh_rules_list()
            self._clear_rule_ui()
            self._on_profile_modified()
            self._update_status("Rule removed")
    
    def update_rule(self):
        """Update selected rule from UI"""
        if not self.selected_rule:
            messagebox.showwarning("No Selection", "Select a rule to update.")
            return
        
        try:
            # Update basic rule properties
            self.selected_rule.name = self.rule_name_entry.get()
            self.selected_rule.description = self.rule_desc_text.get("1.0", tk.END).strip()
            self.selected_rule.priority = int(self.rule_priority_entry.get())
            self.selected_rule.enabled = self.rule_enabled_var.get()
            self.selected_rule.logical_operator = self.rule_logic_combo.get()
            
            self._refresh_rules_list()
            self._on_profile_modified()
            self._update_status(f"Updated rule: {self.selected_rule.name}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid rule values: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update rule: {str(e)}")
    
    def _clear_rule_ui(self):
        """Clear rule UI fields"""
        self.rule_name_entry.delete(0, tk.END)
        self.rule_desc_text.delete("1.0", tk.END)
        self.rule_priority_entry.delete(0, tk.END)
        self.rule_enabled_var.set(True)
        self.rule_logic_combo.set("AND")
        self.conditions_text.delete("1.0", tk.END)
        self.actions_text.delete("1.0", tk.END)

# 
Import dialog classes (will be implemented in dialogs.py)
from .dialogs import (
    ProfileInfoDialog,
    ProfileSelectionDialog,
    ValidationResultDialog,
    RegionEditorDialog,
    RuleEditorDialog
)