"""
Web Browsing Automation Templates

Pre-built templates for web automation tasks including search, form filling,
data extraction, and social media automation.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.profile import AutomationProfile, ProfileSettings
from ..models.region import Region
from ..models.rule import Rule, Condition, Action, ConditionType, ActionType


class WebTemplateBase:
    """Base class for web automation templates"""
    
    def __init__(self, browser: str = "chrome"):
        self.browser = browser.lower()
        self.logger = logging.getLogger(f"mark_i.profiles.templates.web.{self.__class__.__name__}")
        
        # Browser configurations
        self.browser_configs = {
            "chrome": {
                "window_title": "Google Chrome",
                "new_tab_shortcut": "Ctrl+T",
                "close_tab_shortcut": "Ctrl+W",
                "refresh_shortcut": "F5",
                "address_bar_shortcut": "Ctrl+L"
            },
            "firefox": {
                "window_title": "Mozilla Firefox",
                "new_tab_shortcut": "Ctrl+T",
                "close_tab_shortcut": "Ctrl+W", 
                "refresh_shortcut": "F5",
                "address_bar_shortcut": "Ctrl+L"
            },
            "edge": {
                "window_title": "Microsoft Edge",
                "new_tab_shortcut": "Ctrl+T",
                "close_tab_shortcut": "Ctrl+W",
                "refresh_shortcut": "F5",
                "address_bar_shortcut": "Ctrl+L"
            }
        }
    
    def get_browser_config(self) -> Dict[str, str]:
        """Get configuration for current browser"""
        return self.browser_configs.get(self.browser, self.browser_configs["chrome"])
    
    def create_base_profile(self, name: str, description: str) -> AutomationProfile:
        """Create base web automation profile"""
        profile = AutomationProfile.create_new(
            name=name,
            description=description,
            category="web",
            target_application=self.get_browser_config()["window_title"]
        )
        
        # Configure web-specific settings
        profile.settings.monitoring_interval_seconds = 1.5
        profile.settings.max_execution_time_seconds = 600  # 10 minutes
        profile.settings.template_match_threshold = 0.75
        profile.settings.ocr_confidence_threshold = 75
        profile.settings.use_gemini_analysis = True
        profile.settings.screenshot_on_error = True
        
        profile.tags.extend(["web", self.browser, "automation"])
        
        return profile
cl
ass WebSearchTemplate(WebTemplateBase):
    """Template for automated web searching"""
    
    def create_template(self,
                       address_bar_region: Optional[Region] = None,
                       search_box_region: Optional[Region] = None,
                       results_region: Optional[Region] = None,
                       next_page_region: Optional[Region] = None) -> AutomationProfile:
        """Create web search automation profile"""
        
        profile = self.create_base_profile(
            name=f"Web Search - {self.browser.title()}",
            description=f"Automated web search template for {self.browser.title()}"
        )
        
        # Define default regions if not provided
        if not address_bar_region:
            address_bar_region = Region(
                name="Address Bar",
                x=100, y=60, width=800, height=35,
                description="Browser address/URL bar",
                ocr_enabled=False
            )
        
        if not search_box_region:
            search_box_region = Region(
                name="Search Box",
                x=300, y=200, width=400, height=40,
                description="Search engine search input box",
                ocr_enabled=False
            )
        
        if not results_region:
            results_region = Region(
                name="Search Results",
                x=200, y=300, width=800, height=600,
                description="Search results area",
                ocr_enabled=True
            )
        
        if not next_page_region:
            next_page_region = Region(
                name="Next Page",
                x=500, y=950, width=100, height=30,
                description="Next page navigation button",
                ocr_enabled=True
            )
        
        # Add regions to profile
        profile.regions.extend([
            address_bar_region, search_box_region, results_region, next_page_region
        ])
        
        # Create web search rule
        search_rule = Rule(
            name="Perform Web Search",
            description="Navigate to search engine and perform search",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.SYSTEM_STATE,
                    region_name="",
                    parameters={
                        "state_type": "window_active",
                        "state_value": self.get_browser_config()["window_title"]
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter search engine URL (e.g., google.com):",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.RUN_COMMAND,
                    target_region="",
                    parameters={
                        "command": self.get_browser_config()["address_bar_shortcut"],
                        "wait_for_completion": False
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Address Bar",
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
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter search terms:",
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
        
        # Create results processing rule
        results_rule = Rule(
            name="Process Search Results",
            description="Extract and process search results",
            priority=2,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="Search Results",
                    parameters={
                        "text": "results",
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Click on a search result?",
                        "input_type": "yes_no"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Search Results",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 50  # Click on first result
                    }
                )
            ]
        )
        
        profile.rules.extend([search_rule, results_rule])
        
        self.logger.info(f"Created web search template for {self.browser}")
        return profilec
lass FormFillingTemplate(WebTemplateBase):
    """Template for automated web form filling"""
    
    def create_template(self,
                       form_fields: Optional[List[Region]] = None) -> AutomationProfile:
        """Create form filling automation profile"""
        
        profile = self.create_base_profile(
            name=f"Form Filling - {self.browser.title()}",
            description=f"Automated web form filling template for {self.browser.title()}"
        )
        
        # Define default form fields if not provided
        if not form_fields:
            form_fields = [
                Region(
                    name="Name Field",
                    x=300, y=200, width=300, height=30,
                    description="Name input field",
                    ocr_enabled=False
                ),
                Region(
                    name="Email Field",
                    x=300, y=250, width=300, height=30,
                    description="Email input field",
                    ocr_enabled=False
                ),
                Region(
                    name="Phone Field",
                    x=300, y=300, width=300, height=30,
                    description="Phone number input field",
                    ocr_enabled=False
                ),
                Region(
                    name="Message Field",
                    x=300, y=350, width=400, height=100,
                    description="Message/comments text area",
                    ocr_enabled=False
                ),
                Region(
                    name="Submit Button",
                    x=300, y=480, width=100, height=35,
                    description="Form submit button",
                    ocr_enabled=True
                )
            ]
        
        # Add regions to profile
        profile.regions.extend(form_fields)
        
        # Create form filling rule
        form_rule = Rule(
            name="Fill Web Form",
            description="Automatically fill web form with user data",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.SYSTEM_STATE,
                    region_name="",
                    parameters={
                        "state_type": "window_active",
                        "state_value": self.get_browser_config()["window_title"]
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter your full name:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Name Field",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Name Field",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter your email address:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Email Field",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Email Field",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter your phone number:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Phone Field",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Phone Field",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Enter your message:",
                        "input_type": "text"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Message Field",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.TYPE_TEXT,
                    target_region="Message Field",
                    parameters={
                        "text": "{user_input}",
                        "clear_first": True
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Submit the form?",
                        "input_type": "yes_no"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Submit Button",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                )
            ]
        )
        
        profile.rules.append(form_rule)
        
        self.logger.info(f"Created form filling template for {self.browser}")
        return profileclass
 DataExtractionTemplate(WebTemplateBase):
    """Template for automated web data extraction"""
    
    def create_template(self,
                       data_regions: Optional[List[Region]] = None,
                       navigation_region: Optional[Region] = None) -> AutomationProfile:
        """Create data extraction automation profile"""
        
        profile = self.create_base_profile(
            name=f"Data Extraction - {self.browser.title()}",
            description=f"Automated web data extraction template for {self.browser.title()}"
        )
        
        # Define default data regions if not provided
        if not data_regions:
            data_regions = [
                Region(
                    name="Title Area",
                    x=200, y=150, width=600, height=50,
                    description="Page title or heading area",
                    ocr_enabled=True
                ),
                Region(
                    name="Content Area",
                    x=200, y=220, width=800, height=400,
                    description="Main content area for data extraction",
                    ocr_enabled=True
                ),
                Region(
                    name="Table Data",
                    x=200, y=300, width=800, height=300,
                    description="Table or structured data area",
                    ocr_enabled=True
                ),
                Region(
                    name="Links Area",
                    x=200, y=650, width=600, height=100,
                    description="Navigation links or pagination",
                    ocr_enabled=True
                )
            ]
        
        if not navigation_region:
            navigation_region = Region(
                name="Next Button",
                x=700, y=750, width=80, height=30,
                description="Next page or continue button",
                ocr_enabled=True
            )
        
        # Add regions to profile
        profile.regions.extend(data_regions + [navigation_region])
        
        # Create data extraction rule
        extraction_rule = Rule(
            name="Extract Web Data",
            description="Extract structured data from web pages",
            priority=1,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.SYSTEM_STATE,
                    region_name="",
                    parameters={
                        "state_type": "window_active",
                        "state_value": self.get_browser_config()["window_title"]
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 2.0, "wait_type": "fixed"}
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Extract data from this page?",
                        "input_type": "yes_no"
                    }
                ),
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Save extracted data to file?",
                        "input_type": "file_path"
                    }
                )
            ]
        )
        
        # Create navigation rule for multi-page extraction
        navigation_rule = Rule(
            name="Navigate to Next Page",
            description="Navigate to next page for continued extraction",
            priority=2,
            enabled=True,
            logical_operator="AND",
            conditions=[
                Condition(
                    condition_type=ConditionType.OCR_CONTAINS,
                    region_name="Next Button",
                    parameters={
                        "text": "Next",
                        "case_sensitive": False
                    }
                )
            ],
            actions=[
                Action(
                    action_type=ActionType.ASK_USER,
                    target_region="",
                    parameters={
                        "prompt": "Continue to next page?",
                        "input_type": "yes_no"
                    }
                ),
                Action(
                    action_type=ActionType.CLICK,
                    target_region="Next Button",
                    parameters={
                        "click_type": "left",
                        "offset_x": 0,
                        "offset_y": 0
                    }
                ),
                Action(
                    action_type=ActionType.WAIT,
                    target_region="",
                    parameters={"duration": 3.0, "wait_type": "fixed"}
                )
            ]
        )
        
        profile.rules.extend([extraction_rule, navigation_rule])
        
        self.logger.info(f"Created data extraction template for {self.browser}")
        return profile


def create_web_templates(browser: str = "chrome") -> List[AutomationProfile]:
    """Create all web automation templates for specified browser"""
    
    templates = []
    
    # Web search template
    search_template = WebSearchTemplate(browser)
    templates.append(search_template.create_template())
    
    # Form filling template
    form_template = FormFillingTemplate(browser)
    templates.append(form_template.create_template())
    
    # Data extraction template
    extraction_template = DataExtractionTemplate(browser)
    templates.append(extraction_template.create_template())
    
    return templates


def create_chrome_templates() -> List[AutomationProfile]:
    """Create web templates specifically for Google Chrome"""
    return create_web_templates("chrome")


def create_firefox_templates() -> List[AutomationProfile]:
    """Create web templates specifically for Mozilla Firefox"""
    return create_web_templates("firefox")


def create_edge_templates() -> List[AutomationProfile]:
    """Create web templates specifically for Microsoft Edge"""
    return create_web_templates("edge")