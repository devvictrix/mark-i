"""
UI Context Collector

Collects desktop environment, window manager, theme information, and active window details.
"""

import os
import subprocess
import psutil
from typing import Dict, Any, List
from datetime import datetime

from .base_collector import BaseCollector


class UICollector(BaseCollector):
    """Collects UI and desktop environment context"""

    def __init__(self):
        super().__init__("UI Collector")

    def collect(self) -> Dict[str, Any]:
        """Collect comprehensive UI context information"""
        ui_data = {
            'desktop_environment': self._collect_desktop_environment(),
            'window_manager': self._collect_window_manager(),
            'theme': self._collect_theme_info(),
            'workspaces': self._collect_workspace_info(),
            'active_windows': self._collect_active_windows(),
            'input_devices': self._collect_input_devices(),
            'accessibility': self._collect_accessibility_info()
        }
        return ui_data

    def get_refresh_interval(self) -> int:
        """UI context refreshes every 5 seconds for real-time data"""
        return 5

    def is_expensive(self) -> bool:
        """Window enumeration can be expensive"""
        return True

    def _collect_desktop_environment(self) -> Dict[str, Any]:
        """Collect desktop environment information"""
        try:
            de_info = {
                'name': os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown'),
                'session_type': os.environ.get('XDG_SESSION_TYPE', 'Unknown'),
                'session_desktop': os.environ.get('XDG_SESSION_DESKTOP', 'Unknown'),
                'gdm_session': os.environ.get('GDMSESSION', 'Unknown'),
                'desktop_session': os.environ.get('DESKTOP_SESSION', 'Unknown')
            }

            # Try to get version information for common DEs
            de_name = de_info['name'].lower()
            
            if 'gnome' in de_name:
                de_info.update(self._get_gnome_info())
            elif 'kde' in de_name or 'plasma' in de_name:
                de_info.update(self._get_kde_info())
            elif 'xfce' in de_name:
                de_info.update(self._get_xfce_info())
            elif 'mate' in de_name:
                de_info.update(self._get_mate_info())

            return de_info

        except Exception as e:
            self.logger.error(f"Failed to collect desktop environment info: {str(e)}")
            return {'error': str(e)}

    def _get_gnome_info(self) -> Dict[str, Any]:
        """Get GNOME-specific information"""
        gnome_info = {}
        try:
            # Get GNOME Shell version
            result = subprocess.run(['gnome-shell', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gnome_info['shell_version'] = result.stdout.strip()
        except Exception:
            pass

        try:
            # Get GTK version
            result = subprocess.run(['pkg-config', '--modversion', 'gtk+-3.0'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gnome_info['gtk_version'] = result.stdout.strip()
        except Exception:
            pass

        return gnome_info

    def _get_kde_info(self) -> Dict[str, Any]:
        """Get KDE-specific information"""
        kde_info = {}
        try:
            # Get KDE Plasma version
            result = subprocess.run(['plasmashell', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                kde_info['plasma_version'] = result.stdout.strip()
        except Exception:
            pass

        try:
            # Get Qt version
            result = subprocess.run(['qmake', '-query', 'QT_VERSION'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                kde_info['qt_version'] = result.stdout.strip()
        except Exception:
            pass

        return kde_info

    def _get_xfce_info(self) -> Dict[str, Any]:
        """Get XFCE-specific information"""
        xfce_info = {}
        try:
            result = subprocess.run(['xfce4-about', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                xfce_info['version'] = result.stdout.strip()
        except Exception:
            pass

        return xfce_info

    def _get_mate_info(self) -> Dict[str, Any]:
        """Get MATE-specific information"""
        mate_info = {}
        try:
            result = subprocess.run(['mate-about', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                mate_info['version'] = result.stdout.strip()
        except Exception:
            pass

        return mate_info

    def _collect_window_manager(self) -> Dict[str, Any]:
        """Collect window manager information"""
        try:
            wm_info = {
                'name': 'Unknown',
                'version': 'Unknown',
                'compositor': 'Unknown'
            }

            # Check for common window managers
            wm_processes = ['mutter', 'kwin', 'xfwm4', 'openbox', 'i3', 'awesome', 'dwm', 'bspwm']
            
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    if proc_name in wm_processes:
                        wm_info['name'] = proc_name
                        
                        # Try to get version
                        try:
                            if proc_name == 'mutter':
                                result = subprocess.run(['mutter', '--version'], capture_output=True, text=True, timeout=3)
                                if result.returncode == 0:
                                    wm_info['version'] = result.stdout.strip()
                            elif proc_name == 'kwin':
                                result = subprocess.run(['kwin', '--version'], capture_output=True, text=True, timeout=3)
                                if result.returncode == 0:
                                    wm_info['version'] = result.stdout.strip()
                        except Exception:
                            pass
                        break
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Detect compositor
            if os.environ.get('WAYLAND_DISPLAY'):
                wm_info['compositor'] = 'wayland'
            elif os.environ.get('DISPLAY'):
                wm_info['compositor'] = 'x11'

            return wm_info

        except Exception as e:
            self.logger.error(f"Failed to collect window manager info: {str(e)}")
            return {'error': str(e)}

    def _collect_theme_info(self) -> Dict[str, Any]:
        """Collect theme and appearance information"""
        try:
            theme_info = {
                'gtk_theme': 'Unknown',
                'icon_theme': 'Unknown',
                'cursor_theme': 'Unknown',
                'font': 'Unknown'
            }

            # Try to get GTK theme info
            try:
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    theme_info['gtk_theme'] = result.stdout.strip().strip("'")
            except Exception:
                pass

            try:
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'icon-theme'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    theme_info['icon_theme'] = result.stdout.strip().strip("'")
            except Exception:
                pass

            try:
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'cursor-theme'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    theme_info['cursor_theme'] = result.stdout.strip().strip("'")
            except Exception:
                pass

            try:
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'font-name'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    theme_info['font'] = result.stdout.strip().strip("'")
            except Exception:
                pass

            # Try to get scaling factor
            try:
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'scaling-factor'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    theme_info['scaling_factor'] = float(result.stdout.strip())
            except Exception:
                theme_info['scaling_factor'] = 1.0

            return theme_info

        except Exception as e:
            self.logger.error(f"Failed to collect theme info: {str(e)}")
            return {'error': str(e)}

    def _collect_workspace_info(self) -> Dict[str, Any]:
        """Collect workspace information"""
        try:
            workspace_info = {
                'total': 1,
                'current': 1,
                'names': []
            }

            # Try different methods based on window manager
            if os.environ.get('WAYLAND_DISPLAY'):
                workspace_info.update(self._get_wayland_workspaces())
            else:
                workspace_info.update(self._get_x11_workspaces())

            return workspace_info

        except Exception as e:
            self.logger.error(f"Failed to collect workspace info: {str(e)}")
            return {'error': str(e)}

    def _get_wayland_workspaces(self) -> Dict[str, Any]:
        """Get workspace info under Wayland"""
        workspace_info = {}
        
        # Try swaymsg for Sway
        try:
            result = subprocess.run(['swaymsg', '-t', 'get_workspaces'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                import json
                workspaces = json.loads(result.stdout)
                workspace_info['total'] = len(workspaces)
                workspace_info['names'] = [ws['name'] for ws in workspaces]
                current_ws = [ws for ws in workspaces if ws.get('focused')]
                if current_ws:
                    workspace_info['current'] = current_ws[0]['name']
        except Exception:
            pass

        return workspace_info

    def _get_x11_workspaces(self) -> Dict[str, Any]:
        """Get workspace info under X11"""
        workspace_info = {}
        
        try:
            # Try wmctrl
            result = subprocess.run(['wmctrl', '-d'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                workspaces = result.stdout.strip().split('\n')
                workspace_info['total'] = len(workspaces)
                workspace_info['names'] = []
                
                for line in workspaces:
                    parts = line.split()
                    if len(parts) >= 2:
                        if '*' in parts[1]:  # Current workspace
                            workspace_info['current'] = int(parts[0]) + 1
                        if len(parts) >= 9:
                            workspace_info['names'].append(' '.join(parts[8:]))
        except Exception:
            pass

        return workspace_info

    def _collect_active_windows(self) -> List[Dict[str, Any]]:
        """Collect information about active windows"""
        try:
            windows = []
            
            if os.environ.get('WAYLAND_DISPLAY'):
                windows = self._get_wayland_windows()
            else:
                windows = self._get_x11_windows()

            return windows

        except Exception as e:
            self.logger.error(f"Failed to collect active windows: {str(e)}")
            return [{'error': str(e)}]

    def _get_wayland_windows(self) -> List[Dict[str, Any]]:
        """Get window information under Wayland"""
        windows = []
        
        # Try swaymsg for Sway
        try:
            result = subprocess.run(['swaymsg', '-t', 'get_tree'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                import json
                tree = json.loads(result.stdout)
                windows = self._parse_sway_tree(tree)
        except Exception:
            pass

        return windows

    def _parse_sway_tree(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Sway window tree"""
        windows = []
        
        if node.get('type') == 'con' and node.get('name'):
            window_info = {
                'title': node['name'],
                'app_id': node.get('app_id', 'Unknown'),
                'focused': node.get('focused', False),
                'geometry': {
                    'x': node.get('rect', {}).get('x', 0),
                    'y': node.get('rect', {}).get('y', 0),
                    'width': node.get('rect', {}).get('width', 0),
                    'height': node.get('rect', {}).get('height', 0)
                },
                'workspace': node.get('workspace', 'Unknown')
            }
            windows.append(window_info)
        
        # Recursively parse child nodes
        for child in node.get('nodes', []):
            windows.extend(self._parse_sway_tree(child))
        
        for child in node.get('floating_nodes', []):
            windows.extend(self._parse_sway_tree(child))
        
        return windows

    def _get_x11_windows(self) -> List[Dict[str, Any]]:
        """Get window information under X11"""
        windows = []
        
        try:
            # Try wmctrl
            result = subprocess.run(['wmctrl', '-l', '-G'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(None, 7)
                    if len(parts) >= 8:
                        window_info = {
                            'window_id': parts[0],
                            'workspace': int(parts[1]),
                            'geometry': {
                                'x': int(parts[2]),
                                'y': int(parts[3]),
                                'width': int(parts[4]),
                                'height': int(parts[5])
                            },
                            'title': parts[7],
                            'hostname': parts[6]
                        }
                        windows.append(window_info)
        except Exception:
            pass

        return windows

    def _collect_input_devices(self) -> Dict[str, Any]:
        """Collect input device information"""
        try:
            input_info = {
                'keyboards': [],
                'mice': [],
                'touchpads': [],
                'other': []
            }

            # Try to get input devices from /proc/bus/input/devices
            try:
                with open('/proc/bus/input/devices', 'r') as f:
                    content = f.read()
                
                devices = content.split('\n\n')
                for device_block in devices:
                    if not device_block.strip():
                        continue
                    
                    device_info = {}
                    for line in device_block.split('\n'):
                        if line.startswith('N: Name='):
                            device_info['name'] = line.split('=', 1)[1].strip('"')
                        elif line.startswith('H: Handlers='):
                            device_info['handlers'] = line.split('=', 1)[1].strip()
                    
                    if 'name' in device_info:
                        name_lower = device_info['name'].lower()
                        if 'keyboard' in name_lower:
                            input_info['keyboards'].append(device_info)
                        elif 'mouse' in name_lower or 'pointer' in name_lower:
                            input_info['mice'].append(device_info)
                        elif 'touchpad' in name_lower or 'trackpad' in name_lower:
                            input_info['touchpads'].append(device_info)
                        else:
                            input_info['other'].append(device_info)
            
            except Exception:
                pass

            return input_info

        except Exception as e:
            self.logger.error(f"Failed to collect input devices: {str(e)}")
            return {'error': str(e)}

    def _collect_accessibility_info(self) -> Dict[str, Any]:
        """Collect accessibility settings information"""
        try:
            accessibility_info = {
                'screen_reader': False,
                'high_contrast': False,
                'large_text': False,
                'magnifier': False
            }

            # Try to get accessibility settings from gsettings
            try:
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.a11y', 'always-show-universal-access-status'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    accessibility_info['universal_access'] = 'true' in result.stdout.lower()
            except Exception:
                pass

            try:
                result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'text-scaling-factor'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    scaling = float(result.stdout.strip())
                    accessibility_info['large_text'] = scaling > 1.0
                    accessibility_info['text_scaling_factor'] = scaling
            except Exception:
                pass

            return accessibility_info

        except Exception as e:
            self.logger.error(f"Failed to collect accessibility info: {str(e)}")
            return {'error': str(e)}