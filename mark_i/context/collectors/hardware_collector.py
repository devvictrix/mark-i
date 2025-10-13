"""
Hardware Context Collector

Collects comprehensive hardware and performance information including CPU, memory, GPU, storage, and displays.
"""

import platform
import psutil
import subprocess
import logging
import os
from typing import Dict, Any, List

from .base_collector import BaseCollector


class HardwareCollector(BaseCollector):
    """Collects hardware specifications and performance metrics"""

    def __init__(self):
        super().__init__("Hardware Collector")

    def collect(self) -> Dict[str, Any]:
        """Collect comprehensive hardware information"""
        hardware_data = {
            'cpu': self._collect_cpu_info(),
            'memory': self._collect_memory_info(),
            'gpu': self._collect_gpu_info(),
            'storage': self._collect_storage_info(),
            'displays': self._collect_display_info(),
            'system': self._collect_system_info()
        }
        return hardware_data

    def get_refresh_interval(self) -> int:
        """Performance data changes frequently"""
        return 30

    def is_expensive(self) -> bool:
        """GPU detection can be expensive"""
        return True

    def _collect_cpu_info(self) -> Dict[str, Any]:
        """Collect CPU information and current usage"""
        try:
            cpu_info = {
                'model': platform.processor() or 'Unknown',
                'architecture': platform.machine(),
                'cores_physical': psutil.cpu_count(logical=False),
                'cores_logical': psutil.cpu_count(logical=True),
                'usage_percent': psutil.cpu_percent(interval=1),
                'frequency_current': 0,
                'frequency_max': 0,
                'temperature': None
            }

            # Get CPU frequency if available
            try:
                freq_info = psutil.cpu_freq()
                if freq_info:
                    cpu_info['frequency_current'] = round(freq_info.current, 2)
                    cpu_info['frequency_max'] = round(freq_info.max, 2)
            except Exception:
                pass

            # Get CPU temperature (Linux-specific)
            try:
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        for name, entries in temps.items():
                            if 'cpu' in name.lower() or 'core' in name.lower():
                                if entries:
                                    cpu_info['temperature'] = round(entries[0].current, 1)
                                    break
            except Exception:
                pass

            # Get detailed CPU model on Linux
            try:
                if platform.system() == 'Linux':
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if line.startswith('model name'):
                                cpu_info['model'] = line.split(':', 1)[1].strip()
                                break
            except Exception:
                pass

            return cpu_info

        except Exception as e:
            self.logger.error(f"Failed to collect CPU info: {str(e)}")
            return {'error': str(e)}

    def _collect_memory_info(self) -> Dict[str, Any]:
        """Collect memory information and usage"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'usage_percent': round(memory.percent, 1),
                'swap_total_gb': round(swap.total / (1024**3), 2),
                'swap_used_gb': round(swap.used / (1024**3), 2),
                'swap_usage_percent': round(swap.percent, 1) if swap.total > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to collect memory info: {str(e)}")
            return {'error': str(e)}

    def _collect_gpu_info(self) -> List[Dict[str, Any]]:
        """Collect GPU information"""
        gpus = []

        # Try NVIDIA GPUs
        try:
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=name,memory.total,driver_version,utilization.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 4:
                            gpus.append({
                                'name': parts[0],
                                'memory_gb': round(int(parts[1]) / 1024, 1),
                                'driver_version': parts[2],
                                'usage_percent': int(parts[3]),
                                'vendor': 'NVIDIA',
                                'type': 'discrete'
                            })
        except Exception:
            pass

        # Try generic GPU detection with lspci
        try:
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'VGA' in line or 'Display' in line:
                        gpu_name = line.split(': ', 1)[1] if ': ' in line else 'Unknown GPU'
                        if not any(gpu['name'] == gpu_name for gpu in gpus):
                            vendor = 'Intel' if 'Intel' in gpu_name else 'AMD' if 'AMD' in gpu_name else 'Unknown'
                            gpus.append({
                                'name': gpu_name,
                                'vendor': vendor,
                                'type': 'integrated' if vendor == 'Intel' else 'discrete'
                            })
        except Exception:
            pass

        return gpus if gpus else [{'name': 'No GPU detected', 'vendor': 'Unknown'}]

    def _collect_storage_info(self) -> List[Dict[str, Any]]:
        """Collect storage device information"""
        storage_devices = []

        try:
            disk_partitions = psutil.disk_partitions()
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    storage_devices.append({
                        'device': partition.device,
                        'mount_point': partition.mountpoint,
                        'filesystem': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'usage_percent': round((usage.used / usage.total) * 100, 1)
                    })
                except (PermissionError, OSError):
                    continue

        except Exception as e:
            self.logger.error(f"Failed to collect storage info: {str(e)}")
            return [{'error': str(e)}]

        return storage_devices

    def _collect_display_info(self) -> List[Dict[str, Any]]:
        """Collect comprehensive display information"""
        displays = []

        try:
            # Check if running under Wayland or X11
            if os.environ.get('WAYLAND_DISPLAY'):
                displays = self._get_wayland_displays()
            elif os.environ.get('DISPLAY'):
                displays = self._get_x11_displays()
            else:
                displays = self._get_fallback_displays()

        except Exception as e:
            self.logger.error(f"Failed to collect display info: {str(e)}")
            displays = [{'error': str(e)}]

        return displays

    def _get_wayland_displays(self) -> List[Dict[str, Any]]:
        """Get display info under Wayland"""
        displays = []
        
        # Try wlr-randr for wlroots-based compositors
        try:
            result = subprocess.run(['wlr-randr'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                current_display = {}
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(' '):
                        if current_display:
                            displays.append(current_display)
                        current_display = {'name': line.split()[0], 'connected': 'disconnected' not in line}
                    elif 'current' in line and '@' in line:
                        # Parse resolution and refresh rate
                        parts = line.split()
                        for part in parts:
                            if 'x' in part and '@' in part:
                                resolution, refresh = part.split('@')
                                current_display['resolution'] = resolution
                                current_display['refresh_rate'] = float(refresh.replace('Hz', ''))
                                break
                
                if current_display:
                    displays.append(current_display)
        except Exception:
            pass

        # Fallback: try to get basic info from environment
        if not displays:
            displays = [{
                'name': 'Wayland-Display',
                'resolution': 'Unknown',
                'connected': True,
                'session_type': 'wayland'
            }]

        return displays

    def _get_x11_displays(self) -> List[Dict[str, Any]]:
        """Get display info under X11"""
        displays = []
        
        try:
            result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ' connected' in line:
                        parts = line.split()
                        display_name = parts[0]
                        
                        display_info = {
                            'name': display_name,
                            'connected': True,
                            'primary': 'primary' in line,
                            'session_type': 'x11'
                        }
                        
                        # Find current resolution and position
                        for part in parts:
                            if 'x' in part and ('+' in part or part.endswith(')')):
                                if '+' in part:
                                    resolution_pos = part.split('+')
                                    display_info['resolution'] = resolution_pos[0]
                                    if len(resolution_pos) >= 3:
                                        display_info['position'] = {
                                            'x': int(resolution_pos[1]),
                                            'y': int(resolution_pos[2])
                                        }
                                else:
                                    display_info['resolution'] = part.replace('(', '').replace(')', '')
                                break
                        
                        displays.append(display_info)
                    elif ' disconnected' in line:
                        display_name = line.split()[0]
                        displays.append({
                            'name': display_name,
                            'connected': False,
                            'session_type': 'x11'
                        })
        except Exception:
            pass

        return displays

    def _get_fallback_displays(self) -> List[Dict[str, Any]]:
        """Get basic display info as fallback"""
        return [{
            'name': 'Display-0',
            'resolution': 'Unknown',
            'connected': True,
            'primary': True,
            'session_type': 'unknown'
        }]

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect general system information"""
        try:
            boot_time = psutil.boot_time()
            import time
            
            system_info = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'hostname': platform.node(),
                'boot_time': boot_time,
                'uptime_seconds': time.time() - boot_time,
                'python_version': platform.python_version(),
                'architecture': platform.architecture(),
                'machine': platform.machine(),
                'processor': platform.processor()
            }

            # Add environment info
            system_info['environment'] = {
                'display': os.environ.get('DISPLAY'),
                'wayland_display': os.environ.get('WAYLAND_DISPLAY'),
                'session_type': os.environ.get('XDG_SESSION_TYPE'),
                'desktop_session': os.environ.get('XDG_CURRENT_DESKTOP'),
                'user': os.environ.get('USER'),
                'home': os.environ.get('HOME'),
                'shell': os.environ.get('SHELL'),
                'lang': os.environ.get('LANG')
            }

            return system_info

        except Exception as e:
            self.logger.error(f"Failed to collect system info: {str(e)}")
            return {'error': str(e)}