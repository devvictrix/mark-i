"""
Application Context Collector

Discovers installed applications, tracks running processes, and monitors application usage patterns.
"""

import os
import subprocess
import psutil
import json
from pathlib import Path
from typing import Dict, Any, List, Set
from datetime import datetime

from .base_collector import BaseCollector


class ApplicationCollector(BaseCollector):
    """Collects application information and usage data"""

    def __init__(self):
        super().__init__("Application Collector")
        self.app_categories = {
            'browsers': ['firefox', 'chrome', 'chromium', 'safari', 'edge', 'opera', 'brave'],
            'editors': ['code', 'vim', 'nano', 'gedit', 'kate', 'emacs', 'atom', 'sublime', 'notepad++'],
            'terminals': ['gnome-terminal', 'konsole', 'xterm', 'alacritty', 'kitty', 'terminator', 'tilix'],
            'communication': ['discord', 'slack', 'telegram', 'whatsapp', 'zoom', 'teams', 'skype'],
            'development': ['docker', 'git', 'python', 'node', 'npm', 'yarn', 'java', 'gcc', 'make'],
            'media': ['vlc', 'mpv', 'spotify', 'audacity', 'gimp', 'blender', 'obs'],
            'office': ['libreoffice', 'openoffice', 'writer', 'calc', 'impress', 'word', 'excel', 'powerpoint']
        }

    def collect(self) -> Dict[str, Any]:
        """Collect comprehensive application information"""
        app_data = {
            'installed': self._discover_installed_applications(),
            'running': self._get_running_processes(),
            'usage_stats': self._get_usage_statistics(),
            'system_info': self._get_system_app_info()
        }
        return app_data

    def get_refresh_interval(self) -> int:
        """Application data refreshes every 6 hours for installed, 30 seconds for running"""
        return 30  # Frequent refresh for running processes

    def is_expensive(self) -> bool:
        """Application discovery can be expensive"""
        return True

    def _discover_installed_applications(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover installed applications by category"""
        installed_apps = {category: [] for category in self.app_categories.keys()}
        installed_apps['other'] = []

        # Get applications from multiple sources
        all_apps = []
        
        # Method 1: Check common binary paths
        all_apps.extend(self._scan_binary_paths())
        
        # Method 2: Check desktop files (Linux)
        all_apps.extend(self._scan_desktop_files())
        
        # Method 3: Check package manager (Linux)
        all_apps.extend(self._scan_package_manager())

        # Categorize applications
        for app_info in all_apps:
            categorized = False
            app_name_lower = app_info['name'].lower()
            
            for category, keywords in self.app_categories.items():
                if any(keyword in app_name_lower for keyword in keywords):
                    installed_apps[category].append(app_info)
                    categorized = True
                    break
            
            if not categorized:
                installed_apps['other'].append(app_info)

        return installed_apps

    def _scan_binary_paths(self) -> List[Dict[str, Any]]:
        """Scan common binary paths for applications"""
        apps = set()
        binary_paths = ['/usr/bin', '/usr/local/bin', '/bin', '/opt', '/snap/bin']
        
        for path_str in binary_paths:
            path = Path(path_str)
            if path.exists():
                try:
                    for binary in path.iterdir():
                        if binary.is_file() and os.access(binary, os.X_OK):
                            # Convert to frozenset to make it hashable for set
                            app_info = {
                                'name': binary.name,
                                'path': str(binary),
                                'type': 'binary',
                                'source': 'filesystem'
                            }
                            # Create a hashable representation
                            apps.add(frozenset(app_info.items()))
                except (PermissionError, OSError):
                    continue

        # Convert back to dictionaries
        return [dict(app) for app in apps]

    def _scan_desktop_files(self) -> List[Dict[str, Any]]:
        """Scan desktop files for application information"""
        apps = set()
        desktop_paths = [
            '/usr/share/applications',
            '/usr/local/share/applications',
            '~/.local/share/applications'
        ]
        
        for path_str in desktop_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                try:
                    for desktop_file in path.glob('*.desktop'):
                        app_info = self._parse_desktop_file(desktop_file)
                        if app_info:
                            apps.add(frozenset(app_info.items()))
                except (PermissionError, OSError):
                    continue

        return [dict(app) for app in apps]

    def _parse_desktop_file(self, desktop_file: Path) -> Dict[str, Any]:
        """Parse a .desktop file for application information"""
        try:
            with open(desktop_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            app_info = {
                'name': desktop_file.stem,
                'path': str(desktop_file),
                'type': 'desktop_app',
                'source': 'desktop_file'
            }
            
            for line in content.split('\n'):
                if line.startswith('Name='):
                    app_info['display_name'] = line.split('=', 1)[1]
                elif line.startswith('Exec='):
                    app_info['exec_command'] = line.split('=', 1)[1]
                elif line.startswith('Icon='):
                    app_info['icon'] = line.split('=', 1)[1]
                elif line.startswith('Comment='):
                    app_info['description'] = line.split('=', 1)[1]
                elif line.startswith('Categories='):
                    app_info['categories'] = line.split('=', 1)[1].split(';')
            
            return app_info
            
        except Exception as e:
            self.logger.debug(f"Failed to parse desktop file {desktop_file}: {str(e)}")
            return None

    def _scan_package_manager(self) -> List[Dict[str, Any]]:
        """Get installed packages from package manager"""
        apps = set()
        
        # Try different package managers
        package_managers = [
            ('dpkg', ['dpkg', '-l']),
            ('rpm', ['rpm', '-qa']),
            ('pacman', ['pacman', '-Q']),
            ('snap', ['snap', 'list']),
            ('flatpak', ['flatpak', 'list'])
        ]
        
        for pm_name, command in package_managers:
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    apps.update(self._parse_package_output(pm_name, result.stdout))
            except Exception as e:
                self.logger.debug(f"Package manager {pm_name} not available: {str(e)}")
        
        return [dict(app) for app in apps]

    def _parse_package_output(self, pm_name: str, output: str) -> List[Dict[str, Any]]:
        """Parse package manager output"""
        apps = set()
        
        for line in output.split('\n'):
            if not line.strip():
                continue
                
            try:
                if pm_name == 'dpkg':
                    parts = line.split()
                    if len(parts) >= 3 and parts[0] == 'ii':
                        app_info = {
                            'name': parts[1],
                            'version': parts[2],
                            'type': 'package',
                            'source': 'dpkg',
                            'description': ' '.join(parts[3:]) if len(parts) > 3 else ''
                        }
                        apps.add(frozenset(app_info.items()))
                        
                elif pm_name == 'snap':
                    parts = line.split()
                    if len(parts) >= 3 and parts[0] != 'Name':
                        app_info = {
                            'name': parts[0],
                            'version': parts[1],
                            'type': 'snap',
                            'source': 'snap'
                        }
                        apps.add(frozenset(app_info.items()))
                        
                elif pm_name == 'flatpak':
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        app_info = {
                            'name': parts[0],
                            'app_id': parts[1] if len(parts) > 1 else '',
                            'type': 'flatpak',
                            'source': 'flatpak'
                        }
                        apps.add(frozenset(app_info.items()))
                        
            except Exception as e:
                self.logger.debug(f"Failed to parse package line: {line}, error: {str(e)}")
        
        return [dict(app) for app in apps]

    def _get_running_processes(self) -> List[Dict[str, Any]]:
        """Get currently running processes with detailed information"""
        running_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
                try:
                    proc_info = proc.info
                    
                    # Skip kernel processes and very short-lived processes
                    if not proc_info['name'] or proc_info['name'].startswith('['):
                        continue
                    
                    process_data = {
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'command': ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else proc_info['name'],
                        'cpu_percent': round(proc_info['cpu_percent'], 2),
                        'memory_mb': round(proc_info['memory_info'].rss / (1024 * 1024), 2) if proc_info['memory_info'] else 0,
                        'start_time': datetime.fromtimestamp(proc_info['create_time']).isoformat() if proc_info['create_time'] else None
                    }
                    
                    running_processes.append(process_data)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to get running processes: {str(e)}")
            return [{'error': str(e)}]
        
        # Sort by CPU usage (descending)
        running_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        return running_processes

    def _get_usage_statistics(self) -> Dict[str, Any]:
        """Get application usage statistics"""
        # This would typically load from a persistent storage
        # For now, return basic statistics based on running processes
        
        usage_stats = {}
        running_processes = self._get_running_processes()
        
        # Count running instances and calculate basic stats
        app_counts = {}
        for proc in running_processes:
            app_name = proc['name']
            if app_name not in app_counts:
                app_counts[app_name] = {
                    'running_instances': 0,
                    'total_cpu_percent': 0,
                    'total_memory_mb': 0,
                    'first_seen': proc['start_time']
                }
            
            app_counts[app_name]['running_instances'] += 1
            app_counts[app_name]['total_cpu_percent'] += proc['cpu_percent']
            app_counts[app_name]['total_memory_mb'] += proc['memory_mb']
        
        # Convert to usage statistics format
        for app_name, stats in app_counts.items():
            usage_stats[app_name] = {
                'currently_running': True,
                'instances': stats['running_instances'],
                'cpu_usage_percent': round(stats['total_cpu_percent'], 2),
                'memory_usage_mb': round(stats['total_memory_mb'], 2),
                'last_seen': datetime.now().isoformat(),
                'first_seen_today': stats['first_seen']
            }
        
        return usage_stats

    def _get_system_app_info(self) -> Dict[str, Any]:
        """Get system-level application information"""
        try:
            system_info = {
                'total_processes': len(psutil.pids()),
                'package_managers': self._detect_package_managers(),
                'desktop_environment': os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown'),
                'session_type': os.environ.get('XDG_SESSION_TYPE', 'Unknown'),
                'app_directories': self._get_app_directories()
            }
            
            return system_info
            
        except Exception as e:
            self.logger.error(f"Failed to get system app info: {str(e)}")
            return {'error': str(e)}

    def _detect_package_managers(self) -> List[str]:
        """Detect available package managers"""
        package_managers = []
        
        pm_commands = ['dpkg', 'rpm', 'pacman', 'snap', 'flatpak', 'brew', 'pip', 'npm']
        
        for pm in pm_commands:
            try:
                result = subprocess.run(['which', pm], capture_output=True, timeout=2)
                if result.returncode == 0:
                    package_managers.append(pm)
            except Exception:
                continue
        
        return package_managers

    def _get_app_directories(self) -> List[str]:
        """Get common application directories"""
        app_dirs = []
        
        common_dirs = [
            '/usr/bin',
            '/usr/local/bin',
            '/opt',
            '/snap/bin',
            '~/.local/bin',
            '/usr/share/applications',
            '~/.local/share/applications'
        ]
        
        for dir_path in common_dirs:
            expanded_path = Path(dir_path).expanduser()
            if expanded_path.exists():
                app_dirs.append(str(expanded_path))
        
        return app_dirs