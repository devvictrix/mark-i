"""
System Automation Templates

Pre-built templates for system-level automation tasks including file management,
application launching, and system monitoring.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.profile import AutomationProfile, ProfileSettings
from ..models.region import Region
from ..models.rule import Rule, Condition, Action, ConditionType, ActionType


class SystemTemplateBase:
    """Base class for system automation templates"""
    
    def __init__(self, operating_system: str = "windows"):
        self.os = operating_system.lower()
        self.logger = logging.getLogger(f"mark_i.profiles.templates.system.{self.__class__.__name__}")
        
        # OS-specific configurations
        self.os_configs = {
            "windows": {
                "file_manager": "File Explorer",
                "file_manager_shortcut": "Win+E",
                "run_dialog_shortcut": "Win+R",
                "task_manager_shortcut": "Ctrl+Shift+Esc",
                "desktop_shortcut": "Win+D"
            },
            "macos": {
                "file_manager": "Finder",
                "file_manager_shortcut": "Cmd+Space",
                "run_dialog_shortcut": "Cmd+Space",
                "task_manager_shortcut": "Cmd+Option+Esc",
                "desktop_shortcut": "F11"
            },
            "linux": {
                "file_manager": "Files",
                "file_manager_shortcut": "Ctrl+Alt+F",
                "run_dialog_shortcut": "Alt+F2",
                "task_manager_shortcut": "Ctrl+Shift+Esc",
                "desktop_shortcut": "Ctrl+Alt+D"
            }
        }
    
    def get_os_config(self) -> Dict[str, str]:
        """Get configuration for current operating system"""
        return self.os_configs.get(self.os, self.os_configs["windows"])
    
    def create_base_profile(self, name: str, description: str) -> AutomationProfile:
        """Create base system automation profile"""
        profile = AutomationProfile.create_new(
            name=name,
            description=description,
            category="files",
            target_application="System"
        )
        
        # Configure system-specific settings
        profile.settings.monitoring_interval_seconds = 1.0
        profile.settings.max_execution_time_seconds = 300  # 5 minutes
        profile.settings.template_match_threshold = 0.8
        profile.settings.ocr_confidence_threshold = 85
        profile.settings.use_gemini_analysis = True
        profile.settings.screenshot_on_error = True
        
        profile.tags.extend(["system", self.os, "automation"])
        
        return profileclass
 FileManagementTemplate(SystemTemplateBase):
    """Template for automated file management tasks"""
    
    def create_template(self,
                       file_explorer_region: Optional[Region] = None,
                       file_list_region: Optional[Region] = None,
                       toolbar_region: Optional[Region] = None) -> AutomationProfile:
        """Create file management automation profile"""
        
        profile = self.create_base_profile(
            name=f"File Management - {self.os.title()}",
            description=f"Automated file organization and management for {self.os.title()}"
        )
        
        # Define default regions if not provided
        if not file_explorer_region:
            file_explorer_region = Region(
                name="File Explorer Window",
                x=100, y=100, width=800, height=600,
                description="Main file explorer window",
                ocr_enabled=True
            )
        
        if not file_list_region:
            file_list_region = Region(
                name="File List Area",
                x=200, y=200, width=600, height=400,
                description="File and folder listing area",
                ocr_enabled=True
            )
        
        if not toolbar_region:
            toolbar_region = Region(
                name="Toolbar",
                x=100, y=150, width=800, height=40,
                description="File explorer toolbar",
                ocr_enabled=True
            )
        
        # Add regions to profile
        profile.regions.extend([file_explorer_region, file_list_region, toolbar_region])
        
        # Create file organization rule
        organize_rule = Rule(
            name="Organize Files by Type",
            description="Sort and organize files by file type into folders",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.SYSTEM_STATE,
                    region_name="",
                    parameters={
                        "state_type": "window_active",
                        "state_value": self.get_os_config()["file_manager"]
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter folder path to organize:",
                        "input_type": "file_path"
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": self.get_os_config()["file_manager_shortcut"],
                        "wait_for_completion": False
                    }
                ),
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 2.0, "wait_type": "fixed"}
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": "Ctrl+L",  # Focus address bar
                        "wait_for_completion": False
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": "Return",
                        "wait_for_completion": False
                    }
                ),
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 2.0, "wait_type": "fixed"}
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Create folders for file types (Images, Documents, etc.)?",
                        "input_type": "yes_no"
                    }
                )
            ]
        )
        
        # Create file cleanup rule
        cleanup_rule = Rule(
            name="Clean Up Old Files",
            description="Delete or archive files older than specified date",
            priority=2,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="File List Area",
                    parameters={
                        "text": "Modified",
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Delete files older than how many days?",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": "Ctrl+A",  # Select all
                        "wait_for_completion": False
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Move selected files to Recycle Bin?",
                        "input_type": "yes_no"
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": "Delete",
                        "wait_for_completion": False
                    }
                )
            ]
        )
        
        profile.rules.extend([organize_rule, cleanup_rule])
        
        self.logger.info(f"Created file management template for {self.os}")
        return profileclass Ap
plicationLaunchTemplate(SystemTemplateBase):
    """Template for automated application launching and management"""
    
    def create_template(self,
                       start_menu_region: Optional[Region] = None,
                       search_box_region: Optional[Region] = None,
                       taskbar_region: Optional[Region] = None) -> AutomationProfile:
        """Create application launch automation profile"""
        
        profile = self.create_base_profile(
            name=f"Application Launcher - {self.os.title()}",
            description=f"Automated application launching and window management for {self.os.title()}"
        )
        
        # Define default regions if not provided
        if not start_menu_region:
            start_menu_region = Region(
                name="Start Menu",
                x=0, y=700, width=400, height=300,
                description="Start menu or application launcher",
                ocr_enabled=True
            )
        
        if not search_box_region:
            search_box_region = Region(
                name="Search Box",
                x=50, y=750, width=300, height=30,
                description="Application search input box",
                ocr_enabled=False
            )
        
        if not taskbar_region:
            taskbar_region = Region(
                name="Taskbar",
                x=0, y=960, width=1920, height=40,
                description="System taskbar",
                ocr_enabled=True
            )
        
        # Add regions to profile
        profile.regions.extend([start_menu_region, search_box_region, taskbar_region])
        
        # Create application launch rule
        launch_rule = Rule(
            name="Launch Application",
            description="Launch specified application by name",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.SYSTEM_STATE,
                    region_name="",
                    parameters={
                        "state_type": "process_running",
                        "state_value": "explorer.exe"
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter application name to launch:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": self.get_os_config()["run_dialog_shortcut"],
                        "wait_for_completion": False
                    }
                ),
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 1.0, "wait_type": "fixed"}
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Search Box",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": "Return",
                        "wait_for_completion": False
                    }
                ),
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 3.0, "wait_type": "fixed"}
                )
            ]
        )
        
        # Create window management rule
        window_rule = Rule(
            name="Manage Application Windows",
            description="Arrange and manage application windows",
            priority=2,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="Taskbar",
                    parameters={
                        "text": "Running",
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Arrange windows? (tile, cascade, minimize all)",
                        "input_type": "choice"
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": "Win+Left",  # Snap to left
                        "wait_for_completion": False
                    }
                )
            ]
        )
        
        profile.rules.extend([launch_rule, window_rule])
        
        self.logger.info(f"Created application launch template for {self.os}")
        return profile


class SystemMonitoringTemplate(SystemTemplateBase):
    """Template for automated system monitoring and maintenance"""
    
    def create_template(self,
                       task_manager_region: Optional[Region] = None,
                       performance_region: Optional[Region] = None,
                       processes_region: Optional[Region] = None) -> AutomationProfile:
        """Create system monitoring automation profile"""
        
        profile = self.create_base_profile(
            name=f"System Monitor - {self.os.title()}",
            description=f"Automated system monitoring and maintenance for {self.os.title()}"
        )
        
        # Define default regions if not provided
        if not task_manager_region:
            task_manager_region = Region(
                name="Task Manager Window",
                x=200, y=100, width=800, height=600,
                description="Task manager or system monitor window",
                ocr_enabled=True
            )
        
        if not performance_region:
            performance_region = Region(
                name="Performance Tab",
                x=250, y=200, width=700, height=400,
                description="System performance metrics area",
                ocr_enabled=True
            )
        
        if not processes_region:
            processes_region = Region(
                name="Processes List",
                x=250, y=200, width=700, height=400,
                description="Running processes list",
                ocr_enabled=True
            )
        
        # Add regions to profile
        profile.regions.extend([task_manager_region, performance_region, processes_region])
        
        # Create system monitoring rule
        monitor_rule = Rule(
            name="Monitor System Performance",
            description="Check system performance and resource usage",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.TIME_BASED,
                    region_name="",
                    parameters={
                        "time_condition": "after_time",
                        "time_value": "09:00"
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": self.get_os_config()["task_manager_shortcut"],
                        "wait_for_completion": False
                    }
                ),
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 3.0, "wait_type": "fixed"}
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Check CPU and memory usage?",
                        "input_type": "yes_no"
                    }
                )
            ]
        )
        
        # Create process management rule
        process_rule = Rule(
            name="Manage System Processes",
            description="Monitor and manage running processes",
            priority=2,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="Processes List",
                    parameters={
                        "text": "CPU",
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "End high CPU usage processes?",
                        "input_type": "yes_no"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Processes List",
                    parameters={
                        "click_type": "right",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                )
            ]
        )
        
        profile.rules.extend([monitor_rule, process_rule])
        
        self.logger.info(f"Created system monitoring template for {self.os}")
        return profile


def create_system_templates(operating_system: str = "windows") -> List[AutomationProfile]:
    """Create all system automation templates for specified OS"""
    
    templates = []
    
    # File management template
    file_template = FileManagementTemplate(operating_system)
    templates.append(file_template.create_template())
    
    # Application launch template
    app_template = ApplicationLaunchTemplate(operating_system)
    templates.append(app_template.create_template())
    
    # System monitoring template
    monitor_template = SystemMonitoringTemplate(operating_system)
    templates.append(monitor_template.create_template())
    
    return templates


def create_windows_templates() -> List[AutomationProfile]:
    """Create system templates specifically for Windows"""
    return create_system_templates("windows")


def create_macos_templates() -> List[AutomationProfile]:
    """Create system templates specifically for macOS"""
    return create_system_templates("macos")


def create_linux_templates() -> List[AutomationProfile]:
    """Create system templates specifically for Linux"""
    return create_system_templates("linux")