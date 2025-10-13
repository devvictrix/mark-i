"""
MARK-I Storage Manager
Manages all data storage with OS-specific organization.
"""

import os
import json
import platform
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.core.storage_manager")

class StorageManager:
    """Manages all MARK-I data storage with OS-specific organization."""
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        
        self.project_root = Path(project_root)
        self.storage_root = self.project_root / "storage"
        
        # Storage directories
        self.os_storage = self.storage_root / "os"
        self.images_storage = self.storage_root / "images"
        self.logs_storage = self.storage_root / "logs"
        self.cache_storage = self.storage_root / "cache"
        self.knowledge_storage = self.storage_root / "knowledge"
        self.profiles_storage = self.storage_root  # profiles are now in storage root
        
        # OS information
        self.os_info = None
        self.os_id = None
        
        # Initialize storage
        self._initialize_storage()
        self._detect_and_store_os_info()
        
        logger.info(f"StorageManager initialized for OS: {self.os_id}")
    
    def _initialize_storage(self):
        """Initialize all storage directories."""
        directories = [
            self.storage_root,
            self.os_storage,
            self.images_storage,
            self.logs_storage,
            self.cache_storage,
            self.knowledge_storage
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("Storage directories initialized")
    
    def _detect_and_store_os_info(self):
        """Detect OS information and store it."""
        try:
            # Get basic OS info
            self.os_info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "python_version": platform.python_version(),
                "detected_at": datetime.now().isoformat()
            }
            
            # Get detailed Linux info if available
            if platform.system() == "Linux":
                self._get_linux_details()
            elif platform.system() == "Windows":
                self._get_windows_details()
            elif platform.system() == "Darwin":
                self._get_macos_details()
            
            # Create OS identifier
            self.os_id = self._create_os_identifier()
            
            # Store OS info
            self._store_os_info()
            
        except Exception as e:
            logger.error(f"Error detecting OS info: {e}")
            self.os_info = {"system": "unknown", "detected_at": datetime.now().isoformat()}
            self.os_id = "unknown"
    
    def _get_linux_details(self):
        """Get detailed Linux distribution information."""
        try:
            # Try /etc/os-release first
            os_release_path = Path("/etc/os-release")
            if os_release_path.exists():
                with open(os_release_path, 'r') as f:
                    os_release_content = f.read()
                
                # Parse os-release
                os_release_data = {}
                for line in os_release_content.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes
                        value = value.strip('"\'')
                        os_release_data[key] = value
                
                self.os_info.update({
                    "distribution": os_release_data.get("NAME", "Unknown"),
                    "distribution_version": os_release_data.get("VERSION", "Unknown"),
                    "distribution_id": os_release_data.get("ID", "unknown"),
                    "version_codename": os_release_data.get("VERSION_CODENAME", "unknown"),
                    "pretty_name": os_release_data.get("PRETTY_NAME", "Unknown Linux"),
                    "os_release_raw": os_release_content
                })
                
                logger.info(f"Detected Linux: {os_release_data.get('PRETTY_NAME', 'Unknown')}")
            
            # Get additional system info
            try:
                # Kernel version
                uname_result = subprocess.run(["uname", "-r"], capture_output=True, text=True, timeout=2)
                if uname_result.returncode == 0:
                    self.os_info["kernel_version"] = uname_result.stdout.strip()
            except:
                pass
            
            # Desktop environment
            desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")
            session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
            self.os_info.update({
                "desktop_environment": desktop_env,
                "session_type": session_type,
                "display": os.environ.get("DISPLAY", "unknown")
            })
            
        except Exception as e:
            logger.error(f"Error getting Linux details: {e}")
    
    def _get_windows_details(self):
        """Get detailed Windows information."""
        try:
            import winreg
            
            # Get Windows version from registry
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            
            self.os_info.update({
                "windows_version": winreg.QueryValueEx(key, "ProductName")[0],
                "build_number": winreg.QueryValueEx(key, "CurrentBuild")[0],
                "edition": winreg.QueryValueEx(key, "EditionID")[0]
            })
            
            winreg.CloseKey(key)
            
        except Exception as e:
            logger.error(f"Error getting Windows details: {e}")
    
    def _get_macos_details(self):
        """Get detailed macOS information."""
        try:
            # Get macOS version
            result = subprocess.run(["sw_vers"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                macos_info = {}
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        macos_info[key.strip()] = value.strip()
                
                self.os_info.update({
                    "macos_version": macos_info.get("ProductVersion", "Unknown"),
                    "macos_name": macos_info.get("ProductName", "macOS"),
                    "build_version": macos_info.get("BuildVersion", "Unknown")
                })
                
        except Exception as e:
            logger.error(f"Error getting macOS details: {e}")
    
    def _create_os_identifier(self) -> str:
        """Create a unique OS identifier."""
        try:
            system = self.os_info.get("system", "unknown").lower()
            
            if system == "linux":
                dist_id = self.os_info.get("distribution_id", "linux")
                version = self.os_info.get("version_codename", "unknown")
                return f"{dist_id}_{version}"
            elif system == "windows":
                build = self.os_info.get("build_number", "unknown")
                return f"windows_{build}"
            elif system == "darwin":
                version = self.os_info.get("macos_version", "unknown").replace(".", "_")
                return f"macos_{version}"
            else:
                return system
                
        except Exception as e:
            logger.error(f"Error creating OS identifier: {e}")
            return "unknown"
    
    def _store_os_info(self):
        """Store OS information to storage."""
        try:
            os_file = self.os_storage / f"{self.os_id}.json"
            
            with open(os_file, 'w') as f:
                json.dump(self.os_info, f, indent=2)
            
            # Also create a latest.json symlink/copy
            latest_file = self.os_storage / "latest.json"
            shutil.copy2(os_file, latest_file)
            
            logger.info(f"OS info stored: {os_file}")
            
        except Exception as e:
            logger.error(f"Error storing OS info: {e}")
    
    def get_os_info(self) -> Dict[str, Any]:
        """Get current OS information."""
        return self.os_info.copy() if self.os_info else {}
    
    def get_os_id(self) -> str:
        """Get OS identifier."""
        return self.os_id or "unknown"
    
    def get_storage_path(self, storage_type: str) -> Path:
        """Get path for specific storage type."""
        storage_paths = {
            "os": self.os_storage,
            "images": self.images_storage,
            "logs": self.logs_storage,
            "cache": self.cache_storage,
            "knowledge": self.knowledge_storage,
            "profiles": self.profiles_storage,
            "root": self.storage_root
        }
        
        return storage_paths.get(storage_type, self.storage_root)
    
    def store_image(self, image_data: bytes, filename: str, category: str = "general") -> Path:
        """Store image data with categorization."""
        try:
            category_dir = self.images_storage / category
            category_dir.mkdir(exist_ok=True)
            
            # Add timestamp to filename to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            timestamped_filename = f"{name}_{timestamp}{ext}"
            
            image_path = category_dir / timestamped_filename
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Image stored: {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Error storing image: {e}")
            raise
    
    def store_json_data(self, data: Dict[str, Any], filename: str, storage_type: str = "cache") -> Path:
        """Store JSON data in specified storage."""
        try:
            storage_path = self.get_storage_path(storage_type)
            file_path = storage_path / filename
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"JSON data stored: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error storing JSON data: {e}")
            raise
    
    def load_json_data(self, filename: str, storage_type: str = "cache") -> Optional[Dict[str, Any]]:
        """Load JSON data from specified storage."""
        try:
            storage_path = self.get_storage_path(storage_type)
            file_path = storage_path / filename
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error loading JSON data: {e}")
            return None
    
    def cleanup_old_files(self, storage_type: str, days_old: int = 30):
        """Clean up old files from storage."""
        try:
            storage_path = self.get_storage_path(storage_type)
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            cleaned_count = 0
            for file_path in storage_path.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            logger.info(f"Cleaned {cleaned_count} old files from {storage_type} storage")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            stats = {}
            
            for storage_type in ["os", "images", "logs", "cache", "knowledge", "profiles"]:
                storage_path = self.get_storage_path(storage_type)
                
                if storage_path.exists():
                    total_size = 0
                    file_count = 0
                    
                    for file_path in storage_path.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1
                    
                    stats[storage_type] = {
                        "file_count": file_count,
                        "total_size_bytes": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2)
                    }
                else:
                    stats[storage_type] = {
                        "file_count": 0,
                        "total_size_bytes": 0,
                        "total_size_mb": 0.0
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}
    
    def export_os_info(self) -> str:
        """Export OS information as formatted string."""
        if not self.os_info:
            return "OS information not available"
        
        lines = [
            "MARK-I System Information",
            "=" * 30,
            f"OS ID: {self.os_id}",
            f"System: {self.os_info.get('system', 'Unknown')}",
            f"Release: {self.os_info.get('release', 'Unknown')}",
            f"Machine: {self.os_info.get('machine', 'Unknown')}",
            f"Architecture: {self.os_info.get('architecture', 'Unknown')}",
        ]
        
        if self.os_info.get("system") == "Linux":
            lines.extend([
                f"Distribution: {self.os_info.get('distribution', 'Unknown')}",
                f"Version: {self.os_info.get('distribution_version', 'Unknown')}",
                f"Codename: {self.os_info.get('version_codename', 'Unknown')}",
                f"Desktop: {self.os_info.get('desktop_environment', 'Unknown')}",
                f"Session: {self.os_info.get('session_type', 'Unknown')}",
            ])
        
        lines.extend([
            f"Python: {self.os_info.get('python_version', 'Unknown')}",
            f"Detected: {self.os_info.get('detected_at', 'Unknown')}"
        ])
        
        return "\n".join(lines)