"""
Network Context Collector

Monitors network connectivity, interfaces, and configuration information.
"""

import subprocess
import socket
import psutil
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_collector import BaseCollector


class NetworkCollector(BaseCollector):
    """Collects network connectivity and configuration context"""

    def __init__(self):
        super().__init__("Network Collector")

    def collect(self) -> Dict[str, Any]:
        """Collect comprehensive network information"""
        network_data = {
            'interfaces': self._collect_network_interfaces(),
            'connectivity': self._collect_connectivity_info(),
            'vpn': self._collect_vpn_info(),
            'firewall': self._collect_firewall_info(),
            'dns': self._collect_dns_info(),
            'routing': self._collect_routing_info()
        }
        return network_data

    def get_refresh_interval(self) -> int:
        """Network status changes frequently"""
        return 5

    def is_expensive(self) -> bool:
        """Network checks can involve external requests"""
        return True

    def _collect_network_interfaces(self) -> List[Dict[str, Any]]:
        """Collect network interface information"""
        interfaces = []
        
        try:
            # Get interface statistics
            net_if_stats = psutil.net_if_stats()
            net_if_addrs = psutil.net_if_addrs()
            
            for interface_name, stats in net_if_stats.items():
                interface_info = {
                    'name': interface_name,
                    'is_up': stats.isup,
                    'duplex': self._get_duplex_name(stats.duplex),
                    'speed_mbps': stats.speed if stats.speed > 0 else None,
                    'mtu': stats.mtu,
                    'addresses': []
                }
                
                # Get addresses for this interface
                if interface_name in net_if_addrs:
                    for addr in net_if_addrs[interface_name]:
                        addr_info = {
                            'family': self._get_address_family_name(addr.family),
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        }
                        interface_info['addresses'].append(addr_info)
                
                # Get additional interface details
                interface_info.update(self._get_interface_details(interface_name))
                
                interfaces.append(interface_info)
                
        except Exception as e:
            self.logger.error(f"Failed to collect network interfaces: {str(e)}")
            return [{'error': str(e)}]
        
        return interfaces

    def _get_duplex_name(self, duplex_value) -> str:
        """Convert duplex enum to string"""
        duplex_map = {
            1: 'half',
            2: 'full',
            0: 'unknown'
        }
        return duplex_map.get(duplex_value, 'unknown')

    def _get_address_family_name(self, family_value) -> str:
        """Convert address family to string"""
        family_map = {
            2: 'IPv4',
            10: 'IPv6',
            17: 'MAC'
        }
        return family_map.get(family_value, f'family_{family_value}')

    def _get_interface_details(self, interface_name: str) -> Dict[str, Any]:
        """Get additional interface details using system commands"""
        details = {
            'type': 'unknown',
            'driver': 'unknown',
            'wireless': False,
            'ssid': None,
            'signal_strength': None
        }
        
        try:
            # Check if it's a wireless interface
            if 'wl' in interface_name or 'wifi' in interface_name:
                details['type'] = 'wireless'
                details['wireless'] = True
                details.update(self._get_wireless_details(interface_name))
            elif 'eth' in interface_name or 'en' in interface_name:
                details['type'] = 'ethernet'
            elif 'lo' in interface_name:
                details['type'] = 'loopback'
            elif 'tun' in interface_name or 'tap' in interface_name:
                details['type'] = 'vpn'
            elif 'docker' in interface_name or 'br-' in interface_name:
                details['type'] = 'bridge'
            
            # Try to get driver information
            try:
                result = subprocess.run(['ethtool', '-i', interface_name], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('driver:'):
                            details['driver'] = line.split(':', 1)[1].strip()
                            break
            except Exception:
                pass
                
        except Exception as e:
            self.logger.debug(f"Failed to get details for interface {interface_name}: {str(e)}")
        
        return details

    def _get_wireless_details(self, interface_name: str) -> Dict[str, Any]:
        """Get wireless-specific details"""
        wireless_info = {}
        
        try:
            # Try iwconfig
            result = subprocess.run(['iwconfig', interface_name], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                output = result.stdout
                
                # Parse SSID
                if 'ESSID:' in output:
                    ssid_line = [line for line in output.split('\n') if 'ESSID:' in line][0]
                    ssid = ssid_line.split('ESSID:')[1].split()[0].strip('"')
                    if ssid != 'off/any':
                        wireless_info['ssid'] = ssid
                
                # Parse signal strength
                if 'Signal level=' in output:
                    signal_line = [line for line in output.split('\n') if 'Signal level=' in line][0]
                    signal_part = signal_line.split('Signal level=')[1].split()[0]
                    wireless_info['signal_strength'] = signal_part
                    
        except Exception:
            pass
        
        try:
            # Try nmcli as alternative
            result = subprocess.run(['nmcli', 'dev', 'show', interface_name], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'GENERAL.CONNECTION:' in line:
                        connection = line.split(':', 1)[1].strip()
                        if connection and connection != '--':
                            wireless_info['connection_name'] = connection
                            
        except Exception:
            pass
        
        return wireless_info

    def _collect_connectivity_info(self) -> Dict[str, Any]:
        """Collect internet connectivity information"""
        connectivity = {
            'internet_available': False,
            'dns_working': False,
            'public_ip': None,
            'gateway': None,
            'latency_ms': None,
            'connection_quality': 'unknown'
        }
        
        try:
            # Test basic connectivity
            connectivity['internet_available'] = self._test_internet_connectivity()
            connectivity['dns_working'] = self._test_dns_resolution()
            
            if connectivity['internet_available']:
                connectivity['public_ip'] = self._get_public_ip()
                connectivity['latency_ms'] = self._measure_latency()
                connectivity['connection_quality'] = self._assess_connection_quality(connectivity['latency_ms'])
            
            # Get gateway information
            connectivity['gateway'] = self._get_default_gateway()
            
            # Get DNS servers
            connectivity['dns_servers'] = self._get_dns_servers()
            
        except Exception as e:
            self.logger.error(f"Failed to collect connectivity info: {str(e)}")
            connectivity['error'] = str(e)
        
        return connectivity

    def _test_internet_connectivity(self) -> bool:
        """Test if internet is available"""
        try:
            # Try to connect to multiple reliable hosts
            test_hosts = [
                ('8.8.8.8', 53),  # Google DNS
                ('1.1.1.1', 53),  # Cloudflare DNS
                ('208.67.222.222', 53)  # OpenDNS
            ]
            
            for host, port in test_hosts:
                try:
                    socket.create_connection((host, port), timeout=3)
                    return True
                except Exception:
                    continue
            
            return False
            
        except Exception:
            return False

    def _test_dns_resolution(self) -> bool:
        """Test if DNS resolution is working"""
        try:
            socket.gethostbyname('google.com')
            return True
        except Exception:
            return False

    def _get_public_ip(self) -> Optional[str]:
        """Get public IP address"""
        try:
            # Try multiple IP detection services
            services = [
                'https://api.ipify.org',
                'https://icanhazip.com',
                'https://ipecho.net/plain'
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        return response.text.strip()
                except Exception:
                    continue
            
            return None
            
        except Exception:
            return None

    def _measure_latency(self) -> Optional[float]:
        """Measure network latency"""
        try:
            result = subprocess.run(['ping', '-c', '3', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse ping output for average latency
                for line in result.stdout.split('\n'):
                    if 'avg' in line and 'ms' in line:
                        # Extract average from line like: "rtt min/avg/max/mdev = 12.345/23.456/34.567/5.678 ms"
                        parts = line.split('=')[1].strip().split('/')
                        if len(parts) >= 2:
                            return float(parts[1])
            
            return None
            
        except Exception:
            return None

    def _assess_connection_quality(self, latency_ms: Optional[float]) -> str:
        """Assess connection quality based on latency"""
        if latency_ms is None:
            return 'unknown'
        
        if latency_ms < 20:
            return 'excellent'
        elif latency_ms < 50:
            return 'good'
        elif latency_ms < 100:
            return 'fair'
        else:
            return 'poor'

    def _get_default_gateway(self) -> Optional[str]:
        """Get default gateway IP"""
        try:
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'default via' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[2]
            
            return None
            
        except Exception:
            return None

    def _get_dns_servers(self) -> List[str]:
        """Get configured DNS servers"""
        dns_servers = []
        
        try:
            # Try reading /etc/resolv.conf
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('nameserver'):
                        parts = line.split()
                        if len(parts) >= 2:
                            dns_servers.append(parts[1])
                            
        except Exception:
            pass
        
        return dns_servers

    def _collect_vpn_info(self) -> Dict[str, Any]:
        """Collect VPN connection information"""
        vpn_info = {
            'active': False,
            'connections': [],
            'type': None
        }
        
        try:
            # Check for common VPN interfaces
            net_if_stats = psutil.net_if_stats()
            
            for interface_name in net_if_stats.keys():
                if any(vpn_prefix in interface_name for vpn_prefix in ['tun', 'tap', 'ppp', 'vpn']):
                    if net_if_stats[interface_name].isup:
                        vpn_info['active'] = True
                        vpn_info['connections'].append({
                            'interface': interface_name,
                            'type': self._detect_vpn_type(interface_name)
                        })
            
            # Try to get more VPN details using nmcli
            try:
                result = subprocess.run(['nmcli', 'connection', 'show', '--active'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n')[1:]:  # Skip header
                        if 'vpn' in line.lower():
                            parts = line.split()
                            if len(parts) >= 3:
                                vpn_info['connections'].append({
                                    'name': parts[0],
                                    'type': 'NetworkManager VPN',
                                    'device': parts[3] if len(parts) > 3 else 'unknown'
                                })
                                vpn_info['active'] = True
            except Exception:
                pass
                
        except Exception as e:
            self.logger.error(f"Failed to collect VPN info: {str(e)}")
            vpn_info['error'] = str(e)
        
        return vpn_info

    def _detect_vpn_type(self, interface_name: str) -> str:
        """Detect VPN type based on interface name"""
        if 'tun' in interface_name:
            return 'TUN (OpenVPN/WireGuard)'
        elif 'tap' in interface_name:
            return 'TAP (OpenVPN)'
        elif 'ppp' in interface_name:
            return 'PPP (PPTP/L2TP)'
        else:
            return 'Unknown VPN'

    def _collect_firewall_info(self) -> Dict[str, Any]:
        """Collect firewall status information"""
        firewall_info = {
            'enabled': False,
            'type': 'unknown',
            'status': 'unknown'
        }
        
        try:
            # Check UFW (Ubuntu Firewall)
            try:
                result = subprocess.run(['ufw', 'status'], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    output = result.stdout.lower()
                    firewall_info['type'] = 'ufw'
                    if 'status: active' in output:
                        firewall_info['enabled'] = True
                        firewall_info['status'] = 'active'
                    else:
                        firewall_info['status'] = 'inactive'
            except Exception:
                pass
            
            # Check iptables
            if firewall_info['type'] == 'unknown':
                try:
                    result = subprocess.run(['iptables', '-L'], capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        firewall_info['type'] = 'iptables'
                        # Simple check - if there are rules beyond default, firewall is likely active
                        lines = result.stdout.split('\n')
                        if len(lines) > 10:  # More than just default chains
                            firewall_info['enabled'] = True
                            firewall_info['status'] = 'active'
                except Exception:
                    pass
            
            # Check firewalld
            if firewall_info['type'] == 'unknown':
                try:
                    result = subprocess.run(['firewall-cmd', '--state'], capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        firewall_info['type'] = 'firewalld'
                        if 'running' in result.stdout.lower():
                            firewall_info['enabled'] = True
                            firewall_info['status'] = 'running'
                except Exception:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to collect firewall info: {str(e)}")
            firewall_info['error'] = str(e)
        
        return firewall_info

    def _collect_dns_info(self) -> Dict[str, Any]:
        """Collect DNS configuration information"""
        dns_info = {
            'servers': self._get_dns_servers(),
            'search_domains': [],
            'resolver_type': 'unknown'
        }
        
        try:
            # Get search domains from /etc/resolv.conf
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('search') or line.startswith('domain'):
                        parts = line.split()[1:]
                        dns_info['search_domains'].extend(parts)
            
            # Check if systemd-resolved is running
            try:
                result = subprocess.run(['systemctl', 'is-active', 'systemd-resolved'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and 'active' in result.stdout:
                    dns_info['resolver_type'] = 'systemd-resolved'
            except Exception:
                pass
                
        except Exception as e:
            self.logger.error(f"Failed to collect DNS info: {str(e)}")
            dns_info['error'] = str(e)
        
        return dns_info

    def _collect_routing_info(self) -> Dict[str, Any]:
        """Collect routing table information"""
        routing_info = {
            'default_route': None,
            'routes': []
        }
        
        try:
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        if line.startswith('default'):
                            routing_info['default_route'] = line.strip()
                        else:
                            routing_info['routes'].append(line.strip())
                            
        except Exception as e:
            self.logger.error(f"Failed to collect routing info: {str(e)}")
            routing_info['error'] = str(e)
        
        return routing_info