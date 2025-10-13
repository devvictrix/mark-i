"""
Profile Model

Main automation profile definition with settings and metadata.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from .region import Region
from .rule import Rule


@dataclass
class ProfileSettings:
    """Profile execution settings and configuration"""
    monitoring_interval_seconds: float = 1.0
    max_execution_time_seconds: int = 300
    screenshot_on_error: bool = True
    log_level: str = "INFO"
    
    # Visual analysis settings
    template_match_threshold: float = 0.8
    ocr_confidence_threshold: int = 60
    color_tolerance: int = 10
    
    # Execution settings
    action_delay_multiplier: float = 1.0
    retry_on_failure: bool = True
    ask_user_timeout_seconds: int = 30
    
    # AI settings
    use_gemini_analysis: bool = True
    gemini_model: str = "gemini-1.5-flash-latest"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            'monitoring_interval_seconds': self.monitoring_interval_seconds,
            'max_execution_time_seconds': self.max_execution_time_seconds,
            'screenshot_on_error': self.screenshot_on_error,
            'log_level': self.log_level,
            'template_match_threshold': self.template_match_threshold,
            'ocr_confidence_threshold': self.ocr_confidence_threshold,
            'color_tolerance': self.color_tolerance,
            'action_delay_multiplier': self.action_delay_multiplier,
            'retry_on_failure': self.retry_on_failure,
            'ask_user_timeout_seconds': self.ask_user_timeout_seconds,
            'use_gemini_analysis': self.use_gemini_analysis,
            'gemini_model': self.gemini_model
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileSettings':
        """Create settings from dictionary"""
        return cls(
            monitoring_interval_seconds=data.get('monitoring_interval_seconds', 1.0),
            max_execution_time_seconds=data.get('max_execution_time_seconds', 300),
            screenshot_on_error=data.get('screenshot_on_error', True),
            log_level=data.get('log_level', 'INFO'),
            template_match_threshold=data.get('template_match_threshold', 0.8),
            ocr_confidence_threshold=data.get('ocr_confidence_threshold', 60),
            color_tolerance=data.get('color_tolerance', 10),
            action_delay_multiplier=data.get('action_delay_multiplier', 1.0),
            retry_on_failure=data.get('retry_on_failure', True),
            ask_user_timeout_seconds=data.get('ask_user_timeout_seconds', 30),
            use_gemini_analysis=data.get('use_gemini_analysis', True),
            gemini_model=data.get('gemini_model', 'gemini-1.5-flash-latest')
        )


@dataclass
class AutomationProfile:
    """Complete automation profile definition"""
    id: str
    name: str
    description: str
    category: str
    target_application: str
    created_at: datetime
    modified_at: datetime
    version: str = "1.0.0"
    
    # Core components
    regions: List[Region] = field(default_factory=list)
    rules: List[Rule] = field(default_factory=list)
    settings: ProfileSettings = field(default_factory=ProfileSettings)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    author: str = "user"
    is_template: bool = False
    parent_template: Optional[str] = None
    
    def __post_init__(self):
        """Validate profile after initialization"""
        if not self.name.strip():
            raise ValueError("Profile name cannot be empty")
        
        if not self.category.strip():
            raise ValueError("Profile category cannot be empty")
        
        # Update modified time
        self.modified_at = datetime.now()
    
    @classmethod
    def create_new(cls, name: str, description: str, category: str, target_application: str = "") -> 'AutomationProfile':
        """Create a new automation profile with generated ID and timestamps"""
        now = datetime.now()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            target_application=target_application,
            created_at=now,
            modified_at=now
        )
    
    def add_region(self, region: Region):
        """Add a region to this profile"""
        # Check for duplicate names
        if any(r.name == region.name for r in self.regions):
            raise ValueError(f"Region with name '{region.name}' already exists")
        
        self.regions.append(region)
        self.modified_at = datetime.now()
    
    def add_rule(self, rule: Rule):
        """Add a rule to this profile"""
        # Check for duplicate names
        if any(r.name == rule.name for r in self.rules):
            raise ValueError(f"Rule with name '{rule.name}' already exists")
        
        self.rules.append(rule)
        self.modified_at = datetime.now()
    
    def remove_region(self, region_name: str):
        """Remove a region by name"""
        self.regions = [r for r in self.regions if r.name != region_name]
        self.modified_at = datetime.now()
    
    def remove_rule(self, rule_name: str):
        """Remove a rule by name"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        self.modified_at = datetime.now()
    
    def get_region(self, name: str) -> Optional[Region]:
        """Get region by name"""
        for region in self.regions:
            if region.name == name:
                return region
        return None
    
    def get_rule(self, name: str) -> Optional[Rule]:
        """Get rule by name"""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
    
    def get_region_names(self) -> List[str]:
        """Get list of all region names"""
        return [r.name for r in self.regions]
    
    def get_rule_names(self) -> List[str]:
        """Get list of all rule names"""
        return [r.name for r in self.rules]
    
    def get_enabled_rules(self) -> List[Rule]:
        """Get list of enabled rules sorted by priority"""
        enabled_rules = [r for r in self.rules if r.enabled]
        return sorted(enabled_rules, key=lambda r: r.priority, reverse=True)
    
    def validate_references(self) -> List[str]:
        """Validate that all rule references point to existing regions"""
        errors = []
        region_names = self.get_region_names()
        
        for rule in self.rules:
            referenced_regions = rule.get_referenced_regions()
            for region_name in referenced_regions:
                if region_name not in region_names:
                    errors.append(f"Rule '{rule.name}' references unknown region '{region_name}'")
        
        return errors
    
    def add_tag(self, tag: str):
        """Add a tag to this profile"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.modified_at = datetime.now()
    
    def remove_tag(self, tag: str):
        """Remove a tag from this profile"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.modified_at = datetime.now()
    
    def clone(self, new_name: str) -> 'AutomationProfile':
        """Create a copy of this profile with a new name and ID"""
        cloned_data = self.to_dict()
        cloned_data['id'] = str(uuid.uuid4())
        cloned_data['name'] = new_name
        cloned_data['created_at'] = datetime.now().isoformat()
        cloned_data['modified_at'] = datetime.now().isoformat()
        cloned_data['parent_template'] = self.id if self.is_template else self.parent_template
        
        return AutomationProfile.from_dict(cloned_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'target_application': self.target_application,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'version': self.version,
            'regions': [r.to_dict() for r in self.regions],
            'rules': [r.to_dict() for r in self.rules],
            'settings': self.settings.to_dict(),
            'tags': self.tags,
            'author': self.author,
            'is_template': self.is_template,
            'parent_template': self.parent_template
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationProfile':
        """Create profile from dictionary"""
        profile = cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            category=data['category'],
            target_application=data['target_application'],
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at']),
            version=data.get('version', '1.0.0'),
            settings=ProfileSettings.from_dict(data.get('settings', {})),
            tags=data.get('tags', []),
            author=data.get('author', 'user'),
            is_template=data.get('is_template', False),
            parent_template=data.get('parent_template')
        )
        
        # Add regions
        for region_data in data.get('regions', []):
            profile.add_region(Region.from_dict(region_data))
        
        # Add rules
        for rule_data in data.get('rules', []):
            profile.add_rule(Rule.from_dict(rule_data))
        
        return profile
    
    def to_json(self) -> str:
        """Convert profile to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AutomationProfile':
        """Create profile from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: str):
        """Save profile to JSON file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'AutomationProfile':
        """Load profile from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())