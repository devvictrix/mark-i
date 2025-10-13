#!/usr/bin/env python3
"""
Profile Migration Utility for MARK-I
Migrates and reorganizes profile JSON files from storage/ to storage/profiles/
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class ProfileMigrator:
    """Handles migration of profile files to organized structure"""
    
    def __init__(self):
        self.storage_path = Path("storage")
        self.profiles_path = self.storage_path / "profiles"
        
        # File mapping based on design document
        self.file_mapping = {
            "example_profile.json": {
                "new_name": "basic-example-profile.json",
                "category": "examples",
                "description": "Basic example profile demonstrating core MARK-I automation functionalities including region monitoring, color detection, and conditional actions."
            },
            "line_messenger_abc.json": {
                "new_name": "line-messenger-basic.json", 
                "category": "messaging",
                "description": "Basic LINE messenger automation profile for sending simple messages to specific contacts using template matching."
            },
            "line_wife_message_ai.json": {
                "new_name": "line-messenger-ai-enhanced.json",
                "category": "messaging", 
                "description": "AI-enhanced LINE messenger automation profile with intelligent contact detection and message sending capabilities."
            },
            "line_wife_message_ai_gemini_test.json": {
                "new_name": "line-messenger-gemini-test.json",
                "category": "messaging",
                "description": "Experimental LINE messenger automation profile using Google Gemini AI for advanced visual recognition and contact identification."
            },
            "notepad_automator.json": {
                "new_name": "notepad-automator.json",
                "category": "productivity",
                "description": "Notepad automation profile for text processing, TODO detection, and automated text manipulation in Windows Notepad."
            },
            "simple_game_helper.json": {
                "new_name": "simple-game-helper.json",
                "category": "gaming", 
                "description": "Game automation helper profile for monitoring health bars, detecting action icons, and performing automated game actions."
            },
            "poc.json": {
                "new_name": "poc-profile.json",
                "category": "experimental",
                "description": "Proof-of-concept profile for testing new automation features and experimental functionality."
            }
        }
    
    def validate_json_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that a file contains valid JSON with required profile structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required fields
            required_fields = ['profile_description', 'settings', 'regions', 'templates', 'rules']
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"
            
            # Validate settings structure
            if not isinstance(data['settings'], dict):
                return False, "Settings must be a dictionary"
            
            # Validate arrays
            for array_field in ['regions', 'templates', 'rules']:
                if not isinstance(data[array_field], list):
                    return False, f"{array_field} must be an array"
            
            return True, None
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def create_backup(self, source_file: Path) -> Path:
        """Create backup of original file"""
        backup_dir = self.storage_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_file = backup_dir / f"{source_file.name}.backup"
        shutil.copy2(source_file, backup_file)
        return backup_file
    
    def update_profile_description(self, profile_data: dict, new_description: str) -> dict:
        """Update profile description in the JSON data"""
        profile_data['profile_description'] = new_description
        return profile_data
    
    def get_migration_plan(self) -> List[Dict]:
        """Generate migration plan for all profile files"""
        plan = []
        
        for old_name, mapping in self.file_mapping.items():
            source_file = self.storage_path / old_name
            if source_file.exists():
                target_dir = self.profiles_path / mapping['category']
                target_file = target_dir / mapping['new_name']
                
                plan.append({
                    'source': source_file,
                    'target': target_file,
                    'target_dir': target_dir,
                    'new_description': mapping['description'],
                    'category': mapping['category']
                })
        
        return plan
    
    def execute_migration(self, dry_run: bool = False) -> Tuple[bool, List[str]]:
        """Execute the migration plan"""
        messages = []
        plan = self.get_migration_plan()
        
        if dry_run:
            messages.append("DRY RUN - No files will be modified")
        
        # Validate all source files first
        for item in plan:
            is_valid, error = self.validate_json_file(item['source'])
            if not is_valid:
                messages.append(f"ERROR: {item['source'].name} validation failed: {error}")
                return False, messages
        
        messages.append(f"All {len(plan)} source files validated successfully")
        
        if dry_run:
            for item in plan:
                messages.append(f"WOULD MIGRATE: {item['source'].name} -> {item['target']}")
            return True, messages
        
        # Execute actual migration
        try:
            for item in plan:
                # Create backup
                backup_file = self.create_backup(item['source'])
                messages.append(f"Created backup: {backup_file}")
                
                # Ensure target directory exists
                item['target_dir'].mkdir(parents=True, exist_ok=True)
                
                # Read and update profile
                with open(item['source'], 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                # Update description
                profile_data = self.update_profile_description(profile_data, item['new_description'])
                
                # Write to new location
                with open(item['target'], 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=4, ensure_ascii=False)
                
                # Validate migrated file
                is_valid, error = self.validate_json_file(item['target'])
                if not is_valid:
                    messages.append(f"ERROR: Migrated file {item['target']} validation failed: {error}")
                    return False, messages
                
                messages.append(f"MIGRATED: {item['source'].name} -> {item['target']}")
            
            return True, messages
            
        except Exception as e:
            messages.append(f"MIGRATION ERROR: {str(e)}")
            return False, messages
    
    def cleanup_original_files(self) -> Tuple[bool, List[str]]:
        """Remove original files after successful migration"""
        messages = []
        
        try:
            for old_name in self.file_mapping.keys():
                source_file = self.storage_path / old_name
                if source_file.exists():
                    source_file.unlink()
                    messages.append(f"REMOVED: {source_file}")
            
            return True, messages
            
        except Exception as e:
            messages.append(f"CLEANUP ERROR: {str(e)}")
            return False, messages

def main():
    """Main migration function"""
    migrator = ProfileMigrator()
    
    print("MARK-I Profile Migration Utility")
    print("=" * 40)
    
    # First, do a dry run
    print("\n1. Performing dry run validation...")
    success, messages = migrator.execute_migration(dry_run=True)
    
    for message in messages:
        print(f"  {message}")
    
    if not success:
        print("\nDry run failed. Please fix errors before proceeding.")
        return False
    
    print(f"\nDry run successful! Ready to migrate {len(migrator.get_migration_plan())} files.")
    
    # Execute actual migration
    print("\n2. Executing migration...")
    success, messages = migrator.execute_migration(dry_run=False)
    
    for message in messages:
        print(f"  {message}")
    
    if not success:
        print("\nMigration failed. Check backups in storage/backups/")
        return False
    
    print("\nMigration completed successfully!")
    
    # Cleanup original files
    print("\n3. Cleaning up original files...")
    success, messages = migrator.cleanup_original_files()
    
    for message in messages:
        print(f"  {message}")
    
    if success:
        print("\nProfile migration completed successfully!")
        print("All profiles are now organized in storage/profiles/")
    else:
        print("\nMigration completed but cleanup failed. Original files may still exist.")
    
    return success

if __name__ == "__main__":
    main()