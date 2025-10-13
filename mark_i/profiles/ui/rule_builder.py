Condition] = rule.conditions.copy() if rule else []
        self.actions: List[Action] = rule.actions.copy() if rule else []
        
        self.result: Optional[Rule] = None
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
        if rule:
            self._load_rule_data()
        else:
            self._set_defaults()
        
        self._refresh_lists()
        
        self.logger.info("RuleBuilder initialized")
    
    def _setup_window(self):
        """Configure the builder window"""
        title = "Edit Rule" if self.rule else "Create New Rule"
        self.title(title)
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Center on parent
        if self.master:
            self.transient(self.master)
            self.grab_set()
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        
        # Create notebook for sections
        self.notebook = ttk.Notebook(self.main_frame)
        
        # Basic Info tab
        self.info_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.info_frame, text="Rule Info")
        self._create_info_tab()
        
        # Conditions tab
        self.conditions_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.conditions_frame, text="Conditions")
        self._create_conditions_tab()
        
        # Actions tab
        self.actions_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.actions_frame, text="Actions")
        self._create_actions_tab()
        
        # Test tab
        self.test_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.test_frame, text="Test")
        self._create_test_tab()
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self._create_buttons()
    
    def _create_info_tab(self):
        """Create rule information tab"""
        # Configure grid
        self.info_frame.grid_columnconfigure(1, weight=1)
        
        # Rule name
        ctk.CTkLabel(self.info_frame, text="Rule Name:").grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        self.name_entry = ctk.CTkEntry(self.info_frame, width=300)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        # Description
        ctk.CTkLabel(self.info_frame, text="Description:").grid(
            row=1, column=0, sticky="nw", padx=10, pady=5
        )
        self.description_text = ctk.CTkTextbox(self.info_frame, height=100)
        self.description_text.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # Priority
        ctk.CTkLabel(self.info_frame, text="Priority:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5
        )
        self.priority_entry = ctk.CTkEntry(self.info_frame, width=100)
        self.priority_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Enabled
        self.enabled_var = ctk.BooleanVar(value=True)
        self.enabled_check = ctk.CTkCheckBox(
            self.info_frame, text="Rule Enabled", variable=self.enabled_var
        )
        self.enabled_check.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Logical operator
        ctk.CTkLabel(self.info_frame, text="Condition Logic:").grid(
            row=4, column=0, sticky="w", padx=10, pady=5
        )
        self.logic_combo = ctk.CTkComboBox(
            self.info_frame, values=["AND", "OR"], width=100
        )
        self.logic_combo.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        # Help text
        help_text = ("Priority determines execution order (lower numbers execute first).\\n"
                    "AND logic requires ALL conditions to be true.\\n"
                    "OR logic requires ANY condition to be true.")
        
        help_label = ctk.CTkLabel(
            self.info_frame, text=help_text,
            font=("Arial", 10), text_color="gray"
        )
        help_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=10)
    
    def _create_conditions_tab(self):
        """Create conditions management tab"""
        # Configure grid
        self.conditions_frame.grid_columnconfigure(1, weight=1)
        self.conditions_frame.grid_rowconfigure(1, weight=1)
        
        # Conditions list
        conditions_list_frame = ctk.CTkFrame(self.conditions_frame)
        conditions_list_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        conditions_list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(conditions_list_frame, text="Conditions", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=5)
        
        # Conditions listbox
        self.conditions_listbox = tk.Listbox(conditions_list_frame, height=15)
        self.conditions_listbox.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.conditions_listbox.bind("<<ListboxSelect>>", self._on_condition_selected)
        
        # Condition buttons
        self.add_condition_btn = ctk.CTkButton(
            conditions_list_frame, text="Add", width=80,
            command=self._add_condition
        )
        self.add_condition_btn.grid(row=2, column=0, padx=2, pady=5)
        
        self.edit_condition_btn = ctk.CTkButton(
            conditions_list_frame, text="Edit", width=80,
            command=self._edit_condition
        )
        self.edit_condition_btn.grid(row=2, column=1, padx=2, pady=5)
        
        self.remove_condition_btn = ctk.CTkButton(
            conditions_list_frame, text="Remove", width=80,
            command=self._remove_condition
        )
        self.remove_condition_btn.grid(row=2, column=2, padx=2, pady=5)
        
        # Condition details frame
        self.condition_details_frame = ctk.CTkFrame(self.conditions_frame)
        self.condition_details_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        self.condition_details_frame.grid_columnconfigure(1, weight=1)
        
        self._create_condition_details()
    
    def _create_condition_details(self):
        """Create condition details editor"""
        ctk.CTkLabel(self.condition_details_frame, text="Condition Details", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Condition type
        ctk.CTkLabel(self.condition_details_frame, text="Type:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5
        )
        
        condition_types = [ct.value for ct in ConditionType]
        self.condition_type_combo = ctk.CTkComboBox(
            self.condition_details_frame, values=condition_types, width=200,
            command=self._on_condition_type_changed
        )
        self.condition_type_combo.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Region selection
        ctk.CTkLabel(self.condition_details_frame, text="Region:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5
        )
        
        region_names = [region.name for region in self.regions] + ["Screen", "Window"]
        self.condition_region_combo = ctk.CTkComboBox(
            self.condition_details_frame, values=region_names, width=200
        )
        self.condition_region_combo.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Parameters frame (dynamic based on condition type)
        self.condition_params_frame = ctk.CTkFrame(self.condition_details_frame)
        self.condition_params_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Update condition button
        self.update_condition_btn = ctk.CTkButton(
            self.condition_details_frame, text="Update Condition",
            command=self._update_condition
        )
        self.update_condition_btn.grid(row=4, column=0, columnspan=2, pady=10)
    
    def _create_actions_tab(self):
        """Create actions management tab"""
        # Configure grid
        self.actions_frame.grid_columnconfigure(1, weight=1)
        self.actions_frame.grid_rowconfigure(1, weight=1)
        
        # Actions list
        actions_list_frame = ctk.CTkFrame(self.actions_frame)
        actions_list_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        actions_list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(actions_list_frame, text="Actions", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=5)
        
        # Actions listbox
        self.actions_listbox = tk.Listbox(actions_list_frame, height=15)
        self.actions_listbox.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.actions_listbox.bind("<<ListboxSelect>>", self._on_action_selected)
        
        # Action buttons
        self.add_action_btn = ctk.CTkButton(
            actions_list_frame, text="Add", width=80,
            command=self._add_action
        )
        self.add_action_btn.grid(row=2, column=0, padx=2, pady=5)
        
        self.edit_action_btn = ctk.CTkButton(
            actions_list_frame, text="Edit", width=80,
            command=self._edit_action
        )
        self.edit_action_btn.grid(row=2, column=1, padx=2, pady=5)
        
        self.remove_action_btn = ctk.CTkButton(
            actions_list_frame, text="Remove", width=80,
            command=self._remove_action
        )
        self.remove_action_btn.grid(row=2, column=2, padx=2, pady=5)
        
        # Action details frame
        self.action_details_frame = ctk.CTkFrame(self.actions_frame)
        self.action_details_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        self.action_details_frame.grid_columnconfigure(1, weight=1)
        
        self._create_action_details()
    
    def _create_action_details(self):
        """Create action details editor"""
        ctk.CTkLabel(self.action_details_frame, text="Action Details", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Action type
        ctk.CTkLabel(self.action_details_frame, text="Type:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5
        )
        
        action_types = [at.value for at in ActionType]
        self.action_type_combo = ctk.CTkComboBox(
            self.action_details_frame, values=action_types, width=200,
            command=self._on_action_type_changed
        )
        self.action_type_combo.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Target region
        ctk.CTkLabel(self.action_details_frame, text="Target:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5
        )
        
        target_names = [region.name for region in self.regions] + ["Screen", "Window", "System"]
        self.action_target_combo = ctk.CTkComboBox(
            self.action_details_frame, values=target_names, width=200
        )
        self.action_target_combo.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Parameters frame (dynamic based on action type)
        self.action_params_frame = ctk.CTkFrame(self.action_details_frame)
        self.action_params_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Update action button
        self.update_action_btn = ctk.CTkButton(
            self.action_details_frame, text="Update Action",
            command=self._update_action
        )
        self.update_action_btn.grid(row=4, column=0, columnspan=2, pady=10)
    
    def _create_test_tab(self):
        """Create rule testing tab"""
        # Test controls
        test_controls_frame = ctk.CTkFrame(self.test_frame)
        test_controls_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(test_controls_frame, text="Rule Testing", 
                    font=("Arial", 16, "bold")).pack(pady=5)
        
        self.validate_rule_btn = ctk.CTkButton(
            test_controls_frame, text="Validate Rule",
            command=self._validate_rule
        )
        self.validate_rule_btn.pack(side="left", padx=5, pady=5)
        
        self.test_conditions_btn = ctk.CTkButton(
            test_controls_frame, text="Test Conditions",
            command=self._test_conditions
        )
        self.test_conditions_btn.pack(side="left", padx=5, pady=5)
        
        self.simulate_rule_btn = ctk.CTkButton(
            test_controls_frame, text="Simulate Rule",
            command=self._simulate_rule
        )
        self.simulate_rule_btn.pack(side="left", padx=5, pady=5)
        
        # Test results
        test_results_frame = ctk.CTkFrame(self.test_frame)
        test_results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(test_results_frame, text="Test Results", 
                    font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        
        self.test_output = ctk.CTkTextbox(test_results_frame, height=300)
        self.test_output.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _create_buttons(self):
        """Create dialog buttons"""
        self.ok_button = ctk.CTkButton(
            self.button_frame, text="Save Rule", width=120,
            command=self._save_rule
        )
        self.ok_button.pack(side="right", padx=5, pady=10)
        
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", width=100,
            command=self._cancel
        )
        self.cancel_button.pack(side="right", padx=5, pady=10)
        
        self.apply_button = ctk.CTkButton(
            self.button_frame, text="Apply", width=100,
            command=self._apply_changes
        )
        self.apply_button.pack(side="right", padx=5, pady=10)
    
    def _setup_layout(self):
        """Setup main layout"""
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))
        self.button_frame.pack(fill="x")
    
    def _bind_events(self):
        """Bind event handlers"""
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())
    
    def _set_defaults(self):
        """Set default values for new rule"""
        self.name_entry.insert(0, "New Rule")
        self.priority_entry.insert(0, "1")
        self.logic_combo.set("AND")
    
    def _load_rule_data(self):
        """Load existing rule data"""
        if not self.rule:
            return
        
        self.name_entry.insert(0, self.rule.name)
        self.description_text.insert("1.0", self.rule.description)
        self.priority_entry.insert(0, str(self.rule.priority))
        self.enabled_var.set(self.rule.enabled)
        self.logic_combo.set(self.rule.logical_operator)
    
    def _refresh_lists(self):
        """Refresh conditions and actions lists"""
        # Refresh conditions
        self.conditions_listbox.delete(0, tk.END)
        for i, condition in enumerate(self.conditions):
            display = f"{i+1}. {condition.condition_type.value}"
            if condition.region_name:
                display += f" ({condition.region_name})"
            self.conditions_listbox.insert(tk.END, display)
        
        # Refresh actions
        self.actions_listbox.delete(0, tk.END)
        for i, action in enumerate(self.actions):
            display = f"{i+1}. {action.action_type.value}"
            if action.target_region:
                display += f" ({action.target_region})"
            self.actions_listbox.insert(tk.END, display)
    
    def _on_condition_selected(self, event):
        """Handle condition selection"""
        selection = self.conditions_listbox.curselection()
        if selection:
            index = selection[0]
            condition = self.conditions[index]
            self._load_condition_to_editor(condition)
    
    def _on_action_selected(self, event):
        """Handle action selection"""
        selection = self.actions_listbox.curselection()
        if selection:
            index = selection[0]
            action = self.actions[index]
            self._load_action_to_editor(action)
    
    def _load_condition_to_editor(self, condition: Condition):
        """Load condition into editor"""
        self.condition_type_combo.set(condition.condition_type.value)
        if condition.region_name:
            self.condition_region_combo.set(condition.region_name)
        
        self._update_condition_params(condition.condition_type, condition.parameters)
    
    def _load_action_to_editor(self, action: Action):
        """Load action into editor"""
        self.action_type_combo.set(action.action_type.value)
        if action.target_region:
            self.action_target_combo.set(action.target_region)
        
        self._update_action_params(action.action_type, action.parameters)
    
    def _on_condition_type_changed(self, value):
        """Handle condition type change"""
        try:
            condition_type = ConditionType(value)
            self._update_condition_params(condition_type)
        except ValueError:
            pass
    
    def _on_action_type_changed(self, value):
        """Handle action type change"""
        try:
            action_type = ActionType(value)
            self._update_action_params(action_type)
        except ValueError:
            pass
    
    def _update_condition_params(self, condition_type: ConditionType, params: Dict[str, Any] = None):
        """Update condition parameters UI based on type"""
        # Clear existing params
        for widget in self.condition_params_frame.winfo_children():
            widget.destroy()
        
        params = params or {}
        
        if condition_type == ConditionType.VISUAL_MATCH:
            self._create_visual_match_params(self.condition_params_frame, params)
        elif condition_type == ConditionType.OCR_CONTAINS:
            self._create_ocr_params(self.condition_params_frame, params)
        elif condition_type == ConditionType.TEMPLATE_MATCH:
            self._create_template_params(self.condition_params_frame, params)
        elif condition_type == ConditionType.SYSTEM_STATE:
            self._create_system_state_params(self.condition_params_frame, params)
        elif condition_type == ConditionType.TIME_BASED:
            self._create_time_params(self.condition_params_frame, params)
    
    def _update_action_params(self, action_type: ActionType, params: Dict[str, Any] = None):
        """Update action parameters UI based on type"""
        # Clear existing params
        for widget in self.action_params_frame.winfo_children():
            widget.destroy()
        
        params = params or {}
        
        if action_type == ActionType.CLICK:
            self._create_click_params(self.action_params_frame, params)
        elif action_type == ActionType.TYPE_TEXT:
            self._create_type_text_params(self.action_params_frame, params)
        elif action_type == ActionType.WAIT:
            self._create_wait_params(self.action_params_frame, params)
        elif action_type == ActionType.ASK_USER:
            self._create_ask_user_params(self.action_params_frame, params)
        elif action_type == ActionType.RUN_COMMAND:
            self._create_run_command_params(self.action_params_frame, params)
    
    def _create_visual_match_params(self, parent, params):
        """Create visual match condition parameters"""
        ctk.CTkLabel(parent, text="Template Image:").pack(anchor="w", pady=2)
        self.visual_template_entry = ctk.CTkEntry(parent, width=300)
        self.visual_template_entry.pack(anchor="w", pady=2)
        if "template_path" in params:
            self.visual_template_entry.insert(0, params["template_path"])
        
        ctk.CTkLabel(parent, text="Match Threshold (0.0-1.0):").pack(anchor="w", pady=2)
        self.visual_threshold_entry = ctk.CTkEntry(parent, width=100)
        self.visual_threshold_entry.pack(anchor="w", pady=2)
        self.visual_threshold_entry.insert(0, str(params.get("threshold", 0.8)))
    
    def _create_ocr_params(self, parent, params):
        """Create OCR condition parameters"""
        ctk.CTkLabel(parent, text="Text to Find:").pack(anchor="w", pady=2)
        self.ocr_text_entry = ctk.CTkEntry(parent, width=300)
        self.ocr_text_entry.pack(anchor="w", pady=2)
        if "text" in params:
            self.ocr_text_entry.insert(0, params["text"])
        
        self.ocr_case_var = ctk.BooleanVar(value=params.get("case_sensitive", False))
        self.ocr_case_check = ctk.CTkCheckBox(
            parent, text="Case Sensitive", variable=self.ocr_case_var
        )
        self.ocr_case_check.pack(anchor="w", pady=2)
    
    def _create_template_params(self, parent, params):
        """Create template match parameters"""
        ctk.CTkLabel(parent, text="Template File:").pack(anchor="w", pady=2)
        self.template_file_entry = ctk.CTkEntry(parent, width=300)
        self.template_file_entry.pack(anchor="w", pady=2)
        if "template_file" in params:
            self.template_file_entry.insert(0, params["template_file"])
        
        ctk.CTkLabel(parent, text="Confidence (0.0-1.0):").pack(anchor="w", pady=2)
        self.template_confidence_entry = ctk.CTkEntry(parent, width=100)
        self.template_confidence_entry.pack(anchor="w", pady=2)
        self.template_confidence_entry.insert(0, str(params.get("confidence", 0.8)))
    
    def _create_system_state_params(self, parent, params):
        """Create system state parameters"""
        ctk.CTkLabel(parent, text="State Type:").pack(anchor="w", pady=2)
        self.state_type_combo = ctk.CTkComboBox(
            parent, values=["window_active", "process_running", "file_exists", "network_connected"]
        )
        self.state_type_combo.pack(anchor="w", pady=2)
        if "state_type" in params:
            self.state_type_combo.set(params["state_type"])
        
        ctk.CTkLabel(parent, text="State Value:").pack(anchor="w", pady=2)
        self.state_value_entry = ctk.CTkEntry(parent, width=300)
        self.state_value_entry.pack(anchor="w", pady=2)
        if "state_value" in params:
            self.state_value_entry.insert(0, params["state_value"])
    
    def _create_time_params(self, parent, params):
        """Create time-based parameters"""
        ctk.CTkLabel(parent, text="Time Condition:").pack(anchor="w", pady=2)
        self.time_condition_combo = ctk.CTkComboBox(
            parent, values=["after_time", "before_time", "between_times", "day_of_week"]
        )
        self.time_condition_combo.pack(anchor="w", pady=2)
        if "time_condition" in params:
            self.time_condition_combo.set(params["time_condition"])
        
        ctk.CTkLabel(parent, text="Time Value:").pack(anchor="w", pady=2)
        self.time_value_entry = ctk.CTkEntry(parent, width=200)
        self.time_value_entry.pack(anchor="w", pady=2)
        if "time_value" in params:
            self.time_value_entry.insert(0, params["time_value"])
    
    def _create_click_params(self, parent, params):
        """Create click action parameters"""
        ctk.CTkLabel(parent, text="Click Type:").pack(anchor="w", pady=2)
        self.click_type_combo = ctk.CTkComboBox(
            parent, values=["left", "right", "double", "middle"]
        )
        self.click_type_combo.pack(anchor="w", pady=2)
        self.click_type_combo.set(params.get("click_type", "left"))
        
        ctk.CTkLabel(parent, text="Position Offset (x,y):").pack(anchor="w", pady=2)
        offset_frame = ctk.CTkFrame(parent)
        offset_frame.pack(anchor="w", pady=2)
        
        self.click_x_entry = ctk.CTkEntry(offset_frame, width=80)
        self.click_x_entry.pack(side="left", padx=2)
        self.click_x_entry.insert(0, str(params.get("offset_x", 0)))
        
        self.click_y_entry = ctk.CTkEntry(offset_frame, width=80)
        self.click_y_entry.pack(side="left", padx=2)
        self.click_y_entry.insert(0, str(params.get("offset_y", 0)))
    
    def _create_type_text_params(self, parent, params):
        """Create type text action parameters"""
        ctk.CTkLabel(parent, text="Text to Type:").pack(anchor="w", pady=2)
        self.type_text_entry = ctk.CTkTextbox(parent, height=80)
        self.type_text_entry.pack(anchor="w", pady=2, fill="x")
        if "text" in params:
            self.type_text_entry.insert("1.0", params["text"])
        
        self.type_clear_var = ctk.BooleanVar(value=params.get("clear_first", False))
        self.type_clear_check = ctk.CTkCheckBox(
            parent, text="Clear field first", variable=self.type_clear_var
        )
        self.type_clear_check.pack(anchor="w", pady=2)
    
    def _create_wait_params(self, parent, params):
        """Create wait action parameters"""
        ctk.CTkLabel(parent, text="Wait Duration (seconds):").pack(anchor="w", pady=2)
        self.wait_duration_entry = ctk.CTkEntry(parent, width=100)
        self.wait_duration_entry.pack(anchor="w", pady=2)
        self.wait_duration_entry.insert(0, str(params.get("duration", 1.0)))
        
        ctk.CTkLabel(parent, text="Wait Type:").pack(anchor="w", pady=2)
        self.wait_type_combo = ctk.CTkComboBox(
            parent, values=["fixed", "random", "until_condition"]
        )
        self.wait_type_combo.pack(anchor="w", pady=2)
        self.wait_type_combo.set(params.get("wait_type", "fixed"))
    
    def _create_ask_user_params(self, parent, params):
        """Create ask user action parameters"""
        ctk.CTkLabel(parent, text="Question/Prompt:").pack(anchor="w", pady=2)
        self.ask_prompt_entry = ctk.CTkTextbox(parent, height=60)
        self.ask_prompt_entry.pack(anchor="w", pady=2, fill="x")
        if "prompt" in params:
            self.ask_prompt_entry.insert("1.0", params["prompt"])
        
        ctk.CTkLabel(parent, text="Input Type:").pack(anchor="w", pady=2)
        self.ask_type_combo = ctk.CTkComboBox(
            parent, values=["text", "yes_no", "choice", "file_path"]
        )
        self.ask_type_combo.pack(anchor="w", pady=2)
        self.ask_type_combo.set(params.get("input_type", "text"))
    
    def _create_run_command_params(self, parent, params):
        """Create run command action parameters"""
        ctk.CTkLabel(parent, text="Command:").pack(anchor="w", pady=2)
        self.command_entry = ctk.CTkEntry(parent, width=400)
        self.command_entry.pack(anchor="w", pady=2, fill="x")
        if "command" in params:
            self.command_entry.insert(0, params["command"])
        
        self.command_wait_var = ctk.BooleanVar(value=params.get("wait_for_completion", True))
        self.command_wait_check = ctk.CTkCheckBox(
            parent, text="Wait for completion", variable=self.command_wait_var
        )
        self.command_wait_check.pack(anchor="w", pady=2)
    
    # Event handlers
    
    def _add_condition(self):
        """Add new condition"""
        condition = Condition(
            condition_type=ConditionType.VISUAL_MATCH,
            region_name="",
            parameters={}
        )
        self.conditions.append(condition)
        self._refresh_lists()
        
        # Select the new condition
        self.conditions_listbox.selection_set(len(self.conditions) - 1)
        self._load_condition_to_editor(condition)
    
    def _edit_condition(self):
        """Edit selected condition"""
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a condition to edit.")
            return
        
        index = selection[0]
        condition = self.conditions[index]
        self._load_condition_to_editor(condition)
    
    def _remove_condition(self):
        """Remove selected condition"""
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a condition to remove.")
            return
        
        if messagebox.askyesno("Confirm", "Remove selected condition?"):
            index = selection[0]
            del self.conditions[index]
            self._refresh_lists()
    
    def _update_condition(self):
        """Update condition from editor"""
        selection = self.conditions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a condition to update.")
            return
        
        try:
            index = selection[0]
            condition = self.conditions[index]
            
            # Update basic properties
            condition.condition_type = ConditionType(self.condition_type_combo.get())
            condition.region_name = self.condition_region_combo.get()
            
            # Update parameters based on type
            condition.parameters = self._get_condition_parameters(condition.condition_type)
            
            self._refresh_lists()
            messagebox.showinfo("Success", "Condition updated successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update condition: {str(e)}")
    
    def _get_condition_parameters(self, condition_type: ConditionType) -> Dict[str, Any]:
        """Get condition parameters from UI"""
        params = {}
        
        if condition_type == ConditionType.VISUAL_MATCH:
            params["template_path"] = self.visual_template_entry.get()
            params["threshold"] = float(self.visual_threshold_entry.get())
        elif condition_type == ConditionType.OCR_CONTAINS:
            params["text"] = self.ocr_text_entry.get()
            params["case_sensitive"] = self.ocr_case_var.get()
        elif condition_type == ConditionType.TEMPLATE_MATCH:
            params["template_file"] = self.template_file_entry.get()
            params["confidence"] = float(self.template_confidence_entry.get())
        elif condition_type == ConditionType.SYSTEM_STATE:
            params["state_type"] = self.state_type_combo.get()
            params["state_value"] = self.state_value_entry.get()
        elif condition_type == ConditionType.TIME_BASED:
            params["time_condition"] = self.time_condition_combo.get()
            params["time_value"] = self.time_value_entry.get()
        
        return params
    
    def _add_action(self):
        """Add new action"""
        action = Action(
            action_type=ActionType.CLICK,
            target_region="",
            parameters={}
        )
        self.actions.append(action)
        self._refresh_lists()
        
        # Select the new action
        self.actions_listbox.selection_set(len(self.actions) - 1)
        self._load_action_to_editor(action)
    
    def _edit_action(self):
        """Edit selected action"""
        selection = self.actions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an action to edit.")
            return
        
        index = selection[0]
        action = self.actions[index]
        self._load_action_to_editor(action)
    
    def _remove_action(self):
        """Remove selected action"""
        selection = self.actions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an action to remove.")
            return
        
        if messagebox.askyesno("Confirm", "Remove selected action?"):
            index = selection[0]
            del self.actions[index]
            self._refresh_lists()
    
    def _update_action(self):
        """Update action from editor"""
        selection = self.actions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an action to update.")
            return
        
        try:
            index = selection[0]
            action = self.actions[index]
            
            # Update basic properties
            action.action_type = ActionType(self.action_type_combo.get())
            action.target_region = self.action_target_combo.get()
            
            # Update parameters based on type
            action.parameters = self._get_action_parameters(action.action_type)
            
            self._refresh_lists()
            messagebox.showinfo("Success", "Action updated successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update action: {str(e)}")
    
    def _get_action_parameters(self, action_type: ActionType) -> Dict[str, Any]:
        """Get action parameters from UI"""
        params = {}
        
        if action_type == ActionType.CLICK:
            params["click_type"] = self.click_type_combo.get()
            params["offset_x"] = int(self.click_x_entry.get())
            params["offset_y"] = int(self.click_y_entry.get())
        elif action_type == ActionType.TYPE_TEXT:
            params["text"] = self.type_text_entry.get("1.0", tk.END).strip()
            params["clear_first"] = self.type_clear_var.get()
        elif action_type == ActionType.WAIT:
            params["duration"] = float(self.wait_duration_entry.get())
            params["wait_type"] = self.wait_type_combo.get()
        elif action_type == ActionType.ASK_USER:
            params["prompt"] = self.ask_prompt_entry.get("1.0", tk.END).strip()
            params["input_type"] = self.ask_type_combo.get()
        elif action_type == ActionType.RUN_COMMAND:
            params["command"] = self.command_entry.get()
            params["wait_for_completion"] = self.command_wait_var.get()
        
        return params
    
    def _validate_rule(self):
        """Validate the current rule"""
        try:
            rule = self._build_rule()
            
            # Basic validation
            errors = []
            warnings = []
            
            if not rule.name.strip():
                errors.append("Rule name is required")
            
            if not rule.conditions:
                warnings.append("Rule has no conditions - it will always execute")
            
            if not rule.actions:
                errors.append("Rule must have at least one action")
            
            # Validate conditions
            for i, condition in enumerate(rule.conditions):
                if not condition.region_name and condition.condition_type in [
                    ConditionType.VISUAL_MATCH, ConditionType.OCR_CONTAINS, ConditionType.TEMPLATE_MATCH
                ]:
                    warnings.append(f"Condition {i+1} has no region specified")
            
            # Validate actions
            for i, action in enumerate(rule.actions):
                if not action.target_region and action.action_type in [
                    ActionType.CLICK, ActionType.TYPE_TEXT
                ]:
                    warnings.append(f"Action {i+1} has no target region specified")
            
            # Display results
            result_text = "Rule Validation Results:\\n\\n"
            
            if not errors:
                result_text += "✅ Rule validation passed!\\n\\n"
            else:
                result_text += "❌ Validation Errors:\\n"
                for error in errors:
                    result_text += f"  • {error}\\n"
                result_text += "\\n"
            
            if warnings:
                result_text += "⚠️ Warnings:\\n"
                for warning in warnings:
                    result_text += f"  • {warning}\\n"
            
            self.test_output.delete("1.0", tk.END)
            self.test_output.insert("1.0", result_text)
            
        except Exception as e:
            self.test_output.delete("1.0", tk.END)
            self.test_output.insert("1.0", f"Validation failed: {str(e)}")
    
    def _test_conditions(self):
        """Test rule conditions"""
        self.test_output.delete("1.0", tk.END)
        self.test_output.insert("1.0", "Condition testing not yet implemented.\\nThis will test each condition against current screen state.")
    
    def _simulate_rule(self):
        """Simulate rule execution"""
        self.test_output.delete("1.0", tk.END)
        self.test_output.insert("1.0", "Rule simulation not yet implemented.\\nThis will show step-by-step execution preview.")
    
    def _build_rule(self) -> Rule:
        """Build rule from current UI state"""
        name = self.name_entry.get().strip()
        description = self.description_text.get("1.0", tk.END).strip()
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
            self.rule.conditions = self.conditions.copy()
            self.rule.actions = self.actions.copy()
            return self.rule
        else:
            # Create new rule
            return Rule(
                name=name,
                description=description,
                priority=priority,
                enabled=enabled,
                logical_operator=logical_operator,
                conditions=self.conditions.copy(),
                actions=self.actions.copy()
            )
    
    def _apply_changes(self):
        """Apply changes without closing"""
        try:
            self.result = self._build_rule()
            if self.callback:
                self.callback(self.result)
            messagebox.showinfo("Success", "Rule changes applied successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply changes: {str(e)}")
    
    def _save_rule(self):
        """Save rule and close"""
        try:
            self.result = self._build_rule()
            if self.callback:
                self.callback(self.result)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save rule: {str(e)}")
    
    def _cancel(self):
        """Cancel and close"""
        self.result = None
        self.destroy()


def create_rule(parent=None, regions: List[Region] = None, callback: Optional[Callable[[Rule], None]] = None) -> Optional[Rule]:
    """Create a new rule using the rule builder"""
    builder = RuleBuilder(parent, regions, None, callback)
    
    if not callback:
        parent.wait_window(builder) if parent else builder.mainloop()
        return builder.result
    
    return None


def edit_rule(rule: Rule, parent=None, regions: List[Region] = None, callback: Optional[Callable[[Rule], None]] = None) -> Optional[Rule]:
    """Edit an existing rule using the rule builder"""
    builder = RuleBuilder(parent, regions, rule, callback)
    
    if not callback:
        parent.wait_window(builder) if parent else builder.mainloop()
        return builder.result
    
    return None