"""
Email Automation Templates

Pre-built templates for common email automation tasks including sending,
reading, and managing emails across different email clients.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.profile import AutomationProfile, ProfileSettings
from ..models.region import Region
from ..models.rule import Rule, Condition, Action, ConditionType, ActionType


class EmailTemplateBase:
    """Base class for email automation templates"""
    
    def __init__(self, email_client: str = "outlook"):
        self.email_client = email_client.lower()
        self.logger = logging.getLogger(f"mark_i.profiles.templates.email.{self.__class__.__name__}")
        
        # Email client configurations
        self.client_configs = {
            "outlook": {
                "window_title": "Microsoft Outlook",
                "compose_shortcut": "Ctrl+N",
                "send_shortcut": "Ctrl+Enter",
                "reply_shortcut": "Ctrl+R",
                "forward_shortcut": "Ctrl+F"
            },
            "gmail": {
                "window_title": "Gmail",
                "compose_shortcut": "c",
                "send_shortcut": "Ctrl+Enter", 
                "reply_shortcut": "r",
                "forward_shortcut": "f"
            },
            "thunderbird": {
                "window_title": "Mozilla Thunderbird",
                "compose_shortcut": "Ctrl+N",
                "send_shortcut": "Ctrl+Enter",
                "reply_shortcut": "Ctrl+R", 
                "forward_shortcut": "Ctrl+L"
            }
        }
    
    def get_client_config(self) -> Dict[str, str]:
        """Get configuration for current email client"""
        return self.client_configs.get(self.email_client, self.client_configs["outlook"])
    
    def create_base_profile(self, name: str, description: str) -> AutomationProfile:
        """Create base email automation profile"""
        profile = AutomationProfile.create_new(
            name=name,
            description=description,
            category="email",
            target_application=self.get_client_config()["window_title"]
        )
        
        # Configure email-specific settings
        profile.settings.monitoring_interval_seconds = 2.0
        profile.settings.max_execution_time_seconds = 300  # 5 minutes
        profile.settings.template_match_threshold = 0.8
        profile.settings.ocr_confidence_threshold = 80
        profile.settings.use_gemini_analysis = True
        profile.settings.screenshot_on_error = True
        
        profile.tags.extend(["email", self.email_client, "automation"])
        
        return profile


class EmailSendingTemplate(EmailTemplateBase):
    """Template for automated email sending"""
    
    def create_template(self, 
                       recipient_region: Optional[Region] = None,
                       subject_region: Optional[Region] = None,
                       body_region: Optional[Region] = None,
                       send_button_region: Optional[Region] = None) -> AutomationProfile:
        """Create email sending automation profile"""
        
        profile = self.create_base_profile(
            name=f"Email Sending - {self.email_client.title()}",
            description=f"Automated email sending template for {self.email_client.title()}"
        )
        
        # Define default regions if not provided
        if not recipient_region:
            recipient_region = Region(
                name="Recipient Field",
                x=200, y=150, width=400, height=30,
                description="Email recipient input field",
                ocr_enabled=False
            )
        
        if not subject_region:
            subject_region = Region(
                name="Subject Field", 
                x=200, y=200, width=400, height=30,
                description="Email subject input field",
                ocr_enabled=False
            )
        
        if not body_region:
            body_region = Region(
                name="Email Body",
                x=200, y=250, width=600, height=300,
                description="Email message body area",
                ocr_enabled=False
            )
        
        if not send_button_region:
            send_button_region = Region(
                name="Send Button",
                x=200, y=580, width=80, height=30,
                description="Send email button",
                ocr_enabled=True
            )
        
        # Add regions to profile
        profile.regions.extend([
            recipient_region, subject_region, body_region, send_button_region
        ])
        
        # Create email sending rule
        sending_rule = Rule(
            name="Send Email",
            description="Compose and send email with specified content",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.SYSTEM_STATE,
                    region_name="",
                    parameters={
                        "state_type": "window_active",
                        "state_value": self.get_client_config()["window_title"]
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": self.get_client_config()["compose_shortcut"],
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
                        "prompt": "Enter recipient email address:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Recipient Field",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter email subject:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Subject Field",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter email message:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Email Body",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Send email now?",
                        "input_type": "yes_no"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Send Button",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                )
            ]
        )
        
        profile.rules.append(sending_rule)
        
        self.logger.info(f"Created email sending template for {self.email_client}")
        return profile
clas
s EmailReadingTemplate(EmailTemplateBase):
    """Template for automated email reading and processing"""
    
    def create_template(self,
                       inbox_region: Optional[Region] = None,
                       email_list_region: Optional[Region] = None,
                       email_content_region: Optional[Region] = None,
                       search_region: Optional[Region] = None) -> AutomationProfile:
        """Create email reading automation profile"""
        
        profile = self.create_base_profile(
            name=f"Email Reading - {self.email_client.title()}",
            description=f"Automated email reading and processing for {self.email_client.title()}"
        )
        
        # Define default regions if not provided
        if not inbox_region:
            inbox_region = Region(
                name="Inbox Folder",
                x=50, y=200, width=200, height=30,
                description="Inbox folder in navigation pane",
                ocr_enabled=True
            )
        
        if not email_list_region:
            email_list_region = Region(
                name="Email List",
                x=300, y=150, width=400, height=400,
                description="List of emails in current folder",
                ocr_enabled=True
            )
        
        if not email_content_region:
            email_content_region = Region(
                name="Email Content",
                x=750, y=150, width=500, height=400,
                description="Email content preview pane",
                ocr_enabled=True
            )
        
        if not search_region:
            search_region = Region(
                name="Search Box",
                x=300, y=100, width=300, height=30,
                description="Email search input field",
                ocr_enabled=False
            )
        
        # Add regions to profile
        profile.regions.extend([
            inbox_region, email_list_region, email_content_region, search_region
        ])
        
        # Create email reading rules
        
        # Rule 1: Navigate to inbox
        inbox_rule = Rule(
            name="Navigate to Inbox",
            description="Ensure inbox is selected and visible",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.SYSTEM_STATE,
                    region_name="",
                    parameters={
                        "state_type": "window_active",
                        "state_value": self.get_client_config()["window_title"]
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Inbox Folder",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 1.0, "wait_type": "fixed"}
                )
            ]
        )
        
        # Rule 2: Search for specific emails
        search_rule = Rule(
            name="Search Emails",
            description="Search for emails based on criteria",
            priority=2,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="Email List",
                    parameters={
                        "text": "Inbox",
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter search terms (or leave empty to read all):",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Search Box",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
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
                    parameters={"duration": 2.0, "wait_type": "fixed"}
                )
            ]
        )
        
        # Rule 3: Read email content
        read_rule = Rule(
            name="Read Email Content",
            description="Extract and process email content",
            priority=3,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="Email List",
                    parameters={
                        "text": "@",  # Look for email addresses indicating emails are present
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Email List",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 1.0, "wait_type": "fixed"}
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Process this email content?",
                        "input_type": "yes_no"
                    }
                )
            ]
        )
        
        profile.rules.extend([inbox_rule, search_rule, read_rule])
        
        self.logger.info(f"Created email reading template for {self.email_client}")
        return profileclass Em
ailManagementTemplate(EmailTemplateBase):
    """Template for email organization and management tasks"""
    
    def create_template(self,
                       folder_pane_region: Optional[Region] = None,
                       email_list_region: Optional[Region] = None,
                       toolbar_region: Optional[Region] = None) -> AutomationProfile:
        """Create email management automation profile"""
        
        profile = self.create_base_profile(
            name=f"Email Management - {self.email_client.title()}",
            description=f"Automated email organization and management for {self.email_client.title()}"
        )
        
        # Define default regions if not provided
        if not folder_pane_region:
            folder_pane_region = Region(
                name="Folder Pane",
                x=50, y=150, width=200, height=500,
                description="Email folder navigation pane",
                ocr_enabled=True
            )
        
        if not email_list_region:
            email_list_region = Region(
                name="Email List",
                x=300, y=150, width=400, height=400,
                description="List of emails in current folder",
                ocr_enabled=True
            )
        
        if not toolbar_region:
            toolbar_region = Region(
                name="Toolbar",
                x=300, y=100, width=600, height=40,
                description="Email toolbar with action buttons",
                ocr_enabled=True
            )
        
        # Add regions to profile
        profile.regions.extend([folder_pane_region, email_list_region, toolbar_region])
        
        # Create email management rules
        
        # Rule 1: Delete old emails
        delete_old_rule = Rule(
            name="Delete Old Emails",
            description="Delete emails older than specified date",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.SYSTEM_STATE,
                    region_name="",
                    parameters={
                        "state_type": "window_active",
                        "state_value": self.get_client_config()["window_title"]
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Delete emails older than how many days?",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Email List",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
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
                        "prompt": "Delete selected emails?",
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
        
        # Rule 2: Move emails to folders
        move_emails_rule = Rule(
            name="Move Emails to Folders",
            description="Organize emails by moving to appropriate folders",
            priority=2,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="Email List",
                    parameters={
                        "text": "@",  # Emails present
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Select emails to move (click first email):",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Email List",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter target folder name:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": "Ctrl+Shift+V",  # Move to folder
                        "wait_for_completion": False
                    }
                )
            ]
        )
        
        # Rule 3: Mark emails as read/unread
        mark_emails_rule = Rule(
            name="Mark Emails",
            description="Mark emails as read or unread",
            priority=3,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="Email List",
                    parameters={
                        "text": "Unread",
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Email List",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Mark as read or unread?",
                        "input_type": "choice"
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": "Ctrl+Q",  # Mark as read
                        "wait_for_completion": False
                    }
                )
            ]
        )
        
        profile.rules.extend([delete_old_rule, move_emails_rule, mark_emails_rule])
        
        self.logger.info(f"Created email management template for {self.email_client}")
        return profile


def create_email_templates(email_client: str = "outlook") -> List[AutomationProfile]:
    """Create all email automation templates for specified client"""
    
    templates = []
    
    # Email sending template
    sending_template = EmailSendingTemplate(email_client)
    templates.append(sending_template.create_template())
    
    # Email reading template
    reading_template = EmailReadingTemplate(email_client)
    templates.append(reading_template.create_template())
    
    # Email management template
    management_template = EmailManagementTemplate(email_client)
    templates.append(management_template.create_template())
    
    return templates


def create_outlook_templates() -> List[AutomationProfile]:
    """Create email templates specifically for Microsoft Outlook"""
    return create_email_templates("outlook")


def create_gmail_templates() -> List[AutomationProfile]:
    """Create email templates specifically for Gmail"""
    return create_email_templates("gmail")


def create_thunderbird_templates() -> List[AutomationProfile]:
    """Create email templates specifically for Mozilla Thunderbird"""
    return create_email_templates("thunderbird")