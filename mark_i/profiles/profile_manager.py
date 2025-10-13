"""
Profile Manager

Central management system for automation profiles including CRUD operations,
organization, search, and template management.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models.profile import AutomationProfile
from .validation.profile_validator import ProfileValidator


class ProfileManager:
    """Central management of automation profiles"""
    
    def __init__(self, storage_path: str = "storage/profiles"):
        """
        Initialize profile manager
        
        Args:
            storage_path: Base path for profile storage
        """
        self.storage_path = Path(storage_path)
        self.logger = logging.getLogger("mark_i.profiles.manager")
        
        # Initialize validator
        self.validator = ProfileValidator()
        
        # Ensure storage directories exist
        self._ensure_storage_structure()
        
        # Cache for loaded profiles
        self._profile_cache: Dict[str, AutomationProfile] = {}
        
        self.logger.info(f"ProfileManager initialized with storage: {self.storage_path}")
    
    def _ensure_storage_structure(self):
        """Ensure all required storage directories exist"""
        categories = ['email', 'web', 'files', 'templates', 'custom']
        
        for category in categories:
            category_path = self.storage_path / category
            category_path.mkdir(parents=True, exist_ok=True)
            
            # Create category README if it doesn't exist
            readme_path = category_path / "README.md"
            if not readme_path.exists():
                self._create_category_readme(category, readme_path)
    
    def _create_category_readme(self, category: str, readme_path: Path):
        """Create README file for a profile category"""
        descriptions = {
            'email': 'Email automation profiles for sending, reading, and managing emails',
            'web': 'Web browsing automation profiles for search, navigation, and data extraction',
            'files': 'File management automation profiles for organizing, moving, and processing files',
            'templates': 'Template profiles that serve as starting points for creating new automations',
            'custom': 'Custom automation profiles for specialized tasks and workflows'
        }
        
        content = f"""# {category.title()} Automation Profiles

{descriptions.get(category, 'Automation profiles for various tasks')}

## Profile Organization

- Each profile is stored as a JSON file with a descriptive name
- Profile files contain complete automation definitions including regions, rules, and actions
- Use the Profile Manager UI to create, edit, and manage profiles in this category

## Naming Convention

- Use descriptive names that clearly indicate the profile's purpose
- Use kebab-case for file names (e.g., `send-email-template.json`)
- Include version numbers for major changes (e.g., `web-search-v2.json`)

## Best Practices

- Test profiles thoroughly before deploying them for regular use
- Document complex profiles with detailed descriptions
- Use templates as starting points for similar automation tasks
- Keep profiles focused on specific, well-defined tasks
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def create_profile(self, name: str, description: str, category: str, target_application: str = "") -> AutomationProfile:
        """
        Create a new automation profile
        
        Args:
            name: Profile name
            description: Profile description
            category: Profile category (email, web, files, templates, custom)
            target_application: Target application name
            
        Returns:
            Created AutomationProfile instance
        """
        # Validate category
        valid_categories = ['email', 'web', 'files', 'templates', 'custom']
        if category not in valid_categories:
            raise ValueError(f"Invalid category '{category}'. Valid categories: {valid_categories}")
        
        # Check for duplicate names in category
        existing_profiles = self.list_profiles(category)
        if any(p.name == name for p in existing_profiles):
            raise ValueError(f"Profile with name '{name}' already exists in category '{category}'")
        
        # Create new profile
        profile = AutomationProfile.create_new(name, description, category, target_application)
        
        # Save to storage
        self.save_profile(profile)
        
        # Add to cache
        self._profile_cache[profile.id] = profile
        
        self.logger.info(f"Created new profile: {name} (ID: {profile.id})")
        return profile
    
    def load_profile(self, profile_id: str) -> Optional[AutomationProfile]:
        """
        Load a profile by ID
        
        Args:
            profile_id: Profile ID to load
            
        Returns:
            AutomationProfile instance or None if not found
        """
        # Check cache first
        if profile_id in self._profile_cache:
            return self._profile_cache[profile_id]
        
        # Search for profile file
        profile_file = self._find_profile_file(profile_id)
        if not profile_file:
            self.logger.warning(f"Profile not found: {profile_id}")
            return None
        
        try:
            profile = AutomationProfile.load_from_file(profile_file)
            self._profile_cache[profile.id] = profile
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to load profile {profile_id}: {str(e)}")
            return None
    
    def save_profile(self, profile: AutomationProfile) -> bool:
        """
        Save a profile to storage
        
        Args:
            profile: Profile to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate profile comprehensively
            validation_result = self.validator.validate_profile(profile)
            if not validation_result.is_valid:
                self.logger.error(f"Profile validation failed: {validation_result.errors}")
                return False
            
            # Log warnings if any
            if validation_result.warnings:
                self.logger.warning(f"Profile validation warnings: {validation_result.warnings}")
            
            # Determine file path
            category_path = self.storage_path / profile.category
            file_name = self._generate_filename(profile.name)
            file_path = category_path / f"{file_name}.json"
            
            # Update modified time
            profile.modified_at = datetime.now()
            
            # Save to file
            profile.save_to_file(str(file_path))
            
            # Update cache
            self._profile_cache[profile.id] = profile
            
            self.logger.info(f"Saved profile: {profile.name} to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save profile {profile.name}: {str(e)}")
            return False
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a profile
        
        Args:
            profile_id: Profile ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Find profile file
            profile_file = self._find_profile_file(profile_id)
            if not profile_file:
                self.logger.warning(f"Profile file not found for deletion: {profile_id}")
                return False
            
            # Remove file
            os.remove(profile_file)
            
            # Remove from cache
            if profile_id in self._profile_cache:
                del self._profile_cache[profile_id]
            
            self.logger.info(f"Deleted profile: {profile_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete profile {profile_id}: {str(e)}")
            return False
    
    def list_profiles(self, category: Optional[str] = None) -> List[AutomationProfile]:
        """
        List all profiles, optionally filtered by category
        
        Args:
            category: Optional category filter
            
        Returns:
            List of AutomationProfile instances
        """
        profiles = []
        
        # Determine which categories to search
        if category:
            categories = [category]
        else:
            categories = ['email', 'web', 'files', 'templates', 'custom']
        
        for cat in categories:
            category_path = self.storage_path / cat
            if not category_path.exists():
                continue
            
            # Load all JSON files in category
            for json_file in category_path.glob("*.json"):
                try:
                    profile = AutomationProfile.load_from_file(str(json_file))
                    profiles.append(profile)
                    
                    # Add to cache
                    self._profile_cache[profile.id] = profile
                    
                except Exception as e:
                    self.logger.error(f"Failed to load profile from {json_file}: {str(e)}")
        
        # Sort by modified time (newest first)
        profiles.sort(key=lambda p: p.modified_at, reverse=True)
        return profiles
    
    def search_profiles(self, query: str) -> List[AutomationProfile]:
        """
        Search profiles by name, description, or tags
        
        Args:
            query: Search query string
            
        Returns:
            List of matching AutomationProfile instances
        """
        query_lower = query.lower()
        all_profiles = self.list_profiles()
        
        matching_profiles = []
        for profile in all_profiles:
            # Search in name
            if query_lower in profile.name.lower():
                matching_profiles.append(profile)
                continue
            
            # Search in description
            if query_lower in profile.description.lower():
                matching_profiles.append(profile)
                continue
            
            # Search in tags
            if any(query_lower in tag.lower() for tag in profile.tags):
                matching_profiles.append(profile)
                continue
            
            # Search in target application
            if query_lower in profile.target_application.lower():
                matching_profiles.append(profile)
                continue
        
        return matching_profiles
    
    def duplicate_profile(self, profile_id: str, new_name: str) -> Optional[AutomationProfile]:
        """
        Create a duplicate of an existing profile
        
        Args:
            profile_id: ID of profile to duplicate
            new_name: Name for the new profile
            
        Returns:
            New AutomationProfile instance or None if failed
        """
        original_profile = self.load_profile(profile_id)
        if not original_profile:
            return None
        
        try:
            # Clone the profile
            cloned_profile = original_profile.clone(new_name)
            
            # Save the cloned profile
            if self.save_profile(cloned_profile):
                self.logger.info(f"Duplicated profile: {original_profile.name} -> {new_name}")
                return cloned_profile
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to duplicate profile {profile_id}: {str(e)}")
            return None
    
    def get_profile_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored profiles
        
        Returns:
            Dictionary containing profile statistics
        """
        all_profiles = self.list_profiles()
        
        stats = {
            'total_profiles': len(all_profiles),
            'by_category': {},
            'templates': 0,
            'most_recent': None,
            'oldest': None
        }
        
        if not all_profiles:
            return stats
        
        # Count by category
        for profile in all_profiles:
            category = profile.category
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            if profile.is_template:
                stats['templates'] += 1
        
        # Find most recent and oldest
        stats['most_recent'] = max(all_profiles, key=lambda p: p.modified_at).name
        stats['oldest'] = min(all_profiles, key=lambda p: p.created_at).name
        
        return stats
    
    def _find_profile_file(self, profile_id: str) -> Optional[str]:
        """Find the file path for a profile by ID"""
        categories = ['email', 'web', 'files', 'templates', 'custom']
        
        for category in categories:
            category_path = self.storage_path / category
            if not category_path.exists():
                continue
            
            for json_file in category_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('id') == profile_id:
                            return str(json_file)
                except Exception:
                    continue
        
        return None
    
    def _generate_filename(self, profile_name: str) -> str:
        """Generate a safe filename from profile name"""
        # Convert to lowercase and replace spaces with hyphens
        filename = profile_name.lower().replace(' ', '-')
        
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Limit length
        if len(filename) > 50:
            filename = filename[:50]
        
        return filename
    
    def clear_cache(self):
        """Clear the profile cache"""
        self._profile_cache.clear()
        self.logger.info("Profile cache cleared")
    
    def get_cache_size(self) -> int:
        """Get the number of profiles in cache"""
        return len(self._profile_cache)
    
    def validate_profile(self, profile: AutomationProfile):
        """
        Validate a profile without saving it
        
        Args:
            profile: Profile to validate
            
        Returns:
            ValidationResult with errors and warnings
        """
        return self.validator.validate_profile(profile)
    
    def export_profile(self, profile_id: str, export_path: str) -> bool:
        """
        Export a profile to a specific file path
        
        Args:
            profile_id: ID of profile to export
            export_path: Path where to save the exported profile
            
        Returns:
            True if exported successfully, False otherwise
        """
        profile = self.load_profile(profile_id)
        if not profile:
            return False
        
        try:
            profile.save_to_file(export_path)
            self.logger.info(f"Exported profile {profile.name} to {export_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export profile: {str(e)}")
            return False
    
    def import_profile(self, import_path: str) -> Optional[AutomationProfile]:
        """
        Import a profile from a file
        
        Args:
            import_path: Path to the profile file to import
            
        Returns:
            Imported AutomationProfile or None if failed
        """
        try:
            profile = AutomationProfile.load_from_file(import_path)
            
            # Validate imported profile
            validation_result = self.validator.validate_profile(profile)
            if not validation_result.is_valid:
                self.logger.error(f"Imported profile validation failed: {validation_result.errors}")
                return None
            
            # Check for name conflicts
            existing_profiles = self.list_profiles(profile.category)
            if any(p.name == profile.name for p in existing_profiles):
                # Generate unique name
                base_name = profile.name
                counter = 1
                while any(p.name == f"{base_name} ({counter})" for p in existing_profiles):
                    counter += 1
                profile.name = f"{base_name} ({counter})"
            
            # Save imported profile
            if self.save_profile(profile):
                self.logger.info(f"Imported profile: {profile.name}")
                return profile
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to import profile from {import_path}: {str(e)}")
            return None