"""
Dialog Components for Profile Editor

Various dialog windows used by the profile editor for user input and information display.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Optional, List, Tuple, Any

from ..models.profile import AutomationProfile
from ..models.region import Region
from ..models.rule import Rule, Condition, Action, ConditionType, ActionType
from ..validation.profile_validator import ValidationResult


class ProfileInfoDialog(ctk.CTkToplevel):
    """Dialog for entering basic profile information"""
    
    def __init__(self, parent, title="Profile Information"):
        super().__init__(parent)
        
        self.result: Optional[Tuple[str, str, str, str]] = None
        
        self.title(title)
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._setup_layout()
        
        # Focus on name entry
        self.name_entry.focus()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        
        # Profile name
        self.name_label = ctk.CTkLabel(self.main_frame, text="Profile Name:")
        self.name_entry = ctk.CTkEntry(self.main_frame, width=300)
        
        # Description
        self.desc_label = ctk.CTkLabel(self.main_frame, text="Description:")
        self.desc_text = ctk.CTkTextbox(self.main_frame, width=300, height=100)
        
        # Category
        self.category_label = ctk.CTkLabel(self.main_frame, text="Category:")
        self.category_combo = ctk.CTkComboBox(
            self.main_frame,
            values=["email", "web", "files", "templates", "custom"],
            width=200
        )
        self.category_combo.set("custom")
        
        # Target application
        self.app_label = ctk.CTkLabel(self.main_frame, text="Target Application:")
        self.app_entry = ctk.CTkEntry(self.main_frame, width=300)
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.ok_button = ctk.CTkButton(
            self.button_frame, text="OK", width=100,
            command=self._on_ok
        )
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", width=100,
            command=self._on_cancel
        )
    
    def _setup_layout(self):
        """Setup dialog layout"""
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.name_label.pack(anchor="w", pady=(0, 5))
        self.name_entry.pack(anchor="w", pady=(0, 10))
        
        self.desc_label.pack(anchor="w", pady=(0, 5))
        self.desc_text.pack(anchor="w", pady=(0, 10))
        
        self.category_label.pack(anchor="w", pady=(0, 5))
        self.category_combo.pack(anchor="w", pady=(0, 10))
        
        self.app_label.pack(anchor="w", pady=(0, 5))
        self.app_entry.pack(anchor="w", pady=(0, 20))
        
        self.button_frame.pack(fill="x", pady=(10, 0))
        self.ok_button.pack(side="right", padx=(5, 0))
        self.cancel_button.pack(side="right", padx=(5, 5))
        
        # Bind Enter key
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _on_ok(self):
        """Handle OK button"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Invalid Input", "Profile name is required.")
            return
        
        description = self.desc_text.get("1.0", tk.END).strip()
        category = self.category_combo.get()
        target_app = self.app_entry.get().strip()
        
        self.result = (name, description, category, target_app)
        self.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button"""
        self.result = None
        self.destroy()


class ProfileSelectionDialog(ctk.CTkToplevel):
    """Dialog for selecting an existing profile"""
    
    def __init__(self, parent, profiles: List[AutomationProfile]):
        super().__init__(parent)
        
        self.profiles = profiles
        self.selected_profile: Optional[AutomationProfile] = None
        
        self.title("Select Profile")
        self.geometry("600x400")
        self.resizable(True, True)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._setup_layout()
        self._populate_profiles()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        
        # Profile list
        self.list_label = ctk.CTkLabel(self.main_frame, text="Available Profiles:")
        
        # Create listbox with scrollbar
        self.list_frame = ctk.CTkFrame(self.main_frame)
        self.profile_listbox = tk.Listbox(self.list_frame, height=15)
        self.scrollbar = tk.Scrollbar(self.list_frame, orient="vertical")
        self.profile_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.profile_listbox.yview)
        
        # Profile details
        self.details_label = ctk.CTkLabel(self.main_frame, text="Profile Details:")
        self.details_text = ctk.CTkTextbox(self.main_frame, height=100)
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.open_button = ctk.CTkButton(
            self.button_frame, text="Open", width=100,
            command=self._on_open
        )
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", width=100,
            command=self._on_cancel
        )
        
        # Bind selection event
        self.profile_listbox.bind("<<ListboxSelect>>", self._on_selection_changed)
        self.profile_listbox.bind("<Double-Button-1>", lambda e: self._on_open())
    
    def _setup_layout(self):
        """Setup dialog layout"""
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.list_label.pack(anchor="w", pady=(0, 5))
        
        self.list_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.profile_listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.details_label.pack(anchor="w", pady=(0, 5))
        self.details_text.pack(fill="x", pady=(0, 10))
        
        self.button_frame.pack(fill="x")
        self.open_button.pack(side="right", padx=(5, 0))
        self.cancel_button.pack(side="right", padx=(5, 5))
        
        # Bind keys
        self.bind("<Return>", lambda e: self._on_open())
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _populate_profiles(self):
        """Populate the profile list"""
        for profile in self.profiles:
            display_text = f"{profile.name} ({profile.category})"
            self.profile_listbox.insert(tk.END, display_text)
    
    def _on_selection_changed(self, event):
        """Handle profile selection change"""
        selection = self.profile_listbox.curselection()
        if selection:
            index = selection[0]
            profile = self.profiles[index]
            
            # Show profile details
            details = f"Name: {profile.name}\n"
            details += f"Category: {profile.category}\n"
            details += f"Target App: {profile.target_application}\n"
            details += f"Description: {profile.description}\n"
            details += f"Regions: {len(profile.regions)}\n"
            details += f"Rules: {len(profile.rules)}\n"
            details += f"Created: {profile.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            details += f"Modified: {profile.updated_at.strftime('%Y-%m-%d %H:%M')}"
            
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert("1.0", details)
    
    def _on_open(self):
        """Handle Open button"""
        selection = self.profile_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a profile to open.")
            return
        
        index = selection[0]
        self.selected_profile = self.profiles[index]
        self.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button"""
        self.selected_profile = None
        self.destroy()


class ValidationResultDialog(ctk.CTkToplevel):
    """Dialog for displaying profile validation results"""
    
    def __init__(self, parent, result: ValidationResult):
        super().__init__(parent)
        
        self.result = result
        
        self.title("Profile Validation Results")
        self.geometry("600x500")
        self.resizable(True, True)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._setup_layout()
        self._display_results()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        
        # Status label
        if self.result.is_valid:
            status_text = "✅ Profile is valid!"
            status_color = "green"
        else:
            status_text = f"❌ Profile has {len(self.result.errors)} validation errors"
            status_color = "red"
        
        self.status_label = ctk.CTkLabel(
            self.main_frame, text=status_text,
            font=("Arial", 16, "bold")
        )
        
        # Results text area
        self.results_text = ctk.CTkTextbox(self.main_frame, height=300)
        
        # Close button
        self.close_button = ctk.CTkButton(
            self.main_frame, text="Close", width=100,
            command=self.destroy
        )
    
    def _setup_layout(self):
        """Setup dialog layout"""
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.status_label.pack(pady=(0, 20))
        self.results_text.pack(fill="both", expand=True, pady=(0, 20))
        self.close_button.pack()
        
        # Bind Escape key
        self.bind("<Escape>", lambda e: self.destroy())
    
    def _display_results(self):
        """Display validation results"""
        text = ""
        
        if self.result.errors:
            text += "ERRORS:\n"
            text += "=" * 50 + "\n"
            for i, error in enumerate(self.result.errors, 1):
                text += f"{i}. {error}\n"
            text += "\n"
        
        if self.result.warnings:
            text += "WARNINGS:\n"
            text += "=" * 50 + "\n"
            for i, warning in enumerate(self.result.warnings, 1):
                text += f"{i}. {warning}\n"
            text += "\n"
        
        if self.result.is_valid and not self.result.warnings:
            text = "Profile validation passed successfully!\n\n"
            text += "All regions, rules, and settings are properly configured."
        
        self.results_text.insert("1.0", text)


class RegionEditorDialog(ctk.CTkToplevel):
    """Dialog for creating/editing regions"""
    
    def __init__(self, parent, region: Optional[Region] = None):
        super().__init__(parent)
        
        self.region = region
        self.result: Optional[Region] = None
        
        title = "Edit Region" if region else "New Region"
        self.title(title)
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._setup_layout()
        
        if region:
            self._load_region_data()
        
        self.name_entry.focus()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        
        # Region name
        self.name_label = ctk.CTkLabel(self.main_frame, text="Region Name:")
        self.name_entry = ctk.CTkEntry(self.main_frame, width=300)
        
        # Position and size
        self.pos_label = ctk.CTkLabel(self.main_frame, text="Position and Size:", 
                                     font=("Arial", 14, "bold"))
        
        self.x_label = ctk.CTkLabel(self.main_frame, text="X:")
        self.x_entry = ctk.CTkEntry(self.main_frame, width=100)
        
        self.y_label = ctk.CTkLabel(self.main_frame, text="Y:")
        self.y_entry = ctk.CTkEntry(self.main_frame, width=100)
        
        self.width_label = ctk.CTkLabel(self.main_frame, text="Width:")
        self.width_entry = ctk.CTkEntry(self.main_frame, width=100)
        
        self.height_label = ctk.CTkLabel(self.main_frame, text="Height:")
        self.height_entry = ctk.CTkEntry(self.main_frame, width=100)
        
        # Description
        self.desc_label = ctk.CTkLabel(self.main_frame, text="Description:")
        self.desc_text = ctk.CTkTextbox(self.main_frame, width=300, height=100)
        
        # Options
        self.options_label = ctk.CTkLabel(self.main_frame, text="Options:", 
                                         font=("Arial", 14, "bold"))
        
        self.ocr_var = ctk.BooleanVar()
        self.ocr_check = ctk.CTkCheckBox(
            self.main_frame, text="Enable OCR", variable=self.ocr_var
        )
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        
        self.capture_button = ctk.CTkButton(
            self.button_frame, text="Capture Region", width=120,
            command=self._capture_region
        )
        
        self.ok_button = ctk.CTkButton(
            self.button_frame, text="OK", width=100,
            command=self._on_ok
        )
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", width=100,
            command=self._on_cancel
        )
    
    def _setup_layout(self):
        """Setup dialog layout"""
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.name_label.pack(anchor="w", pady=(0, 5))
        self.name_entry.pack(anchor="w", pady=(0, 15))
        
        self.pos_label.pack(anchor="w", pady=(0, 10))
        
        # Position/size in grid
        pos_frame = ctk.CTkFrame(self.main_frame)
        pos_frame.pack(fill="x", pady=(0, 15))
        
        self.x_label.pack(in_=pos_frame, side="left", padx=(10, 5))
        self.x_entry.pack(in_=pos_frame, side="left", padx=(0, 20))
        
        self.y_label.pack(in_=pos_frame, side="left", padx=(0, 5))
        self.y_entry.pack(in_=pos_frame, side="left", padx=(0, 20))
        
        size_frame = ctk.CTkFrame(self.main_frame)
        size_frame.pack(fill="x", pady=(0, 15))
        
        self.width_label.pack(in_=size_frame, side="left", padx=(10, 5))
        self.width_entry.pack(in_=size_frame, side="left", padx=(0, 20))
        
        self.height_label.pack(in_=size_frame, side="left", padx=(0, 5))
        self.height_entry.pack(in_=size_frame, side="left", padx=(0, 20))
        
        self.desc_label.pack(anchor="w", pady=(0, 5))
        self.desc_text.pack(anchor="w", pady=(0, 15))
        
        self.options_label.pack(anchor="w", pady=(0, 10))
        self.ocr_check.pack(anchor="w", pady=(0, 20))
        
        self.button_frame.pack(fill="x")
        self.capture_button.pack(side="left", padx=(0, 10))
        self.ok_button.pack(side="right", padx=(5, 0))
        self.cancel_button.pack(side="right", padx=(5, 5))
        
        # Bind keys
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _load_region_data(self):
        """Load existing region data into form"""
        if not self.region:
            return
        
        self.name_entry.insert(0, self.region.name)
        self.x_entry.insert(0, str(self.region.x))
        self.y_entry.insert(0, str(self.region.y))
        self.width_entry.insert(0, str(self.region.width))
        self.height_entry.insert(0, str(self.region.height))
        self.desc_text.insert("1.0", self.region.description)
        self.ocr_var.set(self.region.ocr_enabled)
    
    def _capture_region(self):
        """Capture region from screen"""
        # This would integrate with screen capture functionality
        messagebox.showinfo("Capture Region", "Screen capture not yet implemented")
    
    def _on_ok(self):
        """Handle OK button"""
        try:
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Input", "Region name is required.")
                return
            
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
            
            if width <= 0 or height <= 0:
                messagebox.showwarning("Invalid Input", "Width and height must be positive.")
                return
            
            description = self.desc_text.get("1.0", tk.END).strip()
            ocr_enabled = self.ocr_var.get()
            
            if self.region:
                # Update existing region
                self.region.name = name
                self.region.x = x
                self.region.y = y
                self.region.width = width
                self.region.height = height
                self.region.description = description
                self.region.ocr_enabled = ocr_enabled
                self.result = self.region
            else:
                # Create new region
                self.result = Region(
                    name=name,
                    x=x, y=y, width=width, height=height,
                    description=description,
                    ocr_enabled=ocr_enabled
                )
            
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for position and size.")
    
    def _on_cancel(self):
        """Handle Cancel button"""
        self.result = None
        self.destroy()


class RuleEditorDialog(ctk.CTkToplevel):
    """Dialog for creating/editing rules"""
    
    def __init__(self, parent, regions: List[Region], rule: Optional[Rule] = None):
        super().__init__(parent)
        
        self.regions = regions
        self.rule = rule
        self.result: Optional[Rule] = None
        
        title = "Edit Rule" if rule else "New Rule"
        self.title(title)
        self.geometry("700x800")
        self.resizable(True, True)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._setup_layout()
        
        if rule:
            self._load_rule_data()
        
        self.name_entry.focus()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame with scrollable content
        self.main_frame = ctk.CTkScrollableFrame(self)
        
        # Basic info
        self.info_label = ctk.CTkLabel(self.main_frame, text="Rule Information", 
                                      font=("Arial", 16, "bold"))
        
        self.name_label = ctk.CTkLabel(self.main_frame, text="Rule Name:")
        self.name_entry = ctk.CTkEntry(self.main_frame, width=400)
        
        self.desc_label = ctk.CTkLabel(self.main_frame, text="Description:")
        self.desc_text = ctk.CTkTextbox(self.main_frame, width=400, height=80)
        
        self.priority_label = ctk.CTkLabel(self.main_frame, text="Priority:")
        self.priority_entry = ctk.CTkEntry(self.main_frame, width=100)
        self.priority_entry.insert(0, "1")
        
        self.enabled_var = ctk.BooleanVar(value=True)
        self.enabled_check = ctk.CTkCheckBox(
            self.main_frame, text="Enabled", variable=self.enabled_var
        )
        
        self.logic_label = ctk.CTkLabel(self.main_frame, text="Logical Operator:")
        self.logic_combo = ctk.CTkComboBox(
            self.main_frame, values=["AND", "OR"], width=100
        )
        self.logic_combo.set("AND")
        
        # Conditions section
        self.conditions_label = ctk.CTkLabel(self.main_frame, text="Conditions", 
                                           font=("Arial", 16, "bold"))
        
        self.conditions_frame = ctk.CTkFrame(self.main_frame)
        self.conditions_list = tk.Listbox(self.conditions_frame, height=6)
        
        self.add_condition_btn = ctk.CTkButton(
            self.conditions_frame, text="Add Condition", width=120,
            command=self._add_condition
        )
        self.edit_condition_btn = ctk.CTkButton(
            self.conditions_frame, text="Edit", width=80,
            command=self._edit_condition
        )
        self.remove_condition_btn = ctk.CTkButton(
            self.conditions_frame, text="Remove", width=80,
            command=self._remove_condition
        )
        
        # Actions section
        self.actions_label = ctk.CTkLabel(self.main_frame, text="Actions", 
                                        font=("Arial", 16, "bold"))
        
        self.actions_frame = ctk.CTkFrame(self.main_frame)
        self.actions_list = tk.Listbox(self.actions_frame, height=6)
        
        self.add_action_btn = ctk.CTkButton(
            self.actions_frame, text="Add Action", width=120,
            command=self._add_action
        )
        self.edit_action_btn = ctk.CTkButton(
            self.actions_frame, text="Edit", width=80,
            command=self._edit_action
        )
        self.remove_action_btn = ctk.CTkButton(
            self.actions_frame, text="Remove", width=80,
            command=self._remove_action
        )
        
        # Dialog buttons
        self.button_frame = ctk.CTkFrame(self)
        self.ok_button = ctk.CTkButton(
            self.button_frame, text="OK", width=100,
            command=self._on_ok
        )
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", width=100,
            command=self._on_cancel
        )
    
    def _setup_layout(self):
        """Setup dialog layout"""
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Basic info
        self.info_label.pack(anchor="w", pady=(0, 15))
        
        self.name_label.pack(anchor="w", pady=(0, 5))
        self.name_entry.pack(anchor="w", pady=(0, 10))
        
        self.desc_label.pack(anchor="w", pady=(0, 5))
        self.desc_text.pack(anchor="w", pady=(0, 10))
        
        # Priority and options in row
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", pady=(0, 20))
        
        self.priority_label.pack(in_=options_frame, side="left", padx=(10, 5))
        self.priority_entry.pack(in_=options_frame, side="left", padx=(0, 20))
        
        self.logic_label.pack(in_=options_frame, side="left", padx=(0, 5))
        self.logic_combo.pack(in_=options_frame, side="left", padx=(0, 20))
        
        self.enabled_check.pack(in_=options_frame, side="left", padx=(0, 10))
        
        # Conditions
        self.conditions_label.pack(anchor="w", pady=(0, 10))
        self.conditions_frame.pack(fill="x", pady=(0, 20))
        
        self.conditions_list.pack(fill="x", padx=10, pady=10)
        
        cond_btn_frame = ctk.CTkFrame(self.conditions_frame)
        cond_btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.add_condition_btn.pack(in_=cond_btn_frame, side="left", padx=(0, 5))
        self.edit_condition_btn.pack(in_=cond_btn_frame, side="left", padx=(0, 5))
        self.remove_condition_btn.pack(in_=cond_btn_frame, side="left")
        
        # Actions
        self.actions_label.pack(anchor="w", pady=(0, 10))
        self.actions_frame.pack(fill="x", pady=(0, 20))
        
        self.actions_list.pack(fill="x", padx=10, pady=10)
        
        act_btn_frame = ctk.CTkFrame(self.actions_frame)
        act_btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.add_action_btn.pack(in_=act_btn_frame, side="left", padx=(0, 5))
        self.edit_action_btn.pack(in_=act_btn_frame, side="left", padx=(0, 5))
        self.remove_action_btn.pack(in_=act_btn_frame, side="left")
        
        # Dialog buttons
        self.button_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.ok_button.pack(side="right", padx=(5, 0))
        self.cancel_button.pack(side="right", padx=(5, 5))
        
        # Bind keys
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _load_rule_data(self):
        """Load existing rule data into form"""
        if not self.rule:
            return
        
        self.name_entry.insert(0, self.rule.name)
        self.desc_text.insert("1.0", self.rule.description)
        self.priority_entry.delete(0, tk.END)
        self.priority_entry.insert(0, str(self.rule.priority))
        self.enabled_var.set(self.rule.enabled)
        self.logic_combo.set(self.rule.logical_operator)
        
        # Load conditions and actions
        self._refresh_conditions()
        self._refresh_actions()
    
    def _refresh_conditions(self):
        """Refresh conditions list"""
        self.conditions_list.delete(0, tk.END)
        if self.rule:
            for condition in self.rule.conditions:
                display = f"{condition.condition_type.value}: {condition.parameters}"
                self.conditions_list.insert(tk.END, display)
    
    def _refresh_actions(self):
        """Refresh actions list"""
        self.actions_list.delete(0, tk.END)
        if self.rule:
            for action in self.rule.actions:
                display = f"{action.action_type.value}: {action.parameters}"
                self.actions_list.insert(tk.END, display)
    
    def _add_condition(self):
        """Add new condition"""
        messagebox.showinfo("Add Condition", "Condition editor not yet implemented")
    
    def _edit_condition(self):
        """Edit selected condition"""
        messagebox.showinfo("Edit Condition", "Condition editor not yet implemented")
    
    def _remove_condition(self):
        """Remove selected condition"""
        selection = self.conditions_list.curselection()
        if selection and self.rule:
            index = selection[0]
            del self.rule.conditions[index]
            self._refresh_conditions()
    
    def _add_action(self):
        """Add new action"""
        messagebox.showinfo("Add Action", "Action editor not yet implemented")
    
    def _edit_action(self):
        """Edit selected action"""
        messagebox.showinfo("Edit Action", "Action editor not yet implemented")
    
    def _remove_action(self):
        """Remove selected action"""
        selection = self.actions_list.curselection()
        if selection and self.rule:
            index = selection[0]
            del self.rule.actions[index]
            self._refresh_actions()
    
    def _on_ok(self):
        """Handle OK button"""
        try:
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Input", "Rule name is required.")
                return
            
            description = self.desc_text.get("1.0", tk.END).strip()
            priority = int(self.priority_entry.get())
            enabled = self.enabled_var.get()
            logical_operator = self.logic_combo.get()
            
            if self.rule:
                # Update existing rule
                self.rule.name = name
                self.rule.description = description
                self.rule.priority = priority
                self.rule.enabled = enabled
                self.rule.logical_operator = logical_operator
                self.result = self.rule
            else:
                # Create new rule
                self.result = Rule(
                    name=name,
                    description=description,
                    priority=priority,
                    enabled=enabled,
                    logical_operator=logical_operator,
                    conditions=[],
                    actions=[]
                )
            
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid priority number.")
    
    def _on_cancel(self):
        """Handle Cancel button"""
        self.result = None
        self.destroy()