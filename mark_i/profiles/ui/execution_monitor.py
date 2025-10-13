"""
Execution Monitor Interface

Real-time monitoring interface for profile execution with progress tracking,
control buttons, execution history, and error reporting.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional, Callable
import logging
from datetime import datetime
from enum import Enum

from ..models.profile import AutomationProfile
from ..testing.profile_tester import ProfileTester, TestResult, TestStep, TestMode
from ..testing.execution_logger import ExecutionLogger, LogEntry, LogLevel


class ExecutionState(Enum):
    """Execution states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMonitorWindow(ctk.CTkToplevel):
    """Real-time execution monitoring interface"""
    
    def __init__(self, parent=None, profile: AutomationProfile = None):
        super().__init__(parent)
        
        self.profile = profile
        self.logger = logging.getLogger("mark_i.profiles.ui.execution_monitor")
        
        # Execution components
        self.profile_tester = ProfileTester()
        self.execution_logger = ExecutionLogger()
        
        # Execution state
        self.execution_state = ExecutionState.IDLE
        self.current_test_result: Optional[TestResult] = None
        self.execution_start_time: Optional[datetime] = None
        self.current_step_index = 0
        
        # Callbacks
        self.on_execution_complete: Optional[Callable[[TestResult], None]] = None
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
        if profile:
            self._load_profile(profile)
        
        self.logger.info("ExecutionMonitorWindow initialized")
    
    def _setup_window(self):
        """Configure the monitor window"""
        title = f"Execution Monitor"
        if self.profile:
            title += f" - {self.profile.name}"
        
        self.title(title)
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
        
        # Create control panel
        self._create_control_panel()
        
        # Create main content area
        self._create_content_area()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_control_panel(self):
        """Create execution control panel"""
        self.control_panel = ctk.CTkFrame(self.main_frame, height=80)
        self.control_panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.control_panel.grid_propagate(False)
        self.control_panel.grid_columnconfigure(6, weight=1)
        
        # Profile info
        self.profile_info_frame = ctk.CTkFrame(self.control_panel)
        self.profile_info_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        self.profile_name_label = ctk.CTkLabel(
            self.profile_info_frame, 
            text="No Profile Loaded",
            font=("Arial", 14, "bold")
        )
        self.profile_name_label.pack(anchor="w", padx=10, pady=2)
        
        self.profile_details_label = ctk.CTkLabel(
            self.profile_info_frame,
            text="",
            font=("Arial", 10)
        )
        self.profile_details_label.pack(anchor="w", padx=10, pady=2)
        
        # Execution mode selection
        self.mode_frame = ctk.CTkFrame(self.control_panel)
        self.mode_frame.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        ctk.CTkLabel(self.mode_frame, text="Execution Mode:").pack(anchor="w", padx=5, pady=2)
        
        self.mode_combo = ctk.CTkComboBox(
            self.mode_frame,
            values=["Simulation", "Dry Run", "Step by Step", "Full Execution"],
            width=150
        )
        self.mode_combo.pack(anchor="w", padx=5, pady=2)
        self.mode_combo.set("Simulation")
        
        # Control buttons
        self.buttons_frame = ctk.CTkFrame(self.control_panel)
        self.buttons_frame.grid(row=0, column=2, sticky="e", padx=10, pady=10)
        
        self.start_btn = ctk.CTkButton(
            self.buttons_frame, text="Start", width=80,
            command=self.start_execution,
            state="disabled"
        )
        self.start_btn.pack(side="left", padx=2)
        
        self.pause_btn = ctk.CTkButton(
            self.buttons_frame, text="Pause", width=80,
            command=self.pause_execution,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=2)
        
        self.step_btn = ctk.CTkButton(
            self.buttons_frame, text="Step", width=80,
            command=self.step_execution,
            state="disabled"
        )
        self.step_btn.pack(side="left", padx=2)
        
        self.stop_btn = ctk.CTkButton(
            self.buttons_frame, text="Stop", width=80,
            command=self.stop_execution,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=2)
        
        self.reset_btn = ctk.CTkButton(
            self.buttons_frame, text="Reset", width=80,
            command=self.reset_execution
        )
        self.reset_btn.pack(side="left", padx=2)
    
    def _create_content_area(self):
        """Create main content area with tabs"""
        # Create notebook for different views
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Progress tab
        self.progress_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.progress_frame, text="Progress")
        self._create_progress_tab()
        
        # Steps tab
        self.steps_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.steps_frame, text="Steps")
        self._create_steps_tab()
        
        # Logs tab
        self.logs_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.logs_frame, text="Logs")
        self._create_logs_tab()
        
        # History tab
        self.history_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.history_frame, text="History")
        self._create_history_tab()
    
    def _create_progress_tab(self):
        """Create execution progress tab"""
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_rowconfigure(2, weight=1)
        
        # Overall progress
        progress_info_frame = ctk.CTkFrame(self.progress_frame)
        progress_info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        progress_info_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(progress_info_frame, text="Overall Progress", 
                    font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        # Progress bar
        self.overall_progress = ttk.Progressbar(
            progress_info_frame, mode='determinate', length=400
        )
        self.overall_progress.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Progress labels
        self.progress_label = ctk.CTkLabel(progress_info_frame, text="Ready to start")
        self.progress_label.grid(row=2, column=0, sticky="w", padx=10, pady=2)
        
        self.time_label = ctk.CTkLabel(progress_info_frame, text="")
        self.time_label.grid(row=2, column=1, sticky="e", padx=10, pady=2)
        
        # Current step info
        current_step_frame = ctk.CTkFrame(self.progress_frame)
        current_step_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        current_step_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(current_step_frame, text="Current Step", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        self.current_step_label = ctk.CTkLabel(current_step_frame, text="No step active")
        self.current_step_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        
        self.step_progress = ttk.Progressbar(
            current_step_frame, mode='indeterminate', length=400
        )
        self.step_progress.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Execution summary
        summary_frame = ctk.CTkFrame(self.progress_frame)
        summary_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        summary_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(summary_frame, text="Execution Summary", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        # Summary stats
        stats_frame = ctk.CTkFrame(summary_frame)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.stats_labels = {}
        stats = ["Total Steps", "Completed", "Failed", "Skipped", "Success Rate"]
        
        for i, stat in enumerate(stats):
            label = ctk.CTkLabel(stats_frame, text=f"{stat}: 0")
            label.grid(row=i//3, column=i%3, sticky="w", padx=10, pady=2)
            self.stats_labels[stat] = label
    
    def _create_steps_tab(self):
        """Create execution steps tab"""
        self.steps_frame.grid_columnconfigure(0, weight=1)
        self.steps_frame.grid_rowconfigure(1, weight=1)
        
        # Steps header
        steps_header = ctk.CTkFrame(self.steps_frame)
        steps_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(steps_header, text="Execution Steps", 
                    font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=5)
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(steps_header)
        filter_frame.pack(side="right", padx=10, pady=5)
        
        self.show_all_btn = ctk.CTkButton(
            filter_frame, text="All", width=60,
            command=lambda: self._filter_steps("all")
        )
        self.show_all_btn.pack(side="left", padx=2)
        
        self.show_errors_btn = ctk.CTkButton(
            filter_frame, text="Errors", width=60,
            command=lambda: self._filter_steps("errors")
        )
        self.show_errors_btn.pack(side="left", padx=2)
        
        # Steps tree
        self.steps_tree = ttk.Treeview(
            self.steps_frame,
            columns=("status", "duration", "result"),
            show="tree headings",
            height=20
        )
        
        self.steps_tree.heading("#0", text="Step")
        self.steps_tree.heading("status", text="Status")
        self.steps_tree.heading("duration", text="Duration")
        self.steps_tree.heading("result", text="Result")
        
        self.steps_tree.column("#0", width=300)
        self.steps_tree.column("status", width=100)
        self.steps_tree.column("duration", width=100)
        self.steps_tree.column("result", width=200)
        
        self.steps_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Steps scrollbar
        steps_scrollbar = ttk.Scrollbar(self.steps_frame, orient="vertical", command=self.steps_tree.yview)
        steps_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
        self.steps_tree.configure(yscrollcommand=steps_scrollbar.set)
    
    def _create_logs_tab(self):
        """Create execution logs tab"""
        self.logs_frame.grid_columnconfigure(0, weight=1)
        self.logs_frame.grid_rowconfigure(1, weight=1)
        
        # Logs header
        logs_header = ctk.CTkFrame(self.logs_frame)
        logs_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(logs_header, text="Execution Logs", 
                    font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=5)
        
        # Log level filter
        level_frame = ctk.CTkFrame(logs_header)
        level_frame.pack(side="right", padx=10, pady=5)
        
        ctk.CTkLabel(level_frame, text="Level:").pack(side="left", padx=5)
        
        self.log_level_combo = ctk.CTkComboBox(
            level_frame,
            values=["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            command=self._filter_logs,
            width=100
        )
        self.log_level_combo.pack(side="left", padx=5)
        self.log_level_combo.set("All")
        
        # Clear logs button
        self.clear_logs_btn = ctk.CTkButton(
            level_frame, text="Clear", width=60,
            command=self._clear_logs
        )
        self.clear_logs_btn.pack(side="left", padx=5)
        
        # Logs text area
        self.logs_text = ctk.CTkTextbox(self.logs_frame, height=400)
        self.logs_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    
    def _create_history_tab(self):
        """Create execution history tab"""
        self.history_frame.grid_columnconfigure(0, weight=1)
        self.history_frame.grid_rowconfigure(1, weight=1)
        
        # History header
        history_header = ctk.CTkFrame(self.history_frame)
        history_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(history_header, text="Execution History", 
                    font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=5)
        
        # History controls
        history_controls = ctk.CTkFrame(history_header)
        history_controls.pack(side="right", padx=10, pady=5)
        
        self.export_history_btn = ctk.CTkButton(
            history_controls, text="Export", width=80,
            command=self._export_history
        )
        self.export_history_btn.pack(side="left", padx=5)
        
        self.clear_history_btn = ctk.CTkButton(
            history_controls, text="Clear", width=80,
            command=self._clear_history
        )
        self.clear_history_btn.pack(side="left", padx=5)
        
        # History tree
        self.history_tree = ttk.Treeview(
            self.history_frame,
            columns=("start_time", "duration", "status", "steps", "errors"),
            show="tree headings",
            height=20
        )
        
        self.history_tree.heading("#0", text="Execution ID")
        self.history_tree.heading("start_time", text="Start Time")
        self.history_tree.heading("duration", text="Duration")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("steps", text="Steps")
        self.history_tree.heading("errors", text="Errors")
        
        self.history_tree.column("#0", width=200)
        self.history_tree.column("start_time", width=150)
        self.history_tree.column("duration", width=100)
        self.history_tree.column("status", width=100)
        self.history_tree.column("steps", width=80)
        self.history_tree.column("errors", width=80)
        
        self.history_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # History scrollbar
        history_scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=self.history_tree.yview)
        history_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ctk.CTkFrame(self.main_frame, height=30)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.status_bar.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready")
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.execution_time_label = ctk.CTkLabel(self.status_bar, text="")
        self.execution_time_label.grid(row=0, column=1, sticky="e", padx=10, pady=5)
    
    def _bind_events(self):
        """Bind event handlers"""
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Bind tester callbacks
        self.profile_tester.on_step_start = self._on_step_start
        self.profile_tester.on_step_complete = self._on_step_complete
        self.profile_tester.on_test_complete = self._on_test_complete
    
    def _load_profile(self, profile: AutomationProfile):
        """Load profile for execution"""
        self.profile = profile
        
        # Update UI
        self.profile_name_label.configure(text=profile.name)
        self.profile_details_label.configure(
            text=f"{profile.category.title()} • {len(profile.regions)} regions • {len(profile.rules)} rules"
        )
        
        # Enable start button
        self.start_btn.configure(state="normal")
        
        self._update_status(f"Loaded profile: {profile.name}")
    
    def _update_status(self, message: str):
        """Update status bar message"""
        self.status_label.configure(text=message)
        self.logger.info(message)
    
    def _update_execution_time(self):
        """Update execution time display"""
        if self.execution_start_time and self.execution_state == ExecutionState.RUNNING:
            elapsed = (datetime.now() - self.execution_start_time).total_seconds()
            self.execution_time_label.configure(text=f"Elapsed: {elapsed:.1f}s")
            
            # Schedule next update
            self.after(1000, self._update_execution_time)
    
    def _update_progress(self):
        """Update progress displays"""
        if not self.current_test_result:
            return
        
        # Update overall progress
        total_steps = len(self.current_test_result.steps)
        completed_steps = len([s for s in self.current_test_result.steps if s.status in ['passed', 'failed', 'skipped']])
        
        if total_steps > 0:
            progress = (completed_steps / total_steps) * 100
            self.overall_progress['value'] = progress
            self.progress_label.configure(text=f"Step {completed_steps} of {total_steps}")
        
        # Update summary stats
        summary = self.current_test_result.summary
        self.stats_labels["Total Steps"].configure(text=f"Total Steps: {summary['total']}")
        self.stats_labels["Completed"].configure(text=f"Completed: {summary['passed']}")
        self.stats_labels["Failed"].configure(text=f"Failed: {summary['failed']}")
        self.stats_labels["Skipped"].configure(text=f"Skipped: {summary['skipped']}")
        
        if summary['total'] > 0:
            success_rate = (summary['passed'] / summary['total']) * 100
            self.stats_labels["Success Rate"].configure(text=f"Success Rate: {success_rate:.1f}%")
    
    def _update_steps_display(self):
        """Update steps tree display"""
        if not self.current_test_result:
            return
        
        # Clear existing items
        for item in self.steps_tree.get_children():
            self.steps_tree.delete(item)
        
        # Add steps
        for step in self.current_test_result.steps:
            status_icon = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'running': '🔄',
                'pending': '⏸️'
            }.get(step.status, '❓')
            
            duration_text = f"{step.duration:.2f}s" if step.duration else ""
            result_text = str(step.result) if step.result else (step.error or "")
            
            self.steps_tree.insert("", "end",
                                 text=f"{status_icon} {step.step_name}",
                                 values=(step.status.title(), duration_text, result_text))
    
    def _add_log_entry(self, level: str, message: str):
        """Add log entry to logs display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}\n"
        
        self.logs_text.insert(tk.END, log_line)
        self.logs_text.see(tk.END)  # Auto-scroll to bottomtionProfile):
        """Set the profile for execution"""
        self._load_profile(profile)