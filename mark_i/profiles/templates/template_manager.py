"""
Template Manager

Centralized management of automation profile templates.
Provides discovery, creation, and customization of pre-built templates.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import json

from ..models.profile import AutomationProfile
from .email_templates import create_email_templates
from .web_templates import create_web_templates  
from .system_templates import create_system_templates


class TemplateManager:
    """Manager for automation profile templates"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.logger = logging.getLogger("mark_i.profiles.templates.manager")
        
        # Set templates directory
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).parent / "data"
        
        self.templates_dir.mkdir(exist_ok=True)
        
        # Template categories and their creation functions
        self.template_categories = {
            "email": {
                "outlook": lambda: create_email_templates("outlook"),
                "gmail": lambda: create_email_templates("gmail"),
                "thunderbird": lambda: create_email_templates("thunderbird")
            },
            "web": {
                "chrome": lambda: create_web_templates("chrome"),
                "firefox": lambda: create_web_templates("firefox"),
                "edge": lambda: create_web_templates("edge")
            },
            "system": {
                "windows": lambda: create_system_templates("windows"),
                "macos": lambda: create_system_templates("macos"),
                "linux": lambda: create_system_templates("linux")
            }
        }
        
        self.logger.info("TemplateManager initialized")
    
    def list_template_categories(self) -> List[str]:
        """Get list of available template categories"""
        return list(self.template_categories.keys())
    
    def list_template_variants(self, category: str) -> List[str]:
        """Get list of variants for a template category"""
        if category not in self.template_categories:
            return []
        return list(self.template_categories[category].keys())
    
    def get_template_info(self, category: str, variant: str = None) -> Dict[str, Any]:
        """Get information about templates in a category/variant"""
        if category not in self.template_categories:
            return {}
        
        info = {
            "category": category,
            "variants": list(self.template_categories[category].keys()),
            "description": self._get_category_description(category)
        }
        
        if variant and variant in self.template_categories[category]:
            # Get sample template to extract info
            try:
                templates = self.template_categories[category][variant]()
                info["variant"] = variant
                info["template_count"] = len(templates)
                info["template_names"] = [t.name for t in templates]
            except Exception as e:
                self.logger.error(f"Failed to get template info for {category}/{variant}: {e}")
                info["error"] = str(e)
        
        return info
    
    def _get_category_description(self, category: str) -> str:
        """Get description for template category"""
        descriptions = {
            "email": "Email automation templates for sending, reading, and managing emails",
            "web": "Web browsing automation templates for search, forms, and data extraction",
            "system": "System automation templates for file management and application control"
        }
        return descriptions.get(category, "Automation templates")
    
    def create_templates(self, category: str, variant: str = None) -> List[AutomationProfile]:
        """Create templates for specified category and variant"""
        if category not in self.template_categories:
            raise ValueError(f"Unknown template category: {category}")
        
        category_templates = self.template_categories[category]
        
        if variant:
            if variant not in category_templates:
                raise ValueError(f"Unknown variant '{variant}' for category '{category}'")
            
            templates = category_templates[variant]()
            self.logger.info(f"Created {len(templates)} templates for {category}/{variant}")
            return templates
        else:
            # Create all variants for the category
            all_templates = []
            for variant_name, template_func in category_templates.items():
                try:
                    templates = template_func()
                    all_templates.extend(templates)
                except Exception as e:
                    self.logger.error(f"Failed to create templates for {category}/{variant_name}: {e}")
            
            self.logger.info(f"Created {len(all_templates)} templates for category {category}")
            return all_templates
    
    def create_all_templates(self) -> Dict[str, List[AutomationProfile]]:
        """Create all available templates organized by category"""
        all_templates = {}
        
        for category in self.template_categories:
            try:
                templates = self.create_templates(category)
                all_templates[category] = templates
            except Exception as e:
                self.logger.error(f"Failed to create templates for category {category}: {e}")
                all_templates[category] = []
        
        total_count = sum(len(templates) for templates in all_templates.values())
        self.logger.info(f"Created {total_count} total templates across all categories")
        
        return all_templates
    
    def save_templates_to_disk(self, templates: List[AutomationProfile], 
                              category: str, variant: str = None) -> bool:
        """Save templates to disk for later use"""
        try:
            # Create category directory
            category_dir = self.templates_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # Determine filename
            if variant:
                filename = f"{variant}_templates.json"
            else:
                filename = f"{category}_templates.json"
            
            filepath = category_dir / filename
            
            # Convert templates to JSON
            templates_data = []
            for template in templates:
                template_dict = template.to_dict()
                templates_data.append(template_dict)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved {len(templates)} templates to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save templates: {e}")
            return False
    
    def load_templates_from_disk(self, category: str, variant: str = None) -> List[AutomationProfile]:
        """Load templates from disk"""
        try:
            # Determine filepath
            category_dir = self.templates_dir / category
            if variant:
                filename = f"{variant}_templates.json"
            else:
                filename = f"{category}_templates.json"
            
            filepath = category_dir / filename
            
            if not filepath.exists():
                self.logger.warning(f"Template file not found: {filepath}")
                return []
            
            # Load from file
            with open(filepath, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
            
            # Convert to AutomationProfile objects
            templates = []
            for template_dict in templates_data:
                try:
                    template = AutomationProfile.from_dict(template_dict)
                    templates.append(template)
                except Exception as e:
                    self.logger.error(f"Failed to load template: {e}")
            
            self.logger.info(f"Loaded {len(templates)} templates from {filepath}")
            return templates
            
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
            return []
    
    def customize_template(self, template: AutomationProfile, 
                          customizations: Dict[str, Any]) -> AutomationProfile:
        """Apply customizations to a template"""
        try:
            # Create a copy of the template
            customized = AutomationProfile.from_dict(template.to_dict())
            
            # Apply basic customizations
            if "name" in customizations:
                customized.name = customizations["name"]
            
            if "description" in customizations:
                customized.description = customizations["description"]
            
            if "target_application" in customizations:
                customized.target_application = customizations["target_application"]
            
            if "tags" in customizations:
                customized.tags.extend(customizations["tags"])
            
            # Apply region customizations
            if "regions" in customizations:
                region_updates = customizations["regions"]
                for region_name, updates in region_updates.items():
                    for region in customized.regions:
                        if region.name == region_name:
                            for key, value in updates.items():
                                if hasattr(region, key):
                                    setattr(region, key, value)
            
            # Apply settings customizations
            if "settings" in customizations:
                settings_updates = customizations["settings"]
                for key, value in settings_updates.items():
                    if hasattr(customized.settings, key):
                        setattr(customized.settings, key, value)
            
            self.logger.info(f"Applied customizations to template: {customized.name}")
            return customized
            
        except Exception as e:
            self.logger.error(f"Failed to customize template: {e}")
            return template
    
    def search_templates(self, query: str, category: str = None) -> List[AutomationProfile]:
        """Search for templates matching query"""
        results = []
        
        # Determine which categories to search
        categories_to_search = [category] if category else self.template_categories.keys()
        
        for cat in categories_to_search:
            try:
                templates = self.create_templates(cat)
                for template in templates:
                    # Search in name, description, and tags
                    search_text = f"{template.name} {template.description} {' '.join(template.tags)}".lower()
                    if query.lower() in search_text:
                        results.append(template)
            except Exception as e:
                self.logger.error(f"Error searching templates in category {cat}: {e}")
        
        self.logger.info(f"Found {len(results)} templates matching '{query}'")
        return results
    
    def get_template_by_name(self, name: str, category: str = None) -> Optional[AutomationProfile]:
        """Get a specific template by name"""
        templates = self.search_templates(name, category)
        
        # Look for exact name match first
        for template in templates:
            if template.name.lower() == name.lower():
                return template
        
        # Return first partial match if no exact match
        return templates[0] if templates else None
    
    def export_template_catalog(self, filepath: Path) -> bool:
        """Export a catalog of all available templates"""
        try:
            catalog = {
                "generated_at": str(datetime.now()),
                "categories": {}
            }
            
            for category in self.template_categories:
                catalog["categories"][category] = {
                    "description": self._get_category_description(category),
                    "variants": {}
                }
                
                for variant in self.template_categories[category]:
                    try:
                        templates = self.template_categories[category][variant]()
                        catalog["categories"][category]["variants"][variant] = {
                            "template_count": len(templates),
                            "templates": [
                                {
                                    "name": t.name,
                                    "description": t.description,
                                    "regions_count": len(t.regions),
                                    "rules_count": len(t.rules),
                                    "tags": t.tags
                                }
                                for t in templates
                            ]
                        }
                    except Exception as e:
                        catalog["categories"][category]["variants"][variant] = {
                            "error": str(e)
                        }
            
            # Save catalog
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(catalog, f, indent=2, default=str)
            
            self.logger.info(f"Exported template catalog to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export template catalog: {e}")
            return False