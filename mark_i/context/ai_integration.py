"""
MARK-I AI Context Integration

Production-ready module for integrating context data with AI systems.
Provides optimized context delivery for intelligent automation decisions.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .context_manager import ContextManager
from .collectors import (
    HardwareCollector,
    ApplicationCollector, 
    UICollector,
    NetworkCollector,
    UserCollector
)


class AIContextProvider:
    """Provides optimized context data for AI integration"""
    
    def __init__(self, auto_start: bool = True):
        """
        Initialize AI Context Provider
        
        Args:
            auto_start: If True, automatically start context collection
        """
        self.logger = logging.getLogger("mark_i.context.ai_integration")
        self.context_manager = ContextManager()
        self._is_initialized = False
        
        if auto_start:
            self.initialize()
    
    def initialize(self):
        """Initialize all context collectors"""
        if self._is_initialized:
            return
        
        collectors = [
            HardwareCollector(),
            ApplicationCollector(),
            UICollector(), 
            NetworkCollector(),
            UserCollector()
        ]
        
        for collector in collectors:
            self.context_manager.register_collector(collector)
        
        # Collect initial context
        self.context_manager.collect_all()
        self._is_initialized = True
        
        self.logger.info("AI Context Provider initialized with all collectors")
    
    def get_system_profile_for_ai(self) -> Dict[str, Any]:
        """
        Get comprehensive system profile for AI initialization
        
        Returns:
            Dictionary containing system profile optimized for AI consumption
        """
        context_data = self.context_manager.get_current_context()
        if not context_data:
            self.logger.warning("No cached context available, collecting fresh data")
            context_data = self.context_manager.collect_all()
        
        return self._create_ai_system_profile(context_data)
    
    def get_task_context_for_ai(self, task: str) -> Dict[str, Any]:
        """
        Get task-relevant context for AI task execution
        
        Args:
            task: The user task to be executed
            
        Returns:
            Dictionary containing task-relevant context
        """
        context_data = self.context_manager.get_current_context()
        if not context_data:
            context_data = self.context_manager.collect_all()
        
        return self._extract_task_context(task, context_data)
    
    def get_real_time_context_for_ai(self) -> Dict[str, Any]:
        """
        Get real-time context for immediate AI queries
        
        Returns:
            Dictionary containing current system state
        """
        # Force fresh collection for real-time data
        context_data = self.context_manager.collect_all(force_refresh=True)
        return self._create_real_time_context(context_data)
    
    def create_ai_prompt_with_context(self, user_message: str, include_full_context: bool = False) -> str:
        """
        Create AI prompt with appropriate context
        
        Args:
            user_message: The user's message/task
            include_full_context: If True, include comprehensive system context
            
        Returns:
            Formatted prompt string for AI
        """
        if include_full_context:
            system_profile = self.get_system_profile_for_ai()
            context_section = self._format_full_context_for_prompt(system_profile)
        else:
            task_context = self.get_task_context_for_ai(user_message)
            context_section = self._format_task_context_for_prompt(task_context)
        
        prompt = f"""MARK-I System Context:
{context_section}

User Request: "{user_message}"

Instructions:
- Use the provided system context to make intelligent decisions
- Adapt responses based on available capabilities and current state
- Consider system limitations and optimize suggestions accordingly
- Provide context-aware automation solutions

Respond with intelligent, system-aware assistance."""
        
        return prompt
    
    def start_background_monitoring(self, interval: int = 60):
        """
        Start background context monitoring
        
        Args:
            interval: Update interval in seconds
        """
        self.context_manager.start_background_collection(interval)
        self.logger.info(f"Started background context monitoring (interval: {interval}s)")
    
    def stop_background_monitoring(self):
        """Stop background context monitoring"""
        self.context_manager.stop_background_collection()
        self.logger.info("Stopped background context monitoring")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get high-level context summary
        
        Returns:
            Dictionary containing context summary
        """
        return self.context_manager.get_system_summary()
    
    def _create_ai_system_profile(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive system profile for AI"""
        profile = {
            'timestamp': context_data.get('collection_timestamp'),
            'system': {
                'platform': 'Unknown',
                'version': 'Unknown',
                'architecture': 'Unknown'
            },
            'hardware': {
                'cpu_cores': 0,
                'cpu_model': 'Unknown',
                'memory_total_gb': 0,
                'memory_usage_percent': 0,
                'gpu_available': False,
                'gpu_info': []
            },
            'network': {
                'internet_available': False,
                'connection_quality': 'unknown',
                'latency_ms': None
            },
            'user': {
                'username': 'unknown',
                'environment': 'unknown',
                'current_directory': 'unknown',
                'development_tools': []
            },
            'ui': {
                'desktop_environment': 'unknown',
                'session_type': 'unknown',
                'active_windows': 0
            }
        }
        
        # Extract data from collectors
        for collector_key, data in context_data.get('context', {}).items():
            if 'error' in data:
                continue
                
            if 'hardware' in collector_key:
                self._extract_hardware_profile(data, profile)
            elif 'network' in collector_key:
                self._extract_network_profile(data, profile)
            elif 'user' in collector_key:
                self._extract_user_profile(data, profile)
            elif 'ui' in collector_key:
                self._extract_ui_profile(data, profile)
        
        return profile
    
    def _extract_hardware_profile(self, data: Dict[str, Any], profile: Dict[str, Any]):
        """Extract hardware information for AI profile"""
        if 'cpu' in data:
            cpu = data['cpu']
            profile['hardware'].update({
                'cpu_cores': cpu.get('cores_logical', 0),
                'cpu_model': cpu.get('model', 'Unknown'),
                'cpu_usage_percent': cpu.get('usage_percent', 0)
            })
        
        if 'memory' in data:
            memory = data['memory']
            profile['hardware'].update({
                'memory_total_gb': memory.get('total_gb', 0),
                'memory_usage_percent': memory.get('usage_percent', 0)
            })
        
        if 'gpu' in data and data['gpu']:
            profile['hardware']['gpu_available'] = True
            profile['hardware']['gpu_info'] = [
                {'name': gpu.get('name', 'Unknown'), 'vendor': gpu.get('vendor', 'Unknown')}
                for gpu in data['gpu'] if 'error' not in gpu
            ]
        
        if 'system' in data:
            system = data['system']
            profile['system'].update({
                'platform': system.get('platform', 'Unknown'),
                'version': system.get('platform_release', 'Unknown'),
                'architecture': system.get('architecture', ['Unknown'])[0] if system.get('architecture') else 'Unknown'
            })
    
    def _extract_network_profile(self, data: Dict[str, Any], profile: Dict[str, Any]):
        """Extract network information for AI profile"""
        if 'connectivity' in data:
            conn = data['connectivity']
            profile['network'].update({
                'internet_available': conn.get('internet_available', False),
                'connection_quality': conn.get('connection_quality', 'unknown'),
                'latency_ms': conn.get('latency_ms')
            })
    
    def _extract_user_profile(self, data: Dict[str, Any], profile: Dict[str, Any]):
        """Extract user information for AI profile"""
        if 'profile' in data:
            user_profile = data['profile']
            profile['user']['username'] = user_profile.get('username', 'unknown')
        
        if 'working_context' in data:
            context = data['working_context']
            profile['user'].update({
                'current_directory': context.get('current_directory', 'unknown'),
                'development_tools': context.get('development_tools', [])
            })
        
        if 'locale' in data:
            locale = data['locale']
            profile['user']['environment'] = f"{locale.get('language', 'unknown')} / {locale.get('timezone', 'unknown')}"
    
    def _extract_ui_profile(self, data: Dict[str, Any], profile: Dict[str, Any]):
        """Extract UI information for AI profile"""
        if 'desktop_environment' in data:
            de = data['desktop_environment']
            profile['ui'].update({
                'desktop_environment': de.get('name', 'unknown'),
                'session_type': de.get('session_type', 'unknown')
            })
        
        if 'active_windows' in data:
            profile['ui']['active_windows'] = len(data['active_windows'])
    
    def _extract_task_context(self, task: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context relevant to specific task"""
        task_lower = task.lower()
        
        # Determine task category
        task_category = 'general'
        if any(word in task_lower for word in ['code', 'develop', 'program', 'script', 'git']):
            task_category = 'development'
        elif any(word in task_lower for word in ['network', 'internet', 'download', 'web']):
            task_category = 'network'
        elif any(word in task_lower for word in ['file', 'folder', 'directory', 'move', 'copy']):
            task_category = 'filesystem'
        elif any(word in task_lower for word in ['window', 'app', 'application', 'gui']):
            task_category = 'ui_automation'
        
        # Extract relevant context based on task category
        relevant_context = {
            'task_category': task_category,
            'capabilities': {},
            'current_state': {},
            'recommendations': []
        }
        
        for collector_key, data in context_data.get('context', {}).items():
            if 'error' in data:
                continue
            
            if task_category == 'development' and 'user' in collector_key:
                relevant_context['capabilities']['development_tools'] = data.get('working_context', {}).get('development_tools', [])
                relevant_context['current_state']['working_directory'] = data.get('working_context', {}).get('current_directory')
                
            elif task_category == 'network' and 'network' in collector_key:
                conn = data.get('connectivity', {})
                relevant_context['current_state']['internet_available'] = conn.get('internet_available', False)
                relevant_context['current_state']['connection_quality'] = conn.get('connection_quality', 'unknown')
                
            elif task_category == 'ui_automation' and 'ui' in collector_key:
                relevant_context['current_state']['desktop_environment'] = data.get('desktop_environment', {}).get('name', 'unknown')
                relevant_context['current_state']['active_windows'] = len(data.get('active_windows', []))
                
            # Always include hardware capabilities for performance considerations
            if 'hardware' in collector_key:
                hardware = {
                    'cpu_cores': data.get('cpu', {}).get('cores_logical', 0),
                    'memory_gb': data.get('memory', {}).get('total_gb', 0),
                    'cpu_usage': data.get('cpu', {}).get('usage_percent', 0)
                }
                relevant_context['capabilities']['hardware'] = hardware
        
        return relevant_context
    
    def _create_real_time_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create real-time context snapshot"""
        real_time = {
            'timestamp': datetime.now().isoformat(),
            'system_load': {},
            'active_processes': [],
            'network_status': {},
            'user_activity': {}
        }
        
        for collector_key, data in context_data.get('context', {}).items():
            if 'error' in data:
                continue
                
            if 'hardware' in collector_key:
                real_time['system_load'] = {
                    'cpu_percent': data.get('cpu', {}).get('usage_percent', 0),
                    'memory_percent': data.get('memory', {}).get('usage_percent', 0)
                }
            elif 'application' in collector_key:
                running = data.get('running', [])
                real_time['active_processes'] = [
                    {'name': proc['name'], 'cpu': proc['cpu_percent']}
                    for proc in running[:10]  # Top 10 processes
                ]
            elif 'network' in collector_key:
                conn = data.get('connectivity', {})
                real_time['network_status'] = {
                    'online': conn.get('internet_available', False),
                    'quality': conn.get('connection_quality', 'unknown')
                }
        
        return real_time
    
    def _format_full_context_for_prompt(self, system_profile: Dict[str, Any]) -> str:
        """Format full system profile for AI prompt"""
        return f"""
System: {system_profile['system']['platform']} {system_profile['system']['version']}
Hardware: {system_profile['hardware']['cpu_cores']}-core CPU, {system_profile['hardware']['memory_total_gb']:.1f}GB RAM
Network: {'Online' if system_profile['network']['internet_available'] else 'Offline'} ({system_profile['network']['connection_quality']})
User: {system_profile['user']['username']} in {system_profile['user']['current_directory']}
Environment: {system_profile['ui']['desktop_environment']} desktop
Development Tools: {', '.join(system_profile['user']['development_tools'][:5])}
"""
    
    def _format_task_context_for_prompt(self, task_context: Dict[str, Any]) -> str:
        """Format task-specific context for AI prompt"""
        context_lines = [
            f"Task Category: {task_context['task_category']}",
            f"System Capabilities: {json.dumps(task_context['capabilities'], indent=2)}",
            f"Current State: {json.dumps(task_context['current_state'], indent=2)}"
        ]
        return '\n'.join(context_lines)


# Global instance for easy access
_ai_context_provider = None

def get_ai_context_provider() -> AIContextProvider:
    """Get global AI context provider instance"""
    global _ai_context_provider
    if _ai_context_provider is None:
        _ai_context_provider = AIContextProvider()
    return _ai_context_provider