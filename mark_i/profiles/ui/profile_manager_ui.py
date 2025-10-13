"""
Profile Manager UI

Main interface for browsing, organizing, and managing automation profiles.
Provides category-based organization, search, filtering, and batch operations.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional, Callable
import logging
from datetime import datetime
from pathlib import Path

from ..models.profile import AutomationProfile
from ..profile_manager import ProfileManager
from ..validation.profile_validator import ProfileValidator
from ..templates.template_manager import TemplateManager
from .profile_editor import ProfileEditorWindow


class ProfileManagerWindow(ctk.CTkToplevel):
    """Main profile management interface"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.profile_manager = ProfileManager()
        self.validator = ProfileValidator()
        self.template_manager = TemplateManager()
        self.logger = logging.getLogger("mark_i.profiles.ui.manager")
        
        # UI state
        self.profiles: List[AutomationProfile] = []
        self.filtered_profiles: List[AutomationProfile] = []
        self.selected_profiles: List[AutomationProfile] = []
        self.current_category = "all"
        self.search_query = ""
        
        # Callbacks
        self.on_profile_selected: Optional[Callable[[AutomationProfile], None]] = None
        self.on_profile_executed: Optional[Callable[[AutomationProfile], None]] = None
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        self._load_profiles()
        
        self.logger.info("ProfileManagerWindow initialized")
    
    def _setup_window(self):
        """Configure the main window"""
        self.title("MARK-I Profile Manager")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        
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
        
        # Create main content area
        self._create_content_area()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self):
        """Create the toolbar with main actions"""
        self.toolbar = ctk.CTkFrame(self.main_frame, height=60)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.toolbar.grid_columnconfigure(8, weight=1)  # Spacer
        
        # New profile button
        self.new_btn = ctk.CTkButton(
            self.toolbar, text="New Profile", width=100,
            command=self.new_profile
        )
        self.new_btn.grid(row=0, column=0, padx=5, pady=10)
        
        # Import button
        self.import_btn = ctk.CTkButton(
            self.toolbar, text="Import", width=80,
            command=self.import_profile
        )
        self.import_btn.grid(row=0, column=1, padx=5, pady=10)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            self.toolbar, text="Export", width=80,
            command=self.export_selected
        )
        self.export_btn.grid(row=0, column=2, padx=5, pady=10)
        
        # Separator
        separator = ctk.CTkFrame(self.toolbar, width=2, height=40)
        separator.grid(row=0, column=3, padx=10, pady=10)
        
        # Edit button
        self.edit_btn = ctk.CTkButton(
            self.toolbar, text="Edit", width=80,
            command=self.edit_selected,
            state="disabled"
        )
        self.edit_btn.grid(row=0, column=4, padx=5, pady=10)
        
        # Duplicate button
        self.duplicate_btn = ctk.CTkButton(
            self.toolbar, text="Duplicate", width=80,
            command=self.duplicate_selected,
            state="disabled"
        )
        self.duplicate_btn.grid(row=0, column=5, padx=5, pady=10)
        
        # Delete button
        self.delete_btn = ctk.CTkButton(
            self.toolbar, text="Delete", width=80,
            command=self.delete_selected,
            state="disabled"
        )
        self.delete_btn.grid(row=0, column=6, padx=5, pady=10)
        
        # Execute button
        self.execute_btn = ctk.CTkButton(
            self.toolbar, text="Execute", width=80,
            command=self.execute_selected,
            state="disabled"
        )
        self.execute_btn.grid(row=0, column=7, padx=5, pady=10)
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self.toolbar, text="Refresh", width=80,
            command=self.refresh_profiles
        )
        self.refresh_btn.grid(row=0, column=9, padx=5, pady=10)
    
    def _create_content_area(self):
        """Create the main content area"""
        # Left panel - Categories and search
        self.left_panel = ctk.CTkFrame(self.main_frame, width=250)
        self.left_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.left_panel.grid_propagate(False)
        self.left_panel.grid_rowconfigure(2, weight=1)
        
        self._create_search_panel()
        self._create_category_panel()
        self._create_template_panel()
        
        # Right panel - Profile list and details
        self.right_panel = ctk.CTkFrame(self.main_frame)
        self.right_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1)
        
        self._create_profile_list()
        self._create_profile_details()
    
    def _create_search_panel(self):
        """Create search and filter panel"""
        search_frame = ctk.CTkFrame(self.left_panel)
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        search_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(search_frame, text="Search Profiles", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, pady=5)
        
        # Search entry
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search by name, description, or tags...")
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        # Filter options
        filter_frame = ctk.CTkFrame(search_frame)
        filter_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.show_enabled_var = ctk.BooleanVar(value=True)
        self.show_enabled_check = ctk.CTkCheckBox(
            filter_frame, text="Show enabled only", 
            variable=self.show_enabled_var,
            command=self._apply_filters
        )
        self.show_enabled_check.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.show_templates_var = ctk.BooleanVar(value=True)
        self.show_templates_check = ctk.CTkCheckBox(
            filter_frame, text="Include templates",
            variable=self.show_templates_var,
            command=self._apply_filters
        )
        self.show_templates_check.grid(row=1, column=0, sticky="w", padx=5, pady=2)
    
    def _create_category_panel(self):
        """Create category selection panel"""
        category_frame = ctk.CTkFrame(self.left_panel)
        category_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        category_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(category_frame, text="Categories", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, pady=5)
        
        # Category buttons
        categories = [
            ("All", "all"),
            ("Email", "email"),
            ("Web", "web"),
            ("Files", "files"),
            ("Templates", "templates"),
            ("Custom", "custom")
        ]
        
        self.category_buttons = {}
        for i, (name, category) in enumerate(categories):
            btn = ctk.CTkButton(
                category_frame, text=name, width=200,
                command=lambda c=category: self._select_category(c)
            )
            btn.grid(row=i+1, column=0, padx=5, pady=2, sticky="ew")
            self.category_buttons[category] = btn
        
        # Highlight "All" by default
        self.category_buttons["all"].configure(fg_color=("gray75", "gray25"))
    
    def _create_template_panel(self):
        """Create template management panel"""
        template_frame = ctk.CTkFrame(self.left_panel)
        template_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        template_frame.grid_columnconfigure(0, weight=1)
        template_frame.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(template_frame, text="Templates", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, pady=5)
        
        # Template category selection
        self.template_category_combo = ctk.CTkComboBox(
            template_frame, 
            values=["email", "web", "system"],
            command=self._on_template_category_changed
        )
        self.template_category_combo.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Template list
        self.template_listbox = tk.Listbox(template_frame, height=8)
        self.template_listbox.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create from template button
        self.create_from_template_btn = ctk.CTkButton(
            template_frame, text="Create from Template",
            command=self.create_from_template
        )
        self.create_from_template_btn.grid(row=3, column=0, padx=5, pady=5)
        
        # Load initial templates
        self._load_templates()
    
    def _create_profile_list(self):
        """Create profile list with details"""
        # Profile list frame
        list_frame = ctk.CTkFrame(self.right_panel)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        # List header
        header_frame = ctk.CTkFrame(list_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(0, weight=1)
        
        self.profile_count_label = ctk.CTkLabel(
            header_frame, text="0 profiles", 
            font=("Arial", 12, "bold")
        )
        self.profile_count_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Sort options
        sort_frame = ctk.CTkFrame(header_frame)
        sort_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)
        
        ctk.CTkLabel(sort_frame, text="Sort by:").grid(row=0, column=0, padx=5)
        
        self.sort_combo = ctk.CTkComboBox(
            sort_frame,
            values=["Name", "Category", "Created", "Modified", "Priority"],
            command=self._on_sort_changed,
            width=120
        )
        self.sort_combo.grid(row=0, column=1, padx=5)
        self.sort_combo.set("Name")
        
        # Profile tree view
        self.profile_tree = ttk.Treeview(
            list_frame,
            columns=("category", "target_app", "regions", "rules", "created", "status"),
            show="tree headings",
            height=15
        )
        
        # Configure columns
        self.profile_tree.heading("#0", text="Name")
        self.profile_tree.heading("category", text="Category")
        self.profile_tree.heading("target_app", text="Target App")
        self.profile_tree.heading("regions", text="Regions")
        self.profile_tree.heading("rules", text="Rules")
        self.profile_tree.heading("created", text="Created")
        self.profile_tree.heading("status", text="Status")
        
        self.profile_tree.column("#0", width=200)
        self.profile_tree.column("category", width=80)
        self.profile_tree.column("target_app", width=120)
        self.profile_tree.column("regions", width=60)
        self.profile_tree.column("rules", width=60)
        self.profile_tree.column("created", width=100)
        self.profile_tree.column("status", width=80)
        
        self.profile_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Scrollbar for tree
        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.profile_tree.yview)
        tree_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
        self.profile_tree.configure(yscrollcommand=tree_scrollbar.set)
    
    def _create_profile_details(self):
        """Create profile details panel"""
        details_frame = ctk.CTkFrame(self.right_panel, height=200)
        details_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        details_frame.grid_propagate(False)
        details_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(details_frame, text="Profile Details", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        # Details text area
        self.details_text = ctk.CTkTextbox(details_frame, height=150)
        self.details_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        
        # Action buttons for selected profile
        actions_frame = ctk.CTkFrame(details_frame)
        actions_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.validate_profile_btn = ctk.CTkButton(
            actions_frame, text="Validate", width=80,
            command=self.validate_selected,
            state="disabled"
        )
        self.validate_profile_btn.pack(side="left", padx=5)
        
        self.test_profile_btn = ctk.CTkButton(
            actions_frame, text="Test", width=80,
            command=self.test_selected,
            state="disabled"
        )
        self.test_profile_btn.pack(side="left", padx=5)
        
        self.clone_profile_btn = ctk.CTkButton(
            actions_frame, text="Clone", width=80,
            command=self.clone_selected,
            state="disabled"
        )
        self.clone_profile_btn.pack(side="left", padx=5)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ctk.CTkFrame(self.main_frame, height=30)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.status_bar.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready")
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.selection_label = ctk.CTkLabel(self.status_bar, text="")
        self.selection_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def _bind_events(self):
        """Bind event handlers"""
        self.profile_tree.bind("<<TreeviewSelect>>", self._on_profile_selected)
        self.profile_tree.bind("<Double-1>", self._on_profile_double_click)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _load_profiles(self):
        """Load profiles from profile manager"""
        try:
            self.profiles = self.profile_manager.list_profiles()
            self._apply_filters()
            self._update_status(f"Loaded {len(self.profiles)} profiles")
        except Exception as e:
            self.logger.error(f"Failed to load profiles: {e}")
            messagebox.showerror("Error", f"Failed to load profiles: {str(e)}")
    
    def _load_templates(self):
        """Load available templates"""
        try:
            category = self.template_category_combo.get() if hasattr(self, 'template_category_combo') else "email"
            templates = self.template_manager.create_templates(category)
            
            self.template_listbox.delete(0, tk.END)
            for template in templates:
                self.template_listbox.insert(tk.END, template.name)
                
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
    
    def _apply_filters(self):
        """Apply current filters to profile list"""
        filtered = self.profiles.copy()
        
        # Apply category filter
        if self.current_category != "all":
            filtered = [p for p in filtered if p.category == self.current_category]
        
        # Apply search filter
        if self.search_query:
            query = self.search_query.lower()
            filtered = [p for p in filtered if 
                       query in p.name.lower() or 
                       query in p.description.lower() or
                       any(query in tag.lower() for tag in p.tags)]
        
        # Apply enabled filter
        if hasattr(self, 'show_enabled_var') and self.show_enabled_var.get():
            # For now, assume all profiles are enabled
            pass
        
        # Apply template filter
        if hasattr(self, 'show_templates_var') and not self.show_templates_var.get():
            filtered = [p for p in filtered if 'template' not in p.tags]
        
        self.filtered_profiles = filtered
        self._update_profile_list()
    
    def _update_profile_list(self):
        """Update the profile tree view"""
        # Clear existing items
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)
        
        # Sort profiles
        sort_key = self.sort_combo.get() if hasattr(self, 'sort_combo') else "Name"
        if sort_key == "Name":
            self.filtered_profiles.sort(key=lambda p: p.name.lower())
        elif sort_key == "Category":
            self.filtered_profiles.sort(key=lambda p: p.category)
        elif sort_key == "Created":
            self.filtered_profiles.sort(key=lambda p: p.created_at, reverse=True)
        elif sort_key == "Modified":
            self.filtered_profiles.sort(key=lambda p: p.updated_at, reverse=True)
        
        # Add profiles to tree
        for profile in self.filtered_profiles:
            # Determine status
            status = "✅ Ready"
            if 'template' in profile.tags:
                status = "📋 Template"
            elif not profile.rules:
                status = "⚠️ No Rules"
            elif not profile.regions:
                status = "⚠️ No Regions"
            
            # Insert into tree
            self.profile_tree.insert("", "end", 
                                   text=profile.name,
                                   values=(
                                       profile.category.title(),
                                       profile.target_application or "Any",
                                       len(profile.regions),
                                       len(profile.rules),
                                       profile.created_at.strftime("%Y-%m-%d"),
                                       status
                                   ),
                                   tags=(profile.id,))
        
        # Update count
        self.profile_count_label.configure(text=f"{len(self.filtered_profiles)} profiles")
    
    def _select_category(self, category: str):
        """Select a category filter"""
        # Update button appearance
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color=("gray70", "gray30"))
        
        self.current_category = category
        self._apply_filters()
    
    def _on_search_changed(self, event):
        """Handle search query change"""
        self.search_query = self.search_entry.get()
        self._apply_filters()
    
    def _on_sort_changed(self, value):
        """Handle sort option change"""
        self._update_profile_list()
    
    def _on_template_category_changed(self, value):
        """Handle template category change"""
        self._load_templates()
    
    def _on_profile_selected(self, event):
        """Handle profile selection"""
        selection = self.profile_tree.selection()
        if not selection:
            self.selected_profiles = []
            self._update_selection_ui()
            return
        
        # Get selected profiles
        self.selected_profiles = []
        for item in selection:
            profile_id = self.profile_tree.item(item)["tags"][0]
            profile = next((p for p in self.filtered_profiles if p.id == profile_id), None)
            if profile:
                self.selected_profiles.append(profile)
        
        self._update_selection_ui()
        
        # Show details for first selected profile
        if self.selected_profiles:
            self._show_profile_details(self.selected_profiles[0])
    
    def _on_profile_double_click(self, event):
        """Handle profile double-click"""
        if self.selected_profiles:
            self.edit_selected()
    
    def _update_selection_ui(self):
        """Update UI based on current selection"""
        has_selection = len(self.selected_profiles) > 0
        single_selection = len(self.selected_profiles) == 1
        
        # Update toolbar buttons
        self.edit_btn.configure(state="normal" if single_selection else "disabled")
        self.duplicate_btn.configure(state="normal" if single_selection else "disabled")
        self.delete_btn.configure(state="normal" if has_selection else "disabled")
        self.execute_btn.configure(state="normal" if single_selection else "disabled")
        
        # Update detail buttons
        self.validate_profile_btn.configure(state="normal" if single_selection else "disabled")
        self.test_profile_btn.configure(state="normal" if single_selection else "disabled")
        self.clone_profile_btn.configure(state="normal" if single_selection else "disabled")
        
        # Update selection label
        if has_selection:
            self.selection_label.configure(text=f"{len(self.selected_profiles)} selected")
        else:
            self.selection_label.configure(text="")
    
    def _show_profile_details(self, profile: AutomationProfile):
        """Show details for selected profile"""
        details = []
        details.append(f"Name: {profile.name}")
        details.append(f"Category: {profile.category.title()}")
        details.append(f"Target Application: {profile.target_application or 'Any'}")
        details.append(f"Description: {profile.description}")
        details.append("")
        details.append(f"Regions: {len(profile.regions)}")
        details.append(f"Rules: {len(profile.rules)}")
        details.append(f"Tags: {', '.join(profile.tags) if profile.tags else 'None'}")
        details.append("")
        details.append(f"Created: {profile.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        details.append(f"Modified: {profile.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        details.append("")
        
        # Settings summary
        settings = profile.settings
        details.append("Settings:")
        details.append(f"  Monitoring Interval: {settings.monitoring_interval_seconds}s")
        details.append(f"  Max Execution Time: {settings.max_execution_time_seconds}s")
        details.append(f"  Template Threshold: {settings.template_match_threshold}")
        details.append(f"  OCR Threshold: {settings.ocr_confidence_threshold}")
        details.append(f"  Use Gemini: {settings.use_gemini_analysis}")
        
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", "\n".join(details))
    
    def _update_status(self, message: str):
        """Update status bar message"""
        self.status_label.configure(text=message)
        self.after(3000, lambda: self.status_label.configure(text="Ready"))
    
    def _on_closing(self):
        """Handle window closing"""
        self.destroy()    

    # Action Methods
    
    def new_profile(self):
        """Create a new profile"""
        try:
            editor = ProfileEditorWindow(self, self.profile_manager)
            editor.focus()
        except Exception as e:
            self.logger.error(f"Failed to open profile editor: {e}")
            messagebox.showerror("Error", f"Failed to open profile editor: {str(e)}")
    
    def import_profile(self):
        """Import profile from file"""
        file_path = filedialog.askopenfilename(
            title="Import Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                profile = AutomationProfile.load_from_file(file_path)
                
                # Check if profile already exists
                existing = self.profile_manager.get_profile(profile.id)
                if existing:
                    if not messagebox.askyesno("Profile Exists", 
                                             f"Profile '{profile.name}' already exists. Replace it?"):
                        return
                
                # Save imported profile
                if self.profile_manager.save_profile(profile):
                    self._load_profiles()
                    self._update_status(f"Imported profile: {profile.name}")
                else:
                    messagebox.showerror("Error", "Failed to save imported profile")
                    
            except Exception as e:
                self.logger.error(f"Failed to import profile: {e}")
                messagebox.showerror("Error", f"Failed to import profile: {str(e)}")
    
    def export_selected(self):
        """Export selected profiles"""
        if not self.selected_profiles:
            messagebox.showwarning("No Selection", "Please select profiles to export.")
            return
        
        if len(self.selected_profiles) == 1:
            # Single profile export
            profile = self.selected_profiles[0]
            file_path = filedialog.asksaveasfilename(
                title="Export Profile",
                defaultextension=".json",
                initialvalue=f"{profile.name}.json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                try:
                    if self.profile_manager.export_profile(profile.id, file_path):
                        self._update_status(f"Exported profile: {profile.name}")
                    else:
                        messagebox.showerror("Error", "Failed to export profile")
                except Exception as e:
                    messagebox.showerror("Error", f"Export failed: {str(e)}")
        else:
            # Multiple profile export
            folder_path = filedialog.askdirectory(title="Select Export Folder")
            if folder_path:
                try:
                    exported = 0
                    for profile in self.selected_profiles:
                        file_path = Path(folder_path) / f"{profile.name}.json"
                        if self.profile_manager.export_profile(profile.id, str(file_path)):
                            exported += 1
                    
                    self._update_status(f"Exported {exported} profiles")
                except Exception as e:
                    messagebox.showerror("Error", f"Batch export failed: {str(e)}")
    
    def edit_selected(self):
        """Edit selected profile"""
        if not self.selected_profiles:
            messagebox.showwarning("No Selection", "Please select a profile to edit.")
            return
        
        if len(self.selected_profiles) > 1:
            messagebox.showwarning("Multiple Selection", "Please select only one profile to edit.")
            return
        
        try:
            profile = self.selected_profiles[0]
            editor = ProfileEditorWindow(self, self.profile_manager)
            # Load the profile into the editor
            # This would require enhancing the ProfileEditorWindow to accept a profile parameter
            editor.focus()
        except Exception as e:
            self.logger.error(f"Failed to open profile editor: {e}")
            messagebox.showerror("Error", f"Failed to open profile editor: {str(e)}")
    
    def duplicate_selected(self):
        """Duplicate selected profile"""
        if not self.selected_profiles:
            messagebox.showwarning("No Selection", "Please select a profile to duplicate.")
            return
        
        profile = self.selected_profiles[0]
        
        try:
            # Create a copy with new ID and name
            duplicate = AutomationProfile.from_dict(profile.to_dict())
            duplicate.name = f"{profile.name} (Copy)"
            duplicate.id = AutomationProfile.generate_id()
            duplicate.created_at = datetime.now()
            duplicate.updated_at = datetime.now()
            
            if self.profile_manager.save_profile(duplicate):
                self._load_profiles()
                self._update_status(f"Duplicated profile: {profile.name}")
            else:
                messagebox.showerror("Error", "Failed to save duplicated profile")
                
        except Exception as e:
            self.logger.error(f"Failed to duplicate profile: {e}")
            messagebox.showerror("Error", f"Failed to duplicate profile: {str(e)}")
    
    def delete_selected(self):
        """Delete selected profiles"""
        if not self.selected_profiles:
            messagebox.showwarning("No Selection", "Please select profiles to delete.")
            return
        
        # Confirm deletion
        if len(self.selected_profiles) == 1:
            profile = self.selected_profiles[0]
            if not messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete profile '{profile.name}'?"):
                return
        else:
            if not messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete {len(self.selected_profiles)} profiles?"):
                return
        
        try:
            deleted = 0
            for profile in self.selected_profiles:
                if self.profile_manager.delete_profile(profile.id):
                    deleted += 1
            
            self._load_profiles()
            self._update_status(f"Deleted {deleted} profiles")
            
        except Exception as e:
            self.logger.error(f"Failed to delete profiles: {e}")
            messagebox.showerror("Error", f"Failed to delete profiles: {str(e)}")
    
    def execute_selected(self):
        """Execute selected profile"""
        if not self.selected_profiles:
            messagebox.showwarning("No Selection", "Please select a profile to execute.")
            return
        
        profile = self.selected_profiles[0]
        
        # Validate profile before execution
        validation_result = self.validator.validate_profile(profile)
        if not validation_result.is_valid:
            if not messagebox.askyesno("Validation Errors", 
                                     f"Profile has {len(validation_result.errors)} validation errors. Execute anyway?"):
                return
        
        try:
            if self.on_profile_executed:
                self.on_profile_executed(profile)
            else:
                messagebox.showinfo("Execute Profile", 
                                  f"Profile '{profile.name}' would be executed.\n"
                                  "Integration with ProfileExecutor not yet implemented.")
            
            self._update_status(f"Executed profile: {profile.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to execute profile: {e}")
            messagebox.showerror("Error", f"Failed to execute profile: {str(e)}")
    
    def validate_selected(self):
        """Validate selected profile"""
        if not self.selected_profiles:
            messagebox.showwarning("No Selection", "Please select a profile to validate.")
            return
        
        profile = self.selected_profiles[0]
        
        try:
            result = self.validator.validate_profile(profile)
            
            # Show validation results in a dialog
            ValidationResultDialog(self, result)
            
        except Exception as e:
            self.logger.error(f"Failed to validate profile: {e}")
            messagebox.showerror("Error", f"Failed to validate profile: {str(e)}")
    
    def test_selected(self):
        """Test selected profile"""
        if not self.selected_profiles:
            messagebox.showwarning("No Selection", "Please select a profile to test.")
            return
        
        profile = self.selected_profiles[0]
        
        try:
            # This would integrate with ProfileTester
            messagebox.showinfo("Test Profile", 
                              f"Profile '{profile.name}' would be tested.\n"
                              "Integration with ProfileTester not yet implemented.")
            
        except Exception as e:
            self.logger.error(f"Failed to test profile: {e}")
            messagebox.showerror("Error", f"Failed to test profile: {str(e)}")
    
    def clone_selected(self):
        """Clone selected profile with modifications"""
        if not self.selected_profiles:
            messagebox.showwarning("No Selection", "Please select a profile to clone.")
            return
        
        # For now, same as duplicate
        self.duplicate_selected()
    
    def create_from_template(self):
        """Create profile from selected template"""
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a template.")
            return
        
        try:
            template_name = self.template_listbox.get(selection[0])
            category = self.template_category_combo.get()
            
            # Get template from template manager
            template = self.template_manager.get_template_by_name(template_name, category)
            if not template:
                messagebox.showerror("Error", "Template not found.")
                return
            
            # Customize template
            customizations = self._get_template_customizations()
            if customizations is None:  # User cancelled
                return
            
            # Create customized profile
            customized_profile = self.template_manager.customize_template(template, customizations)
            
            # Save the new profile
            if self.profile_manager.save_profile(customized_profile):
                self._load_profiles()
                self._update_status(f"Created profile from template: {template_name}")
            else:
                messagebox.showerror("Error", "Failed to save profile from template")
                
        except Exception as e:
            self.logger.error(f"Failed to create from template: {e}")
            messagebox.showerror("Error", f"Failed to create from template: {str(e)}")
    
    def refresh_profiles(self):
        """Refresh profile list"""
        self._load_profiles()
        self._update_status("Profiles refreshed")
    
    def _get_template_customizations(self) -> Optional[Dict[str, Any]]:
        """Get template customizations from user"""
        # Simple dialog for template customization
        dialog = TemplateCustomizationDialog(self)
        if dialog.result:
            return dialog.result
        return None


class TemplateCustomizationDialog(ctk.CTkToplevel):
    """Dialog for customizing template profiles"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.result: Optional[Dict[str, Any]] = None
        
        self.title("Customize Template")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._setup_layout()
        
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
        
        # Target application
        self.app_label = ctk.CTkLabel(self.main_frame, text="Target Application:")
        self.app_entry = ctk.CTkEntry(self.main_frame, width=300)
        
        # Tags
        self.tags_label = ctk.CTkLabel(self.main_frame, text="Additional Tags:")
        self.tags_entry = ctk.CTkEntry(self.main_frame, width=300)
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.ok_button = ctk.CTkButton(
            self.button_frame, text="Create", width=100,
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
        
        self.app_label.pack(anchor="w", pady=(0, 5))
        self.app_entry.pack(anchor="w", pady=(0, 10))
        
        self.tags_label.pack(anchor="w", pady=(0, 5))
        self.tags_entry.pack(anchor="w", pady=(0, 20))
        
        self.button_frame.pack(fill="x")
        self.ok_button.pack(side="right", padx=(5, 0))
        self.cancel_button.pack(side="right", padx=(5, 5))
        
        # Bind keys
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _on_ok(self):
        """Handle OK button"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Invalid Input", "Profile name is required.")
            return
        
        description = self.desc_text.get("1.0", tk.END).strip()
        target_app = self.app_entry.get().strip()
        tags_text = self.tags_entry.get().strip()
        
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()] if tags_text else []
        
        self.result = {
            "name": name,
            "description": description,
            "target_application": target_app,
            "tags": tags
        }
        
        self.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button"""
        self.result = None
        self.destroy()


# Import the ValidationResultDialog from dialogs.py
from .dialogs import ValidationResultDialog