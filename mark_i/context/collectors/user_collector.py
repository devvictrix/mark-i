"""
User Environment Context Collector

Collects user profile information, locale settings, working environment, and behavior patterns.
"""

import os
import pwd
import grp
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from .base_collector import BaseCollector


class UserCollector(BaseCollector):
    """Collects user environment and behavior context"""

    def __init__(self):
        super().__init__("User Environment Collector")

    def collect(self) -> Dict[str, Any]:
        """Collect comprehensive user environment information"""
        user_data = {
            'profile': self._collect_user_profile(),
            'locale': self._collect_locale_info(),
            'working_context': self._collect_working_context(),
            'behavior_patterns': self._collect_behavior_patterns(),
            'preferences': self._collect_user_preferences(),
            'environment_variables': self._collect_environment_info()
        }
        return user_data

    def get_refresh_interval(self) -> int:
        """User environment changes moderately"""
        return 300  # 5 minutes

    def is_expensive(self) -> bool:
        """File system scanning can be expensive"""
        return True

    def _collect_user_profile(self) -> Dict[str, Any]:
        """Collect user profile information"""
        try:
            # Get current user info
            user_info = pwd.getpwuid(os.getuid())
            
            profile_info = {
                'username': user_info.pw_name,
                'uid': user_info.pw_uid,
                'gid': user_info.pw_gid,
                'home_directory': user_info.pw_dir,
                'shell': user_info.pw_shell,
                'real_name': user_info.pw_gecos.split(',')[0] if user_info.pw_gecos else '',
                'groups': self._get_user_groups(),
                'sudo_access': self._check_sudo_access()
            }
            
            # Get additional user info
            profile_info.update(self._get_user_details())
            
            return profile_info
            
        except Exception as e:
            self.logger.error(f"Failed to collect user profile: {str(e)}")
            return {'error': str(e)}

    def _get_user_groups(self) -> List[str]:
        """Get groups the user belongs to"""
        try:
            groups = []
            for group in grp.getgrall():
                if os.getenv('USER') in group.gr_mem:
                    groups.append(group.gr_name)
            
            # Also add primary group
            try:
                primary_group = grp.getgrgid(os.getgid())
                if primary_group.gr_name not in groups:
                    groups.append(primary_group.gr_name)
            except Exception:
                pass
            
            return groups
            
        except Exception:
            return []

    def _check_sudo_access(self) -> bool:
        """Check if user has sudo access"""
        try:
            result = subprocess.run(['sudo', '-n', 'true'], 
                                  capture_output=True, timeout=3)
            return result.returncode == 0
        except Exception:
            return False

    def _get_user_details(self) -> Dict[str, Any]:
        """Get additional user details"""
        details = {}
        
        try:
            # Get user creation time (approximate from home directory)
            home_path = Path.home()
            if home_path.exists():
                stat = home_path.stat()
                details['home_created'] = datetime.fromtimestamp(stat.st_ctime).isoformat()
            
            # Get login history (last few logins)
            try:
                result = subprocess.run(['last', '-n', '5', os.getenv('USER', '')], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    login_history = []
                    for line in result.stdout.split('\n'):
                        if line.strip() and not line.startswith('wtmp'):
                            login_history.append(line.strip())
                    details['recent_logins'] = login_history[:3]  # Last 3 logins
            except Exception:
                pass
            
        except Exception as e:
            self.logger.debug(f"Failed to get user details: {str(e)}")
        
        return details

    def _collect_locale_info(self) -> Dict[str, Any]:
        """Collect locale and internationalization settings"""
        try:
            locale_info = {
                'language': os.environ.get('LANG', 'Unknown'),
                'lc_all': os.environ.get('LC_ALL'),
                'lc_messages': os.environ.get('LC_MESSAGES'),
                'lc_time': os.environ.get('LC_TIME'),
                'lc_numeric': os.environ.get('LC_NUMERIC'),
                'timezone': self._get_timezone(),
                'keyboard_layout': self._get_keyboard_layout(),
                'date_format': self._get_date_format(),
                'time_format': self._get_time_format()
            }
            
            return locale_info
            
        except Exception as e:
            self.logger.error(f"Failed to collect locale info: {str(e)}")
            return {'error': str(e)}

    def _get_timezone(self) -> str:
        """Get system timezone"""
        try:
            # Try multiple methods
            methods = [
                lambda: os.environ.get('TZ'),
                lambda: subprocess.run(['timedatectl', 'show', '--property=Timezone', '--value'], 
                                     capture_output=True, text=True, timeout=3).stdout.strip(),
                lambda: Path('/etc/timezone').read_text().strip() if Path('/etc/timezone').exists() else None,
                lambda: os.readlink('/etc/localtime').split('zoneinfo/')[-1] if os.path.islink('/etc/localtime') else None
            ]
            
            for method in methods:
                try:
                    result = method()
                    if result and result.strip():
                        return result.strip()
                except Exception:
                    continue
            
            return 'Unknown'
            
        except Exception:
            return 'Unknown'

    def _get_keyboard_layout(self) -> str:
        """Get keyboard layout"""
        try:
            # Try different methods based on desktop environment
            methods = [
                # X11 method
                lambda: subprocess.run(['setxkbmap', '-query'], 
                                     capture_output=True, text=True, timeout=3),
                # Localectl method
                lambda: subprocess.run(['localectl', 'status'], 
                                     capture_output=True, text=True, timeout=3)
            ]
            
            for method in methods:
                try:
                    result = method()
                    if result.returncode == 0:
                        output = result.stdout
                        if 'layout:' in output:
                            for line in output.split('\n'):
                                if 'layout:' in line.lower():
                                    return line.split(':')[1].strip()
                        elif 'Layout:' in output:
                            for line in output.split('\n'):
                                if 'Layout:' in line:
                                    return line.split(':')[1].strip()
                except Exception:
                    continue
            
            return 'Unknown'
            
        except Exception:
            return 'Unknown'

    def _get_date_format(self) -> str:
        """Get preferred date format"""
        try:
            result = subprocess.run(['locale', 'date_fmt'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Fallback based on locale
            lang = os.environ.get('LANG', '')
            if 'US' in lang:
                return 'MM/DD/YYYY'
            else:
                return 'DD/MM/YYYY'
                
        except Exception:
            return 'Unknown'

    def _get_time_format(self) -> str:
        """Get preferred time format"""
        try:
            result = subprocess.run(['locale', 't_fmt'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                fmt = result.stdout.strip()
                return '24h' if '%H' in fmt else '12h'
            
            return '24h'  # Default assumption
            
        except Exception:
            return 'Unknown'

    def _collect_working_context(self) -> Dict[str, Any]:
        """Collect current working context"""
        try:
            working_context = {
                'current_directory': os.getcwd(),
                'recent_directories': self._get_recent_directories(),
                'active_projects': self._detect_active_projects(),
                'development_tools': self._detect_development_tools(),
                'workspace_info': self._get_workspace_info()
            }
            
            return working_context
            
        except Exception as e:
            self.logger.error(f"Failed to collect working context: {str(e)}")
            return {'error': str(e)}

    def _get_recent_directories(self) -> List[str]:
        """Get recently accessed directories"""
        recent_dirs = []
        
        try:
            # Check bash history for cd commands
            history_file = Path.home() / '.bash_history'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Look for cd commands in recent history
                for line in reversed(lines[-1000:]):  # Last 1000 commands
                    if line.strip().startswith('cd '):
                        path = line.strip()[3:].strip()
                        if path and path not in recent_dirs:
                            # Expand path
                            expanded_path = Path(path).expanduser()
                            if expanded_path.exists() and expanded_path.is_dir():
                                recent_dirs.append(str(expanded_path))
                        
                        if len(recent_dirs) >= 10:
                            break
            
        except Exception as e:
            self.logger.debug(f"Failed to get recent directories: {str(e)}")
        
        return recent_dirs

    def _detect_active_projects(self) -> List[Dict[str, Any]]:
        """Detect active development projects"""
        projects = []
        
        try:
            # Common project directories
            search_dirs = [
                Path.home() / 'projects',
                Path.home() / 'workspace',
                Path.home() / 'dev',
                Path.home() / 'code',
                Path.home() / 'Documents',
                Path.cwd()
            ]
            
            for search_dir in search_dirs:
                if search_dir.exists() and search_dir.is_dir():
                    projects.extend(self._scan_for_projects(search_dir))
            
            # Sort by last modified time
            projects.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
            
            return projects[:10]  # Top 10 most recent
            
        except Exception as e:
            self.logger.debug(f"Failed to detect active projects: {str(e)}")
            return []

    def _scan_for_projects(self, directory: Path, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Scan directory for development projects"""
        projects = []
        
        try:
            if max_depth <= 0:
                return projects
            
            for item in directory.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    project_info = self._analyze_project_directory(item)
                    if project_info:
                        projects.append(project_info)
                    
                    # Recurse into subdirectories
                    if max_depth > 1:
                        projects.extend(self._scan_for_projects(item, max_depth - 1))
                        
        except (PermissionError, OSError):
            pass
        
        return projects

    def _analyze_project_directory(self, directory: Path) -> Dict[str, Any]:
        """Analyze if directory is a development project"""
        project_indicators = {
            '.git': 'git',
            'package.json': 'node.js',
            'requirements.txt': 'python',
            'Pipfile': 'python',
            'setup.py': 'python',
            'Cargo.toml': 'rust',
            'pom.xml': 'java',
            'build.gradle': 'java',
            'Makefile': 'c/c++',
            'CMakeLists.txt': 'c/c++',
            'composer.json': 'php',
            'Gemfile': 'ruby'
        }
        
        try:
            project_type = None
            for indicator, ptype in project_indicators.items():
                if (directory / indicator).exists():
                    project_type = ptype
                    break
            
            if project_type:
                stat = directory.stat()
                return {
                    'path': str(directory),
                    'name': directory.name,
                    'type': project_type,
                    'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size_mb': self._get_directory_size(directory)
                }
                
        except Exception:
            pass
        
        return None

    def _get_directory_size(self, directory: Path) -> float:
        """Get directory size in MB (with reasonable limits)"""
        try:
            total_size = 0
            file_count = 0
            
            for item in directory.rglob('*'):
                if file_count > 1000:  # Limit to avoid long scans
                    break
                    
                try:
                    if item.is_file():
                        total_size += item.stat().st_size
                        file_count += 1
                except (PermissionError, OSError):
                    continue
            
            return round(total_size / (1024 * 1024), 2)
            
        except Exception:
            return 0.0

    def _detect_development_tools(self) -> List[str]:
        """Detect installed development tools"""
        tools = []
        
        # Common development tools to check
        dev_tools = [
            'git', 'python', 'python3', 'node', 'npm', 'yarn',
            'java', 'javac', 'gcc', 'g++', 'make', 'cmake',
            'docker', 'docker-compose', 'kubectl', 'helm',
            'code', 'vim', 'emacs', 'nano'
        ]
        
        for tool in dev_tools:
            try:
                result = subprocess.run(['which', tool], 
                                      capture_output=True, timeout=1)
                if result.returncode == 0:
                    tools.append(tool)
            except Exception:
                continue
        
        return tools

    def _get_workspace_info(self) -> Dict[str, Any]:
        """Get workspace-specific information"""
        workspace_info = {}
        
        try:
            # Check if in a git repository
            try:
                result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    git_root = result.stdout.strip()
                    workspace_info['git_repository'] = git_root
                    
                    # Get git info
                    workspace_info['git_info'] = self._get_git_info(git_root)
            except Exception:
                pass
            
            # Check for virtual environments
            if os.environ.get('VIRTUAL_ENV'):
                workspace_info['virtual_env'] = os.environ['VIRTUAL_ENV']
            
            if os.environ.get('CONDA_DEFAULT_ENV'):
                workspace_info['conda_env'] = os.environ['CONDA_DEFAULT_ENV']
            
        except Exception as e:
            self.logger.debug(f"Failed to get workspace info: {str(e)}")
        
        return workspace_info

    def _get_git_info(self, git_root: str) -> Dict[str, Any]:
        """Get git repository information"""
        git_info = {}
        
        try:
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  cwd=git_root, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                git_info['current_branch'] = result.stdout.strip()
            
            # Get remote origin
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  cwd=git_root, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                git_info['remote_origin'] = result.stdout.strip()
            
            # Get status
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=git_root, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
                git_info['uncommitted_changes'] = len(changes)
                git_info['is_clean'] = len(changes) == 0
                
        except Exception as e:
            self.logger.debug(f"Failed to get git info: {str(e)}")
        
        return git_info

    def _collect_behavior_patterns(self) -> Dict[str, Any]:
        """Collect user behavior patterns"""
        try:
            patterns = {
                'most_active_hours': self._analyze_active_hours(),
                'preferred_applications': self._get_preferred_applications(),
                'workflow_patterns': self._detect_workflow_patterns(),
                'usage_statistics': self._get_usage_statistics()
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to collect behavior patterns: {str(e)}")
            return {'error': str(e)}

    def _analyze_active_hours(self) -> List[int]:
        """Analyze most active hours based on command history"""
        active_hours = [0] * 24
        
        try:
            history_file = Path.home() / '.bash_history'
            if history_file.exists():
                # This is a simplified analysis - in a real implementation,
                # you'd want to correlate with actual timestamps
                current_hour = datetime.now().hour
                # Assume current activity pattern
                for i in range(-4, 5):  # 4 hours before and after current
                    hour = (current_hour + i) % 24
                    active_hours[hour] += 1
            
            # Return hours with activity (non-zero values)
            return [hour for hour, activity in enumerate(active_hours) if activity > 0]
            
        except Exception:
            return [9, 10, 11, 14, 15, 16]  # Default work hours

    def _get_preferred_applications(self) -> List[str]:
        """Get frequently used applications from history"""
        app_usage = {}
        
        try:
            history_file = Path.home() / '.bash_history'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        command = line.strip().split()[0] if line.strip() else ''
                        if command and not command.startswith('#'):
                            app_usage[command] = app_usage.get(command, 0) + 1
            
            # Sort by usage and return top applications
            sorted_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)
            return [app for app, count in sorted_apps[:10]]
            
        except Exception:
            return ['bash', 'ls', 'cd', 'git']  # Default common commands

    def _detect_workflow_patterns(self) -> Dict[str, List[str]]:
        """Detect common workflow patterns"""
        # This is a simplified implementation
        # In practice, you'd analyze command sequences and application usage
        
        workflows = {
            'development': ['git', 'code', 'python', 'npm', 'docker'],
            'system_admin': ['sudo', 'systemctl', 'ps', 'top', 'grep'],
            'file_management': ['ls', 'cd', 'cp', 'mv', 'rm', 'find']
        }
        
        return workflows

    def _get_usage_statistics(self) -> Dict[str, Any]:
        """Get basic usage statistics"""
        return {
            'session_start': datetime.now().isoformat(),
            'shell_sessions_today': 1,  # Simplified
            'commands_executed_today': 0  # Would need to track this
        }

    def _collect_user_preferences(self) -> Dict[str, Any]:
        """Collect user preferences from various sources"""
        try:
            preferences = {
                'editor': os.environ.get('EDITOR', 'Unknown'),
                'pager': os.environ.get('PAGER', 'Unknown'),
                'browser': os.environ.get('BROWSER', 'Unknown'),
                'terminal': os.environ.get('TERM', 'Unknown'),
                'shell_preferences': self._get_shell_preferences()
            }
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Failed to collect user preferences: {str(e)}")
            return {'error': str(e)}

    def _get_shell_preferences(self) -> Dict[str, Any]:
        """Get shell-specific preferences"""
        shell_prefs = {}
        
        try:
            # Check common shell config files
            config_files = [
                '.bashrc', '.bash_profile', '.zshrc', '.profile'
            ]
            
            for config_file in config_files:
                config_path = Path.home() / config_file
                if config_path.exists():
                    shell_prefs[config_file] = {
                        'exists': True,
                        'size': config_path.stat().st_size,
                        'modified': datetime.fromtimestamp(config_path.stat().st_mtime).isoformat()
                    }
                    
        except Exception as e:
            self.logger.debug(f"Failed to get shell preferences: {str(e)}")
        
        return shell_prefs

    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect relevant environment variables"""
        try:
            # Filter environment variables to include only relevant ones
            relevant_vars = [
                'PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'EDITOR', 'PAGER',
                'LANG', 'LC_ALL', 'TZ', 'DISPLAY', 'WAYLAND_DISPLAY',
                'XDG_CURRENT_DESKTOP', 'XDG_SESSION_TYPE', 'VIRTUAL_ENV',
                'CONDA_DEFAULT_ENV', 'PYTHONPATH', 'NODE_PATH'
            ]
            
            env_info = {}
            for var in relevant_vars:
                value = os.environ.get(var)
                if value:
                    env_info[var] = value
            
            return env_info
            
        except Exception as e:
            self.logger.error(f"Failed to collect environment info: {str(e)}")
            return {'error': str(e)}