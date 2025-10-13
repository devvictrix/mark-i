"""
Quick Launch Manager

Provides quick launch capabilities, keyboard shortcuts, and profile shortcuts
for rapid profile execution from the main MARK-I interface.
"""

import logging
import json
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from datetime import datetime

from ..models.profile import AutomationProfile
from ..profile_manager import ProfileManager
from ..execution.execution_engine import ExecutionEngine, ExecutionMode


class QuickLaunchManager:
    """Manages quick launch profiles and shortcuts"""
    
    def __init__(self, config_dir: str = None):
        self.logger = logging.getLogger("mark_i.profiles.integration.quick_launch")
        
        # Configuration
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".mark_i" / "profiles"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "quick_launch.json"
        
        # Components
        self.profile_manager = ProfileManager()
        self.execution_engine = ExecutionEngine()
        
        # Quick launch configuration
        self.quick_launch_config = self._load_config()
        
        # Callbacks
        self.on_profile_launched: Optional[Callable[[AutomationProfile], None]] = None
        
        self.logger.info("QuickLaunchManager initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load quick launch configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"Failed to load quick launch config: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default quick launch configuration"""
        return {
            "quick_profiles": [],  # List of profile IDs for quick access
            "keyboard_shortcuts": {},  # Keyboard shortcuts mapping
            "favorites": [],  # Favorite profile IDs
            "recent_limit": 10,  # Number of recent profiles to keep
            "auto_launch": {},  # Auto-launch conditions
            "launch_modes": {  # Default launch modes for profiles
                "default": "normal",
                "debug_profiles": [],
                "simulation_profiles": []
            }
        }
    
    def _save_config(self):
        """Save quick launch configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.quick_launch_config, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save quick launch config: {e}")
    
    def add_quick_profile(self, profile_id: str) -> bool:
        """Add profile to quick launch list"""
        try:
            if profile_id not in self.quick_launch_config["quick_profiles"]:
                self.quick_launch_config["quick_profiles"].append(profile_id)
                self._save_config()
                self.logger.info(f"Added profile to quick launch: {profile_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to add quick profile: {e}")
            return False
    
    def remove_quick_profile(self, profile_id: str) -> bool:
        """Remove profile from quick launch list"""
        try:
            if profile_id in self.quick_launch_config["quick_profiles"]:
                self.quick_launch_config["quick_profiles"].remove(profile_id)
                self._save_config()
                self.logger.info(f"Removed profile from quick launch: {profile_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove quick profile: {e}")
            return False
    
    def get_quick_profiles(self) -> List[AutomationProfile]:
        """Get profiles configured for quick launch"""
        profiles = []
        
        try:
            for profile_id in self.quick_launch_config["quick_profiles"]:
                profile = self.profile_manager.get_profile(profile_id)
                if profile:
                    profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Failed to get quick profiles: {e}")
            return []
    
    def set_keyboard_shortcut(self, profile_id: str, shortcut: str) -> bool:
        """Set keyboard shortcut for profile"""
        try:
            # Validate shortcut format
            if not self._validate_shortcut(shortcut):
                self.logger.warning(f"Invalid shortcut format: {shortcut}")
                return False
            
            # Check for conflicts
            existing_profile = self.quick_launch_config["keyboard_shortcuts"].get(shortcut)
            if existing_profile and existing_profile != profile_id:
                self.logger.warning(f"Shortcut {shortcut} already assigned to {existing_profile}")
                return False
            
            self.quick_launch_config["keyboard_shortcuts"][shortcut] = profile_id
            self._save_config()
            
            self.logger.info(f"Set keyboard shortcut {shortcut} for profile {profile_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set keyboard shortcut: {e}")
            return False
    
    def remove_keyboard_shortcut(self, shortcut: str) -> bool:
        """Remove keyboard shortcut"""
        try:
            if shortcut in self.quick_launch_config["keyboard_shortcuts"]:
                del self.quick_launch_config["keyboard_shortcuts"][shortcut]
                self._save_config()
                self.logger.info(f"Removed keyboard shortcut: {shortcut}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove keyboard shortcut: {e}")
            return False
    
    def get_keyboard_shortcuts(self) -> Dict[str, str]:
        """Get all keyboard shortcuts"""
        return self.quick_launch_config["keyboard_shortcuts"].copy()
    
    def launch_by_shortcut(self, shortcut: str) -> bool:
        """Launch profile by keyboard shortcut"""
        try:
            profile_id = self.quick_launch_config["keyboard_shortcuts"].get(shortcut)
            if not profile_id:
                return False
            
            return self.launch_profile(profile_id)
            
        except Exception as e:
            self.logger.error(f"Failed to launch by shortcut: {e}")
            return False
    
    def launch_profile(self, profile_id: str, mode: ExecutionMode = None) -> bool:
        """Launch profile by ID"""
        try:
            profile = self.profile_manager.get_profile(profile_id)
            if not profile:
                self.logger.error(f"Profile not found: {profile_id}")
                return False
            
            # Determine execution mode
            if mode is None:
                mode = self._get_default_mode(profile_id)
            
            # Execute profile
            execution_id = self.execution_engine.execute_profile(profile, mode)
            
            # Update recent profiles
            self._update_recent_profiles(profile_id)
            
            # Callback
            if self.on_profile_launched:
                self.on_profile_launched(profile)
            
            self.logger.info(f"Launched profile: {profile.name} (ID: {execution_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to launch profile: {e}")
            return False
    
    def add_favorite(self, profile_id: str) -> bool:
        """Add profile to favorites"""
        try:
            if profile_id not in self.quick_launch_config["favorites"]:
                self.quick_launch_config["favorites"].append(profile_id)
                self._save_config()
                self.logger.info(f"Added profile to favorites: {profile_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to add favorite: {e}")
            return False
    
    def remove_favorite(self, profile_id: str) -> bool:
        """Remove profile from favorites"""
        try:
            if profile_id in self.quick_launch_config["favorites"]:
                self.quick_launch_config["favorites"].remove(profile_id)
                self._save_config()
                self.logger.info(f"Removed profile from favorites: {profile_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove favorite: {e}")
            return False
    
    def get_favorites(self) -> List[AutomationProfile]:
        """Get favorite profiles"""
        profiles = []
        
        try:
            for profile_id in self.quick_launch_config["favorites"]:
                profile = self.profile_manager.get_profile(profile_id)
                if profile:
                    profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Failed to get favorites: {e}")
            return []
    
    def get_recent_profiles(self) -> List[AutomationProfile]:
        """Get recently launched profiles"""
        profiles = []
        
        try:
            recent_ids = self.quick_launch_config.get("recent_profiles", [])
            for profile_id in recent_ids:
                profile = self.profile_manager.get_profile(profile_id)
                if profile:
                    profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Failed to get recent profiles: {e}")
            return []
    
    def set_auto_launch_condition(self, profile_id: str, condition: Dict[str, Any]) -> bool:
        """Set auto-launch condition for profile"""
        try:
            self.quick_launch_config["auto_launch"][profile_id] = condition
            self._save_config()
            
            self.logger.info(f"Set auto-launch condition for profile: {profile_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set auto-launch condition: {e}")
            return False
    
    def check_auto_launch_conditions(self) -> List[str]:
        """Check which profiles should auto-launch based on conditions"""
        auto_launch_profiles = []
        
        try:
            current_time = datetime.now()
            
            for profile_id, condition in self.quick_launch_config["auto_launch"].items():
                if self._evaluate_auto_launch_condition(condition, current_time):
                    auto_launch_profiles.append(profile_id)
            
            return auto_launch_profiles
            
        except Exception as e:
            self.logger.error(f"Failed to check auto-launch conditions: {e}")
            return []
    
    def get_launch_statistics(self) -> Dict[str, Any]:
        """Get launch statistics"""
        try:
            stats = {
                "quick_profiles_count": len(self.quick_launch_config["quick_profiles"]),
                "keyboard_shortcuts_count": len(self.quick_launch_config["keyboard_shortcuts"]),
                "favorites_count": len(self.quick_launch_config["favorites"]),
                "recent_profiles_count": len(self.quick_launch_config.get("recent_profiles", [])),
                "auto_launch_count": len(self.quick_launch_config["auto_launch"])
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get launch statistics: {e}")
            return {}
    
    # Private helper methods
    
    def _validate_shortcut(self, shortcut: str) -> bool:
        """Validate keyboard shortcut format"""
        # Basic validation - could be enhanced
        valid_modifiers = ["Ctrl", "Alt", "Shift", "Win", "Cmd"]
        parts = shortcut.split("+")
        
        if len(parts) < 2:
            return False
        
        # Check modifiers
        for modifier in parts[:-1]:
            if modifier not in valid_modifiers:
                return False
        
        # Check key
        key = parts[-1]
        if len(key) != 1 and key not in ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"]:
            return False
        
        return True
    
    def _get_default_mode(self, profile_id: str) -> ExecutionMode:
        """Get default execution mode for profile"""
        launch_modes = self.quick_launch_config["launch_modes"]
        
        if profile_id in launch_modes.get("debug_profiles", []):
            return ExecutionMode.DEBUG
        elif profile_id in launch_modes.get("simulation_profiles", []):
            return ExecutionMode.SIMULATION
        else:
            mode_name = launch_modes.get("default", "normal")
            return ExecutionMode(mode_name)
    
    def _update_recent_profiles(self, profile_id: str):
        """Update recent profiles list"""
        try:
            recent_profiles = self.quick_launch_config.get("recent_profiles", [])
            
            # Remove if already in list
            if profile_id in recent_profiles:
                recent_profiles.remove(profile_id)
            
            # Add to front
            recent_profiles.insert(0, profile_id)
            
            # Limit size
            recent_limit = self.quick_launch_config.get("recent_limit", 10)
            recent_profiles = recent_profiles[:recent_limit]
            
            self.quick_launch_config["recent_profiles"] = recent_profiles
            self._save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to update recent profiles: {e}")
    
    def _evaluate_auto_launch_condition(self, condition: Dict[str, Any], current_time: datetime) -> bool:
        """Evaluate auto-launch condition"""
        try:
            condition_type = condition.get("type")
            
            if condition_type == "time":
                target_time = datetime.strptime(condition["time"], "%H:%M").time()
                return current_time.time() >= target_time
            elif condition_type == "day_of_week":
                target_day = condition["day"]  # 0=Monday, 6=Sunday
                return current_time.weekday() == target_day
            elif condition_type == "application_start":
                # Would check if specific application started
                return False  # Placeholder
            elif condition_type == "system_idle":
                # Would check system idle time
                return False  # Placeholder
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate auto-launch condition: {e}")
            return False


class ProfileShortcuts:
    """Manages profile keyboard shortcuts integration with main GUI"""
    
    def __init__(self, main_window, quick_launch_manager: QuickLaunchManager):
        self.main_window = main_window
        self.quick_launch_manager = quick_launch_manager
        self.logger = logging.getLogger("mark_i.profiles.integration.shortcuts")
        
        # Bind shortcuts
        self._bind_shortcuts()
        
        self.logger.info("ProfileShortcuts initialized")
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts to main window"""
        try:
            shortcuts = self.quick_launch_manager.get_keyboard_shortcuts()
            
            for shortcut, profile_id in shortcuts.items():
                # Convert shortcut format for tkinter
                tk_shortcut = self._convert_shortcut_format(shortcut)
                
                # Bind to main window
                self.main_window.bind(
                    tk_shortcut,
                    lambda event, pid=profile_id: self._handle_shortcut(pid)
                )
                
                self.logger.debug(f"Bound shortcut {shortcut} -> {tk_shortcut} for profile {profile_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to bind shortcuts: {e}")
    
    def _convert_shortcut_format(self, shortcut: str) -> str:
        """Convert shortcut format to tkinter format"""
        # Convert from "Ctrl+Shift+P" to "<Control-Shift-P>"
        parts = shortcut.split("+")
        
        # Map modifier names
        modifier_map = {
            "Ctrl": "Control",
            "Alt": "Alt",
            "Shift": "Shift",
            "Win": "Win",
            "Cmd": "Command"
        }
        
        tk_parts = []
        for part in parts:
            if part in modifier_map:
                tk_parts.append(modifier_map[part])
            else:
                tk_parts.append(part.lower())
        
        return f"<{'-'.join(tk_parts)}>"
    
    def _handle_shortcut(self, profile_id: str):
        """Handle keyboard shortcut activation"""
        try:
            success = self.quick_launch_manager.launch_profile(profile_id)
            if not success:
                self.logger.warning(f"Failed to launch profile via shortcut: {profile_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle shortcut: {e}")
    
    def refresh_shortcuts(self):
        """Refresh keyboard shortcut bindings"""
        try:
            # Unbind existing shortcuts (would need to track them)
            # For now, just rebind all
            self._bind_shortcuts()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh shortcuts: {e}")
    
    def add_shortcut(self, profile_id: str, shortcut: str) -> bool:
        """Add new keyboard shortcut"""
        try:
            if self.quick_launch_manager.set_keyboard_shortcut(profile_id, shortcut):
                # Bind the new shortcut
                tk_shortcut = self._convert_shortcut_format(shortcut)
                self.main_window.bind(
                    tk_shortcut,
                    lambda event, pid=profile_id: self._handle_shortcut(pid)
                )
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to add shortcut: {e}")
            return False
    
    def remove_shortcut(self, shortcut: str) -> bool:
        """Remove keyboard shortcut"""
        try:
            if self.quick_launch_manager.remove_keyboard_shortcut(shortcut):
                # Unbind the shortcut
                tk_shortcut = self._convert_shortcut_format(shortcut)
                self.main_window.unbind(tk_shortcut)
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove shortcut: {e}")
            return False